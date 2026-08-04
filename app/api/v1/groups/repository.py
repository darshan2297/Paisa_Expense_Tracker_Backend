"""Data access for expense groups."""

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.groups.models import ExpenseGroup, GroupExpense, GroupSettlement


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[ExpenseGroup]:
    result = await session.execute(
        select(ExpenseGroup)
        .where(ExpenseGroup.user_id == user_id, ExpenseGroup.deleted_at.is_(None))
        .options(
            selectinload(ExpenseGroup.expenses),
            selectinload(ExpenseGroup.settlements),
        )
        .order_by(ExpenseGroup.name)
    )
    return list(result.scalars().unique().all())


async def get_by_id(
    session: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> ExpenseGroup | None:
    result = await session.execute(
        select(ExpenseGroup)
        .where(
            ExpenseGroup.id == group_id,
            ExpenseGroup.user_id == user_id,
            ExpenseGroup.deleted_at.is_(None),
        )
        .options(
            selectinload(ExpenseGroup.expenses),
            selectinload(ExpenseGroup.settlements),
        )
    )
    return result.scalar_one_or_none()


async def create_group(session: AsyncSession, user_id: uuid.UUID, **kwargs: object) -> ExpenseGroup:
    group = ExpenseGroup(user_id=user_id, **kwargs)
    session.add(group)
    await session.flush()
    return group


async def soft_delete_group(session: AsyncSession, group: ExpenseGroup) -> None:
    group.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()


async def create_expense(
    session: AsyncSession, group_id: uuid.UUID, **kwargs: object
) -> GroupExpense:
    expense = GroupExpense(group_id=group_id, **kwargs)
    session.add(expense)
    await session.flush()
    return expense


async def get_expense(
    session: AsyncSession, expense_id: uuid.UUID, group_id: uuid.UUID
) -> GroupExpense | None:
    result = await session.execute(
        select(GroupExpense).where(
            GroupExpense.id == expense_id,
            GroupExpense.group_id == group_id,
            GroupExpense.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def soft_delete_expense(session: AsyncSession, expense: GroupExpense) -> None:
    expense.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()


async def create_settlement(
    session: AsyncSession, group_id: uuid.UUID, **kwargs: object
) -> GroupSettlement:
    settlement = GroupSettlement(group_id=group_id, **kwargs)
    session.add(settlement)
    await session.flush()
    return settlement


async def get_settlement(
    session: AsyncSession, settlement_id: uuid.UUID, group_id: uuid.UUID
) -> GroupSettlement | None:
    result = await session.execute(
        select(GroupSettlement).where(
            GroupSettlement.id == settlement_id,
            GroupSettlement.group_id == group_id,
            GroupSettlement.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def soft_delete_settlement(session: AsyncSession, settlement: GroupSettlement) -> None:
    settlement.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
