"""HTTP layer for loans."""

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.loans import service
from app.api.v1.loans.schemas import (
    LoanCreateRequest,
    LoanResponse,
    LoansSummaryResponse,
    LoanUpdateRequest,
    PrepayRequest,
    PrepayResponse,
    ScheduleRow,
)
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

loans_router = APIRouter(prefix="/loans")
_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@loans_router.get("", summary="List loans")
@default_limit()
async def list_loans(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[LoanResponse]:
    return await service.list_loans(session, current_user.id)


@loans_router.get("/summary", summary="Loans portfolio summary")
@default_limit()
async def loans_summary(
    request: Request,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN),
    session: AsyncSession = Depends(get_session),
) -> LoansSummaryResponse:
    return await service.get_summary(session, current_user.id, month)


@loans_router.post("", status_code=201, summary="Create loan")
@default_limit()
async def create_loan(
    request: Request,
    payload: LoanCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> LoanResponse:
    return await service.create_loan(session, current_user.id, payload)


@loans_router.patch("/{loan_id}", summary="Update loan")
@default_limit()
async def update_loan(
    request: Request,
    loan_id: uuid.UUID,
    payload: LoanUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> LoanResponse:
    return await service.update_loan(session, current_user.id, loan_id, payload)


@loans_router.delete("/{loan_id}", status_code=204, summary="Delete loan")
@default_limit()
async def delete_loan(
    request: Request,
    loan_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_loan(session, current_user.id, loan_id)
    return Response(status_code=204)


@loans_router.get("/{loan_id}/schedule", summary="Amortization schedule")
@default_limit()
async def loan_schedule(
    request: Request,
    loan_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[ScheduleRow]:
    return await service.get_schedule(session, current_user.id, loan_id)


@loans_router.post("/{loan_id}/prepay", summary="Prepayment calculator")
@default_limit()
async def prepay_loan(
    request: Request,
    loan_id: uuid.UUID,
    payload: PrepayRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PrepayResponse:
    return await service.prepay(session, current_user.id, loan_id, payload)
