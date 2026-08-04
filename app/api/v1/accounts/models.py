"""Account ORM model.

A user's money-holding container (cash/bank/wallet) - see F2 in
`docs/FEATURE_ROADMAP.md`. The product design this app is based on has no
account concept at all (every screen shows a single net balance); this
table is a deliberate addition, documented as a mockup deviation, so a real
ledger knows *where* money sits.

There is no accounts UI yet: every user gets exactly one "Cash" account,
created lazily via `service.ensure_default_account` (see that function's
docstring for why auth triggers this without importing this module
directly). `GET /accounts` exists so the entity is inspectable, but nothing
in the frontend calls it yet - add POST/PATCH/DELETE when an Accounts
management screen becomes its own roadmap item.
"""

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, SoftDeleteMixin, TimestampMixin, UUIDPKMixin


class AccountKind(StrEnum):
    CASH = "cash"
    BANK = "bank"
    WALLET = "wallet"


class Account(Base, UUIDPKMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, server_default=AccountKind.CASH.value)

    # ISO 4217 code - see docs/DATABASE_STANDARDS.md money-column convention.
    # No stored balance column: balance is always derived from transactions
    # (sum of income minus expense for this account) to avoid the two ever
    # drifting apart.
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="INR")
