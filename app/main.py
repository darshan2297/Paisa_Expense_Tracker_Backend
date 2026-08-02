"""FastAPI application factory.

`create_app()` builds and returns the configured FastAPI instance:
middleware stack, routers, exception handlers, and Redis lifecycle.
Background jobs run via Celery (separate worker process), not in-process.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from app.api.portal.router import portal_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.redis import close_redis
from app.middleware.error_handling import ErrorHandlingMiddleware, register_exception_handlers
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.response_envelope import ResponseEnvelopeMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await close_redis()


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore[arg-type]

    register_exception_handlers(app)

    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(ResponseEnvelopeMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(portal_router)
    app.include_router(api_v1_router)

    return app


app = create_app()
