"""HTTP layer for shared expense groups."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.groups import service
from app.api.v1.groups.schemas import (
    GroupCreateRequest,
    GroupExpenseCreateRequest,
    GroupResponse,
    GroupSettlementCreateRequest,
    GroupUpdateRequest,
    MemberBalance,
)
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

groups_router = APIRouter(prefix="/groups")


@groups_router.get("", summary="List expense groups")
@default_limit()
async def list_groups(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[GroupResponse]:
    return await service.list_groups(session, current_user.id)


@groups_router.post("", status_code=201, summary="Create expense group")
@default_limit()
async def create_group(
    request: Request,
    payload: GroupCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GroupResponse:
    return await service.create_group(session, current_user.id, payload)


@groups_router.patch("/{group_id}", summary="Update expense group")
@default_limit()
async def update_group(
    request: Request,
    group_id: uuid.UUID,
    payload: GroupUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GroupResponse:
    return await service.update_group(session, current_user.id, group_id, payload)


@groups_router.delete("/{group_id}", status_code=204, summary="Delete expense group")
@default_limit()
async def delete_group(
    request: Request,
    group_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_group(session, current_user.id, group_id)
    return Response(status_code=204)


@groups_router.post("/{group_id}/expenses", summary="Add group expense")
@default_limit()
async def add_group_expense(
    request: Request,
    group_id: uuid.UUID,
    payload: GroupExpenseCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GroupResponse:
    return await service.add_expense(session, current_user.id, group_id, payload)


@groups_router.delete("/{group_id}/expenses/{expense_id}", summary="Delete group expense")
@default_limit()
async def delete_group_expense(
    request: Request,
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GroupResponse:
    return await service.delete_expense(session, current_user.id, group_id, expense_id)


@groups_router.post("/{group_id}/settlements", summary="Record settlement")
@default_limit()
async def add_settlement(
    request: Request,
    group_id: uuid.UUID,
    payload: GroupSettlementCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GroupResponse:
    return await service.add_settlement(session, current_user.id, group_id, payload)


@groups_router.delete("/{group_id}/settlements/{settlement_id}", summary="Delete a settlement")
@default_limit()
async def delete_settlement(
    request: Request,
    group_id: uuid.UUID,
    settlement_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> GroupResponse:
    return await service.delete_settlement(session, current_user.id, group_id, settlement_id)


@groups_router.get("/{group_id}/balances", summary="Member balances")
@default_limit()
async def group_balances(
    request: Request,
    group_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[MemberBalance]:
    return await service.get_balances(session, current_user.id, group_id)
