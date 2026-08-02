# Paisa Backend

FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL backend for the Paisa personal finance
tracker. Part of a two-repo project — see the
[workspace docs](../docs/ARCHITECTURE.md) (in the local development workspace, one
level up from this repo) for the full system architecture, feature roadmap, and
engineering philosophy.

## Quick Start

```bash
poetry install
cp .env.example .env    # then edit DATABASE_URL etc.
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

API docs: `http://localhost:8000/docs` (Swagger) once running.

See `docs/INSTALLATION.md` for full local setup (including via Docker) and
`docs/DEVELOPMENT_GUIDE.md` for day-to-day workflow.

## Docs in this repo

| Doc | Covers |
|---|---|
| `docs/INSTALLATION.md` | First-time local setup |
| `docs/ENVIRONMENT.md` | Every environment variable, what it does |
| `docs/DEVELOPMENT_GUIDE.md` | Day-to-day dev workflow, adding a feature |
| `docs/DOCKER_GUIDE.md` | Building/running the Docker image |
| `docs/CICD_GUIDE.md` | What the GitHub Actions pipelines do |
| `docs/CODING_STANDARDS.md` | Lint/format/type rules and layering conventions |
| `docs/API_STANDARDS.md` | REST conventions, envelope, pagination |
| `docs/DATABASE_STANDARDS.md` | Schema conventions, migrations |
| `docs/TROUBLESHOOTING.md` | Common local-dev problems |

Shared architecture, the feature roadmap, git workflow, and deployment guide live in
the workspace-level `docs/` folder alongside this repo (not duplicated here — see
`docs/DEVELOPMENT_GUIDE.md` for the exact relative path).
