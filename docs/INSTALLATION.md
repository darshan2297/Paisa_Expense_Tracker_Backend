# Backend — Installation

## Prerequisites

- Python 3.13+ (the project pins `python = "^3.13"` in `pyproject.toml` — an older
  interpreter will fail `poetry install`'s dependency resolution for some packages)
- [Poetry](https://python-poetry.org/) 1.8+
- PostgreSQL 16 (or Docker, to run one via `docker-compose.yml` in the workspace root)

## Option A — Native (Poetry + a local/Docker Postgres)

```bash
poetry install
cp .env.example .env
# edit .env: at minimum set a real JWT_SECRET_KEY; DATABASE_URL default matches
# the workspace docker-compose Postgres (paisa/paisa@localhost:5432/paisa)
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

Health check: `curl http://localhost:8000/api/v1/health` should return the standard
envelope with `"status": "ok"`.

## Option B — Full stack via Docker Compose

From the **workspace root** (one directory up, containing both `backend/` and
`frontend/`):
```bash
docker compose up --build
```
This starts Postgres, the backend (running migrations automatically via
`entrypoint.sh`), and the frontend web build together. See the workspace's
`docs/ARCHITECTURE.md` and this repo's `docs/DOCKER_GUIDE.md`.

## Running Tests

```bash
poetry run pytest
```

Integration tests expect a reachable Postgres — either the docker-compose one or a
local instance matching `DATABASE_URL`.

## Pre-commit Hooks

```bash
poetry run pre-commit install
```
Runs Black, Ruff, isort, and MyPy on every commit — see `docs/CODING_STANDARDS.md`.
