"""User ORM model — auth identity and profile fields only.

Customizable settings live in `configurations` (catalog) and
`user_configurations` (per-user values). Operational security state
(`vault_locked`, backup metadata) stays here.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class User(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Account-level app PIN (bcrypt). Nullable until the user completes PIN setup.
    # Device unlock still caches a local hash; this column is the source of truth
    # across browsers/devices (see docs/DEVELOPER_PHILOSOPHY.md §8.6).
    hashed_pin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    vault_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_backup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_backup_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    credential_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
