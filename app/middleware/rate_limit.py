"""Rate limiting via slowapi, backed by its default in-memory store.

Deliberately no Redis: per the project's Phase-0 architecture decision, this
single-process in-memory limiter is sufficient for now. If the app is ever
scaled to multiple processes/instances, this limiter becomes per-instance
(not globally shared) - revisit with a shared backend at that point.

`limiter` is registered on `app.state.limiter` in `app.main.create_app()`.
There is deliberately NO `SlowAPIMiddleware` installed (see the detailed
comment in `app.main.create_app()`: it subclasses `BaseHTTPMiddleware`,
which breaks async DB connections for any route it wraps). This means
routes do NOT get rate-limited automatically - every route that should be
rate limited must explicitly use one of the decorators below. There is no
implicit default; an un-decorated route is not rate limited at all.

    from app.middleware.rate_limit import default_limit, strict_limit

    @router.get("/transactions")
    @default_limit()
    async def list_transactions(request: Request, ...): ...

    @router.post("/auth/login")
    @strict_limit()
    async def login(request: Request, ...): ...

Note: slowapi requires the decorated endpoint to accept a `request: Request`
parameter so it can inspect the client key.
"""

from collections.abc import Callable

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.response import error_envelope

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])

# Stricter preset for sensitive, auth-style endpoints (login, refresh,
# change-password) to slow down brute-force/credential-stuffing attempts.
STRICT_RATE_LIMIT = "5/minute"


def default_limit() -> Callable:  # type: ignore[type-arg]
    """Decorator applying the project's standard rate limit
    (`Settings.RATE_LIMIT_DEFAULT`). Apply to every route that isn't
    sensitive enough to need `strict_limit()` instead - see module docstring.
    """
    return limiter.limit(settings.RATE_LIMIT_DEFAULT)


def strict_limit() -> Callable:  # type: ignore[type-arg]
    """Decorator applying the stricter auth-endpoint rate limit."""
    return limiter.limit(STRICT_RATE_LIMIT)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Convert slowapi's `RateLimitExceeded` into the standard error envelope
    (status 429), instead of slowapi's default plain-text response, so
    clients get a consistent response shape regardless of error source.
    """
    response = JSONResponse(
        status_code=429,
        content=error_envelope(status_code=429, message=f"Rate limit exceeded: {exc.detail}"),
    )
    # Preserve slowapi's Retry-After / X-RateLimit-* headers on the response.
    return request.app.state.limiter._inject_headers(  # type: ignore[no-any-return]
        response, request.state.view_rate_limit
    )
