#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec "${PYTHON:-python3}" -m uvicorn server.app.main:app --host "${TEAMZ_HOST:-0.0.0.0}" --port "${TEAMZ_PORT:-8787}"
