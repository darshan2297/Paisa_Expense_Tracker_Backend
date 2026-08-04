"""Data access for notifications."""

import datetime as dt
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.notifications.models import Notification, PushToken


async def list_notifications(session: AsyncSession, user_id: uuid.UUID) -> list[Notification]:
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().all())


async def get_notification(
    session: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
) -> Notification | None:
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def mark_read(session: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
    await session.execute(
        update(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .values(read_at=dt.datetime.now(dt.UTC))
    )


async def mark_all_read(session: AsyncSession, user_id: uuid.UUID) -> None:
    await session.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=dt.datetime.now(dt.UTC))
    )


async def create_notification(session: AsyncSession, **kwargs: object) -> Notification:
    n = Notification(**kwargs)
    session.add(n)
    await session.flush()
    return n


async def upsert_push_token(
    session: AsyncSession, user_id: uuid.UUID, token: str, label: str | None
) -> PushToken:
    result = await session.execute(select(PushToken).where(PushToken.expo_push_token == token))
    existing = result.scalar_one_or_none()
    if existing:
        existing.user_id = user_id
        existing.device_label = label
        await session.flush()
        return existing
    pt = PushToken(user_id=user_id, expo_push_token=token, device_label=label)
    session.add(pt)
    await session.flush()
    return pt


async def delete_push_token(session: AsyncSession, token: str, user_id: uuid.UUID) -> None:
    result = await session.execute(
        select(PushToken).where(PushToken.expo_push_token == token, PushToken.user_id == user_id)
    )
    pt = result.scalar_one_or_none()
    if pt:
        await session.delete(pt)
