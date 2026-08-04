"""Business logic for credit cards."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.cards import repository
from app.api.v1.cards.models import CreditCard
from app.api.v1.cards.schemas import (
    CardAmountRequest,
    CardPaymentHistoryItem,
    CardsSummaryResponse,
    CreditCardCreateRequest,
    CreditCardResponse,
    CreditCardUpdateRequest,
)
from app.api.v1.transactions.models import Transaction
from app.core.exceptions import NotFoundError, ValidationError
from app.deps import record_transaction


def _to_response(card: CreditCard) -> CreditCardResponse:
    return CreditCardResponse.model_validate(card)


async def list_cards(session: AsyncSession, user_id: uuid.UUID) -> list[CreditCardResponse]:
    cards = await repository.list_by_user(session, user_id)
    return [_to_response(c) for c in cards]


async def get_summary(session: AsyncSession, user_id: uuid.UUID) -> CardsSummaryResponse:
    cards = await list_cards(session, user_id)
    total_limit = sum((c.credit_limit for c in cards), Decimal("0"))
    total_outstanding = sum((c.outstanding for c in cards), Decimal("0"))
    utilization = float(total_outstanding / total_limit * 100) if total_limit else 0.0
    return CardsSummaryResponse(
        total_limit=total_limit,
        total_outstanding=total_outstanding,
        utilization_pct=round(utilization, 1),
        cards=cards,
    )


async def list_payment_history(
    session: AsyncSession, user_id: uuid.UUID, limit: int = 20
) -> list[CardPaymentHistoryItem]:
    """Recent card payments — txs linked to a card whose note ends with 'payment'."""
    cards = {c.id: c for c in await repository.list_by_user(session, user_id)}
    if not cards:
        return []
    result = await session.execute(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
            Transaction.card_id.is_not(None),
            Transaction.note.ilike("%payment%"),
        )
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .limit(limit)
    )
    items: list[CardPaymentHistoryItem] = []
    for txn in result.scalars().all():
        if txn.card_id is None:
            continue
        card = cards.get(txn.card_id)
        label = f"{card.bank} {card.name}" if card else (txn.note or "Card payment")
        sub = f"{txn.date.day} {txn.date.strftime('%b %Y')}"
        items.append(
            CardPaymentHistoryItem(
                id=txn.id,
                card_id=txn.card_id,
                label=label,
                sub=sub,
                amount=txn.amount,
                date=txn.date,
            )
        )
    return items


async def create_card(
    session: AsyncSession, user_id: uuid.UUID, payload: CreditCardCreateRequest
) -> CreditCardResponse:
    if payload.outstanding > payload.credit_limit:
        raise ValidationError("Outstanding cannot exceed credit limit")
    card = await repository.create(session, user_id, **payload.model_dump())
    return _to_response(card)


async def update_card(
    session: AsyncSession, user_id: uuid.UUID, card_id: uuid.UUID, payload: CreditCardUpdateRequest
) -> CreditCardResponse:
    card = await repository.get_by_id(session, card_id, user_id)
    if card is None:
        raise NotFoundError("Credit card not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(card, field, value)
    if card.outstanding > card.credit_limit:
        raise ValidationError("Outstanding cannot exceed credit limit")
    await session.flush()
    return _to_response(card)


async def delete_card(session: AsyncSession, user_id: uuid.UUID, card_id: uuid.UUID) -> None:
    card = await repository.get_by_id(session, card_id, user_id)
    if card is None:
        raise NotFoundError("Credit card not found")
    await repository.soft_delete(session, card)


async def record_payment(
    session: AsyncSession,
    user_id: uuid.UUID,
    card_id: uuid.UUID,
    account_id: uuid.UUID,
    payload: CardAmountRequest,
) -> CreditCardResponse:
    card = await repository.get_by_id(session, card_id, user_id)
    if card is None:
        raise NotFoundError("Credit card not found")
    if payload.amount > card.outstanding:
        raise ValidationError("Payment exceeds outstanding balance")
    from app.deps import list_categories

    categories = await list_categories(session)
    other = next((c for c in categories if c.name == "Other"), categories[0])
    category_id = payload.category_id or other.id
    await record_transaction(
        session,
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type_="expense",
        amount=payload.amount,
        date=dt.date.today(),
        note=payload.note or f"{card.bank} {card.name} payment",
        card_id=card.id,
    )
    card.outstanding -= payload.amount
    await session.flush()
    return _to_response(card)


async def record_spend(
    session: AsyncSession,
    user_id: uuid.UUID,
    card_id: uuid.UUID,
    payload: CardAmountRequest,
) -> CreditCardResponse:
    card = await repository.get_by_id(session, card_id, user_id)
    if card is None:
        raise NotFoundError("Credit card not found")
    if card.outstanding + payload.amount > card.credit_limit:
        raise ValidationError("Spend would exceed credit limit")
    from app.deps import list_categories

    categories = await list_categories(session)
    shopping = next((c for c in categories if c.name == "Shopping"), categories[0])
    category_id = payload.category_id or shopping.id
    await record_transaction(
        session,
        user_id=user_id,
        account_id=(await _default_account(session, user_id)),
        category_id=category_id,
        type_="expense",
        amount=payload.amount,
        date=dt.date.today(),
        note=payload.note or f"{card.bank} {card.name} spend",
        card_id=card.id,
    )
    card.outstanding += payload.amount
    await session.flush()
    return _to_response(card)


async def _default_account(session: AsyncSession, user_id: uuid.UUID) -> uuid.UUID:
    from app.api.v1.accounts.service import ensure_default_account

    account = await ensure_default_account(session, user_id)
    return account.id
