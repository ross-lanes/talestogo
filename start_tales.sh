#!/bin/bash

# Simple Tales Startup Script
# This starts both the backend API and frontend dev server

echo "🤖 Starting Tales locally..."
echo ""

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this from the tales_project directory"
    exit 1
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Tales..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Tales stopped"
    exit 0
}

# Set up trap to catch Ctrl+C and cleanup
trap cleanup SIGINT SIGTERM

# Start backend in background
echo "📡 Starting backend API..."
DATABASE_URL="postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3" \
PYTHONPATH=/Users/rachelkremen/Documents/Code/tales_project \
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/tales_backend.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ Backend failed to start. Check /tmp/tales_backend.log for errors"
    exit 1
fi

echo "✅ Backend running on http://localhost:8000"
echo "   (Logs: /tmp/tales_backend.log)"

# Start frontend in background
echo ""
echo "🎨 Starting frontend..."
cd frontend
npm run dev > /tmp/tales_frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 2

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start. Check /tmp/tales_frontend.log for errors"
    kill $BACKEND_PID
    exit 1
fi

echo "✅ Frontend running on http://localhost:5173"
echo "   (Logs: /tmp/tales_frontend.log)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Tales is running!"
echo ""
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "   Backend logs:  tail -f /tmp/tales_backend.log"
echo "   Frontend logs: tail -f /tmp/tales_frontend.log"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Wait for user to press Ctrl+C
wait
