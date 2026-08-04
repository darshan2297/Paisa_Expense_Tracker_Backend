"""Data access for the goals table."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.goals.models import Goal


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[Goal]:
    result = await session.execute(
        select(Goal)
        .where(Goal.user_id == user_id, Goal.deleted_at.is_(None))
        .order_by(Goal.is_emergency.desc(), Goal.name)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, goal_id: uuid.UUID, user_id: uuid.UUID) -> Goal | None:
    result = await session.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id, Goal.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_emergency(session: AsyncSession, user_id: uuid.UUID) -> Goal | None:
    result = await session.execute(
        select(Goal).where(
            Goal.user_id == user_id, Goal.is_emergency.is_(True), Goal.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()


async def create(
    session: AsyncSession,
    user_id: uuid.UUID,
    *,
    name: str,
    target_amount: Decimal,
    saved_amount: Decimal,
    monthly_contribution: Decimal,
    is_emergency: bool,
    due_day: int | None,
) -> Goal:
    goal = Goal(
        user_id=user_id,
        name=name,
        target_amount=target_amount,
        saved_amount=saved_amount,
        monthly_contribution=monthly_contribution,
        is_emergency=is_emergency,
        due_day=due_day,
    )
    session.add(goal)
    await session.flush()
    return goal


async def clear_emergency_flag(
    session: AsyncSession, user_id: uuid.UUID, except_id: uuid.UUID | None = None
) -> None:
    stmt = (
        update(Goal)
        .where(Goal.user_id == user_id, Goal.is_emergency.is_(True), Goal.deleted_at.is_(None))
        .values(is_emergency=False)
    )
    if except_id is not None:
        stmt = stmt.where(Goal.id != except_id)
    await session.execute(stmt)


async def soft_delete(session: AsyncSession, goal: Goal) -> None:
    goal.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
