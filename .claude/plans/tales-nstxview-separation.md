# Tales & NSTXView Separation Plan

## Current State

**Architecture:** Modular monolith - everything in one codebase, one database, one deployment.

### What's Shared:
| Component | Shared? | Details |
|-----------|---------|---------|
| Database | YES | Single PostgreSQL on Railway |
| Authentication | YES | Google + Microsoft OAuth, shared JWT |
| User model | YES | `allowed_products` field controls access |
| Frontend | YES | Single React app with product switcher |
| Docker image | YES | One container for everything |
| Railway project | YES | One deployment per environment |

### NSTXView-Specific Components:
- **Backend:** `app/routers/nstxview.py`, `outliers.py`, `thresholds.py`
- **Services:** `app/services/nstxview/` (7 files)
- **Models:** 12 NSTXView tables in `models.py`
- **Frontend:** `frontend/src/pages/nstxview/` (10 components)
- **Scripts:** `scripts/process_nstxview_papers.py`, `run_nstxview_processing.sh`
- **External:** Google Drive sync, ChromaDB vector store

---

## Questions to Answer Before Choosing an Approach

### 1. PPPL Deployment Goal
- [ ] PPPL hosts ONLY NSTXView (Tales stays on robotrachel.com)
- [ ] PPPL hosts BOTH Tales and NSTXView
- [ ] Not sure yet

### 2. Database Preference
- [ ] Completely separate databases (cleaner, more work)
- [ ] Same database, just organize code better (simpler)
- [ ] Separate databases only when moving to PPPL

### 3. Authentication at PPPL
- [ ] Use existing Google/Microsoft OAuth
- [ ] PPPL has their own identity provider (LDAP, Shibboleth, etc.)
- [ ] Need a separate auth system for NSTXView
- [ ] Not sure yet

### 4. Timeline
- [ ] Hard deadline in January (minimal changes only)
- [ ] Some flexibility (can do moderate refactoring)
- [ ] No rush (can do full separation)

---

## Option A: Code Reorganization Only (Easiest)

**What:** Reorganize files to clearly distinguish Tales vs NSTXView. Keep same database and deployment.

**Changes:**
1. Rename `tales_project/` to something neutral like `pppl_apps/` or `robotrachel_apps/`
2. Create clear folder structure:
   ```
   pppl_apps/
   ├── app/
   │   ├── tales/           # Tales-specific routers & services
   │   ├── nstxview/        # NSTXView routers & services (move from services/nstxview)
   │   ├── shared/          # Auth, users, common utilities
   │   └── models/          # Split into tales_models.py, nstxview_models.py
   ├── frontend/
   │   ├── tales/           # Tales pages
   │   └── nstxview/        # NSTXView pages
   ```
3. Update imports throughout

**Pros:**
- Minimal risk
- No OAuth/Railway changes
- Can be done in a day or two

**Cons:**
- Still one database
- Still one deployment
- Doesn't help with PPPL separation

**Effort:** 1-2 days

---

## Option B: Separate Databases, Same Codebase (Medium)

**What:** Create a second PostgreSQL database for NSTXView data, but keep shared auth/users in original database.

**Changes:**
1. Create new Railway PostgreSQL instance for NSTXView
2. Add `NSTXVIEW_DATABASE_URL` environment variable
3. Create separate SQLAlchemy engine/session for NSTXView models
4. Migrate existing NSTXView data to new database
5. Keep user/auth tables in original database (shared)

**Database Split:**
```
Original DB (tales):          New DB (nstxview):
- users                       - nstx_papers
- tenants                     - nstx_shots
- queries                     - nstx_parameters
- responses                   - nstx_phenomena
- brands                      - nstx_paper_chunks
- [all Tales tables]          - nstx_conversations
                              - parameter_thresholds
                              - ingestion_batches
```

**Pros:**
- Data clearly separated
- Can backup/migrate NSTXView DB independently
- Easier to move NSTXView to PPPL later

**Cons:**
- Need to manage two database connections
- User foreign keys need careful handling
- Railway cost increases (second DB)
- OAuth config stays the same

**Effort:** 3-5 days

**Railway Changes:**
- Add new PostgreSQL service
- Add `NSTXVIEW_DATABASE_URL` env var
- No OAuth changes needed

---

## Option C: Full Separation into Two Apps (Hardest)

**What:** Split into two completely independent applications with their own databases, deployments, and optionally auth.

**Changes:**
1. Create new repository: `nstxview/`
2. Copy NSTXView-specific code
3. Create separate Railway project
4. Set up separate database
5. Either:
   - a) Share OAuth (both apps verify same Google/Microsoft tokens)
   - b) Separate auth (NSTXView gets its own user system)

**New Structure:**
```
tales_project/               nstxview/
├── app/                     ├── app/
│   ├── routers/            │   ├── routers/
│   │   └── [Tales only]    │   │   ├── papers.py
│   └── services/           │   │   ├── chat.py
│       └── [Tales only]    │   │   └── outliers.py
├── frontend/               │   └── services/
└── [Tales-only files]      │       └── [NSTXView services]
                            ├── frontend/
                            └── [NSTXView-only files]
```

**Pros:**
- Complete independence
- Easy to transfer NSTXView to PPPL
- No cross-contamination risk
- Can have different deployment schedules

**Cons:**
- Most work
- Need to duplicate auth code (or create shared auth service)
- Two Railway projects to manage
- User management complexity

**Effort:** 1-2 weeks

**Railway/OAuth Changes:**
- New Railway project for NSTXView
- New PostgreSQL instance
- If separate auth: New Google OAuth app, new Microsoft app registration
- If shared auth: Both apps use same OAuth credentials, verify tokens independently

---

## Recommendation

**For a January PPPL deadline:** Option A or B

- **Option A** if you just want clarity now and will do full separation later
- **Option B** if you want NSTXView data portable and ready to migrate

**For full separation:** Option C, but start now and plan for 1-2 weeks of work

---

## Questions for You

1. Which option sounds right given your PPPL timeline?
2. Will PPPL want their own authentication, or can we use Google OAuth?
3. Is there a specific PPPL infrastructure we need to target (Kubernetes, specific cloud, on-prem)?
