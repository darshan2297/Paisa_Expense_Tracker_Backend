"""Milestone ORM model."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Milestone(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "milestones"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(String(512), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
