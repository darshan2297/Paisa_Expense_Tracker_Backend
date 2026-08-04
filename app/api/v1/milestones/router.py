"""HTTP layer for milestones."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.milestones import service
from app.api.v1.milestones.schemas import (
    MilestoneCreateRequest,
    MilestoneResponse,
    MilestoneUpdateRequest,
)
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

milestones_router = APIRouter(prefix="/milestones")


@milestones_router.get("", summary="List milestones")
@default_limit()
async def list_milestones(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[MilestoneResponse]:
    return await service.list_milestones(session, current_user.id)


@milestones_router.post("", status_code=201, summary="Create milestone")
@default_limit()
async def create_milestone(
    request: Request,
    payload: MilestoneCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> MilestoneResponse:
    return await service.create_milestone(session, current_user.id, payload)


@milestones_router.patch("/{milestone_id}", summary="Update milestone")
@default_limit()
async def update_milestone(
    request: Request,
    milestone_id: uuid.UUID,
    payload: MilestoneUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> MilestoneResponse:
    return await service.update_milestone(session, current_user.id, milestone_id, payload)


@milestones_router.delete("/{milestone_id}", status_code=204, summary="Delete milestone")
@default_limit()
async def delete_milestone(
    request: Request,
    milestone_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_milestone(session, current_user.id, milestone_id)
    return Response(status_code=204)
