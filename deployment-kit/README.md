# Tales Deployment Kit

This kit contains everything you need to deploy Tales at your organization.

## What's Included

| File | Description |
|------|-------------|
| `README.md` | This file - quick start guide |
| `.env.template` | Environment variables template |
| `docker-compose.yml` | Docker configuration |
| `setup.sh` | Helper script for initial setup |
| `IT_DEPLOYMENT_GUIDE.md` | Complete IT deployment instructions |
| `IT_DEPLOYMENT_GUIDE.docx` | Word version of IT guide |
| `USER_GUIDE.md` | End-user documentation |
| `USER_GUIDE.docx` | Word version of user guide |

---

## Quick Start (5 Minutes)

### Prerequisites

- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- At least one LLM API key (Gemini recommended)

### Step 1: Configure Environment

Copy the template and add your API keys:

```bash
cp .env.template .env
```

Edit `.env` and add at minimum:

```bash
# REQUIRED: At least one LLM API key
GEMINI_API_KEY=your-gemini-api-key

# REQUIRED: Security keys (generate with: python3 -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=your-random-secret-key
ENCRYPTION_KEY=your-random-encryption-key
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

## What's Next?

After logging in:

1. **Configure LLM Providers** (optional) - Go to Profile > LLM Configuration to customize provider names/colors
2. **Create a Brand** - Go to Manage > Brands and add your first brand to monitor
3. **Add Queries** - Add questions that users might ask AI platforms about your brand
4. **Run Collection** - Go to Data > Collect & Analyze to gather AI responses

**Automated Collection:** Once configured, Tales automatically collects data on the 1st, 7th, 14th, and 21st of each month. Reports are generated monthly, quarterly, and annually. See the IT Deployment Guide for scheduler details.

---

## Authentication Options

| Method | Setup Required | Notes |
|--------|----------------|-------|
| Email/Password | None | Works immediately after setup |
| Google OAuth | Optional | Add `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to `.env` |
| Microsoft OAuth | Optional | Add `MICROSOFT_CLIENT_ID` and `MICROSOFT_CLIENT_SECRET` to `.env` |

---

## LLM Provider Configuration

Tales auto-detects which API keys you've configured and makes those providers available. You only need to configure the providers you want to use.

### Default Providers

| Provider | Environment Variable | Get API Key | Notes |
|----------|---------------------|-------------|-------|
| Google Gemini | `GEMINI_API_KEY` | https://makersuite.google.com/app/apikey | **Recommended** - Cheapest, supports analysis + web search |
| OpenAI (ChatGPT) | `OPENAI_API_KEY` | https://platform.openai.com/api-keys | Good for data collection |
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys | Good for data collection |
| Perplexity | `PERPLEXITY_API_KEY` | https://www.perplexity.ai/settings/api | Supports web search |

**Minimum requirement:** At least one LLM API key. We recommend Gemini because it's the cheapest and supports both analysis and web search features.

### Custom Providers

You can add up to 2 additional custom providers (6 total). For custom providers, define your own environment variable:

```bash
# Example: Adding Mistral
MISTRAL_API_KEY=your-mistral-key
```

Then configure the provider in the Admin UI (LLM Configuration) and specify the environment variable name.

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
