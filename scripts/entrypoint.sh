#!/bin/bash
set -e

echo "[entrypoint] Stamping Alembic head..."
python -m alembic stamp head 2>/dev/null || true

echo "[entrypoint] Starting FastAPI..."
exec fastapi run --host 0.0.0.0 --port 8000
