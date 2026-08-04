"""Data access for the `categories` table.

Returns ORM objects (or `None`); never raises and never contains business
rules - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.categories.models import Category


async def list_categories(session: AsyncSession) -> list[Category]:
    result = await session.execute(
        select(Category)
        .where(Category.deleted_at.is_(None))
        .order_by(Category.kind, Category.sort_order)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, category_id: uuid.UUID | str) -> Category | None:
    result = await session.execute(
        select(Category).where(Category.id == category_id, Category.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()
