"""Data access for the `accounts` table.

Returns ORM objects (or `None`); never raises and never contains business
rules - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.accounts.models import Account, AccountKind


async def list_accounts(session: AsyncSession, user_id: uuid.UUID | str) -> list[Account]:
    result = await session.execute(
        select(Account)
        .where(Account.user_id == user_id, Account.deleted_at.is_(None))
        .order_by(Account.created_at)
    )
    return list(result.scalars().all())


async def get_default_account(session: AsyncSession, user_id: uuid.UUID | str) -> Account | None:
    """The account transactions attach to - currently just "the user's
    first account", since there's no account-selection UI yet (see the
    module docstring in `models.py`).
    """
    result = await session.execute(
        select(Account)
        .where(Account.user_id == user_id, Account.deleted_at.is_(None))
        .order_by(Account.created_at)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_account(
    session: AsyncSession,
    user_id: uuid.UUID | str,
    name: str,
    kind: AccountKind = AccountKind.CASH,
) -> Account:
    account = Account(user_id=user_id, name=name, kind=kind.value)
    session.add(account)
    await session.flush()
    return account
