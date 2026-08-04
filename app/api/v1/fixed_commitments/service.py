"""Business logic for fixed commitments.

Receives/returns plain values or Pydantic schemas; never constructs an
`HTTPException` - see docs/DEVELOPER_PHILOSOPHY.md §2.1.

Uses `app.deps` (`find_transaction_for_commitment`, `record_transaction`,
`remove_transaction_by_id`, all re-exported from `transactions.service`)
for the "mark paid" flow rather than importing `transactions` directly -
see docs/DEVELOPER_PHILOSOPHY.md §2.2. Safe to import `app.deps` here:
nothing re-exports *from* this module, so there's no import cycle.
"""

import datetime as dt
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.categories.schemas import CategoryResponse
from app.api.v1.fixed_commitments import repository
from app.api.v1.fixed_commitments.models import FixedCommitment
from app.api.v1.fixed_commitments.schemas import FixedCommitmentCreateRequest, FixedCommitmentResponse, FixedCommitmentUpdateRequest
from app.core.exceptions import NotFoundError
from app.deps import find_transaction_for_commitment, record_transaction, remove_transaction_by_id

_UNKNOWN_CATEGORY_COLOR = "#A79E92"


def _to_response(
    commitment: FixedCommitment,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
    linked_transaction_id: uuid.UUID | None,
) -> FixedCommitmentResponse:
    category = cat_by_id.get(commitment.category_id)
    if category is None:
        category = CategoryResponse(
            id=commitment.category_id, kind="expense", name="Unknown", color=_UNKNOWN_CATEGORY_COLOR, sort_order=0
        )
    return FixedCommitmentResponse(
        id=commitment.id,
        name=commitment.name,
        category=category,
        amount=commitment.amount,
        due_day=commitment.due_day,
        kind=commitment.kind,
        paid_this_month=linked_transaction_id is not None,
        linked_transaction_id=linked_transaction_id,
    )


async def list_commitments(
    session: AsyncSession,
    user_id: uuid.UUID,
    month: str,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
) -> list[FixedCommitmentResponse]:
    commitments = await repository.list_by_user(session, user_id)
    responses = []
    for commitment in commitments:
        linked_id = await find_transaction_for_commitment(session, commitment.id, month)
        responses.append(_to_response(commitment, cat_by_id, linked_id))
    return responses


async def create_commitment(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: FixedCommitmentCreateRequest,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
) -> FixedCommitmentResponse:
    category = cat_by_id.get(payload.category_id)
    if category is None:
        raise NotFoundError("Category not found")

    commitment = await repository.create(
        session,
        user_id=user_id,
        name=payload.name,
        category_id=payload.category_id,
        amount=payload.amount,
        due_day=payload.due_day,
        kind=payload.kind,
    )
    return _to_response(commitment, cat_by_id, None)


async def update_commitment(
    session: AsyncSession,
    user_id: uuid.UUID,
    commitment_id: uuid.UUID,
    payload: FixedCommitmentUpdateRequest,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
    month: str,
) -> FixedCommitmentResponse:
    commitment = await repository.get_by_id(session, commitment_id, user_id)
    if commitment is None:
        raise NotFoundError("Fixed commitment not found")
    if payload.category_id is not None:
        if cat_by_id.get(payload.category_id) is None:
            raise NotFoundError("Category not found")
        commitment.category_id = payload.category_id
    if payload.name is not None:
        commitment.name = payload.name
    if payload.amount is not None:
        commitment.amount = payload.amount
    if payload.due_day is not None:
        commitment.due_day = payload.due_day
    if payload.kind is not None:
        commitment.kind = payload.kind
    await session.flush()
    linked_id = await find_transaction_for_commitment(session, commitment.id, month)
    return _to_response(commitment, cat_by_id, linked_id)


async def delete_commitment(session: AsyncSession, user_id: uuid.UUID, commitment_id: uuid.UUID) -> None:
    commitment = await repository.get_by_id(session, commitment_id, user_id)
    if commitment is None:
        raise NotFoundError("Fixed commitment not found")
    await repository.soft_delete(session, commitment)


async def toggle_paid(
    session: AsyncSession,
    user_id: uuid.UUID,
    commitment_id: uuid.UUID,
    month: str,
    account_id: uuid.UUID,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
) -> FixedCommitmentResponse:
    """Mirrors the design's `toggleFixedPaid`: soft-deletes the linked
    transaction if one already exists for this month, else creates one.
    """
    commitment = await repository.get_by_id(session, commitment_id, user_id)
    if commitment is None:
        raise NotFoundError("Fixed commitment not found")

    existing_linked_id = await find_transaction_for_commitment(session, commitment.id, month)
    if existing_linked_id is not None:
        await remove_transaction_by_id(session, existing_linked_id)
        return _to_response(commitment, cat_by_id, None)

    year, mon = (int(part) for part in month.split("-"))
    due_date = dt.date(year, mon, min(commitment.due_day, 28))
    new_transaction_id = await record_transaction(
        session,
        user_id=user_id,
        account_id=account_id,
        category_id=commitment.category_id,
        type_="expense",
        amount=commitment.amount,
        date=due_date,
        note=commitment.name,
        fixed_commitment_id=commitment.id,
    )
    return _to_response(commitment, cat_by_id, new_transaction_id)
