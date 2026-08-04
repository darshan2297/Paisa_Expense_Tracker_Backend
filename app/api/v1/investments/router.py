"""HTTP layer for investments."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.investments import service
from app.api.v1.investments.schemas import (
    InvestmentCreateRequest,
    InvestmentResponse,
    InvestmentUpdateRequest,
    InvestmentsSummaryResponse,
    UpdateValueRequest,
)
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

investments_router = APIRouter(prefix="/investments")


@investments_router.get("", summary="List investments")
@default_limit()
async def list_investments(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[InvestmentResponse]:
    return await service.list_investments(session, current_user.id)


@investments_router.get("/summary", summary="Portfolio summary")
@default_limit()
async def investments_summary(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> InvestmentsSummaryResponse:
    return await service.get_summary(session, current_user.id)


@investments_router.post("", status_code=201, summary="Create investment")
@default_limit()
async def create_investment(
    request: Request,
    payload: InvestmentCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> InvestmentResponse:
    return await service.create_investment(session, current_user.id, payload)


@investments_router.patch("/{investment_id}", summary="Update investment")
@default_limit()
async def update_investment(
    request: Request,
    investment_id: uuid.UUID,
    payload: InvestmentUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> InvestmentResponse:
    return await service.update_investment(session, current_user.id, investment_id, payload)


@investments_router.post("/{investment_id}/update-value", summary="Update current value")
@default_limit()
async def update_investment_value(
    request: Request,
    investment_id: uuid.UUID,
    payload: UpdateValueRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> InvestmentResponse:
    return await service.update_value(session, current_user.id, investment_id, payload)


@investments_router.delete("/{investment_id}", status_code=204, summary="Delete investment")
@default_limit()
async def delete_investment(
    request: Request,
    investment_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_investment(session, current_user.id, investment_id)
    return Response(status_code=204)
