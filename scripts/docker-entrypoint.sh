#!/bin/sh
# Docker entrypoint script for Tales
# Uses exec to ensure signals are forwarded properly to uvicorn

set -e

# Run database migrations/setup
echo "Initializing database..."
python -c 'from app.database import engine, Base; from app import models; Base.metadata.create_all(bind=engine)'

# Use exec to replace shell with uvicorn (proper signal handling)
echo "Starting Tales server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
