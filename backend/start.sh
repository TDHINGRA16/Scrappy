#!/usr/bin/env bash
set -e

# start.sh - start application server
# Behavior:
# - If USE_PYTHON_RUN=1 -> runs `python run.py` (foreground)
# - Else -> runs gunicorn with uvicorn workers

: "${PORT:=8888}"
: "${GUNICORN_WORKERS:=7}"
# No RQ/Redis workers are started by this script (not using Redis queues)

echo "Starting start.sh with PORT=${PORT} GUNICORN_WORKERS=${GUNICORN_WORKERS}"

echo "Not starting RQ workers (Redis/RQ not used in this deployment)"

# Run application
if [ "${USE_PYTHON_RUN}" = "1" ]; then
  echo "Running python run.py (foreground)"
  exec python run.py
else
  # Prefer gunicorn with uvicorn workers in production
  if command -v gunicorn >/dev/null 2>&1; then
    echo "Starting gunicorn with ${GUNICORN_WORKERS} workers on 0.0.0.0:${PORT}"
    exec gunicorn main:app -k uvicorn.workers.UvicornWorker --workers "${GUNICORN_WORKERS}" --bind 0.0.0.0:"${PORT}" --log-level info
  else
    echo "gunicorn not found; falling back to uvicorn"
    exec uvicorn main:app --host 0.0.0.0 --port "${PORT}" --workers 1
  fi
fi
