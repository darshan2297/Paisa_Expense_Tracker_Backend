"""Data access for the `fixed_commitments` table.

Returns ORM objects (or `None`); never raises and never contains business
rules - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.fixed_commitments.models import FixedCommitment


async def list_by_user(session: AsyncSession, user_id: uuid.UUID | str) -> list[FixedCommitment]:
    result = await session.execute(
        select(FixedCommitment)
        .where(FixedCommitment.user_id == user_id, FixedCommitment.deleted_at.is_(None))
        .order_by(FixedCommitment.due_day)
    )
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, commitment_id: uuid.UUID | str, user_id: uuid.UUID | str
) -> FixedCommitment | None:
    result = await session.execute(
        select(FixedCommitment).where(
            FixedCommitment.id == commitment_id,
            FixedCommitment.user_id == user_id,
            FixedCommitment.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create(
    session: AsyncSession,
    user_id: uuid.UUID | str,
    name: str,
    category_id: uuid.UUID,
    amount: Decimal,
    due_day: int,
    kind: str,
) -> FixedCommitment:
    commitment = FixedCommitment(
        user_id=user_id, name=name, category_id=category_id, amount=amount, due_day=due_day, kind=kind
    )
    session.add(commitment)
    await session.flush()
    return commitment


async def soft_delete(session: AsyncSession, commitment: FixedCommitment) -> None:
    commitment.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
