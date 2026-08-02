"""Application-level exception hierarchy.

Route/service code should raise these instead of FastAPI's `HTTPException`
directly, so error handling (status code + envelope shape) stays centralized
in `app.middleware.error_handling`. Each exception carries a human-readable
`message` and an optional list of field-level `errors` (used mainly by
`ValidationError`).
"""

from typing import Any


class AppError(Exception):
    """Base class for all application-raised errors.

    Attributes:
        status_code: HTTP status code the error handler should map this to.
        message: Human-readable summary shown to the client.
        errors: Optional list of structured error details (e.g. per-field
            validation failures), surfaced in the response envelope's
            `errors` field.
    """

    status_code: int = 500

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        self.message = message
        self.errors = errors or []
        super().__init__(message)


class UnauthorizedError(AppError):
    """Raised when the caller isn't authenticated, or their credentials/token
    are missing, invalid, expired, or revoked. Maps to HTTP 401.
    """

    status_code = 401

    def __init__(
        self, message: str = "Not authenticated", errors: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(message, errors)


class NotFoundError(AppError):
    """Raised when a requested resource does not exist. Maps to HTTP 404."""

    status_code = 404

    def __init__(
        self, message: str = "Resource not found", errors: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(message, errors)


class ConflictError(AppError):
    """Raised on a state conflict (e.g. duplicate unique key). Maps to HTTP 409."""

    status_code = 409

    def __init__(
        self, message: str = "Conflict", errors: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(message, errors)


class ForbiddenError(AppError):
    """Raised when the caller is authenticated but not authorized. Maps to HTTP 403."""

    status_code = 403

    def __init__(
        self, message: str = "Forbidden", errors: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(message, errors)


class ValidationError(AppError):
    """Raised for domain-level validation failures. Maps to HTTP 422."""

    status_code = 422

    def __init__(
        self, message: str = "Validation failed", errors: list[dict[str, Any]] | None = None
    ) -> None:
        super().__init__(message, errors)
