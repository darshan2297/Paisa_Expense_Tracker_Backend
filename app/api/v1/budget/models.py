"""BudgetSetting ORM model.

A single monthly-budget configuration per user - see F4 in
`docs/FEATURE_ROADMAP.md`. One row per user (not per-month): "applies to
every month unless you change it", matching the product design's own
`budget`/`alertPct`/`leadDays` state fields. Per
`docs/FEATURE_ROADMAP.md`'s "Deviations" section, per-category budgets are
explicitly deferred to a future v2 enhancement - this is a single global
number.
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class BudgetSetting(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "budget_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True
    )
    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    # Percent of the budget remaining at which the Overview/Planned screens
    # show a "running low" alert - matches the design's 5-60 slider range.
    alert_pct: Mapped[int] = mapped_column(Integer, nullable=False, server_default="20")

    # Days before a fixed commitment's due date the "Coming up" reminder
    # list should surface it. Stored only - no notification is sent in this
    # phase (that's F17, once APScheduler/push wiring lands).
    reminder_lead_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="15")
