"""Declarative base and reusable mixins for SQLAlchemy 2.0 ORM models.

Uses the typed `Mapped` / `mapped_column` style exclusively — never the
legacy `Column`/`Query` API. All domain models (added in later phases)
should inherit `Base` plus whichever mixins apply.

Money/domain conventions for future phases (NOT implemented here, no
domain models exist yet in Phase-0):
  - Money columns are always `NUMERIC(14, 2)` (SQLAlchemy `Numeric(14, 2)`),
    paired with a `currency: Mapped[str]` column typed `VARCHAR(3)`
    (ISO 4217 code, e.g. "INR", "USD"). NEVER use `Float`/`float` for money —
    binary floating point cannot represent currency exactly and will
    silently corrupt balances over time.
  - Every domain table (accounts, transactions, budgets, etc.) will carry a
    `user_id: Mapped[uuid.UUID]` foreign key to the users table once auth
    lands, enforcing per-user data isolation at the schema level.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class UUIDPKMixin:
    """Adds a UUID primary key column named `id`, generated client-side.

    Using a client-generated UUID (rather than a DB sequence) means the id
    is known immediately after construction, before the row is flushed —
    useful for building related objects in the same unit of work.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Adds `created_at` / `updated_at` columns with server-side defaults.

    Both timestamps are set by the database itself (`server_default=func.now()`)
    rather than application code, so they remain correct regardless of which
    process/timezone the app server runs in, and are always populated even
    for rows inserted outside the ORM (e.g. raw SQL, migrations).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Adds a nullable `deleted_at` column for soft deletion.

    Rows are never physically deleted; a non-null `deleted_at` marks them as
    deleted. Query-side filtering (e.g. a default scope excluding soft-deleted
    rows) will be introduced alongside the first domain model that uses this
    mixin — not implemented in Phase-0 since there are no domain models yet.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
