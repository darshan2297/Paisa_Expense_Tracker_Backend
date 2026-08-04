"""HTTP layer for insurance policies."""

import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.policies import service
from app.api.v1.policies.schemas import (
    PoliciesSummaryResponse,
    PolicyCreateRequest,
    PolicyResponse,
    PolicyUpdateRequest,
)
from app.deps import CurrentUser, DefaultAccountId, InsuranceCategoryId, get_session
from app.middleware.rate_limit import default_limit

policies_router = APIRouter(prefix="/policies")


@policies_router.get("", summary="List insurance policies")
@default_limit()
async def list_policies(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> list[PolicyResponse]:
    return await service.list_policies(session, current_user.id)


@policies_router.get("/summary", summary="Policies summary")
@default_limit()
async def policies_summary(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PoliciesSummaryResponse:
    return await service.get_summary(session, current_user.id)


@policies_router.post("", status_code=201, summary="Create policy")
@default_limit()
async def create_policy(
    request: Request,
    payload: PolicyCreateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PolicyResponse:
    return await service.create_policy(session, current_user.id, payload)


@policies_router.patch("/{policy_id}", summary="Update policy")
@default_limit()
async def update_policy(
    request: Request,
    policy_id: uuid.UUID,
    payload: PolicyUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PolicyResponse:
    return await service.update_policy(session, current_user.id, policy_id, payload)


@policies_router.post("/{policy_id}/toggle-paid", summary="Mark this policy's premium paid/unpaid")
@default_limit()
async def toggle_premium_paid(
    request: Request,
    policy_id: uuid.UUID,
    current_user: CurrentUser,
    account_id: DefaultAccountId,
    category_id: InsuranceCategoryId,
    session: AsyncSession = Depends(get_session),
) -> PolicyResponse:
    return await service.toggle_premium_paid(
        session, current_user.id, policy_id, account_id, category_id
    )


@policies_router.delete("/{policy_id}", status_code=204, summary="Delete policy")
@default_limit()
async def delete_policy(
    request: Request,
    policy_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.delete_policy(session, current_user.id, policy_id)
    return Response(status_code=204)
