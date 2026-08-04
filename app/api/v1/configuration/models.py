"""Catalog of all customizable configuration options.

Each row defines one setting key, its type, default, and UI metadata.
Adding a new app setting = insert one row here (+ frontend wiring).
"""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base_model import Base, TimestampMixin, UUIDPKMixin


class Configuration(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "configurations"
    __table_args__ = (UniqueConstraint("key", name="uq_configurations_key"),)

    key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    value_type: Mapped[str] = mapped_column(String(16), nullable=False)
    default_value: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    allowed_values: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user_values: Mapped[list["UserConfiguration"]] = relationship(back_populates="configuration")


class UserConfiguration(Base, UUIDPKMixin, TimestampMixin):
    """Per-user value for a catalog configuration option."""

    __tablename__ = "user_configurations"
    __table_args__ = (
        UniqueConstraint("user_id", "configuration_id", name="uq_user_configurations_user_option"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    configuration_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("configurations.id"), nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(255), nullable=False)

    configuration: Mapped[Configuration] = relationship(back_populates="user_values")
