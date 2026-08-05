"""Business logic for transactions.

Receives/returns plain values or Pydantic schemas; never constructs an
`HTTPException` - see docs/DEVELOPER_PHILOSOPHY.md §2.1.

Functions here take a `cat_by_id` lookup (built by the router from
`app.deps.list_categories`) instead of importing the categories module
directly - this file is never allowed to import `app.deps` itself, since
`app.deps` will (from F4 onward) import `get_month_totals` back out of this
module for the budget module to reuse; if this module also imported
`app.deps`, that would be a circular import. See
docs/DEVELOPER_PHILOSOPHY.md §2.2.
"""

import datetime as dt
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.categories.schemas import CategoryResponse
from app.api.v1.transactions import repository
from app.api.v1.transactions.models import Transaction, TransactionType
from app.api.v1.transactions.schemas import (
    CategoryBreakdownItem,
    TransactionCreateRequest,
    TransactionListResponse,
    TransactionResponse,
    TransactionsSummaryResponse,
    TransactionUpdateRequest,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.core.pagination import PageParams
from app.core.storage import (
    ALLOWED_RECEIPT_CONTENT_TYPES,
    MAX_RECEIPT_BYTES,
    extension_for,
    receipt_dir,
    resolve_stored_path,
)

_UNKNOWN_CATEGORY_COLOR = "#A79E92"


def _to_response(
    transaction: Transaction, cat_by_id: dict[uuid.UUID, CategoryResponse]
) -> TransactionResponse:
    category = cat_by_id.get(transaction.category_id)
    if category is None:
        # Defensive: categories are a fixed seeded taxonomy that's never
        # deleted in this phase, so this should never trigger in practice.
        category = CategoryResponse(
            id=transaction.category_id,
            kind=transaction.type,
            name="Unknown",
            color=_UNKNOWN_CATEGORY_COLOR,
            sort_order=0,
        )
    has_receipt = bool(transaction.receipt_path)
    return TransactionResponse(
        id=transaction.id,
        account_id=transaction.account_id,
        type=transaction.type,
        amount=transaction.amount,
        currency=transaction.currency,
        date=transaction.date,
        note=transaction.note,
        category=category,
        created_at=transaction.created_at,
        has_receipt=has_receipt,
        receipt_url=f"/api/v1/transactions/{transaction.id}/receipt" if has_receipt else None,
    )


async def list_transactions(
    session: AsyncSession,
    user_id: uuid.UUID,
    month: str,
    type_filter: str | None,
    query: str | None,
    params: PageParams,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
) -> TransactionListResponse:
    matching_category_ids = None
    if query:
        matching_category_ids = [
            c.id for c in cat_by_id.values() if query.lower() in c.name.lower()
        ]

    rows, total = await repository.list_transactions(
        session, user_id, month, type_filter, query, matching_category_ids, params
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return TransactionListResponse(
        data=[_to_response(t, cat_by_id) for t in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


async def get_summary(
    session: AsyncSession,
    user_id: uuid.UUID,
    month: str,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
    card_only: bool = False,
) -> TransactionsSummaryResponse:
    income_total, expense_total = await get_month_totals(session, user_id, month)

    # `card_only` scopes just the category breakdown to card-linked spend
    # (see Credit Cards' "Category spending on cards" panel) - income/expense
    # totals and recent activity stay whole-month, matching every other
    # caller of this same summary (This Month, Overview).
    category_sums = await repository.sum_expense_by_category(session, user_id, month, card_only)
    breakdown = []
    for category_id, amount in category_sums:
        category = cat_by_id.get(category_id)
        pct = float(amount / expense_total * 100) if expense_total else 0.0
        breakdown.append(
            CategoryBreakdownItem(
                category_id=category_id,
                name=category.name if category else "Unknown",
                color=category.color if category else _UNKNOWN_CATEGORY_COLOR,
                amount=amount,
                pct=round(pct, 1),
            )
        )

    recent = await repository.list_recent(session, user_id, month, limit=6)
    return TransactionsSummaryResponse(
        income_total=income_total,
        expense_total=expense_total,
        net_balance=income_total - expense_total,
        category_breakdown=breakdown,
        recent=[_to_response(t, cat_by_id) for t in recent],
    )


async def create_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    payload: TransactionCreateRequest,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
) -> TransactionResponse:
    category = cat_by_id.get(payload.category_id)
    if category is None:
        raise NotFoundError("Category not found")
    if category.kind != payload.type:
        raise ValidationError(
            f"'{category.name}' is a {category.kind} category, not {payload.type}"
        )

    transaction = await repository.create_transaction(
        session,
        user_id=user_id,
        account_id=account_id,
        category_id=payload.category_id,
        type=payload.type,
        amount=payload.amount,
        date=payload.date,
        note=payload.note,
    )
    return _to_response(transaction, cat_by_id)


async def delete_transaction(
    session: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> None:
    transaction = await repository.get_by_id(session, transaction_id, user_id)
    if transaction is None:
        raise NotFoundError("Transaction not found")
    await repository.soft_delete(session, transaction)


async def attach_receipt(
    session: AsyncSession,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    file: UploadFile,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
) -> TransactionResponse:
    """Store a receipt/slip image for an existing transaction under STORAGE_DIR."""
    transaction = await repository.get_by_id(session, transaction_id, user_id)
    if transaction is None:
        raise NotFoundError("Transaction not found")

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_RECEIPT_CONTENT_TYPES:
        raise ValidationError("Receipt must be a JPG, PNG, WEBP, or PDF file")

    data = await file.read()
    if not data:
        raise ValidationError("Receipt file is empty")
    if len(data) > MAX_RECEIPT_BYTES:
        raise ValidationError("Receipt must be 10 MB or smaller")

    ext = extension_for(content_type, file.filename)
    relative = f"receipts/{user_id}/{transaction_id}{ext}"
    dest = receipt_dir(str(user_id)) / f"{transaction_id}{ext}"

    # Replace any previous receipt file for this transaction.
    if transaction.receipt_path:
        try:
            old = resolve_stored_path(transaction.receipt_path)
            if old.is_file():
                old.unlink()
        except ValueError:
            pass

    dest.write_bytes(data)
    transaction.receipt_path = relative
    await session.flush()
    return _to_response(transaction, cat_by_id)


def receipt_file_path(transaction: Transaction) -> Path:
    if not transaction.receipt_path:
        raise NotFoundError("No receipt attached")
    path = resolve_stored_path(transaction.receipt_path)
    if not path.is_file():
        raise NotFoundError("Receipt file missing")
    return path


async def get_transaction_for_receipt(
    session: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction:
    transaction = await repository.get_by_id(session, transaction_id, user_id)
    if transaction is None:
        raise NotFoundError("Transaction not found")
    if not transaction.receipt_path:
        raise NotFoundError("No receipt attached")
    return transaction


async def update_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: TransactionUpdateRequest,
    cat_by_id: dict[uuid.UUID, CategoryResponse],
) -> TransactionResponse:
    transaction = await repository.get_by_id(session, transaction_id, user_id)
    if transaction is None:
        raise NotFoundError("Transaction not found")
    if payload.category_id is not None:
        category = cat_by_id.get(payload.category_id)
        if category is None:
            raise NotFoundError("Category not found")
        if category.kind != transaction.type:
            raise ValidationError(f"'{category.name}' is not a {transaction.type} category")
        transaction.category_id = payload.category_id
    if payload.amount is not None:
        transaction.amount = payload.amount
    if payload.date is not None:
        transaction.date = payload.date
    if payload.note is not None:
        transaction.note = payload.note
    await session.flush()
    return _to_response(transaction, cat_by_id)


async def get_month_totals(
    session: AsyncSession, user_id: uuid.UUID, month: str
) -> tuple[Decimal, Decimal]:
    """`(income_total, expense_total)` for the month.

    Reused by the budget module (via `app.deps`, from F4 onward) to compute
    "spent this month" without duplicating this aggregation query - see the
    module docstring re: why this file never imports `app.deps` itself.
    """
    totals = await repository.sum_by_type(session, user_id, month)
    return (
        totals.get(TransactionType.INCOME.value, Decimal(0)),
        totals.get(TransactionType.EXPENSE.value, Decimal(0)),
    )


async def get_all_time_totals(session: AsyncSession, user_id: uuid.UUID) -> tuple[Decimal, Decimal]:
    """`(income_total, expense_total)` across every transaction ever recorded.

    Reused by the net_worth module to derive net cash (income - expense) the
    same way `get_month_totals` derives a single month's totals - see that
    function's docstring for why this file never imports `app.deps` itself.
    """
    totals = await repository.sum_by_type_all_time(session, user_id)
    return (
        totals.get(TransactionType.INCOME.value, Decimal(0)),
        totals.get(TransactionType.EXPENSE.value, Decimal(0)),
    )


async def record_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    category_id: uuid.UUID,
    type_: str,
    amount: Decimal,
    date: dt.date,
    note: str | None,
    fixed_commitment_id: uuid.UUID | None = None,
    bill_id: uuid.UUID | None = None,
    card_id: uuid.UUID | None = None,
    policy_id: uuid.UUID | None = None,
    ledger_entry_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Create a transaction row and return just its id.

    Reused by the fixed-commitments module (via `app.deps`, from F5
    onward) for its "mark commitment paid" action - it only needs the new
    row's id to store as `linked_transaction_id`, not a full
    `TransactionResponse` (it has no `cat_by_id` to build one with). Also
    reused by policies' "mark premium paid" the same way.
    """
    transaction = await repository.create_transaction(
        session,
        user_id=user_id,
        account_id=account_id,
        category_id=category_id,
        type=type_,
        amount=amount,
        date=date,
        note=note,
        fixed_commitment_id=fixed_commitment_id,
        bill_id=bill_id,
        card_id=card_id,
        policy_id=policy_id,
        ledger_entry_id=ledger_entry_id,
    )
    return transaction.id


async def find_transaction_for_commitment(
    session: AsyncSession, fixed_commitment_id: uuid.UUID, month: str
) -> uuid.UUID | None:
    """Reused by fixed_commitments (via `app.deps`) to check whether a
    commitment's "mark paid" transaction already exists for a given month.
    """
    transaction = await repository.get_by_fixed_commitment_and_month(
        session, fixed_commitment_id, month
    )
    return transaction.id if transaction else None


async def find_transaction_for_bill(
    session: AsyncSession, bill_id: uuid.UUID, due_date: dt.date
) -> uuid.UUID | None:
    transaction = await repository.get_by_bill_and_due_date(session, bill_id, due_date)
    return transaction.id if transaction else None


async def find_transaction_for_policy(
    session: AsyncSession, policy_id: uuid.UUID
) -> uuid.UUID | None:
    transaction = await repository.get_latest_by_policy_id(session, policy_id)
    return transaction.id if transaction else None


async def find_transaction_for_ledger_entry(
    session: AsyncSession, ledger_entry_id: uuid.UUID
) -> uuid.UUID | None:
    transaction = await repository.get_by_ledger_entry_id(session, ledger_entry_id)
    return transaction.id if transaction else None


async def remove_transaction_by_id(session: AsyncSession, transaction_id: uuid.UUID) -> None:
    """Soft-delete without an ownership check - reused by fixed_commitments
    (via `app.deps`) "un-pay" flow, which already resolved this id from a
    commitment it verified belongs to the current user.
    """
    transaction = await repository.get_by_id_unscoped(session, transaction_id)
    if transaction is not None and transaction.deleted_at is None:
        await repository.soft_delete(session, transaction)
