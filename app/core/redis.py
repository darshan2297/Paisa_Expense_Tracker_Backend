"""Async Redis client singleton.

Used by the API process for caching. Celery workers use the sync redis client
via Celery's own connection pool.
"""

from functools import lru_cache

import redis.asyncio as aioredis

from app.core.config import get_settings


@lru_cache
def get_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)


async def ping_redis() -> bool:
    try:
        redis = get_redis()
        return bool(await redis.ping())
    except Exception:
        return False


async def close_redis() -> None:
    if get_redis.cache_info().currsize:
        redis = get_redis()
        await redis.aclose()
        get_redis.cache_clear()
