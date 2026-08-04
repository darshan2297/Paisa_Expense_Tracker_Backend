"""HTTP layer for fixed commitments. Thin adapter only - no business logic,
no direct DB access. See docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.fixed_commitments import service
from app.api.v1.fixed_commitments.schemas import (
    FixedCommitmentCreateRequest,
    FixedCommitmentResponse,
    FixedCommitmentUpdateRequest,
)
from app.deps import CurrentUser, DefaultAccountId, get_session, list_categories
from app.middleware.rate_limit import default_limit

fixed_commitments_router = APIRouter(prefix="/fixed-commitments")

_MONTH_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@fixed_commitments_router.get("", summary="List fixed commitments with this month's paid status")
@default_limit()
async def list_fixed_commitments(
    request: Request,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN, description='"YYYY-MM"'),
    session: AsyncSession = Depends(get_session),
) -> list[FixedCommitmentResponse]:
    categories = await list_categories(session)
    cat_by_id = {c.id: c for c in categories}
    return await service.list_commitments(session, current_user.id, month, cat_by_id)


@fixed_commitments_router.post("", status_code=201, summary="Create a fixed commitment")
@default_limit()
async def create_fixed_commitment(
    request: Request,
    payload: FixedCommitmentCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> FixedCommitmentResponse:
    categories = await list_categories(session)
    cat_by_id = {c.id: c for c in categories}
    return await service.create_commitment(session, current_user.id, payload, cat_by_id)


@fixed_commitments_router.patch("/{commitment_id}", summary="Update a fixed commitment")
@default_limit()
async def update_fixed_commitment(
    request: Request,
    commitment_id: uuid.UUID,
    payload: FixedCommitmentUpdateRequest,
    current_user: CurrentUser,
    month: str = Query(pattern=_MONTH_PATTERN, description='"YYYY-MM"'),
    session: AsyncSession = Depends(get_session),
) -> FixedCommitmentResponse:
    categories = await list_categories(session)
    cat_by_id = {c.id: c for c in categories}
    return await service.update_commitment(
        session, current_user.id, commitment_id, payload, cat_by_id, month
    )


@fixed_commitments_router.delete(
    "/{commitment_id}", status_code=204, summary="Delete a fixed commitment"
)
@default_limit()
async def delete_fixed_commitment(
    request: Request,
    commitment_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_commitment(session, current_user.id, commitment_id)
    return Response(status_code=204)


@fixed_commitments_router.post(
    "/{commitment_id}/toggle-paid", summary="Mark a commitment paid/unpaid for a month"
)
@default_limit()
async def toggle_paid(
    request: Request,
    commitment_id: uuid.UUID,
    current_user: CurrentUser,
    account_id: DefaultAccountId,
    month: str = Query(pattern=_MONTH_PATTERN, description='"YYYY-MM"'),
    session: AsyncSession = Depends(get_session),
) -> FixedCommitmentResponse:
    categories = await list_categories(session)
    cat_by_id = {c.id: c for c in categories}
    return await service.toggle_paid(
        session, current_user.id, commitment_id, month, account_id, cat_by_id
    )
