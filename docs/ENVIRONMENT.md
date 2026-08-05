# Backend — Environment Variables

All settings are defined in `app/core/config.py` (`Settings`, a `pydantic-settings`
class) and loaded from a `.env` file or real environment variables — `.env` always
wins for local dev, real env vars are what's used on Render. Copy `.env.example` to
`.env` to get started; never commit the real `.env`.

## Dev vs prod files

| File | Committed? | Purpose |
|---|---|---|
| `.env.example` | Yes | Local **dev** template |
| `.env.production.example` | Yes | **Prod** template — copy values to Render/host env |
| `.env` | No | Active local dev config |
| `.env.production` | No | Optional local prod smoke-test |

Switching to production requires **only env changes** — no code changes.

## Variables

| Variable | Dev default | Prod |
|---|---|---|
| `APP_NAME` | `Paisa API` | same |
| `APP_VERSION` | `0.1.0` | bump per release |
| `ENVIRONMENT` | `dev` | `prod` |
| `DATABASE_URL` | local Postgres | Neon/hosted URL |
| `DATABASE_SSL_REQUIRED` | `false` | `true` |
| `JWT_SECRET_KEY` | placeholder | `openssl rand -hex 32` |
| `JWT_ACCESS_EXPIRE_MINUTES` | `15` | `15` |
| `JWT_REFRESH_EXPIRE_DAYS` | `30` | `30` |
| `CORS_ORIGINS` | localhost Expo/web ports | production frontend URL(s) |
| `REDIS_URL` | `redis://localhost:6379/0` | hosted Redis |
| `CELERY_BROKER_URL` | `redis://localhost:6379/1` | hosted Redis db 1 |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/2` | hosted Redis db 2 |
| `CACHE_DEFAULT_TTL_SECONDS` | `300` | `300` |
| `RATE_LIMIT_DEFAULT` | `100/minute` | `100/minute` |
| `PORT` | *(local dev: pass `--port 8001` to uvicorn)* | Render injects this |

Optional:

| Variable | Feature |
|---|---|
| `RESEND_API_KEY`, `EMAIL_FROM` | F17 email reminders (Resend). Option B: `EMAIL_FROM=Paisa <onboarding@resend.dev>` (only delivers to your Resend account email; Paisa `User.email` must match). Verified domain: `Paisa <reminders@yourdomain.com>`. |
| `CRON_SECRET` | Protects `POST /api/v1/internal/reminders/run` (GitHub Actions daily-reminders workflow). Also set as repo secret `CRON_SECRET` with `API_BASE_URL`. |
| `STORAGE_BACKEND`, `R2_*` | F19/F20 file storage |

## Local dev processes

```bash
redis-server                                                    # Terminal 1
poetry run uvicorn app.main:app --reload --port 8001            # Terminal 2
poetry run celery -A app.worker.celery_app worker --beat -l info  # Terminal 3
```

Verify the developer portal at `http://localhost:8001/`.
