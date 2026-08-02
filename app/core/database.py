"""Async SQLAlchemy engine/session setup.

A single module-level engine and sessionmaker are created lazily and reused
for the lifetime of the process. `get_session()` is a FastAPI dependency
that yields an `AsyncSession` and guarantees it is closed (and any open
transaction rolled back on error) once the request finishes.
"""

from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    """Return the process-wide cached async engine.

    `pool_pre_ping=True` guards against stale connections (e.g. after a DB
    restart or idle-timeout disconnect) being handed out from the pool.
    """
    settings = get_settings()
    # Hosted Postgres providers (e.g. Neon) require SSL; asyncpg takes it via
    # connect_args rather than a `sslmode=` URL query param. See
    # Settings.DATABASE_SSL_REQUIRED and docs/DEPLOYMENT_GUIDE.md.
    connect_args = {"ssl": "require"} if settings.DATABASE_SSL_REQUIRED else {}
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.ENVIRONMENT == "dev",
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args,
    )


@lru_cache
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide cached session factory."""
    return async_sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped `AsyncSession`.

    Usage: `session: AsyncSession = Depends(get_session)`.
    Rolls back automatically if an exception propagates out of the route,
    and always closes the session at the end of the request.
    """
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
