"""Bill ORM model — one-off and recurring utility/subscription bills (F5).

Separate from `fixed_commitments` (monthly EMIs with due_day). Bills carry a
full due date, frequency, auto-pay flag, and per-bill lead days — matching the
design's `bills` array.
"""

import datetime as dt
import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class BillFrequency(StrEnum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class BillKind(StrEnum):
    ELECTRICITY = "electricity"
    INTERNET = "internet"
    MOBILE = "mobile"
    CREDIT_CARD = "credit_card"
    GAS = "gas"
    OTHER = "other"


class Bill(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "bills"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    due_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False, server_default="monthly")
    auto_pay: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    lead_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="3")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_on: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
