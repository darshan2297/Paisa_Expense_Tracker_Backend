# Backend — Development Guide

## Daily Workflow

```bash
poetry install                        # once, or after pyproject.toml changes
poetry run uvicorn app.main:app --reload
poetry run pytest                     # before every commit
poetry run pre-commit run --all-files # if you didn't install the git hook
```

## Adding a New Feature Module

Following `FEATURE_ROADMAP.md` (workspace `docs/`) one feature at a time:

1. Create `app/api/v1/<module>/` with `router.py`, `schemas.py`, `service.py`,
   `repository.py`, `models.py` (and `exceptions.py` if the module needs its own
   error cases beyond the shared `core/exceptions.py` hierarchy).
2. Register the module's router in `app/api/v1/router.py`.
3. Write the Alembic migration: `poetry run alembic revision -m "add <module> tables"`
   then hand-write `upgrade()`/`downgrade()` (autogenerate is a starting point, always
   review its output — see `docs/DATABASE_STANDARDS.md`).
4. Follow the layering rule strictly: `router.py` calls `service.py` calls
   `repository.py`. No SQLAlchemy import in a router file; no `HTTPException` raised
   from a repository or service (raise `core/exceptions.py` types instead — the
   registered exception handlers in `app/middleware/error_handling.py` translate them).
5. Add tests: `tests/unit/` for pure logic (no DB), `tests/integration/` for the full
   request cycle against a real Postgres.
6. Update the workspace `docs/ARCHITECTURE.md` module table and
   `docs/FEATURE_ROADMAP.md` status column.

## Project Layout Recap

```
app/api/v1/<module>/   one per feature — router/schemas/service/repository/models
app/core/              shared infra: config, security, database, exceptions, response, pagination, logging
app/middleware/        request_id, response_envelope, error_handling, rate_limit
app/scheduler/         APScheduler setup + jobs/ (one file per recurring job)
alembic/versions/      migrations, one per feature, YYYY_MM_DD_NNNN_description.py
tests/unit/            no DB, no HTTP
tests/integration/     real Postgres, full request cycle (httpx.AsyncClient)
```

## Middleware Order (don't get this backwards)

Starlette executes middleware added via `add_middleware()` in **reverse** order for
the request path (last added = outermost). `app/main.py` adds them in the order that
achieves: CORS (outermost) → RequestId → RateLimit → ResponseEnvelope → error handlers
(innermost, closest to the route) — see the comment in `app/main.py` before touching
this.

## Auth (once F1 ships)

`app/core/security.py` already has `hash_password`/`verify_password`/
`create_access_token`/`create_refresh_token`/`decode_token` as pure utilities — F1
wires them into an actual `auth` module and a `User` model with a `credential_version`
column (see the workspace `docs/DEVELOPER_PHILOSOPHY.md` §8.2 for why).
