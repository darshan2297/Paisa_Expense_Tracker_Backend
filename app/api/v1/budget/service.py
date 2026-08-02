"""Business logic for the budget module.

Receives/returns plain values or Pydantic schemas; never constructs an
`HTTPException` - see docs/DEVELOPER_PHILOSOPHY.md §2.1.

Uses `app.deps.get_month_totals` (re-exported from `transactions.service`)
to compute "spent this month" rather than duplicating that aggregation
query - see docs/DEVELOPER_PHILOSOPHY.md §2.2. Safe to import `app.deps`
here: nothing re-exports *from* this module, so there's no import cycle
(contrast with `transactions.service`, which must never import `app.deps`
since `app.deps` imports things out of it).
"""

import calendar
import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.budget import repository
from app.api.v1.budget.schemas import (
    BudgetSettingResponse,
    BudgetSettingUpdateRequest,
    BudgetSummaryResponse,
)
from app.deps import get_month_totals

_DEFAULT_MONTHLY_AMOUNT = Decimal(0)
_DEFAULT_ALERT_PCT = 20
_DEFAULT_REMINDER_LEAD_DAYS = 15


async def get_settings(session: AsyncSession, user_id: uuid.UUID) -> BudgetSettingResponse:
    setting = await repository.get_by_user_id(session, user_id)
    if setting is None:
        return BudgetSettingResponse(
            monthly_amount=_DEFAULT_MONTHLY_AMOUNT,
            alert_pct=_DEFAULT_ALERT_PCT,
            reminder_lead_days=_DEFAULT_REMINDER_LEAD_DAYS,
        )
    return BudgetSettingResponse.model_validate(setting)


async def update_settings(
    session: AsyncSession, user_id: uuid.UUID, payload: BudgetSettingUpdateRequest
) -> BudgetSettingResponse:
    setting = await repository.upsert(
        session,
        user_id,
        monthly_amount=payload.monthly_amount,
        alert_pct=payload.alert_pct,
        reminder_lead_days=payload.reminder_lead_days,
    )
    return BudgetSettingResponse.model_validate(setting)


def _days_remaining_in_month(month: str) -> int:
    year, mon = (int(part) for part in month.split("-"))
    days_in_month = calendar.monthrange(year, mon)[1]
    today = dt.date.today()
    if (today.year, today.month) == (year, mon):
        return max(1, days_in_month - today.day + 1)
    if dt.date(year, mon, 1) > today:
        return days_in_month
    return 1  # a fully past month - "per day left" isn't meaningful there


async def get_summary(session: AsyncSession, user_id: uuid.UUID, month: str) -> BudgetSummaryResponse:
    setting = await get_settings(session, user_id)
    _income, spent = await get_month_totals(session, user_id, month)
    remaining = setting.monthly_amount - spent
    pct_remaining = float(remaining / setting.monthly_amount * 100) if setting.monthly_amount else 0.0
    days_remaining = _days_remaining_in_month(month)

    return BudgetSummaryResponse(
        monthly_amount=setting.monthly_amount,
        spent=spent,
        remaining=remaining,
        pct_remaining=round(pct_remaining, 1),
        per_day_left=round(remaining / days_remaining, 2),
        days_remaining_in_month=days_remaining,
    )
