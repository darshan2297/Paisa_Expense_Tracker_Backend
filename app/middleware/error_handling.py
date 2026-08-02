"""Centralized error handling.

Two complementary layers:

1. `register_exception_handlers(app)` registers FastAPI/Starlette exception
   handlers for our `AppError` hierarchy plus the framework's own
   `HTTPException` / `RequestValidationError`. These run in Starlette's
   `ExceptionMiddleware`, which is *innermost* by construction (it wraps the
   router directly) - exactly where we want error formatting to happen,
   closest to the route.

2. `ErrorHandlingMiddleware` is a last-resort safety net added as the
   innermost custom middleware (via `add_middleware`, added first so it
   ends up just outside the exception-handler layer). It catches anything
   that still escapes as a raised exception (bugs in other middleware,
   truly unexpected errors) and turns it into a logged 500 response instead
   of letting Starlette's default `ServerErrorMiddleware` return a bare
   unstructured error.

Both paths build the same envelope shape via `app.core.response.error_envelope`.
"""

import logging
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.exceptions import AppError
from app.core.response import error_envelope

logger = logging.getLogger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle our own `AppError` hierarchy (NotFoundError, ConflictError, etc.)."""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(status_code=exc.status_code, message=exc.message, errors=exc.errors),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle FastAPI/Starlette's built-in `HTTPException` (e.g. raised by
    dependencies, or 404 for an unmatched route) with the same envelope shape.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=error_envelope(status_code=exc.status_code, message=str(exc.detail)),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic/FastAPI request validation errors with field-level detail."""
    errors = [
        {"loc": list(err["loc"]), "msg": err["msg"], "type": err["type"]} for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_envelope(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            errors=errors,
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for anything not covered above. Logs with the request id and
    never leaks internal details (message, stack trace) to the client.
    """
    logger.exception(
        "Unhandled exception while processing request", extra={"request_id": _request_id(request)}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_envelope(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Internal server error",
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Wire all exception handlers onto the FastAPI app. Call once from `create_app()`."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Last-resort safety net; see module docstring."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        try:
            return await call_next(request)
        except Exception:
            logger.exception(
                "Unhandled exception escaped routing/exception handlers",
                extra={"request_id": _request_id(request)},
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_envelope(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Internal server error",
                ),
            )
