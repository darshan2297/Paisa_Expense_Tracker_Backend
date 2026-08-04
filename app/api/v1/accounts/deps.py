"""FastAPI dependency resolving "the account a new transaction attaches to".

Re-exported via `app.deps` for other feature modules (transactions,
fixed_commitments) to consume without importing this module directly - the
same pattern `app.deps` already uses for `auth`'s `CurrentUser` - see
docs/DEVELOPER_PHILOSOPHY.md §2.2.
"""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.accounts import service
from app.api.v1.auth.deps import CurrentUser
from app.core.database import get_session


async def get_default_account_id(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> uuid.UUID:
    account = await service.ensure_default_account(session, current_user.id)
    return account.id


DefaultAccountId = Annotated[uuid.UUID, Depends(get_default_account_id)]
