"""Data access for bills."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.bills.models import Bill


async def list_by_user(session: AsyncSession, user_id: uuid.UUID | str) -> list[Bill]:
    result = await session.execute(
        select(Bill)
        .where(Bill.user_id == user_id, Bill.deleted_at.is_(None))
        .order_by(Bill.due_date)
    )
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, bill_id: uuid.UUID | str, user_id: uuid.UUID | str
) -> Bill | None:
    result = await session.execute(
        select(Bill).where(
            Bill.id == bill_id,
            Bill.user_id == user_id,
            Bill.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create(
    session: AsyncSession,
    user_id: uuid.UUID | str,
    name: str,
    kind: str,
    amount: Decimal,
    due_date: dt.date,
    frequency: str,
    auto_pay: bool,
    lead_days: int,
    note: str | None,
) -> Bill:
    bill = Bill(
        user_id=user_id,
        name=name,
        kind=kind,
        amount=amount,
        due_date=due_date,
        frequency=frequency,
        auto_pay=auto_pay,
        lead_days=lead_days,
        note=note,
    )
    session.add(bill)
    await session.flush()
    return bill


async def soft_delete(session: AsyncSession, bill: Bill) -> None:
    bill.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
