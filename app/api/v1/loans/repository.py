"""Data access for loans."""

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.loans.models import Loan


async def list_by_user(session: AsyncSession, user_id: uuid.UUID) -> list[Loan]:
    result = await session.execute(
        select(Loan).where(Loan.user_id == user_id, Loan.deleted_at.is_(None)).order_by(Loan.name)
    )
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, loan_id: uuid.UUID, user_id: uuid.UUID) -> Loan | None:
    result = await session.execute(
        select(Loan).where(Loan.id == loan_id, Loan.user_id == user_id, Loan.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, user_id: uuid.UUID, **kwargs: object) -> Loan:
    loan = Loan(user_id=user_id, **kwargs)
    session.add(loan)
    await session.flush()
    return loan


async def soft_delete(session: AsyncSession, loan: Loan) -> None:
    loan.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
