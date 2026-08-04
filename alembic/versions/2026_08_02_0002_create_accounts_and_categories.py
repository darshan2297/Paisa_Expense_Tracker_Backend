"""create accounts and categories tables

Revision ID: 6f2a1c8e4b7d
Revises: 385751604dcf
Create Date: 2026-08-02 09:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6f2a1c8e4b7d"
down_revision: str | Sequence[str] | None = "385751604dcf"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The exact 12 expense + 7 income categories/colors from the product
# design's `CATS` constant - see docs/FEATURE_ROADMAP.md F2.
_EXPENSE_CATEGORIES = [
    ("Food & Dining", "#E08A70"),
    ("Groceries", "#7FA87C"),
    ("Transport", "#6C9BC9"),
    ("Rent", "#8C7BC7"),
    ("Utilities", "#C99A5B"),
    ("Shopping", "#D177A6"),
    ("Health", "#5FA8A0"),
    ("Entertainment", "#B58BD9"),
    ("Education", "#7A8FD6"),
    ("Savings", "#2F7D6E"),
    ("Insurance", "#5B54D6"),
    ("Other", "#A79E92"),
]
_INCOME_CATEGORIES = [
    ("Salary", "#5B54D6"),
    ("Freelance", "#4C9C7E"),
    ("Business", "#C99A5B"),
    ("Interest", "#6C9BC9"),
    ("Dividend", "#2F7D6E"),
    ("Gift", "#D177A6"),
    ("Other", "#A79E92"),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "accounts",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=16), server_default="cash", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_accounts_user_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
    )
    op.create_index(op.f("ix_accounts_user_id"), "accounts", ["user_id"], unique=False)

    op.create_table(
        "categories",
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("kind", "name", name=op.f("uq_categories_kind")),
    )

    # --- Data migration: seed the fixed category taxonomy ---
    categories_table = sa.table(
        "categories",
        sa.column("id", sa.UUID()),
        sa.column("kind", sa.String()),
        sa.column("name", sa.String()),
        sa.column("color", sa.String()),
        sa.column("sort_order", sa.Integer()),
    )
    seed_rows = [
        {"id": uuid.uuid4(), "kind": "expense", "name": name, "color": color, "sort_order": i}
        for i, (name, color) in enumerate(_EXPENSE_CATEGORIES)
    ] + [
        {"id": uuid.uuid4(), "kind": "income", "name": name, "color": color, "sort_order": i}
        for i, (name, color) in enumerate(_INCOME_CATEGORIES)
    ]
    op.bulk_insert(categories_table, seed_rows)

    # --- Data migration: backfill a default "Cash" account for any user
    # created before this migration (new users get one at registration -
    # see app.api.v1.accounts.service.ensure_default_account). ---
    connection = op.get_bind()
    existing_user_ids = connection.execute(sa.text("SELECT id FROM users")).scalars().all()
    if existing_user_ids:
        accounts_table = sa.table(
            "accounts",
            sa.column("id", sa.UUID()),
            sa.column("user_id", sa.UUID()),
            sa.column("name", sa.String()),
            sa.column("kind", sa.String()),
            sa.column("currency", sa.String()),
        )
        op.bulk_insert(
            accounts_table,
            [
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "name": "Cash",
                    "kind": "cash",
                    "currency": "INR",
                }
                for user_id in existing_user_ids
            ],
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("categories")
    op.drop_index(op.f("ix_accounts_user_id"), table_name="accounts")
    op.drop_table("accounts")
