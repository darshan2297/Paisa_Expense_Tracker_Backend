"""Shared expense group ORM models."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class ExpenseGroup(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "expense_groups"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    members: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    expenses: Mapped[list["GroupExpense"]] = relationship(back_populates="group")
    settlements: Mapped[list["GroupSettlement"]] = relationship(back_populates="group")


class GroupExpense(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "group_expenses"

    group_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("expense_groups.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    payer: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    split_type: Mapped[str] = mapped_column(String(16), nullable=False, server_default="equal")
    splits: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    group: Mapped[ExpenseGroup] = relationship(back_populates="expenses")


class GroupSettlement(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "group_settlements"

    group_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("expense_groups.id"), nullable=False
    )
    from_member: Mapped[str] = mapped_column(String(255), nullable=False)
    to_member: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)

    group: Mapped[ExpenseGroup] = relationship(back_populates="settlements")
