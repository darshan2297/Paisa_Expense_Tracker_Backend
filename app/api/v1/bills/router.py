"""HTTP layer for bills."""

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.bills import service
from app.api.v1.bills.schemas import BillCreateRequest, BillResponse, BillUpdateRequest
from app.deps import CurrentUser, DefaultAccountId, UtilitiesCategoryId, get_session
from app.middleware.rate_limit import default_limit

bills_router = APIRouter(prefix="/bills")

_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@bills_router.get("", summary="List bills with due status")
@default_limit()
async def list_bills(
    request: Request,
    current_user: CurrentUser,
    month: str | None = Query(default=None, pattern=_MONTH_PATTERN),
    session: AsyncSession = Depends(get_session),
) -> list[BillResponse]:
    return await service.list_bills(session, current_user.id, month)


@bills_router.post("", status_code=201, summary="Create a bill")
@default_limit()
async def create_bill(
    request: Request,
    payload: BillCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BillResponse:
    return await service.create_bill(session, current_user.id, payload)


@bills_router.patch("/{bill_id}", summary="Update a bill")
@default_limit()
async def update_bill(
    request: Request,
    bill_id: uuid.UUID,
    payload: BillUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BillResponse:
    return await service.update_bill(session, current_user.id, bill_id, payload)


@bills_router.delete("/{bill_id}", status_code=204, summary="Delete a bill")
@default_limit()
async def delete_bill(
    request: Request,
    bill_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_bill(session, current_user.id, bill_id)
    return Response(status_code=204)


@bills_router.post("/{bill_id}/pay", summary="Mark a bill paid")
@default_limit()
async def pay_bill(
    request: Request,
    bill_id: uuid.UUID,
    current_user: CurrentUser,
    account_id: DefaultAccountId,
    utilities_category_id: UtilitiesCategoryId,
    session: AsyncSession = Depends(get_session),
) -> BillResponse:
    return await service.pay_bill(
        session, current_user.id, bill_id, account_id, utilities_category_id
    )


@bills_router.post("/{bill_id}/unpay", summary="Undo bill payment")
@default_limit()
async def unpay_bill(
    request: Request,
    bill_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BillResponse:
    return await service.unpay_bill(session, current_user.id, bill_id)


@bills_router.post("/{bill_id}/toggle-auto", summary="Toggle auto-pay")
@default_limit()
async def toggle_auto(
    request: Request,
    bill_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> BillResponse:
    return await service.toggle_bill_auto(session, current_user.id, bill_id)
