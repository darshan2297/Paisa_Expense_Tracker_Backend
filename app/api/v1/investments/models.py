"""Investment ORM model."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Investment(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "investments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    invested_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    monthly_sip: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, server_default="0")
    opened_on: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
