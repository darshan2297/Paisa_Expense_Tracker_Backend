"""HTTP layer for savings goals."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.goals import service
from app.api.v1.goals.schemas import (
    EmergencyFundResponse,
    GoalContributeRequest,
    GoalCreateRequest,
    GoalResponse,
    GoalSummaryResponse,
    GoalUpdateRequest,
)
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

goals_router = APIRouter(prefix="/goals")


@goals_router.get("", summary="List savings goals")
@default_limit()
async def list_goals(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[GoalResponse]:
    return await service.list_goals(session, current_user.id)


@goals_router.get("/emergency", summary="Emergency fund status")
@default_limit()
async def get_emergency_fund(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> EmergencyFundResponse:
    return await service.get_emergency_fund(session, current_user.id)


@goals_router.get("/summary", summary="Goals portfolio summary")
@default_limit()
async def get_goals_summary(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GoalSummaryResponse:
    return await service.get_summary(session, current_user.id)


@goals_router.post("", status_code=201, summary="Create a savings goal")
@default_limit()
async def create_goal(
    request: Request,
    payload: GoalCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GoalResponse:
    return await service.create_goal(session, current_user.id, payload)


@goals_router.patch("/{goal_id}", summary="Update a savings goal")
@default_limit()
async def update_goal(
    request: Request,
    goal_id: uuid.UUID,
    payload: GoalUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GoalResponse:
    return await service.update_goal(session, current_user.id, goal_id, payload)


@goals_router.delete("/{goal_id}", status_code=204, summary="Delete a savings goal")
@default_limit()
async def delete_goal(
    request: Request,
    goal_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_goal(session, current_user.id, goal_id)
    return Response(status_code=204)


@goals_router.post("/{goal_id}/contribute", summary="Add to goal saved amount")
@default_limit()
async def contribute_to_goal(
    request: Request,
    goal_id: uuid.UUID,
    payload: GoalContributeRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GoalResponse:
    return await service.contribute(session, current_user.id, goal_id, payload)
