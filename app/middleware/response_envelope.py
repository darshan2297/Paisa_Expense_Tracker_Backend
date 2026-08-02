"""Wraps successful JSON responses in the standard envelope.

Route handlers are free to return plain Pydantic models / dicts without
knowing anything about the envelope shape — this middleware does the
wrapping uniformly. Responses that are already enveloped (produced by the
error-handling exception handlers, which build the envelope themselves
since they also need to set `success: False` / `errors`), that aren't JSON
(e.g. streaming responses, redirects), or that carry no body (e.g. a `204`)
are passed through untouched.

Must sit closer to the route than CORS/RequestId/RateLimit but outside
ErrorHandling, so it only ever sees the *final* body for successful
responses — error responses already exit through ErrorHandling before
reaching this layer on their way out.

Implemented as a pure ASGI middleware, not a `BaseHTTPMiddleware` subclass -
see `app.middleware.request_id`'s module docstring for why: BaseHTTPMiddleware
runs the downstream app in a separate anyio task, which breaks asyncpg/
SQLAlchemy-async connections used by any route this middleware wraps.
"""

import json
from collections.abc import Awaitable, Callable

from starlette.types import Message, Receive, Scope, Send

from app.core.response import success_envelope

_ENVELOPE_MARKER_KEYS = {"success", "status_code", "data", "message", "errors"}


def _header_value(headers: list[tuple[bytes, bytes]], name: bytes) -> bytes:
    for key, value in headers:
        if key.lower() == name:
            return value
    return b""


def _without_header(headers: list[tuple[bytes, bytes]], name: bytes) -> list[tuple[bytes, bytes]]:
    return [(k, v) for k, v in headers if k.lower() != name]


class ResponseEnvelopeMiddleware:
    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]]) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_message: Message | None = None
        body_chunks: list[bytes] = []

        async def send_wrapper(message: Message) -> None:
            nonlocal start_message

            if message["type"] == "http.response.start":
                # Deferred, not forwarded yet - we don't know the final body
                # (and therefore the final Content-Length) until all
                # `http.response.body` chunks have arrived.
                start_message = message
                return

            if message["type"] != "http.response.body":
                await send(message)
                return

            body_chunks.append(message.get("body", b""))
            if message.get("more_body", False):
                return  # more chunks still coming

            assert start_message is not None
            await _finalize(start_message, b"".join(body_chunks), send)

        await self.app(scope, receive, send_wrapper)


async def _finalize(start_message: Message, body: bytes, send: Send) -> None:
    status_code = start_message["status"]
    headers: list[tuple[bytes, bytes]] = list(start_message.get("headers", []))
    content_type = _header_value(headers, b"content-type").decode("latin-1")

    if "application/json" not in content_type or not body:
        # Not JSON, or genuinely empty (e.g. a 204) - pass through unchanged.
        await send(start_message)
        await send({"type": "http.response.body", "body": body, "more_body": False})
        return

    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Claims to be JSON but isn't parseable - pass through unchanged
        # rather than raise, since we can't do anything better here.
        await send(start_message)
        await send({"type": "http.response.body", "body": body, "more_body": False})
        return

    if isinstance(parsed, dict) and _ENVELOPE_MARKER_KEYS.issubset(parsed.keys()):
        # Already enveloped upstream (e.g. by an exception handler) - don't double-wrap.
        envelope = parsed
    else:
        envelope = success_envelope(data=parsed, status_code=status_code)

    new_body = json.dumps(envelope).encode("utf-8")
    new_headers = _without_header(headers, b"content-length")
    new_headers.append((b"content-length", str(len(new_body)).encode("latin-1")))

    await send({**start_message, "headers": new_headers})
    await send({"type": "http.response.body", "body": new_body, "more_body": False})
