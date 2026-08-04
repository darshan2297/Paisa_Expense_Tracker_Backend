"""Business logic for insurance policies.

Uses `app.deps` (`find_transaction_for_policy`, `record_transaction`,
`remove_transaction_by_id`, all re-exported from `transactions.service`)
for the "mark premium paid" flow rather than importing `transactions`
directly - mirrors `fixed_commitments.service` and `bills.service`, see
docs/DEVELOPER_PHILOSOPHY.md §2.2.
"""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.policies import repository
from app.api.v1.policies.models import Policy
from app.api.v1.policies.schemas import (
    PoliciesSummaryResponse,
    PolicyCreateRequest,
    PolicyResponse,
    PolicyUpdateRequest,
)
from app.core.exceptions import NotFoundError
from app.deps import find_transaction_for_policy, record_transaction, remove_transaction_by_id

_FREQ_MULTIPLIER = {"monthly": 12, "quarterly": 4, "yearly": 1}


def _to_response(policy: Policy, linked_transaction_id: uuid.UUID | None) -> PolicyResponse:
    return PolicyResponse(
        id=policy.id,
        name=policy.name,
        provider=policy.provider,
        kind=policy.kind,
        cover_amount=policy.cover_amount,
        premium=policy.premium,
        frequency=policy.frequency,
        renewal_date=policy.renewal_date,
        note=policy.note,
        premium_paid=linked_transaction_id is not None,
        linked_transaction_id=linked_transaction_id,
    )


async def list_policies(session: AsyncSession, user_id: uuid.UUID) -> list[PolicyResponse]:
    rows = await repository.list_by_user(session, user_id)
    responses = []
    for policy in rows:
        linked_id = await find_transaction_for_policy(session, policy.id)
        responses.append(_to_response(policy, linked_id))
    return responses


async def get_summary(session: AsyncSession, user_id: uuid.UUID) -> PoliciesSummaryResponse:
    policies = await list_policies(session, user_id)
    total_cover = sum((p.cover_amount for p in policies), Decimal("0"))
    annual_premium = sum(
        (p.premium * _FREQ_MULTIPLIER.get(p.frequency, 1) for p in policies), Decimal("0")
    )
    next_renewal = policies[0] if policies else None
    return PoliciesSummaryResponse(
        total_cover=total_cover,
        annual_premium=annual_premium,
        policy_count=len(policies),
        next_renewal=next_renewal,
        policies=policies,
    )


async def create_policy(
    session: AsyncSession, user_id: uuid.UUID, payload: PolicyCreateRequest
) -> PolicyResponse:
    policy = await repository.create(session, user_id, **payload.model_dump())
    return _to_response(policy, None)


async def update_policy(
    session: AsyncSession, user_id: uuid.UUID, policy_id: uuid.UUID, payload: PolicyUpdateRequest
) -> PolicyResponse:
    policy = await repository.get_by_id(session, policy_id, user_id)
    if policy is None:
        raise NotFoundError("Policy not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    await session.flush()
    linked_id = await find_transaction_for_policy(session, policy.id)
    return _to_response(policy, linked_id)


async def delete_policy(session: AsyncSession, user_id: uuid.UUID, policy_id: uuid.UUID) -> None:
    policy = await repository.get_by_id(session, policy_id, user_id)
    if policy is None:
        raise NotFoundError("Policy not found")
    await repository.soft_delete(session, policy)


async def toggle_premium_paid(
    session: AsyncSession,
    user_id: uuid.UUID,
    policy_id: uuid.UUID,
    account_id: uuid.UUID,
    category_id: uuid.UUID,
) -> PolicyResponse:
    """Mirrors fixed_commitments.service.toggle_paid / bills.service's
    equivalent: soft-deletes the linked transaction if one already exists
    for this policy, else records one dated today for the premium amount.
    """
    policy = await repository.get_by_id(session, policy_id, user_id)
    if policy is None:
        raise NotFoundError("Policy not found")

    existing_linked_id = await find_transaction_for_policy(session, policy.id)
    if existing_linked_id is not None:
        await remove_transaction_by_id(session, existing_linked_id)
        return _to_response(policy, None)

    new_transaction_id = await record_transaction(
        session,
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type_="expense",
        amount=policy.premium,
        date=dt.date.today(),
        note=f"{policy.name} premium",
        policy_id=policy.id,
    )
    return _to_response(policy, new_transaction_id)
