"""Data access for credit cards."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.cards.models import CreditCard


async def list_by_user(session: AsyncSession, user_id: uuid.UUID | str) -> list[CreditCard]:
    result = await session.execute(
        select(CreditCard)
        .where(CreditCard.user_id == user_id, CreditCard.deleted_at.is_(None))
        .order_by(CreditCard.name)
    )
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, card_id: uuid.UUID | str, user_id: uuid.UUID | str
) -> CreditCard | None:
    result = await session.execute(
        select(CreditCard).where(
            CreditCard.id == card_id,
            CreditCard.user_id == user_id,
            CreditCard.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, user_id: uuid.UUID | str, **fields: object) -> CreditCard:
    card = CreditCard(user_id=user_id, **fields)
    session.add(card)
    await session.flush()
    return card


async def soft_delete(session: AsyncSession, card: CreditCard) -> None:
    card.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
