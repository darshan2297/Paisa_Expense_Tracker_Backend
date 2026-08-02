"""FixedCommitment ORM model.

Recurring EMIs/loans/subscriptions/bills the user pays every month - the
fixed-commitments slice of F5 in `docs/FEATURE_ROADMAP.md` (full Bills
support - one-off bills, due-date push reminders via APScheduler - is
still ⬜, tracked separately).
"""

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class FixedCommitmentKind(StrEnum):
    EMI = "emi"
    HOME_LOAN = "home_loan"
    PERSONAL_LOAN = "personal_loan"
    SUBSCRIPTION = "subscription"
    BILL = "bill"


class FixedCommitment(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "fixed_commitments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Day of month (1-28, matching the design's `Math.min(dueDay, 28)`
    # clamp so every commitment has a valid date even in February).
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
