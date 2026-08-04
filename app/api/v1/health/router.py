"""Health-check endpoints.

`/health/live` is dependency-free liveness. `/health/ready` pings Postgres
and Redis. `/health` is a backward-compatible alias for live.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.redis import ping_redis

router = APIRouter()


def _live_payload() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/live", summary="Liveness check")
async def health_live() -> dict[str, str]:
    return _live_payload()


@router.get("/health", summary="Liveness check (legacy alias)")
async def health_check() -> dict[str, str]:
    return _live_payload()


@router.get("/health/ready", summary="Readiness check (Postgres + Redis)")
async def health_ready(session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    settings = get_settings()
    db_ok = False
    redis_ok = await ping_redis()
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    operational = db_ok and redis_ok
    return {
        "status": "ok" if operational else "degraded",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database": db_ok,
            "redis": redis_ok,
        },
    }
