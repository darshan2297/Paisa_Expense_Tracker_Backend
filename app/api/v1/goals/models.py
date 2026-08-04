"""Goal ORM model — savings goals including optional emergency fund flag."""

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Goal(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "goals"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    saved_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    monthly_contribution: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    is_emergency: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    due_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
