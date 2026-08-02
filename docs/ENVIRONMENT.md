# Backend — Environment Variables

All settings are defined in `app/core/config.py` (`Settings`, a `pydantic-settings`
class) and loaded from a `.env` file or real environment variables — `.env` always
wins for local dev, real env vars are what's used on Render. Copy `.env.example` to
`.env` to get started; never commit the real `.env`.

| Variable | Default | Notes |
|---|---|---|
| `APP_NAME` | `Paisa API` | Cosmetic, shown in `/api/v1/health` |
| `APP_VERSION` | `0.1.0` | Cosmetic |
| `ENVIRONMENT` | `dev` | One of `dev` / `test` / `prod`. Controls SQL echo logging (`dev` only) |
| `DATABASE_URL` | `postgresql+asyncpg://paisa:paisa@localhost:5432/paisa` | Must use the `asyncpg` driver scheme |
| `DATABASE_SSL_REQUIRED` | `false` | Set `true` for hosted Postgres (Neon) — see the workspace `docs/DEPLOYMENT_GUIDE.md` |
| `JWT_SECRET_KEY` | `change-me-in-prod` | **Must** be overridden with a real random secret outside local dev (`openssl rand -hex 32`) |
| `JWT_ACCESS_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `JWT_REFRESH_EXPIRE_DAYS` | `30` | Refresh token lifetime |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list, e.g. `http://localhost:3000,http://localhost:5173` |
| `RATE_LIMIT_DEFAULT` | `100/minute` | slowapi limit-string syntax |
| `PORT` | *(unset locally)* | Not a `Settings` field — read directly by `entrypoint.sh`/uvicorn. Render injects this; defaults to `8000` if unset |

JWT auth utilities (`app/core/security.py`) exist as of Phase 0 but aren't wired to any
route yet — real auth env vars matter starting in Feature F1.
