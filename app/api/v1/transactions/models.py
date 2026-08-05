"""Transaction ORM model.

The core ledger row - see F3 in `docs/FEATURE_ROADMAP.md`. Every other
domain in this slice (Overview summary, Planned/Budget spend tracking,
Fixed Commitments "mark paid") reads from or writes to this table, so its
`(user_id, date)` composite index matters from day one - see
docs/DATABASE_STANDARDS.md.

No `category`/`account` ORM relationships are declared here even though FK
columns exist: display info for those is resolved by the service layer via
`app.deps` (`get_category`), not an ORM-level cross-module join - see
docs/DEVELOPER_PHILOSOPHY.md §2.2 (feature modules never import another
feature module's `models.py` directly, including for relationships).
"""

import datetime as dt
import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Date, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class TransactionType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class Transaction(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_user_id_date", "user_id", "date"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # How cash moved: cash / upi / card / netbanking / cheque / other.
    payment_method: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Relative path under STORAGE_DIR, e.g. receipts/{user_id}/{txn_id}.jpg
    receipt_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Nullable FK to `fixed_commitments.id` (added by the F5 migration,
    # after both tables already exist) - a transaction created by "mark
    # commitment paid" links back to it so "toggle paid" can find and
    # remove it again. NULL for every ordinary, manually-entered transaction.
    fixed_commitment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fixed_commitments.id"), nullable=True
    )
    bill_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("bills.id"), nullable=True
    )
    card_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("credit_cards.id"), nullable=True
    )
    policy_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("policies.id"), nullable=True
    )
    ledger_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("ledger_entries.id"), nullable=True
    )
