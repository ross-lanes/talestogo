#!/bin/bash
set -e

echo "🚀 Starting local development environment..."

# Load local environment variables
export $(cat .env.local | grep -v '^#' | xargs)

# Remove old local database if it exists
if [ -f "local_dev.db" ]; then
    echo "📦 Removing old local database..."
    rm local_dev.db
fi

# Initialize database
echo "🗄️  Initializing local SQLite database..."
python3 -c "
from app.database import engine, Base
from app import models
Base.metadata.create_all(bind=engine)
print('✅ Database initialized')
"

echo ""
echo "✅ Local environment ready!"
echo ""
echo "To start the servers:"
echo "  Backend:  python3 -m uvicorn app.main:app --reload --port 8000"
echo "  Frontend: cd frontend && npm run dev"
echo ""
