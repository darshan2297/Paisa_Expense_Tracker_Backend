"""FastAPI application factory.

`create_app()` builds and returns the configured FastAPI instance:
middleware stack, routers, exception handlers, and the APScheduler
start/stop lifecycle. Kept as a factory (rather than a bare module-level
`app`) so tests can construct fresh app instances with overridden
dependencies/settings if needed.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware

from app import scheduler
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.error_handling import ErrorHandlingMiddleware, register_exception_handlers
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.response_envelope import ResponseEnvelopeMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Start background jobs on boot, stop them cleanly on shutdown."""
    scheduler.start()
    yield
    scheduler.shutdown()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # --- Rate limiting (slowapi) setup ---
    # `app.state.limiter` + the RateLimitExceeded handler are required by
    # slowapi regardless of middleware; the middleware itself just applies
    # `default_limits` automatically to routes that don't specify their own.
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # Exception handlers run in Starlette's ExceptionMiddleware, which wraps
    # the router directly - i.e. innermost by construction, regardless of
    # add_middleware order below. Registering these here (rather than as a
    # custom middleware) is what gets us "closest to the route" for free.
    register_exception_handlers(app)

    # --- Middleware stack ---
    #
    # IMPORTANT: Starlette executes middleware added via `add_middleware()`
    # in REVERSE order for the request path - the LAST one added ends up as
    # the OUTERMOST layer (first to see the request, last to see the
    # response). We want, from outermost to innermost:
    #
    #     CORS -> RequestId -> RateLimit -> ResponseEnvelope -> ErrorHandling
    #
    # so we must call `add_middleware()` in the OPPOSITE order: innermost
    # first, outermost last.
    #
    #   1. ErrorHandlingMiddleware - innermost custom layer; a safety net
    #      that catches anything raised by the route/routing that isn't
    #      already handled by the exception handlers above.
    #   2. ResponseEnvelopeMiddleware - needs to see the final JSON body
    #      before it leaves the app, so it must sit outside ErrorHandling
    #      (error responses are already enveloped by the exception handlers
    #      and are detected/passed through unchanged) but inside everything
    #      else.
    #   3. SlowAPIMiddleware - rejects over-limit requests before they reach
    #      envelope/error wrapping.
    #   4. RequestIdMiddleware - must run early enough that the request id
    #      exists for every downstream layer (logging, error handling), so
    #      it sits outside rate limiting/envelope/error handling.
    #   5. CORSMiddleware - MUST be outermost so preflight `OPTIONS`
    #      requests are answered immediately and never reach any other
    #      middleware (auth, rate limiting, etc. would otherwise incorrectly
    #      apply to preflight requests).
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(ResponseEnvelopeMiddleware)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router)

    return app


app = create_app()
