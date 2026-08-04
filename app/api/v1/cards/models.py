"""Credit card ORM model (F6)."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class CreditCard(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "credit_cards"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    bank: Mapped[str] = mapped_column(String(255), nullable=False)
    network: Mapped[str] = mapped_column(String(64), nullable=False, server_default="Visa")
    last4: Mapped[str] = mapped_column(String(4), nullable=False)
    credit_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    outstanding: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    statement_day: Mapped[int] = mapped_column(Integer, nullable=False)
    due_day: Mapped[int] = mapped_column(Integer, nullable=False)
    opened_on: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
