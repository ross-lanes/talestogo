# Tales To Go

Tales is an AI reputation monitoring platform that tracks how brands are represented across major AI platforms (ChatGPT, Claude, Gemini, Perplexity).

## ⚠️ Critical Rule: Do Not Touch tales_project

This repository (`talestogo`, local path `/Users/rkremen/Documents/Code/TalesToGo/`) is the **public, sanitized version** of Tales — the one shared with U.S. National Labs (PPPL, PNNL, Argonne, LLNL, etc.) for self-deployment. It is intentionally a separate codebase from Rachel's private dev repo.

The private dev repo is `tales_project` (local path `/Users/rkremen/Documents/Code/tales_project/`, GitHub `rtwodeetwo/tales_project`). It contains Rachel's keys, the front door, and unsanitized features.

**Any work done in this repo (TalesToGo / talestogo) must NEVER:**
- Read from, write to, or modify `/Users/rkremen/Documents/Code/tales_project/`
- Push to or pull from `github.com/rtwodeetwo/tales_project`
- Be confused with `tales_project` in commit messages, PR descriptions, or documentation

If a change is needed in both repos, treat them as two separate, independent commits in two separate working trees.

## Tech Stack

- **Backend**: Python/FastAPI with SQLAlchemy ORM
- **Frontend**: React/TypeScript with Vite, Material-UI
- **Database**: PostgreSQL
- **Auth**: Email/password + optional Google/Microsoft OAuth

## Project Structure

```
TalesToGo/
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
├── docs/                  # Documentation
│   ├── USER_GUIDE.md     # End user documentation
│   ├── IT_DEPLOYMENT_GUIDE.md # IT deployment instructions
│   └── ENV_VARS_REFERENCE.md # Environment variable reference
├── docker-compose.yml    # Docker deployment config
└── Dockerfile            # Container build config
```

## LLM Configuration

Tales supports up to 6 LLM providers for data collection and analysis:
- **ChatGPT** (OpenAI) - via `OPENAI_API_KEY`
- **Claude** (Anthropic) - via `ANTHROPIC_API_KEY`
- **Gemini** (Google) - via `GEMINI_API_KEY` (recommended for analysis and web search)
- **Perplexity** - via `PERPLEXITY_API_KEY` (supports web search)
- Up to 2 custom OpenAI-compatible providers

## Development Commands

```bash
# Start backend locally
python3 -m uvicorn app.main:app --reload --port 8000

# Start frontend locally
cd frontend && npm run dev

# Run with Docker
docker compose up -d
```

## Deployment

See [docs/IT_DEPLOYMENT_GUIDE.md](docs/IT_DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

### Quick Start (Docker)

```bash
# 1. Copy and configure environment
cp .env.template .env
# Edit .env with your API keys and secrets

# 2. Start application
docker compose up -d

# 3. Create initial admin
docker compose exec app python scripts/admin/setup_initial_admin.py
```

## Environment Variables

Required for deployment:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - For authentication tokens
- `ENCRYPTION_KEY` - Fernet key for API key storage
- `GEMINI_API_KEY` - Required for analysis (other LLM keys optional)

Optional:
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY` - For querying those platforms
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - For Google OAuth
- `MICROSOFT_CLIENT_ID` / `MICROSOFT_CLIENT_SECRET` - For Microsoft OAuth
- `RESEND_API_KEY` - For sending invitation emails
- `FROM_EMAIL` - Email address for sending
- `FRONTEND_URL` - For CORS and email links

See [docs/ENV_VARS_REFERENCE.md](docs/ENV_VARS_REFERENCE.md) for complete list.

## Key Features

- Multi-brand support (users can track up to 20 brands)
- Brand sharing between users
- Automated data collection with scheduling
- Response analysis extracting: mentions, sentiment, positioning, competitors, descriptors
- Report generation with AI-written summaries
- Analytics dashboard with charts
- Configurable site settings for white-labeling
