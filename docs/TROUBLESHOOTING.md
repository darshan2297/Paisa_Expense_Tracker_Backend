# Backend — Troubleshooting

**`poetry install` fails resolving dependencies / wrong Python version**
Confirm `python3 --version` (or whichever interpreter Poetry picked via
`poetry env info`) is 3.13+. Poetry will not silently fall back to an older
interpreter — install 3.13 (pyenv, deadsnakes PPA, or your OS's package manager) and
`poetry env use 3.13`.

**`alembic upgrade head` can't connect to the database**
Check `DATABASE_URL` in `.env` — for docker-compose it should point at `postgres`
(the compose service name), not `localhost`, if running the migration *inside* the
backend container; `localhost` is correct if running Alembic from your host machine
against the compose-exposed port `5432`.

**`MissingGreenlet` error at runtime**
A SQLAlchemy relationship was lazy-loaded implicitly on an async session. Use
`selectinload`/`joinedload` explicitly in the query instead — see the workspace
`docs/DEVELOPER_PHILOSOPHY.md` §2.3.

**A route returns a 500 with no useful detail**
Check the logs for the `request_id` in the error response and grep for it — every log
line in that request's lifecycle carries the same ID (`app/middleware/request_id.py`).

**Neon connection fails with an SSL error**
Set `DATABASE_SSL_REQUIRED=true` — Neon requires SSL and `asyncpg` doesn't parse a
`sslmode=` query parameter the way `psycopg2` does; SSL is enabled via `connect_args`
in `app/core/database.py` instead. See `docs/ENVIRONMENT.md`.

**MyPy complains about a third-party import with no stubs**
Check `pyproject.toml`'s `[[tool.mypy.overrides]]` — if it's a genuinely stub-less
package, add it there rather than weakening `strict` mode globally or sprinkling
`# type: ignore` throughout the codebase.

**Render backend takes 30–60 seconds to respond**
Expected — Render's free tier spins down idle services. See the workspace
`docs/DEPLOYMENT_GUIDE.md`.
