"""Standard response envelope used across the entire API.

Every JSON response (success or error) is shaped as:

    {
        "success": bool,
        "status_code": int,
        "data": <payload | null>,
        "message": <str | null>,
        "errors": <list | null>
    }

Route handlers may return plain data/Pydantic models — the
`response_envelope` middleware wraps them automatically. The helpers here
exist for the (fewer) cases where a route or exception handler wants to
build the envelope explicitly, e.g. from within an exception handler where
there is no middleware pass left to run.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Envelope(BaseModel, Generic[T]):
    """Typed response envelope, generic over the `data` payload type."""

    success: bool
    status_code: int
    data: T | None = None
    message: str | None = None
    errors: list[dict[str, Any]] | None = None


def success_envelope(
    data: Any = None,
    *,
    status_code: int = 200,
    message: str | None = None,
) -> dict[str, Any]:
    """Build a success envelope dict."""
    return {
        "success": True,
        "status_code": status_code,
        "data": data,
        "message": message,
        "errors": None,
    }


def error_envelope(
    *,
    status_code: int,
    message: str,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build an error envelope dict."""
    return {
        "success": False,
        "status_code": status_code,
        "data": None,
        "message": message,
        "errors": errors or [],
    }
