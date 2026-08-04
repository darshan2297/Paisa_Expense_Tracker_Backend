"""Business logic for categories.

Receives/returns plain values or Pydantic schemas; never constructs an
`HTTPException` - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.categories import repository
from app.api.v1.categories.schemas import CategoryResponse
from app.core.cache import cache_get, cache_set
from app.core.config import get_settings

_CATEGORIES_CACHE_NS = "categories"
_CATEGORIES_CACHE_KEY = "all"
_CATEGORIES_TTL = 3600


async def list_categories(session: AsyncSession) -> list[CategoryResponse]:
    settings = get_settings()
    if settings.ENVIRONMENT != "test":
        cached = await cache_get(_CATEGORIES_CACHE_NS, _CATEGORIES_CACHE_KEY)
        if cached is not None:
            return [CategoryResponse.model_validate(item) for item in cached]

    categories = await repository.list_categories(session)
    responses = [CategoryResponse.model_validate(c) for c in categories]
    if settings.ENVIRONMENT != "test":
        await cache_set(
            _CATEGORIES_CACHE_NS,
            _CATEGORIES_CACHE_KEY,
            [r.model_dump(mode="json") for r in responses],
            ttl_seconds=_CATEGORIES_TTL,
        )
    return responses


async def get_category(session: AsyncSession, category_id: uuid.UUID | str) -> CategoryResponse | None:
    """Used by other feature modules (transactions, fixed_commitments) via
    `app.deps` to resolve category display info (name/color/kind) without
    an ORM-level cross-module join - see docs/DEVELOPER_PHILOSOPHY.md §2.2.
    """
    category = await repository.get_by_id(session, category_id)
    return CategoryResponse.model_validate(category) if category else None
