"""Bank import job ORM models."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, TimestampMixin, UUIDPKMixin


class ImportJob(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "import_jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="uploaded")
    row_count: Mapped[int] = mapped_column(nullable=False, server_default="0")


class ImportRow(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "import_rows"

    job_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("import_jobs.id"), nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    merchant: Mapped[str] = mapped_column(String(512), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    suggested_category_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    state: Mapped[str] = mapped_column(String(16), nullable=False, server_default="ready")
    duplicate_of_txn_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
