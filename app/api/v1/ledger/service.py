"""Business logic for people ledger."""

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ledger import repository
from app.api.v1.ledger.models import LedgerEntry
from app.api.v1.ledger.schemas import (
    LedgerEntryCreateRequest,
    LedgerEntryResponse,
    LedgerEntryUpdateRequest,
    PersonBalance,
)
from app.core.exceptions import NotFoundError


def _to_response(entry: LedgerEntry) -> LedgerEntryResponse:
    return LedgerEntryResponse.model_validate(entry)


async def list_entries(
    session: AsyncSession, user_id: uuid.UUID, person: str | None = None
) -> list[LedgerEntryResponse]:
    rows = await repository.list_by_user(session, user_id, person)
    return [_to_response(r) for r in rows]


async def list_people_balances(session: AsyncSession, user_id: uuid.UUID) -> list[PersonBalance]:
    rows = await repository.list_by_user(session, user_id)
    balances: dict[str, Decimal] = {}
    for entry in rows:
        delta = Decimal("0")
        if entry.direction == "lent":
            delta = entry.amount
        elif entry.direction == "received":
            delta = -entry.amount
        elif entry.direction == "borrowed":
            delta = -entry.amount
        elif entry.direction == "repaid":
            delta = entry.amount
        balances[entry.person_name] = balances.get(entry.person_name, Decimal("0")) + delta
    return [
        PersonBalance(person_name=name, net_balance=bal)
        for name, bal in sorted(balances.items(), key=lambda x: abs(x[1]), reverse=True)
    ]


async def create_entry(
    session: AsyncSession, user_id: uuid.UUID, payload: LedgerEntryCreateRequest
) -> LedgerEntryResponse:
    entry = await repository.create(session, user_id, **payload.model_dump())
    return _to_response(entry)


async def update_entry(
    session: AsyncSession, user_id: uuid.UUID, entry_id: uuid.UUID, payload: LedgerEntryUpdateRequest
) -> LedgerEntryResponse:
    entry = await repository.get_by_id(session, entry_id, user_id)
    if entry is None:
        raise NotFoundError("Ledger entry not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await session.flush()
    return _to_response(entry)


async def delete_entry(session: AsyncSession, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
    entry = await repository.get_by_id(session, entry_id, user_id)
    if entry is None:
        raise NotFoundError("Ledger entry not found")
    await repository.soft_delete(session, entry)
