"""Data access for the `budget_settings` table.

Returns ORM objects (or `None`); never raises and never contains business
rules - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.budget.models import BudgetSetting


async def get_by_user_id(session: AsyncSession, user_id: uuid.UUID | str) -> BudgetSetting | None:
    result = await session.execute(
        select(BudgetSetting).where(
            BudgetSetting.user_id == user_id, BudgetSetting.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()


async def upsert(
    session: AsyncSession,
    user_id: uuid.UUID | str,
    monthly_amount: Decimal,
    alert_pct: int,
    reminder_lead_days: int,
) -> BudgetSetting:
    existing = await get_by_user_id(session, user_id)
    if existing is not None:
        existing.monthly_amount = monthly_amount
        existing.alert_pct = alert_pct
        existing.reminder_lead_days = reminder_lead_days
        await session.flush()
        return existing

    setting = BudgetSetting(
        user_id=user_id,
        monthly_amount=monthly_amount,
        alert_pct=alert_pct,
        reminder_lead_days=reminder_lead_days,
    )
    session.add(setting)
    await session.flush()
    return setting
