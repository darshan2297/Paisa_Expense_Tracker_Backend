"""HTTP layer for categories. Thin adapter only - no business logic, no
direct DB access. See docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.categories import service
from app.api.v1.categories.schemas import CategoryResponse
from app.deps import CurrentUser, get_session
from app.middleware.rate_limit import default_limit

categories_router = APIRouter(prefix="/categories")


@categories_router.get("", summary="List the seeded expense/income category taxonomy")
@default_limit()
async def list_categories(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[CategoryResponse]:
    return await service.list_categories(session)
