#!/bin/bash

# This script is used to run the FastAPI server and Celery worker for development.
# It is designed to be run from the root of the tales_project directory.

# --- Instructions ---
# 1. Make this script executable: chmod +x run.sh
# 2. To run, you will need TWO separate Cloud Shell terminals.
# 3. In Terminal 1, run: ./run.sh server
# 4. In Terminal 2, run: ./run.sh worker
# --------------------

# Ensure the virtual environment is sourced
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Function to start the FastAPI server
start_server() {
    echo "Starting FastAPI server on http://0.0.0.0:8000..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to start the Celery worker
start_worker() {
    echo "Starting Celery worker..."
    # Start the worker and the beat scheduler in one command
    celery -A celery_app.celery worker --beat --loglevel=info
}

# Check the first argument passed to the script
case "$1" in
    server)
        start_server
        ;;
    worker)
        start_worker
        ;;
    *)
        echo "Usage: $0 {server|worker}"
        exit 1
        ;;
esac
