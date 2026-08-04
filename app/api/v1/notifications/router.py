"""HTTP layer for notifications."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.notifications import service
from app.api.v1.notifications.schemas import NotificationResponse, PushTokenCreateRequest
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

notifications_router = APIRouter()


@notifications_router.get("/notifications", summary="List notifications")
@default_limit()
async def list_notifications(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[NotificationResponse]:
    return await service.list_notifications(session, current_user.id)


@notifications_router.patch(
    "/notifications/{notification_id}/read", summary="Mark notification read"
)
@default_limit()
async def mark_notification_read(
    request: Request,
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.mark_read(session, current_user.id, notification_id)
    return Response(status_code=204)


@notifications_router.post("/notifications/read-all", summary="Mark all notifications read")
@default_limit()
async def mark_all_read(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.mark_all_read(session, current_user.id)
    return Response(status_code=204)


@notifications_router.post("/push-tokens", status_code=201, summary="Register push token")
@default_limit()
async def register_push_token(
    request: Request,
    payload: PushTokenCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.register_push_token(session, current_user.id, payload)
    return Response(status_code=201)


@notifications_router.delete("/push-tokens/{token}", summary="Remove push token")
@default_limit()
async def delete_push_token(
    request: Request,
    token: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_push_token(session, current_user.id, token)
    return Response(status_code=204)
