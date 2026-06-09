# Security Policy

## Overview

This document describes the security practices, testing methodology, and vulnerability disclosure policy for Tales — an AI reputation monitoring platform designed for self-hosted deployment at research institutions.

Tales is maintained by RobotRachel and shared with U.S. Department of Energy national laboratories (PPPL, PNNL, Argonne, LLNL) under an MIT license for self-hosted, air-gappable deployment.

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security concerns directly to the maintainer:

- **Email**: robotrachel@gmail.com
- **Subject line**: `[SECURITY] Tales — <brief description>`
- **Expected response time**: Within 72 hours

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce
- Any suggested mitigations

You will receive acknowledgement within 72 hours and a resolution plan within 14 days for confirmed vulnerabilities.

---

## Security Testing

Tales undergoes static analysis and dependency auditing before each release. The results below reflect the state of the `main` branch as of **2026-06-08** (post-merge of PRs #1, #2, #3, #4).

### Static Application Security Testing (SAST)

| Tool | Scope | Findings | Notes |
|------|-------|----------|-------|
| [Bandit](https://bandit.readthedocs.io/) v1.9+ | Python backend (`app/`, runtime web application) | **0** medium/high severity | 3 B608 (SQL injection) false positives suppressed with `# nosec B608`; all use format-validated identifiers, not user input |
| Bandit (same run) | Python ops scripts (`scripts/testing/`) | **0** medium/high severity | `scripts/admin/` and `scripts/migrations/` are excluded via `[tool.bandit]` in `pyproject.toml` — these are one-shot local-dev scripts not part of the deployed surface area and not user-reachable |
| [npm audit](https://docs.npmjs.com/cli/commands/npm-audit) | Frontend JavaScript dependencies | **0** vulnerabilities | |

**Bandit suppression rationale** — The three `# nosec B608` annotations appear in migration utility files (`run_migrations.py`, `migration_helper.py`). In each case, the SQL identifier (table name or sequence name) is validated against a strict allowlist or regex format check before being interpolated. No user-supplied input reaches these queries.

### Dependency Vulnerability Scanning

| Tool | Scope | Findings | Notes |
|------|-------|----------|-------|
| [pip-audit](https://pypi.org/project/pip-audit/) | Python packages | **0** application CVEs | 2 CVEs affect the `pip` package manager itself (CVE-2026-3219, CVE-2026-6357); the Dockerfile upgrades pip during build (`pip install --upgrade pip`) |
| [npm audit](https://docs.npmjs.com/cli/commands/npm-audit) | npm packages | **0** | |

### Reproducing the audit

```bash
# Static analysis
bandit -r app/ scripts/ -ll -c pyproject.toml

# Python dependency CVEs
pip-audit --strict -r requirements.txt

# JavaScript dependency CVEs
cd frontend && npm audit
```

All three commands exit zero with no findings on the current `main`.

### Audit log

| Date | Branch / commit | bandit | pip-audit | npm audit | Notes |
|------|-----------------|--------|-----------|-----------|-------|
| 2026-06-09 | `bing-web-search` (pre-merge) | 0 medium/high | 0 CVEs | 0 vulns | Adds Bing as a web-search provider (`bing_v7` retrieval + analysis-LLM synthesis; `bing_grounded` via Azure AI Foundry, gated behind `pip install talestogo[bing-grounded]` optional extra). 64/64 pytest passing. The Azure AI Foundry SDK is NOT a base dependency — non-Bing deployers see no install-size or runtime impact. |
| 2026-06-08 | `main` @ `7536ceaf` | 0 medium/high | 0 CVEs | 0 vulns | Post-merge re-audit covering PRs #1 (Azure provider-agnostic refactor — new `_call_azure` codepath, `api_version` plumbing) and #3 (`/responses/` defensive limit clamp). 53/53 pytest passing. Confirms the merged state is still clean. |
| 2026-06-08 | `main` @ `f77ee3a8` | 0 medium/high | 0 CVEs | 0 vulns | Initial 2026-06-08 audit. Bumped `vitest` / `@vitest/ui` from 4.0.8 → 4.1.8 to clear [GHSA-5xrq-8626-4rwp](https://github.com/advisories/GHSA-5xrq-8626-4rwp) (critical, dev-only). Added `[tool.bandit]` exclusions for offline ops scripts. |
| 2026-05-09 | `strip-to-tales-only` | 0 medium/high (after 3 `# nosec B608`) | 0 CVEs | 0 vulns | Initial post-strip baseline. Established the SBOMs below. |

### Software Bill of Materials (SBOM)

SBOMs are provided in [CycloneDX 1.6](https://cyclonedx.org/) JSON format, as recommended under [Executive Order 14028](https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/) (Improving the Nation's Cybersecurity).

| File | Contents |
|------|----------|
| [`docs/security/sbom-python.cdx.json`](docs/security/sbom-python.cdx.json) | 31 Python runtime dependencies |
| [`docs/security/sbom-npm.cdx.json`](docs/security/sbom-npm.cdx.json) | 520 JavaScript dependencies (direct + transitive) |

SBOMs are regenerated with each release using:
- Python: [`cyclonedx-bom`](https://pypi.org/project/cyclonedx-bom/)
- JavaScript: [`@cyclonedx/cyclonedx-npm`](https://www.npmjs.com/package/@cyclonedx/cyclonedx-npm)

---

## Secure Development Practices

### Authentication & Authorization

- JWT-based authentication with configurable expiry
- Passwords hashed with bcrypt (cost factor 12)
- All API endpoints require authentication except `/health`, `/auth/login`, `/auth/config`, and `/site/branding`
- Admin-only endpoints enforce `is_admin` flag; no email-based role hardcoding
- Optional OAuth 2.0 / OIDC via Microsoft Entra ID or Google

### API Keys

- LLM provider API keys are stored encrypted at rest using Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
- Keys are never returned in API responses; only masked previews are exposed

### Transport Security

- HTTPS is enforced at the reverse proxy / load balancer layer (see `docs/IT_DEPLOYMENT_GUIDE.md`)
- HSTS, X-Frame-Options, X-Content-Type-Options, and Referrer-Policy headers are set by the application
- Content Security Policy (CSP) is applied with a per-request nonce for inline styles
- Fonts are self-hosted; no external CDN calls from the browser

### Rate Limiting

- Login and registration endpoints are rate-limited via [SlowAPI](https://pypi.org/project/slowapi/) (default: 5 requests/minute per IP)

### Input Validation

- All API request bodies are validated with Pydantic v2 schemas before reaching business logic
- Email addresses validated with `email-validator` (RFC-compliant)
- File uploads (query bulk import) are restricted to `.xlsx` format with column validation

### Database

- All user-facing queries use SQLAlchemy ORM with parameterized queries
- Raw SQL is used only in migration utilities, with identifier allowlisting
- Row-level data isolation: all queries are scoped by `user_id`; users cannot access other users' data

### Docker Hardening

- Multi-stage build — build tools are not present in the runtime image
- Application runs as a non-root user (`appuser`)
- Only `libpq5` runtime library added to the slim base image
- Health check configured for container orchestration

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main` branch | ✅ Active |
| Older branches | ❌ Not maintained |

PNNL and other deploying institutions are encouraged to pull from `main` and report any issues through the channel above.

---

## Known Limitations

- **Frontend bundle size**: The main JavaScript bundle is ~2.2 MB uncompressed / 613 KB gzipped. This is a performance concern (slow first paint), not a security issue. Code splitting is tracked as a future improvement.
- **No DAST**: Dynamic Application Security Testing (e.g., OWASP ZAP) has not been performed against a live deployment. Institutions with strict DAST requirements may wish to run their own scan post-deployment.
- **Scheduler**: The built-in APScheduler runs in-process. For high-security environments, consider setting `ENABLE_SCHEDULER=false` and triggering collection/analysis via the API from an external cron job.
