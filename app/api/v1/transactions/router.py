"""HTTP layer for transactions. Thin adapter only - no business logic, no
direct DB access. See docs/DEVELOPER_PHILOSOPHY.md §2.1.

Resolves the category taxonomy once per request via `app.deps.list_categories`
(re-exported from the `categories` module) and passes it into the service
layer as a plain `cat_by_id` dict, rather than the service layer importing
`categories` itself - see `transactions.service`'s module docstring.
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.transactions import service
from app.api.v1.transactions.schemas import (
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
    TransactionsSummaryResponse,
)
from app.deps import CurrentUser, DefaultAccountId, PageParamsDep, get_session, list_categories
from app.middleware.rate_limit import default_limit

transactions_router = APIRouter(prefix="/transactions")

_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@transactions_router.get("", summary="List the current user's transactions for a month")
@default_limit()
async def list_transactions(
    request: Request,
    current_user: CurrentUser,
    params: PageParamsDep,
    month: str = Query(pattern=_MONTH_PATTERN, description='"YYYY-MM"'),
    type_filter: str | None = Query(default=None, alias="type", pattern="^(expense|income)$"),
    q: str | None = Query(default=None, max_length=200),
    session: AsyncSession = Depends(get_session),
) -> TransactionListResponse:
    categories = await list_categories(session)
    cat_by_id = {c.id: c for c in categories}
    return await service.list_transactions(session, current_user.id, month, type_filter, q, params, cat_by_id)


@transactions_router.get("/summary", summary="Income/expense/category totals for a month")
@default_limit()
async def get_summary(
    request: Request,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN, description='"YYYY-MM"'),
    session: AsyncSession = Depends(get_session),
) -> TransactionsSummaryResponse:
    categories = await list_categories(session)
    cat_by_id = {c.id: c for c in categories}
    return await service.get_summary(session, current_user.id, month, cat_by_id)


@transactions_router.post("", status_code=201, summary="Create a transaction")
@default_limit()
async def create_transaction(
    request: Request,
    payload: TransactionCreateRequest,
    current_user: CurrentUser,
    account_id: DefaultAccountId,
    session: AsyncSession = Depends(get_session),
) -> TransactionResponse:
    categories = await list_categories(session)
    cat_by_id = {c.id: c for c in categories}
    return await service.create_transaction(session, current_user.id, account_id, payload, cat_by_id)


@transactions_router.delete("/{transaction_id}", status_code=204, summary="Delete a transaction")
@default_limit()
async def delete_transaction(
    request: Request,
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_transaction(session, current_user.id, transaction_id)
    return Response(status_code=204)
