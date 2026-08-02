# Backend — Database Standards

## Schema Rules

- UUID primary key on every table (`app/core/base_model.py`'s `UUIDPKMixin`).
- `created_at`/`updated_at`/`deleted_at` on every table (`TimestampMixin` +
  `SoftDeleteMixin`) — soft delete is the default; every query filters
  `deleted_at IS NULL` unless intentionally including deleted rows.
- Every domain table (from F2 onward) carries a `user_id` FK, even with one user
  today — see the workspace `docs/DEVELOPER_PHILOSOPHY.md` §7.2 for why this is a
  hard rule, not a convenience.
- Money columns: `NUMERIC(14,2)`, never `FLOAT`/`DOUBLE`. Pair with a
  `currency VARCHAR(3) DEFAULT 'INR'` column.
- Enum-like columns: `VARCHAR` validated by a Python `Enum` + Pydantic — not a native
  Postgres `ENUM` type (adding a value to a native enum needs `ALTER TYPE`; a `VARCHAR`
  doesn't).

## Naming

- Foreign keys: `fk_{table}_{column}`. Unique constraints: `uq_{table}_{column}`.
  Indexes: `ix_{table}_{column(s)}`.

## Migrations

- Alembic, one migration per feature phase: `alembic/versions/YYYY_MM_DD_NNNN_description.py`.
- **Append-only** — never edit a committed migration; supersede it with a new one.
- Every migration has both `upgrade()` and `downgrade()` unless a downgrade is
  genuinely impossible.
- `entrypoint.sh` runs `alembic upgrade head` automatically before the API starts, in
  every environment (local Docker, CI test job, Render) — never rely on someone
  remembering to run it by hand.
- Generate a starting point with `poetry run alembic revision --autogenerate -m "..."`,
  but always hand-review the diff — autogenerate misses some changes (e.g. renamed
  columns look like a drop+add) and never infers indexes you haven't already declared
  on the model.

## Indexing

Add indexes in the same migration as the table, based on known query patterns: every
FK column used in a `WHERE`, `created_at` (ordering/pagination), `deleted_at`
(soft-delete filter), and the obvious composites (e.g. `(user_id, date)` on
`transactions`, the table nearly everything after F3 reads from).

## Connections

`app/core/database.py` creates one process-wide async engine (`pool_pre_ping=True` to
guard against stale connections). SSL for hosted Postgres (Neon) is enabled via
`connect_args={"ssl": "require"}` when `Settings.DATABASE_SSL_REQUIRED` is true — see
`docs/ENVIRONMENT.md` and the workspace `docs/DEPLOYMENT_GUIDE.md`.
