"""Business logic for bills."""

import calendar
import datetime as dt
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.bills import repository
from app.api.v1.bills.models import Bill
from app.api.v1.bills.schemas import BillCreateRequest, BillResponse, BillUpdateRequest
from app.core.exceptions import ConflictError, NotFoundError
from app.deps import find_transaction_for_bill, record_transaction, remove_transaction_by_id


def _status_label(days_until: int, lead_days: int, paid_on: dt.date | None) -> str:
    if paid_on is not None:
        return "Paid"
    if days_until < 0:
        return f"{abs(days_until)}d overdue"
    if days_until == 0:
        return "Due today"
    if days_until <= lead_days:
        return f"in {days_until} days"
    return "Active"


def _to_response(
    bill: Bill, today: dt.date, linked_transaction_id: uuid.UUID | None
) -> BillResponse:
    days_until = (bill.due_date - today).days
    return BillResponse(
        id=bill.id,
        name=bill.name,
        kind=bill.kind,
        amount=bill.amount,
        due_date=bill.due_date,
        frequency=bill.frequency,
        auto_pay=bill.auto_pay,
        lead_days=bill.lead_days,
        note=bill.note,
        paid_on=bill.paid_on,
        days_until_due=days_until,
        status_label=_status_label(days_until, bill.lead_days, bill.paid_on),
        linked_transaction_id=linked_transaction_id,
    )


def advance_due_date(due_date: dt.date, frequency: str) -> dt.date:
    """Advance a bill's due date by its frequency (auto-repeat rollover)."""
    if frequency == "weekly":
        return due_date + dt.timedelta(days=7)
    if frequency == "quarterly":
        month = due_date.month + 3
        year = due_date.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day = min(due_date.day, calendar.monthrange(year, month)[1])
        return dt.date(year, month, day)
    if frequency == "yearly":
        year = due_date.year + 1
        month = due_date.month
        day = min(due_date.day, calendar.monthrange(year, month)[1])
        return dt.date(year, month, day)
    # monthly default
    month = due_date.month + 1
    year = due_date.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    day = min(due_date.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)


async def list_bills(
    session: AsyncSession, user_id: uuid.UUID, month: str | None = None
) -> list[BillResponse]:
    today = dt.date.today()
    bills = await repository.list_by_user(session, user_id)
    responses: list[BillResponse] = []
    for bill in bills:
        linked_id = await find_transaction_for_bill(session, bill.id, bill.due_date)
        responses.append(_to_response(bill, today, linked_id))

    if month:
        year, mon = (int(p) for p in month.split("-"))
        start = dt.date(year, mon, 1)
        end = dt.date(year, mon, calendar.monthrange(year, mon)[1])
        # Always keep unpaid bills (incl. overdue from prior months) so the
        # Bills screen matches dashboard reminder_count; month only scopes paid.
        responses = [
            r
            for r in responses
            if r.paid_on is None
            or start <= r.due_date <= end
            or (r.paid_on is not None and start <= r.paid_on <= end)
        ]
    return sorted(responses, key=lambda r: (r.paid_on is not None, r.due_date))


async def create_bill(
    session: AsyncSession, user_id: uuid.UUID, payload: BillCreateRequest
) -> BillResponse:
    bill = await repository.create(
        session,
        user_id=user_id,
        name=payload.name,
        kind=payload.kind,
        amount=payload.amount,
        due_date=payload.due_date,
        frequency=payload.frequency,
        auto_pay=payload.auto_pay,
        lead_days=payload.lead_days,
        note=payload.note,
    )
    return _to_response(bill, dt.date.today(), None)


async def update_bill(
    session: AsyncSession, user_id: uuid.UUID, bill_id: uuid.UUID, payload: BillUpdateRequest
) -> BillResponse:
    bill = await repository.get_by_id(session, bill_id, user_id)
    if bill is None:
        raise NotFoundError("Bill not found")
    if payload.name is not None:
        bill.name = payload.name
    if payload.kind is not None:
        bill.kind = payload.kind
    if payload.amount is not None:
        bill.amount = payload.amount
    if payload.due_date is not None:
        bill.due_date = payload.due_date
    if payload.frequency is not None:
        bill.frequency = payload.frequency
    if payload.auto_pay is not None:
        bill.auto_pay = payload.auto_pay
    if payload.lead_days is not None:
        bill.lead_days = payload.lead_days
    if payload.note is not None:
        bill.note = payload.note
    await session.flush()
    linked_id = await find_transaction_for_bill(session, bill.id, bill.due_date)
    return _to_response(bill, dt.date.today(), linked_id)


async def delete_bill(session: AsyncSession, user_id: uuid.UUID, bill_id: uuid.UUID) -> None:
    bill = await repository.get_by_id(session, bill_id, user_id)
    if bill is None:
        raise NotFoundError("Bill not found")
    await repository.soft_delete(session, bill)


async def pay_bill(
    session: AsyncSession,
    user_id: uuid.UUID,
    bill_id: uuid.UUID,
    account_id: uuid.UUID,
    utilities_category_id: uuid.UUID,
) -> BillResponse:
    bill = await repository.get_by_id(session, bill_id, user_id)
    if bill is None:
        raise NotFoundError("Bill not found")
    if bill.paid_on is not None:
        raise ConflictError("Bill is already paid for this cycle")

    today = dt.date.today()
    tx_id = await record_transaction(
        session,
        user_id=user_id,
        account_id=account_id,
        category_id=utilities_category_id,
        type_="expense",
        amount=bill.amount,
        date=today,
        note=bill.note or bill.name,
        bill_id=bill.id,
    )
    bill.paid_on = today
    await session.flush()
    return _to_response(bill, today, tx_id)


async def unpay_bill(session: AsyncSession, user_id: uuid.UUID, bill_id: uuid.UUID) -> BillResponse:
    bill = await repository.get_by_id(session, bill_id, user_id)
    if bill is None:
        raise NotFoundError("Bill not found")
    linked_id = await find_transaction_for_bill(session, bill.id, bill.due_date)
    if linked_id:
        await remove_transaction_by_id(session, linked_id)
    bill.paid_on = None
    await session.flush()
    return _to_response(bill, dt.date.today(), None)


async def toggle_bill_auto(
    session: AsyncSession, user_id: uuid.UUID, bill_id: uuid.UUID
) -> BillResponse:
    bill = await repository.get_by_id(session, bill_id, user_id)
    if bill is None:
        raise NotFoundError("Bill not found")
    bill.auto_pay = not bill.auto_pay
    await session.flush()
    linked_id = await find_transaction_for_bill(session, bill.id, bill.due_date)
    return _to_response(bill, dt.date.today(), linked_id)


async def rollover_paid_bills(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Advance due dates for paid recurring bills (monthly auto-repeat)."""
    today = dt.date.today()
    count = 0
    bills = await repository.list_by_user(session, user_id)
    for bill in bills:
        if bill.paid_on is None or bill.due_date > today:
            continue
        bill.due_date = advance_due_date(bill.due_date, bill.frequency)
        bill.paid_on = None
        count += 1
    if count:
        await session.flush()
    return count
