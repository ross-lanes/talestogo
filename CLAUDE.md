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

### Known Issues — pre-existing or deferred

These were discovered during the strip-to-Tales cleanup. The first three groups have been **resolved on this branch** (Phase 6.1 - 6.4). The remaining group is genuinely deferred. None block PNNL deployment.

#### ✅ Fixed in Phase 6.2: pytest test suite

  Was: 33 broken tests (3 collection-error files, 32 stale-signature failures in test_crud.py).
  Now: 32 passing, 0 failing.
  - `tests/test_api.py`, `tests/test_celery_tasks.py`, `tests/test_tasks.py`, `tests/test_main.py` deleted (all referenced removed modules / outdated API assumptions).
  - `tests/test_crud.py` updated to seed a TEST_USER_ID and pass `user_id=TEST_USER_ID` through all 64 CRUD call sites; descriptor schema updated from old `category`/`target_for_pppl` fields to current `is_target`.
  - Production bug found and fixed: `app/crud.py:get_target_descriptors` was filtering on `models.TargetDescriptor.target_for_pppl == True`, but that column was renamed to `is_target` long ago. Would have raised AttributeError at runtime when admins viewed target descriptors.

#### ✅ Fixed in Phase 6.3: google.generativeai end-of-life

  Migrated `app/ai_generator.py`, `app/services/generic_llm_client.py`, and `app/services/llm_service.py` from the deprecated `google.generativeai` SDK to the supported `google-genai` SDK. `requirements.txt` updated. The "All support for google.generativeai has ended" FutureWarning that was logged on every backend startup is gone.

#### ✅ Fixed in Phase 6.4: npm vulnerabilities

  Was: 18 vulnerabilities (9 moderate, 8 high, 1 critical).
  Now: 0 vulnerabilities.
  - `npm audit fix` upgraded transitive deps with safe patches.
  - The remaining critical (jspdf) and high (xlsx) were both packages declared in `package.json` but not actually used: `jspdf` had zero imports anywhere, `xlsx` had three import-but-never-used statements. Both packages uninstalled and the dead imports removed. Bundle size unchanged.

#### ✅ Fixed in Phase 6.1: repo cleanliness

  ~200 files removed from the repo root: ~18 sample `report_*.md` files, ~36 personal debug/admin scripts, ~45 historical dev-doc markdowns, tracked binary artifacts (`file:crudtest`, `tales.db`, `tales.db.backup_*`, `celerybeat-schedule.db`, etc.), old distribution archives, exports, Word docs, the `deployment-kit-pppl/` PPPL bundle, the `images/` and `report_charts/` directories, and Rachel-specific platform configs (`apprunner.yaml`, `nixpacks.toml`, `Procfile`, `render.yaml`, `railway_build.sh`, `docker-compose.{nstxview,pppl}.yml`). `.gitignore` updated to prevent these patterns from sneaking back in.

  Repo root is now AGENTS.md, CLAUDE.md, Dockerfile, LICENSE, README.md, app/, deployment-kit/, docker-compose.yml, docs/, frontend/, migrations/, pyproject.toml, requirements.txt, scripts/, start_tales.sh, tests/.

#### ⏳ Deferred — deprecation warnings from upstream library upgrades

These are not bugs today but are scheduled-for-removal API uses. Out of scope for the strip-to-Tales mission; deferred to a future maintenance pass.

- **Pydantic v1-style `class Config`** in:
  - `app/routers/batches.py:33` (`BatchResponse`)
  - `app/routers/scheduled_tasks.py:51` (`ScheduleResponse`)
  - `app/routers/scheduled_tasks.py:79` (`HistoryResponse`)
  Should be migrated to Pydantic v2 `model_config = ConfigDict(...)`.
- **FastAPI `@app.on_event("startup")` / `@app.on_event("shutdown")`** in `app/main.py:209` and `app/main.py:265`. Should be migrated to lifespan event handlers.

#### ⏳ Deferred — frontend bundle size

- `npm run build` warns: "Some chunks are larger than 500 kB after minification" (main bundle ~2.18 MB / 613 KB gzipped). Suggestion is dynamic `import()` for code-splitting or `manualChunks`. Pre-existing; Tales loads fine, just a slow first-paint. Out of scope for cleanup.

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
