"""Data access for insurance policies."""

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.policies.models import Policy


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[Policy]:
    result = await session.execute(
        select(Policy)
        .where(Policy.user_id == user_id, Policy.deleted_at.is_(None))
        .order_by(Policy.renewal_date)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, policy_id: uuid.UUID, user_id: uuid.UUID) -> Policy | None:
    result = await session.execute(
        select(Policy).where(
            Policy.id == policy_id, Policy.user_id == user_id, Policy.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, user_id: uuid.UUID, **kwargs: object) -> Policy:
    policy = Policy(user_id=user_id, **kwargs)  # type: ignore[arg-type]
    session.add(policy)
    await session.flush()
    return policy


async def soft_delete(session: AsyncSession, policy: Policy) -> None:
    policy.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
