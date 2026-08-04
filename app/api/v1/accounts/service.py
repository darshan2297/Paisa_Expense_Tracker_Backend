"""Business logic for accounts.

Receives/returns plain values or Pydantic schemas; never constructs an
`HTTPException` - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.accounts import repository
from app.api.v1.accounts.models import Account, AccountKind
from app.api.v1.accounts.schemas import AccountResponse


async def ensure_default_account(session: AsyncSession, user_id: uuid.UUID | str) -> Account:
    """Idempotent get-or-create for the user's single implicit account.

    Called from `auth.service.register` (via `app.deps`, never a direct
    import - see docs/DEVELOPER_PHILOSOPHY.md §2.2 module-isolation rule)
    so every user has an account before they can log a transaction. Also
    self-heals if one is ever missing when a transaction is created
    (defensive; not expected in practice since registration always creates
    one).
    """
    account = await repository.get_default_account(session, user_id)
    if account is not None:
        return account
    return await repository.create_account(session, user_id, name="Cash", kind=AccountKind.CASH)


async def list_accounts(session: AsyncSession, user_id: uuid.UUID | str) -> list[AccountResponse]:
    accounts = await repository.list_accounts(session, user_id)
    return [AccountResponse.model_validate(a) for a in accounts]
