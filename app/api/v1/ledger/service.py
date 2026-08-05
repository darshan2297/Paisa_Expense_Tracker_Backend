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

# Cash movement for each people-ledger direction.
# lent / repaid → money left the wallet (expense)
# borrowed / received → money entered the wallet (income)
_DIRECTION_CASH: dict[str, tuple[str, str]] = {
    "lent": ("expense", "Lent to"),
    "repaid": ("expense", "Repaid"),
    "borrowed": ("income", "Borrowed from"),
    "received": ("income", "Received from"),
}


def _to_response(entry: LedgerEntry) -> LedgerEntryResponse:
    return LedgerEntryResponse.model_validate(entry)


def _cash_note(entry: LedgerEntry) -> str:
    _type, verb = _DIRECTION_CASH.get(entry.direction, ("expense", "People"))
    base = f"{verb} {entry.person_name}".strip()
    if entry.note:
        return f"{base} · {entry.note}"
    return base


async def _category_for_type(session: AsyncSession, type_: str) -> uuid.UUID:
    from app.deps import list_categories

    categories = await list_categories(session)
    matching = [c for c in categories if c.kind == type_]
    other = next((c for c in matching if c.name == "Other"), None)
    if other is not None:
        return other.id
    if not matching:
        raise NotFoundError(f"No {type_} category configured")
    return matching[0].id


async def _ensure_cash_transaction(session: AsyncSession, user_id: uuid.UUID, entry: LedgerEntry) -> None:
    """Mirror a people-ledger row into cash transactions (Transactions screen)."""
    from app.api.v1.accounts.service import ensure_default_account
    from app.deps import find_transaction_for_ledger_entry, record_transaction

    mapping = _DIRECTION_CASH.get(entry.direction)
    if mapping is None:
        return
    existing = await find_transaction_for_ledger_entry(session, entry.id)
    if existing is not None:
        return

    type_, _verb = mapping
    account = await ensure_default_account(session, user_id)
    category_id = await _category_for_type(session, type_)
    await record_transaction(
        session,
        user_id=user_id,
        account_id=account.id,
        category_id=category_id,
        type_=type_,
        amount=entry.amount,
        date=entry.date,
        note=_cash_note(entry),
        ledger_entry_id=entry.id,
    )


async def _remove_cash_transaction(session: AsyncSession, entry_id: uuid.UUID) -> None:
    from app.deps import find_transaction_for_ledger_entry, remove_transaction_by_id

    linked = await find_transaction_for_ledger_entry(session, entry_id)
    if linked is not None:
        await remove_transaction_by_id(session, linked)


async def list_entries(
    session: AsyncSession, user_id: uuid.UUID, person: str | None = None
) -> list[LedgerEntryResponse]:
    rows = await repository.list_by_user(session, user_id, person)
    # Backfill cash transactions for entries created before settle-up linked to Transactions.
    for row in rows:
        await _ensure_cash_transaction(session, user_id, row)
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
    await _ensure_cash_transaction(session, user_id, entry)
    return _to_response(entry)


async def update_entry(
    session: AsyncSession,
    user_id: uuid.UUID,
    entry_id: uuid.UUID,
    payload: LedgerEntryUpdateRequest,
) -> LedgerEntryResponse:
    entry = await repository.get_by_id(session, entry_id, user_id)
    if entry is None:
        raise NotFoundError("Ledger entry not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await session.flush()
    # Rebuild linked cash row so amount/date/note stay aligned.
    await _remove_cash_transaction(session, entry.id)
    await _ensure_cash_transaction(session, user_id, entry)
    return _to_response(entry)


async def delete_entry(session: AsyncSession, user_id: uuid.UUID, entry_id: uuid.UUID) -> None:
    entry = await repository.get_by_id(session, entry_id, user_id)
    if entry is None:
        raise NotFoundError("Ledger entry not found")
    await _remove_cash_transaction(session, entry.id)
    await repository.soft_delete(session, entry)
