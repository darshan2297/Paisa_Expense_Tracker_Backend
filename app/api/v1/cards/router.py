"""HTTP layer for credit cards."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.cards import service
from app.api.v1.cards.schemas import (
    CardAmountRequest,
    CardsSummaryResponse,
    CreditCardCreateRequest,
    CreditCardResponse,
    CreditCardUpdateRequest,
)
from app.deps import CurrentUser, DefaultAccountId, get_session
from app.middleware.rate_limit import default_limit

cards_router = APIRouter(prefix="/cards")


@cards_router.get("", summary="List credit cards")
@default_limit()
async def list_cards(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[CreditCardResponse]:
    return await service.list_cards(session, current_user.id)


@cards_router.get("/summary", summary="Portfolio utilization summary")
@default_limit()
async def cards_summary(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> CardsSummaryResponse:
    return await service.get_summary(session, current_user.id)


@cards_router.post("", status_code=201, summary="Create a credit card")
@default_limit()
async def create_card(
    request: Request,
    payload: CreditCardCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> CreditCardResponse:
    return await service.create_card(session, current_user.id, payload)


@cards_router.patch("/{card_id}", summary="Update a credit card")
@default_limit()
async def update_card(
    request: Request,
    card_id: uuid.UUID,
    payload: CreditCardUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> CreditCardResponse:
    return await service.update_card(session, current_user.id, card_id, payload)


@cards_router.delete("/{card_id}", status_code=204, summary="Delete a credit card")
@default_limit()
async def delete_card(
    request: Request,
    card_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_card(session, current_user.id, card_id)
    return Response(status_code=204)


@cards_router.post("/{card_id}/pay", summary="Record a card payment")
@default_limit()
async def pay_card(
    request: Request,
    card_id: uuid.UUID,
    payload: CardAmountRequest,
    current_user: CurrentUser,
    account_id: DefaultAccountId,
    session: AsyncSession = Depends(get_session),
) -> CreditCardResponse:
    return await service.record_payment(session, current_user.id, card_id, account_id, payload)


@cards_router.post("/{card_id}/spend", summary="Record card spend")
@default_limit()
async def spend_on_card(
    request: Request,
    card_id: uuid.UUID,
    payload: CardAmountRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> CreditCardResponse:
    return await service.record_spend(session, current_user.id, card_id, payload)
