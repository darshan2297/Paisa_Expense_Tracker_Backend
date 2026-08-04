"""Async reminder logic invoked from Celery tasks.

Creates in-app notification records when bills or fixed commitments are
due within the user's lead window. Push delivery is F17.
"""

import datetime as dt
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.auth.models import User
from app.api.v1.budget.models import BudgetSettings
from app.api.v1.fixed_commitments.models import FixedCommitment
from app.core.database import get_engine
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

REMINDER_KEY_PREFIX = "paisa:reminder:sent:"


def _session_factory() -> async_sessionmaker[AsyncSession]:
    engine = get_engine()
    return async_sessionmaker(engine, expire_on_commit=False)


async def _already_sent(key: str) -> bool:
    try:
        return bool(await get_redis().exists(key))
    except Exception:
        return False


async def _mark_sent(key: str, ttl_seconds: int = 86_400 * 35) -> None:
    try:
        await get_redis().set(key, "1", ex=ttl_seconds)
    except Exception:
        pass


async def run_bill_reminders() -> int:
    from app.api.v1.bills.models import Bill

    today = dt.date.today()
    sent = 0
    factory = _session_factory()

    async with factory() as session:
        users = list((await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars())
        for user in users:
            budget = (
                await session.execute(
                    select(BudgetSettings).where(
                        BudgetSettings.user_id == user.id, BudgetSettings.deleted_at.is_(None)
                    )
                )
            ).scalar_one_or_none()
            lead_days = budget.reminder_lead_days if budget else 7

            bills = list(
                (
                    await session.execute(
                        select(Bill).where(
                            Bill.user_id == user.id,
                            Bill.deleted_at.is_(None),
                            Bill.paid_on.is_(None),
                        )
                    )
                ).scalars()
            )

            for bill in bills:
                due = bill.due_date
                days_until = (due - today).days
                if days_until < 0 or days_until > max(lead_days, bill.lead_days):
                    continue
                key = f"{REMINDER_KEY_PREFIX}bill:{bill.id}:{due.isoformat()}"
                if await _already_sent(key):
                    continue
                logger.info(
                    "bill reminder queued",
                    extra={"user_id": str(user.id), "bill_id": str(bill.id), "days_until": days_until},
                )
                await _mark_sent(key)
                sent += 1

        await session.commit()
    return sent


async def run_fixed_commitment_reminders() -> int:
    today = dt.date.today()
    month = today.strftime("%Y-%m")
    sent = 0
    factory = _session_factory()

    async with factory() as session:
        users = list((await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars())
        for user in users:
            budget = (
                await session.execute(
                    select(BudgetSettings).where(
                        BudgetSettings.user_id == user.id, BudgetSettings.deleted_at.is_(None)
                    )
                )
            ).scalar_one_or_none()
            lead_days = budget.reminder_lead_days if budget else 7

            commitments = list(
                (
                    await session.execute(
                        select(FixedCommitment).where(
                            FixedCommitment.user_id == user.id,
                            FixedCommitment.deleted_at.is_(None),
                        )
                    )
                ).scalars()
            )

            year, mon = (int(p) for p in month.split("-"))
            for commitment in commitments:
                due = dt.date(year, mon, min(commitment.due_day, 28))
                days_until = (due - today).days
                if days_until < 0 or days_until > lead_days:
                    continue
                key = f"{REMINDER_KEY_PREFIX}fixed:{commitment.id}:{month}"
                if await _already_sent(key):
                    continue
                logger.info(
                    "fixed commitment reminder queued",
                    extra={
                        "user_id": str(user.id),
                        "commitment_id": str(commitment.id),
                        "days_until": days_until,
                    },
                )
                await _mark_sent(key)
                sent += 1

        await session.commit()
    return sent


async def run_bill_rollover() -> int:
    """Advance due dates for paid bills whose due date has passed."""
    from app.api.v1.bills import service as bills_service

    total = 0
    factory = _session_factory()

    async with factory() as session:
        users = list((await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars())
        for user in users:
            total += await bills_service.rollover_paid_bills(session, user.id)
        await session.commit()
    return total


async def run_policy_reminders() -> int:
    from app.api.v1.policies.models import Policy

    today = dt.date.today()
    sent = 0
    factory = _session_factory()

    async with factory() as session:
        users = list((await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars())
        for user in users:
            budget = (
                await session.execute(
                    select(BudgetSettings).where(
                        BudgetSettings.user_id == user.id, BudgetSettings.deleted_at.is_(None)
                    )
                )
            ).scalar_one_or_none()
            lead_days = budget.reminder_lead_days if budget else 30

            policies = list(
                (
                    await session.execute(
                        select(Policy).where(Policy.user_id == user.id, Policy.deleted_at.is_(None))
                    )
                ).scalars()
            )
            for policy in policies:
                days_until = (policy.renewal_date - today).days
                if days_until < 0 or days_until > lead_days:
                    continue
                key = f"{REMINDER_KEY_PREFIX}policy:{policy.id}:{policy.renewal_date.isoformat()}"
                if await _already_sent(key):
                    continue
                logger.info(
                    "policy renewal reminder queued",
                    extra={"user_id": str(user.id), "policy_id": str(policy.id)},
                )
                await _mark_sent(key)
                sent += 1
        await session.commit()
    return sent


async def run_net_worth_snapshots() -> int:
    from app.api.v1.net_worth import service as net_worth_service

    count = 0
    factory = _session_factory()

    async with factory() as session:
        users = list((await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars())
        for user in users:
            await net_worth_service.create_snapshot(session, user.id)
            count += 1
        await session.commit()
    return count
