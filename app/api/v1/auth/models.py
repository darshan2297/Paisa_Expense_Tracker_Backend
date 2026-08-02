"""User ORM model.

Single `users` table (see docs/DATABASE_STANDARDS.md and the workspace
architecture plan): no separate `profiles`/`preferences` tables, since both
are a strict 1:1 with a user and splitting them out would be normalization
for its own sake with no real query benefit at this scale.

There is no public self-registration in this product (a deliberate decision
— see docs/DEVELOPMENT_GUIDE.md): the single user is created by
`scripts/seed.py`, and this table is designed for exactly one row today
while carrying the shape (its own primary key, `credential_version`-based
session revocation) that a future multi-user pivot would need.
"""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class User(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # ISO 4217 code. Single-currency in practice (INR) but stored explicitly
    # rather than assumed - see docs/DATABASE_STANDARDS.md.
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")

    # Day of month (1-28) the user considers their "month" to start on, for
    # budget/reporting period calculations in later phases.
    month_start_day: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")

    # --- Preferences (flat columns, not a separate table - see class docstring) ---
    dark_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    week_start_monday: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    round_up_savings: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    digest_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    sound_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    # Bumped on password change / explicit "log out everywhere". Checked
    # against the `cv` JWT claim on every authenticated request so a stale
    # access token stops working immediately, with no Redis denylist - see
    # docs/DEVELOPER_PHILOSOPHY.md §8.2.
    credential_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
