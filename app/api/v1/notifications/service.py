"""Business logic for notifications."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.notifications import repository
from app.api.v1.notifications.schemas import NotificationResponse, PushTokenCreateRequest
from app.core.exceptions import NotFoundError


async def list_notifications(
    session: AsyncSession, user_id: uuid.UUID
) -> list[NotificationResponse]:
    rows = await repository.list_notifications(session, user_id)
    return [NotificationResponse.model_validate(r) for r in rows]


async def mark_read(session: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
    n = await repository.get_notification(session, notification_id, user_id)
    if n is None:
        raise NotFoundError("Notification not found")
    await repository.mark_read(session, notification_id, user_id)


async def mark_all_read(session: AsyncSession, user_id: uuid.UUID) -> None:
    await repository.mark_all_read(session, user_id)


async def register_push_token(
    session: AsyncSession, user_id: uuid.UUID, payload: PushTokenCreateRequest
) -> None:
    await repository.upsert_push_token(
        session, user_id, payload.expo_push_token, payload.device_label
    )


async def delete_push_token(session: AsyncSession, user_id: uuid.UUID, token: str) -> None:
    await repository.delete_push_token(session, token, user_id)
