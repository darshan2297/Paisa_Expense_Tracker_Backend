"""Thin cache helpers on top of Redis.

Financial data (transactions, summaries) must never be cached here — only
safe read-mostly payloads like the seeded category taxonomy.
"""

import json
from typing import Any

from app.core.config import get_settings
from app.core.redis import get_redis


def _key(namespace: str, key: str) -> str:
    return f"paisa:{namespace}:{key}"


async def cache_get(namespace: str, key: str) -> Any | None:
    try:
        raw = await get_redis().get(_key(namespace, key))
    except Exception:
        return None
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(namespace: str, key: str, value: Any, ttl_seconds: int | None = None) -> None:
    settings = get_settings()
    ttl = ttl_seconds if ttl_seconds is not None else settings.CACHE_DEFAULT_TTL_SECONDS
    try:
        await get_redis().set(_key(namespace, key), json.dumps(value, default=str), ex=ttl)
    except Exception:
        return


async def cache_delete(namespace: str, key: str) -> None:
    try:
        await get_redis().delete(_key(namespace, key))
    except Exception:
        return
