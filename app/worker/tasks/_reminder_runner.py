"""Async reminder logic invoked from Celery tasks.

Creates in-app notification records and sends Resend emails when bills,
fixed commitments, or policies are due within the user's lead window.

Behavior: once inside the lead window (including the due day), remind
**every day** until the item is marked paid. Redis only dedupes same-day
re-runs of the Celery job — not the whole lead window.
"""

from __future__ import annotations

import datetime as dt
import logging
import uuid
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.v1.auth.models import User
from app.api.v1.budget.models import BudgetSetting
from app.api.v1.fixed_commitments.models import FixedCommitment
from app.api.v1.notifications import repository as notifications_repo
from app.core.database import get_engine
from app.core.email import send_reminder_email
from app.core.redis import get_redis
from app.deps import find_transaction_for_commitment, find_transaction_for_policy

logger = logging.getLogger(__name__)

REMINDER_KEY_PREFIX = "paisa:reminder:sent:"
_IST = ZoneInfo("Asia/Kolkata")
# Same-day dedupe only — allows a fresh reminder each calendar day.
_DAILY_DEDUP_TTL_SECONDS = 86_400 * 2


def _today_ist() -> dt.date:
    return dt.datetime.now(_IST).date()


def _session_factory() -> async_sessionmaker[AsyncSession]:
    engine = get_engine()
    return async_sessionmaker(engine, expire_on_commit=False)


async def _already_sent(key: str) -> bool:
    try:
        return bool(await get_redis().exists(key))
    except Exception:
        return False


async def _mark_sent(key: str, ttl_seconds: int = _DAILY_DEDUP_TTL_SECONDS) -> None:
    try:
        await get_redis().set(key, "1", ex=ttl_seconds)
    except Exception:
        pass


def _in_lead_window(days_until: int, lead_days: int) -> bool:
    """True from lead_days before due through the due day (inclusive)."""
    return 0 <= days_until <= lead_days


def _due_phrase(days_until: int) -> str:
    if days_until == 0:
        return "due today"
    if days_until == 1:
        return "due tomorrow"
    return f"due in {days_until} days"


async def _deliver_reminder(
    session: AsyncSession,
    *,
    user: User,
    kind: str,
    title: str,
    body: str,
    entity_type: str,
    entity_id: uuid.UUID,
    amount: Decimal | None = None,
    due_label: str | None = None,
    days_until: int | None = None,
) -> None:
    await notifications_repo.create_notification(
        session,
        user_id=user.id,
        kind=kind,
        title=title,
        body=body,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    send_reminder_email(
        to=user.email,
        recipient_name=user.name,
        kind=kind,
        title=title,
        body=body,
        amount=amount,
        due_label=due_label,
        days_until=days_until,
    )


async def run_bill_reminders() -> int:
    from app.api.v1.bills.models import Bill

    today = _today_ist()
    sent = 0
    factory = _session_factory()

    async with factory() as session:
        users = list(
            (await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars()
        )
        for user in users:
            budget = (
                await session.execute(
                    select(BudgetSetting).where(
                        BudgetSetting.user_id == user.id, BudgetSetting.deleted_at.is_(None)
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
                window = max(lead_days, bill.lead_days)
                if not _in_lead_window(days_until, window):
                    continue
                # Daily key: remind again tomorrow if still unpaid.
                key = f"{REMINDER_KEY_PREFIX}bill:{bill.id}:{due.isoformat()}:{today.isoformat()}"
                if await _already_sent(key):
                    continue

                phrase = _due_phrase(days_until)
                title = f"{bill.name} is {phrase}"
                body = (
                    f"Your {bill.kind.replace('_', ' ')} bill of "
                    f"₹{bill.amount} is {phrase} ({due.strftime('%d %b %Y')})."
                )
                await _deliver_reminder(
                    session,
                    user=user,
                    kind="bill_due",
                    title=title,
                    body=body,
                    entity_type="bill",
                    entity_id=bill.id,
                    amount=bill.amount,
                    due_label=due.strftime("%d %b %Y"),
                    days_until=days_until,
                )
                logger.info(
                    "bill reminder sent",
                    extra={
                        "user_id": str(user.id),
                        "bill_id": str(bill.id),
                        "days_until": days_until,
                    },
                )
                await _mark_sent(key)
                sent += 1

        await session.commit()
    return sent


async def run_fixed_commitment_reminders() -> int:
    today = _today_ist()
    month = today.strftime("%Y-%m")
    sent = 0
    factory = _session_factory()

    async with factory() as session:
        users = list(
            (await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars()
        )
        for user in users:
            budget = (
                await session.execute(
                    select(BudgetSetting).where(
                        BudgetSetting.user_id == user.id, BudgetSetting.deleted_at.is_(None)
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
                # Skip if already marked paid for this month.
                if await find_transaction_for_commitment(session, commitment.id, month):
                    continue

                due = dt.date(year, mon, min(commitment.due_day, 28))
                days_until = (due - today).days
                if not _in_lead_window(days_until, lead_days):
                    continue
                key = (
                    f"{REMINDER_KEY_PREFIX}fixed:{commitment.id}:{month}:{today.isoformat()}"
                )
                if await _already_sent(key):
                    continue

                phrase = _due_phrase(days_until)
                title = f"{commitment.name} is {phrase}"
                body = (
                    f"Your {commitment.kind.replace('_', ' ')} payment of "
                    f"₹{commitment.amount} is {phrase} ({due.strftime('%d %b %Y')})."
                )
                await _deliver_reminder(
                    session,
                    user=user,
                    kind="fixed_due",
                    title=title,
                    body=body,
                    entity_type="fixed_commitment",
                    entity_id=commitment.id,
                    amount=commitment.amount,
                    due_label=due.strftime("%d %b %Y"),
                    days_until=days_until,
                )
                logger.info(
                    "fixed commitment reminder sent",
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
        users = list(
            (await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars()
        )
        for user in users:
            total += await bills_service.rollover_paid_bills(session, user.id)
        await session.commit()
    return total


async def run_policy_reminders() -> int:
    from app.api.v1.policies.models import Policy

    today = _today_ist()
    sent = 0
    factory = _session_factory()

    async with factory() as session:
        users = list(
            (await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars()
        )
        for user in users:
            budget = (
                await session.execute(
                    select(BudgetSetting).where(
                        BudgetSetting.user_id == user.id, BudgetSetting.deleted_at.is_(None)
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
                if await find_transaction_for_policy(session, policy.id):
                    continue

                days_until = (policy.renewal_date - today).days
                if not _in_lead_window(days_until, lead_days):
                    continue
                key = (
                    f"{REMINDER_KEY_PREFIX}policy:{policy.id}:"
                    f"{policy.renewal_date.isoformat()}:{today.isoformat()}"
                )
                if await _already_sent(key):
                    continue

                phrase = _due_phrase(days_until)
                title = f"{policy.name} renewal is {phrase}"
                body = (
                    f"Your {policy.provider} policy premium of ₹{policy.premium} "
                    f"renews {phrase} ({policy.renewal_date.strftime('%d %b %Y')})."
                )
                await _deliver_reminder(
                    session,
                    user=user,
                    kind="policy_renewal",
                    title=title,
                    body=body,
                    entity_type="policy",
                    entity_id=policy.id,
                    amount=policy.premium,
                    due_label=policy.renewal_date.strftime("%d %b %Y"),
                    days_until=days_until,
                )
                logger.info(
                    "policy renewal reminder sent",
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
        users = list(
            (await session.execute(select(User).where(User.deleted_at.is_(None)))).scalars()
        )
        for user in users:
            await net_worth_service.create_snapshot(session, user.id)
            count += 1
        await session.commit()
    return count
