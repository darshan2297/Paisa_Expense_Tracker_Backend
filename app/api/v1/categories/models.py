"""Category ORM model.

A shared, seeded expense/income taxonomy (not per-user) - see F2 in
`docs/FEATURE_ROADMAP.md`. Seeded once via migration
(`2026_..._create_accounts_and_categories.py`) with the exact 12 expense +
7 income categories from the product design; not user-editable in this
phase.
"""

from enum import StrEnum

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class CategoryKind(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class Category(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("kind", "name"),)

    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
