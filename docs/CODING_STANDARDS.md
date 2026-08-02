# Backend — Coding Standards

## Tooling (all enforced in pre-commit and CI — see `pyproject.toml`)

| Tool | Purpose | Command |
|---|---|---|
| Black | Formatting (line length 100) | `poetry run black .` |
| Ruff | Linting (`E`,`F`,`I`,`W`,`UP`,`B` rule sets) | `poetry run ruff check .` |
| isort | Import ordering (black-compatible profile) | `poetry run isort .` |
| MyPy | Static typing, `strict = true` | `poetry run mypy .` |

Two Ruff rules are deliberately ignored project-wide (see the comment in
`pyproject.toml`): `E501` (Black already enforces line length) and `UP043`/`UP046`/
`UP047` (PEP 695 generic syntax — kept classic `TypeVar`/`Generic[T]` style instead).
MyPy has narrow `ignore_missing_imports` overrides for `apscheduler`/`passlib`/
`slowapi` only, because those ship no type stubs — never widen this to other modules
without a real reason.

## Layering Rule (the one that matters most)

```
router.py  →  service.py  →  repository.py  →  models.py
```
- `router.py`: HTTP only. No SQLAlchemy import, ever.
- `service.py`: business logic. No `HTTPException`, no `Response` construction.
- `repository.py`: SQLAlchemy queries. Returns ORM objects. Raises
  `core/exceptions.py` types (or nothing), never `HTTPException`.

See the workspace `docs/DEVELOPER_PHILOSOPHY.md` §2.1 for the full rationale and an
anti-pattern example.

## Naming

- Files/directories: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE_CASE`.
- HTTP route segments: `lowercase-hyphen`.
- DB table names: `snake_case`, plural.
- Alembic migrations: `YYYY_MM_DD_NNNN_description.py`.

## Async Discipline

Every DB call is `await`ed against an `AsyncSession`. No synchronous blocking call
(`requests.get`, `time.sleep`, a sync SQLAlchemy session) belongs anywhere in a request
path — see the workspace `docs/DEVELOPER_PHILOSOPHY.md` §2.3.

## Comments

Default to none. Write one only to explain a non-obvious invariant a reader would
otherwise violate (e.g. "flush(), not commit() — the caller owns the transaction
boundary"). Never restate what the code already says.
