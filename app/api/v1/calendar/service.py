"""Calendar and heatmap aggregation service."""

import calendar
import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.bills import repository as bills_repo
from app.api.v1.calendar.schemas import (
    ActualItem,
    CalendarResponse,
    DayCell,
    HeatmapCell,
    HeatmapResponse,
    PlannedItem,
)
from app.api.v1.fixed_commitments import repository as fc_repo
from app.api.v1.goals import repository as goals_repo
from app.api.v1.loans import repository as loans_repo
from app.api.v1.policies import repository as policies_repo
from app.api.v1.transactions.models import Transaction, TransactionType
from app.api.v1.transactions.repository import month_bounds


async def _transactions_by_day(
    session: AsyncSession, user_id: uuid.UUID, month: str
) -> dict[dt.date, list[Transaction]]:
    start, end = month_bounds(month)
    result = await session.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.date >= start,
            Transaction.date <= end,
        )
    )
    by_day: dict[dt.date, list[Transaction]] = {}
    for txn in result.scalars().all():
        by_day.setdefault(txn.date, []).append(txn)
    return by_day


async def get_calendar(session: AsyncSession, user_id: uuid.UUID, month: str) -> CalendarResponse:
    by_day = await _transactions_by_day(session, user_id, month)
    year, mon = (int(part) for part in month.split("-"))
    days_in_month = calendar.monthrange(year, mon)[1]

    goals = await goals_repo.list_by_user(session, user_id)
    bills = await bills_repo.list_by_user(session, user_id)
    policies = await policies_repo.list_by_user(session, user_id)
    loans = await loans_repo.list_by_user(session, user_id)
    commitments = await fc_repo.list_by_user(session, user_id)

    days: list[DayCell] = []
    planned_total = Decimal("0")
    actual_out = Decimal("0")
    actual_in = Decimal("0")
    highest_out = Decimal("0")

    for day_num in range(1, days_in_month + 1):
        date = dt.date(year, mon, day_num)
        txns = by_day.get(date, [])
        inflow = sum(
            (t.amount for t in txns if t.type == TransactionType.INCOME.value), Decimal("0")
        )
        outflow = sum(
            (t.amount for t in txns if t.type == TransactionType.EXPENSE.value), Decimal("0")
        )
        actual_in += inflow
        actual_out += outflow
        highest_out = max(highest_out, outflow)

        planned: list[PlannedItem] = []
        for g in goals:
            if g.monthly_contribution > 0 and g.due_day == day_num:
                planned.append(
                    PlannedItem(label=g.name, kind="Goal", amount=g.monthly_contribution)
                )
                planned_total += g.monthly_contribution
        for bill in bills:
            if bill.due_date == date and bill.paid_on is None:
                planned.append(PlannedItem(label=bill.name, kind="Bill", amount=bill.amount))
                planned_total += bill.amount
        for policy in policies:
            if policy.renewal_date == date:
                planned.append(
                    PlannedItem(label=policy.name, kind="Insurance", amount=policy.premium)
                )
                planned_total += policy.premium
        for loan in loans:
            if loan.start_date.day == day_num:
                from app.api.v1.loans.schemas import compute_emi

                emi = compute_emi(loan.principal, loan.rate_pct, loan.tenure_months)
                planned.append(PlannedItem(label=loan.name, kind="EMI", amount=emi))
                planned_total += emi
        for fc in commitments:
            if fc.due_day == day_num:
                planned.append(PlannedItem(label=fc.name, kind="Fixed", amount=fc.amount))
                planned_total += fc.amount

        actual = [
            ActualItem(
                id=str(t.id),
                title=t.note or t.type,
                amount=t.amount,
                type=t.type,
            )
            for t in txns
        ]
        days.append(
            DayCell(date=date, inflow=inflow, outflow=outflow, planned=planned, actual=actual)
        )

    return CalendarResponse(
        month=month,
        days=days,
        net_flow=actual_in - actual_out,
        highest_day_outflow=highest_out,
        planned_total=planned_total,
        actual_total=actual_out,
    )


async def get_heatmap(session: AsyncSession, user_id: uuid.UUID, weeks: int) -> HeatmapResponse:
    """Last N weeks of spend intensity — matches design HTML heatmap grid.

    Week columns end on Saturday (JS ``getDay`` week). Intensity is 0–3 from
    average spend thresholds (not a 0–4 max-normalized scale).
    """
    today = dt.date.today()
    # JS: end = today + (6 - today.getDay()) → Saturday of the current week.
    js_weekday = (today.weekday() + 1) % 7  # Sun=0 … Sat=6
    end = today + dt.timedelta(days=6 - js_weekday)
    start = end - dt.timedelta(days=weeks * 7 - 1)

    result = await session.execute(
        select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.type == TransactionType.EXPENSE.value,
            Transaction.date >= start,
            Transaction.date <= end,
        )
    )
    by_day: dict[dt.date, Decimal] = {}
    for txn in result.scalars().all():
        by_day[txn.date] = by_day.get(txn.date, Decimal("0")) + txn.amount

    spend_values = list(by_day.values())
    avg_spend = float(sum(spend_values) / len(spend_values)) if spend_values else 1.0

    weekday_totals: dict[str, Decimal] = {
        d: Decimal("0") for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    }
    dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    cells: list[HeatmapCell] = []
    current = start
    while current <= end:
        amt = by_day.get(current, Decimal("0"))
        value = float(amt)
        if value == 0:
            intensity = 0
        elif value < avg_spend * 0.6:
            intensity = 1
        elif value < avg_spend * 1.4:
            intensity = 2
        else:
            intensity = 3
        weekday_totals[dow_names[current.weekday()]] += amt
        cells.append(HeatmapCell(date=current, intensity=intensity, amount=amt))
        current += dt.timedelta(days=1)

    return HeatmapResponse(weeks=weeks, cells=cells, weekday_totals=weekday_totals)
