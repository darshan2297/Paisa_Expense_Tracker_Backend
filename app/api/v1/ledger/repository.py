"""Data access for ledger entries."""

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.ledger.models import LedgerEntry


async def list_by_user(
    session: AsyncSession, user_id: uuid.UUID, person: str | None = None
) -> list[LedgerEntry]:
    stmt = select(LedgerEntry).where(LedgerEntry.user_id == user_id, LedgerEntry.deleted_at.is_(None))
    if person:
        stmt = stmt.where(LedgerEntry.person_name.ilike(person))
    stmt = stmt.order_by(LedgerEntry.date.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_by_id(session: AsyncSession, entry_id: uuid.UUID, user_id: uuid.UUID) -> LedgerEntry | None:
    result = await session.execute(
        select(LedgerEntry).where(
            LedgerEntry.id == entry_id, LedgerEntry.user_id == user_id, LedgerEntry.deleted_at.is_(None)
        )
    )
    return result.scalar_one_or_none()


async def create(session: AsyncSession, user_id: uuid.UUID, **kwargs: object) -> LedgerEntry:
    entry = LedgerEntry(user_id=user_id, **kwargs)  # type: ignore[arg-type]
    session.add(entry)
    await session.flush()
    return entry


async def soft_delete(session: AsyncSession, entry: LedgerEntry) -> None:
    entry.deleted_at = dt.datetime.now(dt.UTC)
    await session.flush()
