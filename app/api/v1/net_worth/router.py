"""HTTP layer for net worth."""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.net_worth import service
from app.api.v1.net_worth.schemas import NetWorthCurrentResponse, NetWorthHistoryResponse
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

net_worth_router = APIRouter(prefix="/net-worth")


@net_worth_router.get("/current", summary="Current net worth")
@default_limit()
async def net_worth_current(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> NetWorthCurrentResponse:
    return await service.get_current(session, current_user.id)


@net_worth_router.get("/history", summary="Net worth history")
@default_limit()
async def net_worth_history(
    request: Request,
    current_user: CurrentUser,
    months: int = Query(default=12, ge=1, le=60),
    session: AsyncSession = Depends(get_session),
) -> NetWorthHistoryResponse:
    return await service.get_history(session, current_user.id, months)


@net_worth_router.post("/snapshot", summary="Record net worth snapshot")
@default_limit()
async def net_worth_snapshot(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> NetWorthCurrentResponse:
    return await service.create_snapshot(session, current_user.id)
