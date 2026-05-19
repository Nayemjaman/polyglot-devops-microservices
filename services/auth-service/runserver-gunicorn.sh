#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export POSTGRES_DB="${POSTGRES_DB:-auth_service_db}"
export POSTGRES_USER="${POSTGRES_USER:-auth_service_user}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-auth_service_password}"
export POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-6432}"

exec ./venv/bin/gunicorn core.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --bind "${BIND_ADDRESS:-0.0.0.0:8000}" \
  --workers "${GUNICORN_WORKERS:-4}"
