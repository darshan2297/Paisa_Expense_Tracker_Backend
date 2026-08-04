"""Loan ORM model."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Loan(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "loans"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    principal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    rate_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    tenure_months: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    outstanding: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
