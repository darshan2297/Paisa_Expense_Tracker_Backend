"""HTTP layer for people ledger."""

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ledger import service
from app.api.v1.ledger.schemas import (
    LedgerEntryCreateRequest,
    LedgerEntryResponse,
    LedgerEntryUpdateRequest,
    PersonBalance,
)
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

ledger_router = APIRouter(prefix="/ledger")


@ledger_router.get("", summary="List ledger entries")
@default_limit()
async def list_ledger(
    request: Request,
    current_user: CurrentUser,
    person: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[LedgerEntryResponse]:
    return await service.list_entries(session, current_user.id, person)


@ledger_router.get("/people", summary="Per-person net balances")
@default_limit()
async def list_people(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[PersonBalance]:
    return await service.list_people_balances(session, current_user.id)


@ledger_router.post("", status_code=201, summary="Create ledger entry")
@default_limit()
async def create_ledger_entry(
    request: Request,
    payload: LedgerEntryCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> LedgerEntryResponse:
    return await service.create_entry(session, current_user.id, payload)


@ledger_router.patch("/{entry_id}", summary="Update ledger entry")
@default_limit()
async def update_ledger_entry(
    request: Request,
    entry_id: uuid.UUID,
    payload: LedgerEntryUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> LedgerEntryResponse:
    return await service.update_entry(session, current_user.id, entry_id, payload)


@ledger_router.delete("/{entry_id}", status_code=204, summary="Delete ledger entry")
@default_limit()
async def delete_ledger_entry(
    request: Request,
    entry_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_entry(session, current_user.id, entry_id)
    return Response(status_code=204)
