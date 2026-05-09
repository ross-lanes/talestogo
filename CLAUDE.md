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

## Session Log: 2026-05-08 — Strip-to-Tales-Only Cleanup

### Context

Rachel sent the talestogo deployment kit to PNNL (Pacific Northwest National Laboratory) on Feb 2, 2026. PNNL responded in early May 2026 wanting a meeting before deploying. Their main asks: solidify repo location/access, establish contribution guidelines, and confirm scope.

While preparing for that meeting, we discovered the talestogo repo still contained code for **8 non-Tales products** (Heads, Canon, Big Idea, NSTXView, Vision, Pulse, Voice, Guardian) — vestiges of the broader "Solstice AI Suite" architecture. PNNL only needs Tales. So we started a cleanup branch to strip the repo down to just Tales.

### Work completed today

1. **Discovered local TalesToGo folder was not a git clone.** Grafted `.git` from `github.com/rtwodeetwo/talestogo` into the local folder, did a `git checkout HEAD -- .` to bring local files in line with GitHub (12 files were ~4 days behind GitHub; 11 files including the `frontend/src/pages/heads/` directory existed on GitHub but were missing locally).

2. **Pushed an MIT LICENSE** to `github.com/rtwodeetwo/talestogo` via the GitHub API (commit `3e8b170`). Copyright: "Rachel Kremen" — Rachel confirmed she is the legal copyright holder after checking with PPPL legal.

3. **Created a Google Doc with PNNL meeting Q&A:** "PNNL Tales Deployment - Meeting Prep & Q&A" (https://docs.google.com/document/d/1NlOGu-8YmWOkGeue36GlcefuzxyGok3WdzJGQBdUYBI/edit). Covers: how PNNL gets updates, build-locally vs. Docker Hub, how to access the full source code, registry-mirror requirements.

4. **Drafted a reply to Ross Lanes at PNNL** confirming the GitHub URL is the canonical source and offering to add `ross-lanes` and `domskurka-pnnl` as collaborators.

5. **Started branch `strip-to-tales-only`** with the following commits:
   - `Phase 1a: Remove non-Tales backend routers and services` — deleted `app/routers/{heads,personas,canon,bigidea}.py`, `app/services/{persona_generator,pptx_generator}.py`, plus stale `.backup`/dead-code files. Updated `main.py`. (11 files changed, +146 -3,344)
   - `Phase 1b: Strip non-Tales code from shared backend files` — removed `PersonaType`, `PersonaGeneration`, `Persona` models; `allowed_products` column on User; all persona schemas/CRUD; `_Settings` and `TenantConfig` in config.py; `check_product_access` middleware (deleted `app/dependencies.py`); deleted `app/services/perplexity_service.py` (was Heads-only). (9 files changed, +23 -846)
   - `Phase 2a: Delete non-Tales frontend pages, services, types, and assets` — deleted `frontend/src/pages/{heads,canon,bigidea}/` directories, `HowHeadsWorks.tsx`, `HowCanonWorks.tsx`, `headsService.ts`, `bigideaService.ts`, `types/heads.ts`, `types/bigidea.ts`, and 4 product logo PNG/SVG files in `frontend/public/`. (35 files deleted)
   - `Phase 2b: Remove multi-product abstraction from frontend` — deleted `ProductContext.tsx` and `ProductSwitcher.tsx`; rewrote `AppContent.tsx` (~480 → ~280 lines); cleaned up `Layout.tsx` (removed product-conditional logic, switcher, `getMenuItems` switch); cleaned up `UserManagement.tsx` (removed `allowed_products` UI, replaced "App Access" column with "Tenant"); cleaned up `api.ts`, `AuthContext.tsx`, `types/index.ts`. (8 files changed, +294 -1,229)

**Cumulative as of pause:** ~85 files removed, ~5,400 lines deleted, ~470 added. Backend has zero orphan refs to deleted modules. Frontend has zero orphan refs to ProductContext/ProductSwitcher/useProduct/allowed_products/persona/heads/canon/bigidea.

### Key decision: KEEP multi-tenancy

Rachel originally asked to strip multi-tenancy entirely. After investigation we found:
- Only 91 `tenant_id` references across 10 files (heavily concentrated in tenants.py, llm_providers.py)
- Pages do NOT load tenant_id — data is scoped by `user_id`
- `tenant_id` is mostly used for: brand-sharing scope, LLM provider scoping, tenant management API
- The actually-problematic part (the "Solstice HC" hardcoded mapping, product-tenant config) was already gone after Phase 1b

We chose **Option D: keep multi-tenancy** infrastructure. Each lab can be a tenant if they want, or ignore the feature entirely (`tenant_id` is nullable). What was removed: `Solstice HC` config, `solsticehc.net` email-domain mapping, the `TENANT_PRODUCTS` product-tenant access map.

### Remaining phases (as of pause on 2026-05-08)

| Phase | Scope |
|---|---|
| **3** | Migrations cleanup — delete `migrations/{add_heads_tables.py, add_solstice_tenant.py, add_allowed_products.py}` |
| **4** | Docs cleanup — `CLAUDE.md`, `README.md`, `USER_GUIDE.md`, `IT_DEPLOYMENT_GUIDE.md` — remove Heads/Canon/Solstice references, "Solstice AI Suite" branding |
| **5** | Remove "Generate Report All Data" button — frontend only (`ReportsPage.tsx` lines 244-253 + `generateAllDataMutation` lines 77-94). **Leave the backend endpoint** `/tasks/generate-all-data-report/` in place. **NOTE:** apps.robotrachel.com is built from `tales_project`, NOT this repo. Removing the button here only affects the public PNNL version. The production app needs an independent change in `tales_project`. |
| **6** | Full evals & testing — backend `pytest`, frontend `npm install` + `npm run build`, fresh DB integration test, backend smoke test, manual Tales feature checklist, multi-tenancy verification |
| **7** | Fresh SAST + dependency audit — `bandit`, `semgrep`, `pip-audit`, `npm audit`. Diff against existing reports (`bandit-report.json`, `semgrep-report.json`, `pip-audit-report.json`, `npm-audit-report.json`) to confirm no new vulnerabilities. **No DAST.** |
| **8** | Push `strip-to-tales-only` branch to GitHub `talestogo`, merge to `main` |

### Where state lives

- **Local working tree:** `/Users/rkremen/Documents/Code/TalesToGo/` on branch `strip-to-tales-only`
- **Remote:** `origin → github.com/rtwodeetwo/talestogo.git`
- **Branch is local-only** at pause time — has not been pushed to GitHub
- Commit count on branch: 4 (Phases 1a, 1b, 2a, 2b)

### Outstanding follow-ups (outside this branch)

- **Reply to Ross Lanes (PNNL)** with the GitHub URL and offer to add him + Domenic Skurka as collaborators (draft is in conversation, not yet sent)
- **Add LICENSE to `tales_project`** if Rachel wants the same MIT license there (separate task, separate repo)
- **Remove "Generate Report All Data" button from `tales_project`** if Rachel wants it gone from production (separate task, separate repo)
- **Consider GitHub repo description / contributing guidelines** before PNNL clones

### Known Issues — pre-existing or deferred (NOT fixed by this branch)

These were discovered during the strip-to-Tales cleanup but were either pre-existing in the talestogo repo before this branch began or were intentionally left out of scope. None of them block PNNL deployment. Listed here so a future session has the full picture and so they aren't silently forgotten.

#### Pre-existing bugs (broken since the initial talestogo commit)

- **`tests/test_api.py` — broken import.** `from app.main import app as fastapi_app, get_db` fails with `ImportError: cannot import name 'get_db'`. `get_db` lives in `app.database`, not `app.main`. Fix is a one-line import change. We did not touch this test file.
- **`tests/test_celery_tasks.py` — broken import.** `from celery_app.tasks import (...)` fails with `ModuleNotFoundError: No module named 'celery_app'`. Celery was apparently removed from the codebase at some point but this test file was never updated or deleted.
- **`tests/test_tasks.py` — broken import** (same shape as `test_celery_tasks.py`).
- **`tests/test_crud.py` — 32 failing tests.** All fail with `TypeError: create_analysis_history() missing 1 required positional argument: 'user_id'`. The `user_id` argument was added when multi-tenancy was introduced, but `test_crud.py` was never updated to match. Git log confirms `user_id` has been required since the initial commit on talestogo.

  Net pytest state: of ~5 test files, 3 fail to even collect, 1 has 32 failing tests, 1 (`test_main.py`) is empty. Our cleanup did not touch any of them.

#### Pre-existing dependency issues

- **`google.generativeai` package is end-of-life.** Importing the backend logs `FutureWarning: All support for the 'google.generativeai' package has ended. ... Please switch to the 'google.genai' package as soon as possible.` Used in `app/services/generic_llm_client.py`. Migration to `google.genai` is straightforward but pre-existing.
- **18 npm vulnerabilities reported on `npm install`** (9 moderate, 8 high, 1 critical). All from transitive deps in `frontend/package-lock.json`. Phase 7 will surface specifics; deferred to that phase.

#### Deprecation warnings from upstream library upgrades

These are not bugs today but are scheduled-for-removal API uses:

- **Pydantic v1-style `class Config`** in:
  - `app/routers/batches.py:33` (`BatchResponse`)
  - `app/routers/scheduled_tasks.py:51` (`ScheduleResponse`)
  - `app/routers/scheduled_tasks.py:79` (`HistoryResponse`)
  Should be migrated to Pydantic v2 `model_config = ConfigDict(...)`.
- **FastAPI `@app.on_event("startup")` / `@app.on_event("shutdown")`** in `app/main.py:209` and `app/main.py:265`. Should be migrated to lifespan event handlers.

#### Repo cleanliness — out of scope for the strip-to-Tales mission

These won't affect PNNL's deployment but are noise the public repo could do without:

- **~16 generated sample report markdown files at repo root** (`report_*.md` for PPPL, Princeton Engineering, Physics of Plasmas, TALES test reports). Real reports Rachel generated; not deployment artifacts.
- **~13 personal debug/admin scripts at repo root** (`check_*.py`, `fix_*.py`, `manual_*.py`, `force_*.py`, `emergency_*.py`, `merge_*.py`, etc.). Personal Tales operator scripts that don't belong in a public deployment repo.
- **~50 historical dev docs at repo root** (login system investigations, methodology docs, OAuth visual guides, implementation summaries, theme flash notes, etc.). Many predate or are unrelated to PNNL deployment. The PNNL-facing docs (`docs/`, `deployment-kit/`) are clean.
- **Tracked binary artifacts at repo root:**
  - `file:crudtest` — SQLite DB literally with a colon in the filename, accidentally committed in the initial commit
  - `tales.db`, `tales.db.old`, `tales.db.backup_*` — local SQLite DBs and backups
  - `celerybeat-schedule.db`, `celerybeat-schedule-shm` — Celery scheduler artifacts despite Celery no longer being in the code
- **Old distribution / export files** at repo root: `tales_to_go_20260127.zip`, `tales_export_20251106_202307.json`, `sqlite_export.json`, `user_data_export.sql`, `user_data_export_v2.sql`.
- **Duplicate methodology files**: `Methodology_Additions.md` and `Methodology_Additions.txt` (.txt is a duplicate of the .md).
- **Two Word docs at repo root**: `Internal_Developer_Guide_With_Additions.docx` and `PPPL_Developer_Guide_Suggested_Additions.docx`.
- **`deployment-kit-pppl/data/pppl_brand.json`** still contains `"original_owner_email": "robotrachel@gmail.com"` (PPPL-specific demo data, intentionally not edited).
- **Old SAST/audit JSON files at repo root**: `bandit-report.json`, `npm-audit-report.json`, `pip-audit-report.json`, `semgrep-report.json`. Will be regenerated in Phase 7.

#### Frontend performance note (not a bug)

- `npm run build` warns: "Some chunks are larger than 500 kB after minification" (the main JS bundle is ~2.18 MB / 612 KB gzipped). Suggestion is dynamic `import()` for code-splitting, or `build.rollupOptions.output.manualChunks`. Pre-existing; Tales loads fine, just a slow first-paint.

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
