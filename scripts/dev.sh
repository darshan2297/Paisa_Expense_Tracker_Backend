#!/usr/bin/env bash
# Local API on port 8001 (matches frontend EXPO_PUBLIC_API_URL default).
set -euo pipefail
cd "$(dirname "$0")/.."
exec poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
