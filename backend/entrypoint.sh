#!/bin/sh
set -e

echo "[WatchMe] Running Alembic database migrations..."
alembic upgrade head || {
    echo "[WatchMe] Warning: Alembic migration failed or DB not yet ready. Continuing startup..."
}

echo "[WatchMe] Starting FastAPI backend with Uvicorn..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips="*"
