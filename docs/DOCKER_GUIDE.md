# Backend — Docker Guide

## Image Structure

Multi-stage `Dockerfile`:
- **`builder`** stage: `python:3.13-slim` + Poetry, installs only `main` (production)
  dependencies into an in-project virtualenv (`.venv`). Build tools (`build-essential`)
  live only here.
- **`final`** stage: fresh `python:3.13-slim`, copies just the built `.venv` and the
  application source — no build toolchain, no Poetry, in the shipped image. Runs as a
  non-root `appuser`.

`entrypoint.sh` runs `alembic upgrade head` before starting `uvicorn`, so the image is
never running against an out-of-date schema. It binds to `${PORT:-8000}` — defaults to
`8000` locally, respects whatever `PORT` a host (e.g. Render) injects.

## Building Locally

```bash
docker build -t paisa-backend:local .
docker run --rm -p 8000:8000 --env-file .env paisa-backend:local
```
(Point `DATABASE_URL` in `.env` at a reachable Postgres — `host.docker.internal` if
it's running on your host machine outside Docker, or a container on the same Docker
network.)

## Via docker-compose (recommended for local full-stack dev)

From the workspace root: `docker compose up --build` — brings up Postgres, this
backend, and the frontend web build together, wired via the shared Docker network. See
the workspace's `docker-compose.yml` and `docs/ARCHITECTURE.md`.

## Production Image

CI builds and pushes this same image (`ghcr.io/darshan2297/paisa-backend`) on every
release — see `docs/CICD_GUIDE.md`. Render pulls and runs it — see the workspace's
`docs/DEPLOYMENT_GUIDE.md` for the full hosting setup.

**Note:** `.env` is never copied into the image (`.dockerignore` excludes it) — all
configuration is environment-variable-injected at container start, so the same image
works locally, in CI, and on Render without ever containing a secret.
