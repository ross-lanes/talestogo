# Tales Deployment Kit (PPPL-Compliant)

This kit contains everything you need to deploy Tales at your organization. It follows the PPPL Internal Developer Guide standards for container-first deployment.

## What's Included

| File | Description |
|------|-------------|
| `README.md` | This file - quick start guide |
| `.env.template` | Environment variables template (PPPL-compliant) |
| `docker-compose.yml` | Docker configuration (PPPL-compliant) |
| `setup.sh` | Helper script for initial setup |
| `IT_DEPLOYMENT_GUIDE.md` | Complete IT deployment instructions |
| `IT_DEPLOYMENT_GUIDE.docx` | Word version of IT guide |
| `USER_GUIDE.md` | End-user documentation |
| `USER_GUIDE.docx` | Word version of user guide |

---

## PPPL Compliance

This deployment kit follows PPPL standards:
- Multi-stage Dockerfile with `node:20-alpine` and `python:3.11-slim`
- GitLab CI/CD with proper tagging (`:latest`, version tags, branch names)
- OIDC variable naming (`OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`)
- All secrets via environment variables

---

## Quick Start (5 Minutes)

### Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- At least one LLM API key (Gemini recommended)
- OIDC credentials from IT (if using Entra ID authentication)

### Step 1: Configure Environment

Copy the template and add your values:

```bash
cp .env.template .env
```

Edit `.env` and add at minimum:

```bash
# REQUIRED: Security keys (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))")
APP_SECRET=your-random-secret-key
ENCRYPTION_KEY=your-random-encryption-key

# REQUIRED: At least one LLM API key
GEMINI_API_KEY=your-gemini-api-key

# OIDC Configuration (IT provides these)
OIDC_CLIENT_ID=from-it-department
OIDC_CLIENT_SECRET=from-it-department
```

### Step 2: Start Tales

```bash
docker compose up -d
```

Wait for containers to start (about 30 seconds).

### Step 3: Create Admin Account

```bash
docker compose exec app python scripts/admin/setup_initial_admin.py
```

Follow the prompts. **Save the generated password - it's shown only once.**

### Step 4: Log In

Open your browser to: `http://localhost:8080`

Log in with the admin credentials from Step 3.

---

## Multi-Lab Deployment

Each lab deploys their own instance with lab-specific configuration:

### Lab-Specific Variables

```bash
# Your lab's Entra ID credentials (from IT)
OIDC_CLIENT_ID=your-lab-client-id
OIDC_CLIENT_SECRET=your-lab-client-secret

# Optional: Tenant-specific OIDC endpoint
OIDC_DISCOVERY_URL=https://login.microsoftonline.com/{your-tenant-id}/v2.0/.well-known/openid-configuration

# Branding for your lab
SITE_NAME=ORNL Tales
SITE_LOGO_URL=https://your-lab.gov/logo.png
SITE_PRIMARY_COLOR=#00629B
```

### Authentication Flags

Control which login methods are available:

```bash
ENABLE_LOCAL_AUTH=true       # Email/password
ENABLE_MICROSOFT_AUTH=true   # Entra ID / Microsoft
ENABLE_GOOGLE_AUTH=false     # Google OAuth
```

---

## What's Next?

After logging in:

1. **Configure LLM Providers** (optional) - Go to Profile > LLM Configuration to customize provider names/colors
2. **Create a Brand** - Go to Manage > Brands and add your first brand to monitor
3. **Add Queries** - Add questions that users might ask AI platforms about your brand
4. **Run Collection** - Go to Data > Collect & Analyze to gather AI responses

**Automated Collection:** Once configured, Tales automatically collects data on the 1st, 7th, 14th, and 21st of each month. Reports are generated monthly, quarterly, and annually.

---

## Authentication Options

| Method | Setup Required | Variables |
|--------|----------------|-----------|
| Email/Password | None | `ENABLE_LOCAL_AUTH=true` (default) |
| Microsoft/Entra ID | OIDC credentials from IT | `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET` |
| Google OAuth | Optional | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `ENABLE_GOOGLE_AUTH=true` |

---

## LLM Provider Configuration

Tales auto-detects which API keys you've configured and makes those providers available.

| Provider | Environment Variable | Get API Key | Notes |
|----------|---------------------|-------------|-------|
| Google Gemini | `GEMINI_API_KEY` | https://makersuite.google.com/app/apikey | **Recommended** - Cheapest, supports analysis + web search |
| OpenAI (ChatGPT) | `OPENAI_API_KEY` | https://platform.openai.com/api-keys | Good for data collection |
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys | Good for data collection |
| Perplexity | `PERPLEXITY_API_KEY` | https://www.perplexity.ai/settings/api | Supports web search |

**Minimum requirement:** At least one LLM API key. We recommend Gemini because it's the cheapest and supports both analysis and web search features.

---

## PPPL Variable Reference

| PPPL Standard | Legacy Name | Description |
|---------------|-------------|-------------|
| `APP_SECRET` | `JWT_SECRET_KEY` | JWT signing secret |
| `OIDC_CLIENT_ID` | `MICROSOFT_CLIENT_ID` | Azure AD client ID |
| `OIDC_CLIENT_SECRET` | `MICROSOFT_CLIENT_SECRET` | Azure AD client secret |
| `OIDC_DISCOVERY_URL` | (new) | OIDC discovery endpoint |

Legacy variable names are supported for backwards compatibility.

---

## Troubleshooting

### Container won't start

```bash
docker compose logs app
```

Check for missing environment variables or database connection issues.

### Can't log in

Verify you're using the correct credentials from the setup script. If you forgot the password, create a new admin:

```bash
docker compose exec app python scripts/admin/setup_initial_admin.py
```

### LLM features not working

1. Check that API keys are set in `.env`
2. Restart the container: `docker compose restart app`
3. Go to LLM Configuration and click "Test" on each provider

---

## Support

- Full IT documentation: `IT_DEPLOYMENT_GUIDE.md`
- User documentation: `USER_GUIDE.md`
- Contact your Tales administrator for additional help
