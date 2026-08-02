"""Assigns a unique request id to every incoming request.

The id is:
  1. Stored on `request.state.request_id` for use by route handlers/dependencies.
  2. Pushed into the `request_id_ctx_var` contextvar so log lines emitted
     anywhere during this request are automatically tagged with it.
  3. Echoed back to the client as the `X-Request-ID` response header, so a
     client/ops engineer can correlate a specific response with server logs.

This middleware must run early in the chain (added so it ends up as the
second-outermost layer, right inside CORS) so the id exists before any
other middleware or route code that might want to log against it.
"""

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import request_id_ctx_var

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        token = request_id_ctx_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx_var.reset(token)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
