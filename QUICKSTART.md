# Tales - Quick Start Guide

## Starting Tales Locally (Simple Method)

Just run this from the `tales_project` directory:

```bash
./start_tales.sh
```

That's it! This starts both the backend and frontend automatically.

**What you'll see:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

**To stop:** Press `Ctrl+C`

---

## What's Running

When you start Tales, you get:

1. **Backend API** (FastAPI on port 8000)
   - Handles all data collection, analysis, reports
   - APScheduler runs automatically for scheduled tasks
   - No Redis needed, no Celery worker needed

2. **Frontend** (React + Vite on port 5173)
   - Your main user interface
   - Hot-reload enabled for development

---

## Troubleshooting

**Backend won't start?**
```bash
tail -f /tmp/tales_backend.log
```

**Frontend won't start?**
```bash
tail -f /tmp/tales_frontend.log
```

**Check if ports are in use:**
```bash
lsof -i :8000  # Backend port
lsof -i :5173  # Frontend port
```

**Kill stuck processes:**
```bash
kill $(lsof -t -i:8000)  # Kill backend
kill $(lsof -t -i:5173)  # Kill frontend
```

---

## Manual Start (if you prefer)

**Backend only:**
```bash
DATABASE_URL="postgresql://user:password@your-db-host:5432/your_database" \
PYTHONPATH=/path/to/tales_project \
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend only (in separate terminal):**
```bash
cd frontend
npm run dev
```

---

## Architecture Notes

- **No Celery worker needed** - APScheduler handles scheduled tasks automatically when the backend starts
- **No Redis needed** - Threading model handles all concurrency
- **Single command startup** - `./start_tales.sh` runs everything
- **Supports 50+ concurrent tasks** - Thread pool prevents overload

---

## Production Deployment

When you're ready to deploy:

1. Delete the `tales-celery-worker` service in Render dashboard
2. Push these changes to GitHub
3. Render will automatically redeploy with the new architecture

Cost savings: ~$5-10/month (no Redis needed)
