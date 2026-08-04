#!/usr/bin/env bash
# Container entrypoint: run pending DB migrations, then start the API server.
#
# Fails fast (`set -e`) so a broken migration never results in the app
# silently serving traffic against an out-of-date schema.
set -euo pipefail

echo "[entrypoint] Running database migrations..."
alembic upgrade head

echo "[entrypoint] Seeding reference data (configuration catalog)..."
python -m scripts.seed_reference_data

echo "[entrypoint] Starting API server..."
# Render (and most PaaS hosts) inject PORT and expect the process to bind to it;
# default to 8000 for local/docker-compose use where nothing sets PORT.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
