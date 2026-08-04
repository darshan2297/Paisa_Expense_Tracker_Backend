"""Data access for investments."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.investments.models import Investment


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[Investment]:
    result = await session.execute(
        select(Investment)
        .where(Investment.user_id == user_id, Investment.deleted_at.is_(None))
        .order_by(Investment.name)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, investment_id: uuid.UUID, user_id: uuid.UUID) -> Investment | None:
    result = await session.execute(
        select(Investment).where(
            Investment.id == investment_id,
            Investment.user_id == user_id,
            Investment.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, user_id: uuid.UUID, **kwargs: object) -> Investment:
    inv = Investment(user_id=user_id, **kwargs)  # type: ignore[arg-type]
    session.add(inv)
    await session.flush()
    return inv


async def soft_delete(session: AsyncSession, investment: Investment) -> None:
    investment.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
