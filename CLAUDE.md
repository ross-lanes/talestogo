# Tales Project

Tales is an AI reputation monitoring platform that tracks how brands are represented across major AI platforms (ChatGPT, Claude, Gemini, Perplexity).

## Tech Stack

- **Backend**: Python/FastAPI with SQLAlchemy ORM
- **Frontend**: React/TypeScript with Vite, Material-UI
- **Database**: PostgreSQL (hosted on Render)
- **Hosting**: Railway (separate frontend/backend services)
- **Auth**: Google OAuth + JWT tokens

## Project Structure

```
tales_project/
├── app/                    # FastAPI backend
│   ├── main.py            # App entry point
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   ├── crud.py            # Database operations
│   ├── routers/           # API endpoints
│   └── services/          # Business logic
│       ├── llm_service.py # LLM API calls
│       └── data_pipeline.py # Collection/analysis workflow
├── frontend/              # React frontend
│   └── src/
│       ├── pages/         # Page components
│       ├── components/    # Reusable components
│       └── services/api.ts # API client
├── scripts/admin/         # Admin scripts
│   ├── collect_responses.py
│   ├── analyze_responses.py
│   └── generate_report.py
├── Procfile               # Railway start command
└── nixpacks.toml          # Railway build config
```

## LLM Configuration

Current LLM usage (as of Nov 2025):
- **Data Collection**: Queries sent to ChatGPT, Claude, Gemini, Perplexity
- **Response Analysis**: Gemini 2.5 Pro (`analyze_raw_response` in llm_service.py)
- **Report Writing**: Gemini 2.5 Pro (generate_report.py)
## Development Commands

```bash
# Start backend locally
python3 -m uvicorn app.main:app --reload --port 8000

# Start frontend locally
cd frontend && npm run dev

# Run both (from project root)
./start_local.sh
```

## Deployment

### Environments

**Development** (dev branch):
- Frontend: https://tales-frontend-development.up.railway.app
- Backend: https://tales-backend-development.up.railway.app

**Production** (main branch):
- Frontend: https://apps.robotrachel.com
- Backend: https://apps.robotrachel.com

### Deploy to Production
```bash
git checkout main
git merge dev
git push
```

### Deploy to Development
```bash
git checkout dev
git push origin dev
```

Railway auto-deploys when changes are pushed to the respective branches.

## Environment Variables

Required on Railway backend:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - For authentication tokens
- `ENCRYPTION_KEY` - Fernet key for API key storage
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth
- `PERPLEXITY_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`
- `FRONTEND_URL` - For CORS (e.g., https://tales.robotrachel.com)

## Key Features

- Multi-brand support (users can track up to 20 brands)
- Brand sharing between users
- Automated data collection with scheduling
- Response analysis extracting: mentions, sentiment, positioning, competitors, descriptors
- Report generation with AI-written summaries
- Analytics dashboard with charts
