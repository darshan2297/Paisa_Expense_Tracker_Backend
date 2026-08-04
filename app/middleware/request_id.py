"""Assigns a unique request id to every incoming request.

The id is:
  1. Stored on `scope["state"]["request_id"]` (readable as
     `request.state.request_id` in routes/dependencies).
  2. Pushed into the `request_id_ctx_var` contextvar so log lines emitted
     anywhere during this request are automatically tagged with it.
  3. Echoed back to the client as the `X-Request-ID` response header, so a
     client/ops engineer can correlate a specific response with server logs.

This middleware must run early in the chain (added so it ends up as the
second-outermost layer, right inside CORS) so the id exists before any
other middleware or route code that might want to log against it.

Implemented as a pure ASGI middleware (raw `__call__(scope, receive, send)`),
NOT a `starlette.middleware.base.BaseHTTPMiddleware` subclass. BaseHTTPMiddleware
runs the downstream app in a separate anyio task (via its `call_next`
implementation) from the one the middleware itself runs in - which breaks
asyncpg/SQLAlchemy-async connections if anything downstream awaits a
connection checked out in the "wrong" task ("Future attached to a different
loop" / "got result for unknown protocol state"). Every custom middleware in
this stack (`request_id`, `response_envelope`, `error_handling`) is written
as pure ASGI for exactly this reason - see the sibling modules' docstrings.
"""

import uuid
from collections.abc import Awaitable, Callable

from starlette.types import Message, Receive, Scope, Send

from app.core.logging import request_id_ctx_var

REQUEST_ID_HEADER = b"x-request-id"


class RequestIdMiddleware:
    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_ctx_var.set(request_id)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((REQUEST_ID_HEADER, request_id.encode("ascii")))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_id_ctx_var.reset(token)
