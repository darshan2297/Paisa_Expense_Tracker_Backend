"""Data access for the `transactions` table.

Returns ORM objects (or `None`)/plain aggregates; never raises and never
contains business rules - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import calendar
import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.transactions.models import Transaction, TransactionType
from app.core.pagination import PageParams


def month_bounds(month: str) -> tuple[dt.date, dt.date]:
    """First/last calendar day of a "YYYY-MM" month string."""
    year, mon = (int(part) for part in month.split("-"))
    start = dt.date(year, mon, 1)
    end = dt.date(year, mon, calendar.monthrange(year, mon)[1])
    return start, end


def _scope(
    stmt: Select[Any],
    user_id: uuid.UUID | str,
    start: dt.date,
    end: dt.date,
    type_filter: str | None,
    query: str | None,
    matching_category_ids: list[uuid.UUID] | None,
) -> Select[Any]:
    stmt = stmt.where(
        Transaction.user_id == user_id,
        Transaction.deleted_at.is_(None),
        Transaction.date >= start,
        Transaction.date <= end,
    )
    if type_filter:
        stmt = stmt.where(Transaction.type == type_filter)
    if query:
        note_match = Transaction.note.ilike(f"%{query}%")
        if matching_category_ids:
            stmt = stmt.where(note_match | Transaction.category_id.in_(matching_category_ids))
        else:
            stmt = stmt.where(note_match)
    return stmt


async def list_transactions(
    session: AsyncSession,
    user_id: uuid.UUID | str,
    month: str,
    type_filter: str | None,
    query: str | None,
    matching_category_ids: list[uuid.UUID] | None,
    params: PageParams,
) -> tuple[list[Transaction], int]:
    start, end = month_bounds(month)
    count_stmt = _scope(
        select(func.count()).select_from(Transaction),
        user_id,
        start,
        end,
        type_filter,
        query,
        matching_category_ids,
    )
    total = (await session.execute(count_stmt)).scalar_one()

    rows_stmt = (
        _scope(select(Transaction), user_id, start, end, type_filter, query, matching_category_ids)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(params.size)
        .offset(params.offset)
    )
    rows = (await session.execute(rows_stmt)).scalars().all()
    return list(rows), total


async def list_recent(
    session: AsyncSession, user_id: uuid.UUID | str, month: str, limit: int = 6
) -> list[Transaction]:
    start, end = month_bounds(month)
    stmt = (
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.date >= start,
            Transaction.date <= end,
        )
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


def _cash_relevant_filter():
    """Cash has left the bank for: non-card expenses, or card *payments*.

    Card *spends* raise outstanding (liability) but must not also reduce cash
    — otherwise net worth is hit twice. Payments (`note` contains 'payment')
    are the moment cash actually leaves.
    """
    from sqlalchemy import or_

    return or_(
        Transaction.type != TransactionType.EXPENSE.value,
        Transaction.card_id.is_(None),
        Transaction.note.ilike("%payment%"),
    )


async def sum_by_type(
    session: AsyncSession, user_id: uuid.UUID | str, month: str
) -> dict[str, Decimal]:
    start, end = month_bounds(month)
    stmt = (
        select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.date >= start,
            Transaction.date <= end,
            _cash_relevant_filter(),
        )
        .group_by(Transaction.type)
    )
    rows = (await session.execute(stmt)).all()
    return {row[0]: Decimal(row[1]) for row in rows}


async def sum_by_type_all_time(
    session: AsyncSession, user_id: uuid.UUID | str
) -> dict[str, Decimal]:
    """Same as `sum_by_type` but with no date filter - the all-time
    income/expense totals a net-cash figure needs (see net_worth service),
    as opposed to `sum_by_type`'s single-month scope used by the monthly
    summary screens.
    """
    stmt = (
        select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            _cash_relevant_filter(),
        )
        .group_by(Transaction.type)
    )
    rows = (await session.execute(stmt)).all()
    return {row[0]: Decimal(row[1]) for row in rows}


async def sum_expense_by_category(
    session: AsyncSession, user_id: uuid.UUID | str, month: str, card_only: bool = False
) -> list[tuple[uuid.UUID, Decimal]]:
    start, end = month_bounds(month)
    conditions = [
        Transaction.user_id == user_id,
        Transaction.deleted_at.is_(None),
        Transaction.type == TransactionType.EXPENSE.value,
        Transaction.date >= start,
        Transaction.date <= end,
    ]
    if card_only:
        # Card *spend* only — exclude repayments so "Category spending on
        # cards" is not inflated by Pay full / Pay minimum / Pay EMI.
        conditions.append(Transaction.card_id.isnot(None))
        conditions.append(~Transaction.note.ilike("%payment%"))
    stmt = (
        select(Transaction.category_id, func.sum(Transaction.amount))
        .where(*conditions)
        .group_by(Transaction.category_id)
        .order_by(func.sum(Transaction.amount).desc())
    )
    return [(row[0], Decimal(row[1])) for row in (await session.execute(stmt)).all()]


async def create_transaction(session: AsyncSession, **fields: object) -> Transaction:
    transaction = Transaction(**fields)
    session.add(transaction)
    await session.flush()
    return transaction


async def get_by_id(
    session: AsyncSession, transaction_id: uuid.UUID | str, user_id: uuid.UUID | str
) -> Transaction | None:
    result = await session.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def soft_delete(session: AsyncSession, transaction: Transaction) -> None:
    transaction.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()


async def get_by_id_unscoped(
    session: AsyncSession, transaction_id: uuid.UUID | str
) -> Transaction | None:
    """No `user_id`/ownership filter - used only for the fixed-commitments
    "toggle paid" flow, which resolves the transaction id from a commitment
    it already verified belongs to the current user.
    """
    return await session.get(Transaction, transaction_id)


async def get_by_fixed_commitment_and_month(
    session: AsyncSession, fixed_commitment_id: uuid.UUID | str, month: str
) -> Transaction | None:
    start, end = month_bounds(month)
    result = await session.execute(
        select(Transaction).where(
            Transaction.fixed_commitment_id == fixed_commitment_id,
            Transaction.date >= start,
            Transaction.date <= end,
            Transaction.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_by_bill_and_due_date(
    session: AsyncSession, bill_id: uuid.UUID | str, due_date: dt.date
) -> Transaction | None:
    result = await session.execute(
        select(Transaction)
        .where(
            Transaction.bill_id == bill_id,
            Transaction.deleted_at.is_(None),
        )
        .order_by(Transaction.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_by_ledger_entry_id(
    session: AsyncSession, ledger_entry_id: uuid.UUID | str
) -> Transaction | None:
    result = await session.execute(
        select(Transaction)
        .where(
            Transaction.ledger_entry_id == ledger_entry_id,
            Transaction.deleted_at.is_(None),
        )
        .order_by(Transaction.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_by_policy_id(
    session: AsyncSession, policy_id: uuid.UUID | str
) -> Transaction | None:
    result = await session.execute(
        select(Transaction)
        .where(
            Transaction.policy_id == policy_id,
            Transaction.deleted_at.is_(None),
        )
        .order_by(Transaction.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
