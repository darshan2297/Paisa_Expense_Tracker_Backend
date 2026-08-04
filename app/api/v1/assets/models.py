"""Asset ORM model."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class Asset(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "assets"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    purchase_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    acquired_on: Mapped[dt.date | None] = mapped_column(Date, nullable=True)


class NetWorthSnapshot(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "net_worth_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    snapshot_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    total_assets: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    net_worth: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    breakdown_json: Mapped[str] = mapped_column(String, nullable=False, server_default="{}")
