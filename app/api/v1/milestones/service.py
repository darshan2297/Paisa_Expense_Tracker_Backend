"""Business logic for milestones."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.milestones import repository
from app.api.v1.milestones.models import Milestone
from app.api.v1.milestones.schemas import (
    MilestoneCreateRequest,
    MilestoneResponse,
    MilestoneUpdateRequest,
)
from app.core.exceptions import NotFoundError


def _to_response(m: Milestone) -> MilestoneResponse:
    return MilestoneResponse.model_validate(m)


async def list_milestones(session: AsyncSession, user_id: uuid.UUID) -> list[MilestoneResponse]:
    rows = await repository.list_by_user(session, user_id)
    return [_to_response(r) for r in rows]


async def create_milestone(
    session: AsyncSession, user_id: uuid.UUID, payload: MilestoneCreateRequest
) -> MilestoneResponse:
    m = await repository.create(session, user_id, **payload.model_dump())
    return _to_response(m)


async def update_milestone(
    session: AsyncSession, user_id: uuid.UUID, milestone_id: uuid.UUID, payload: MilestoneUpdateRequest
) -> MilestoneResponse:
    m = await repository.get_by_id(session, milestone_id, user_id)
    if m is None:
        raise NotFoundError("Milestone not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(m, field, value)
    await session.flush()
    return _to_response(m)


async def delete_milestone(session: AsyncSession, user_id: uuid.UUID, milestone_id: uuid.UUID) -> None:
    m = await repository.get_by_id(session, milestone_id, user_id)
    if m is None:
        raise NotFoundError("Milestone not found")
    await repository.soft_delete(session, m)
