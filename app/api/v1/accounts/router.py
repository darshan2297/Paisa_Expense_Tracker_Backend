"""HTTP layer for accounts. Thin adapter only - no business logic, no direct
DB access. See docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.accounts import service
from app.api.v1.accounts.schemas import AccountResponse
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

accounts_router = APIRouter(prefix="/accounts")


@accounts_router.get("", summary="List the current user's accounts")
@default_limit()
async def list_accounts(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[AccountResponse]:
    return await service.list_accounts(session, current_user.id)
