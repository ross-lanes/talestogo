#!/bin/bash

# This script is used to run the FastAPI server for development.
# It is designed to be run from the root of the tales_project directory.

# --- Instructions ---
# 1. Make this script executable: chmod +x run.sh
# 2. Run: ./run.sh
#
# NOTE: Celery worker has been removed. APScheduler runs automatically
# when the FastAPI server starts (no separate worker process needed).
# --------------------

# Ensure the virtual environment is sourced
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Start the FastAPI server (APScheduler starts automatically)
echo "Starting FastAPI server on http://0.0.0.0:8000..."
echo "APScheduler will start automatically for scheduled tasks."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
