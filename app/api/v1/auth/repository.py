"""Data access for the `users` table.

Returns ORM objects (or `None`); never raises `HTTPException` and never
contains business rules - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.models import User


async def count_users(session: AsyncSession) -> int:
    """Count of non-deleted users - used to gate one-time registration
    (see service.register): this product has no ongoing public signup, only
    a single bootstrap account creation while the table is empty.
    """
    result = await session.execute(
        select(func.count()).select_from(User).where(User.deleted_at.is_(None))
    )
    return result.scalar_one()


async def get_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_by_id(session: AsyncSession, user_id: uuid.UUID | str) -> User | None:
    result = await session.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, **fields: object) -> User:
    user = User(**fields)
    session.add(user)
    await session.flush()
    return user
