"""Data access for milestones."""

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.milestones.models import Milestone


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[Milestone]:
    result = await session.execute(
        select(Milestone)
        .where(Milestone.user_id == user_id, Milestone.deleted_at.is_(None))
        .order_by(Milestone.date.desc())
    )
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, milestone_id: uuid.UUID, user_id: uuid.UUID
) -> Milestone | None:
    result = await session.execute(
        select(Milestone).where(
            Milestone.id == milestone_id,
            Milestone.user_id == user_id,
            Milestone.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, user_id: uuid.UUID, **kwargs: object) -> Milestone:
    m = Milestone(user_id=user_id, **kwargs)
    session.add(m)
    await session.flush()
    return m


async def soft_delete(session: AsyncSession, milestone: Milestone) -> None:
    milestone.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
