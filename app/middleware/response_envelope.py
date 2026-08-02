"""Wraps successful JSON responses in the standard envelope.

Route handlers are free to return plain Pydantic models / dicts without
knowing anything about the envelope shape — this middleware does the
wrapping uniformly. Responses that are already enveloped (produced by the
error-handling exception handlers, which build the envelope themselves
since they also need to set `success: False` / `errors`) or that aren't
JSON (e.g. streaming responses, redirects) are passed through untouched.

Must sit closer to the route than CORS/RequestId/RateLimit but outside
ErrorHandling, so it only ever sees the *final* body for successful
responses — error responses already exit through ErrorHandling before
reaching this layer on their way out.
"""

import json
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.response import success_envelope

_ENVELOPE_MARKER_KEYS = {"success", "status_code", "data", "message", "errors"}


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            # Not JSON (e.g. plain text, file download, redirect) - leave as-is.
            return response

        body_bytes = b"".join([section async for section in response.body_iterator])  # type: ignore[attr-defined]

        try:
            parsed = json.loads(body_bytes) if body_bytes else None
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not actually JSON-parseable despite the header; pass through unchanged.
            return Response(
                content=body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        if isinstance(parsed, dict) and _ENVELOPE_MARKER_KEYS.issubset(parsed.keys()):
            # Already enveloped upstream (e.g. by an exception handler) - don't double-wrap.
            envelope = parsed
        else:
            envelope = success_envelope(data=parsed, status_code=response.status_code)

        headers = dict(response.headers)
        headers.pop("content-length", None)  # let JSONResponse recompute this
        return JSONResponse(content=envelope, status_code=response.status_code, headers=headers)
