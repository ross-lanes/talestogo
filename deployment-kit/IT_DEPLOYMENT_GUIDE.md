# Tales IT Deployment Guide

This guide is for IT teams deploying Tales at their organization. Tales is an AI reputation monitoring platform that tracks how your organization is represented across major AI platforms (ChatGPT, Claude, Gemini, Perplexity).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Initial Admin Setup](#initial-admin-setup)
5. [Verification](#verification)
6. [Optional: OAuth Configuration](#optional-oauth-configuration)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Docker** (version 20.10 or later)
- **Docker Compose** (version 2.0 or later)

### Required API Keys

You will need API keys from one or more LLM providers. Tales supports up to 6 LLM providers. API keys are configured exclusively through environment variables in the `.env` file.

| Provider | Purpose | Environment Variable | Get API Key |
|----------|---------|---------------------|-------------|
| Google Gemini | AI queries + analysis + web search | `GEMINI_API_KEY` | https://makersuite.google.com/app/apikey |
| OpenAI | ChatGPT queries | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| Anthropic | Claude queries | `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys |
| Perplexity | Perplexity queries + web search | `PERPLEXITY_API_KEY` | https://www.perplexity.ai/settings/api |

**Note:** You can configure any combination of LLMs you choose. At minimum, configure one provider with analysis capability (Gemini recommended). For the "State of the LLMs" report section, you need at least one provider with web search capability (Gemini or Perplexity).

**Partial Configuration:** You do not need API keys for all providers. Tales automatically detects which API keys are present and only makes those providers available. For example, if you only set `GEMINI_API_KEY`, only Gemini will appear as an available provider.

### Network Requirements

- Outbound HTTPS access to LLM provider APIs
- Port 8080 (or your chosen port) available for the web interface

---

## Quick Start

### 1. Download the Deployment Kit

Download the Tales deployment kit to your server.

### 2. Create Environment File

Copy the template and edit with your values:

```bash
cp .env.template .env
nano .env  # or use your preferred editor
```

**Minimum required variables:**

```bash
# Security (generate unique values for your deployment)
APP_SECRET=<generate-random-string>
ENCRYPTION_KEY=<generate-random-string>

# LLM API Keys (at minimum, you need Gemini for analysis)
GEMINI_API_KEY=<your-gemini-api-key>

# Optional but recommended: keys for querying other AI platforms
OPENAI_API_KEY=<your-openai-api-key>
ANTHROPIC_API_KEY=<your-anthropic-api-key>
PERPLEXITY_API_KEY=<your-perplexity-api-key>
```

**Generate secure random keys:**

```bash
# Run this twice to generate APP_SECRET and ENCRYPTION_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Start the Application

```bash
docker compose up -d
```

This will:
- Pull the Tales application container from Docker Hub
- Start a PostgreSQL database container
- Initialize the database schema
- Start the web server on port 8080

### 4. Create Initial Admin

Run the admin setup script inside the container:

```bash
docker compose exec app python scripts/admin/setup_initial_admin.py
```

Follow the prompts to create your first admin user. **Save the generated password securely.**

### 5. Access Tales

Open your browser to: `http://localhost:8080`

Log in with the admin credentials created in step 4.

---

## Configuration

### Environment Variables

See `.env.template` for a complete list of environment variables.

### Key Configuration Options

| Variable | Description |
|----------|-------------|
| `APP_SECRET` | JWT signing secret (required) |
| `ENCRYPTION_KEY` | Key for encrypting stored API keys (required) |
| `OIDC_CLIENT_ID` | Azure AD / Entra ID client ID |
| `OIDC_CLIENT_SECRET` | Azure AD / Entra ID client secret |
| `SITE_NAME` | Your organization's name for the UI |
| `SITE_PRIMARY_COLOR` | Primary theme color (hex) |

### Authentication Flags

Control which login methods are available:

```bash
ENABLE_LOCAL_AUTH=true       # Email/password login
ENABLE_MICROSOFT_AUTH=true   # Microsoft/Entra ID login
ENABLE_GOOGLE_AUTH=false     # Google login (disabled by default)
```

### Branding

Customize the appearance for your organization:

```bash
SITE_NAME=Your Organization Tales
SITE_LOGO_URL=https://your-org.gov/logo.png
SITE_PRIMARY_COLOR=#003e60
SITE_SECONDARY_COLOR=#75c9c8
```

### Changing the Port

To run on a different port, set it via environment variable:

```bash
APP_PORT=3000 docker compose up -d
```

### Using an External Database

To use your own PostgreSQL server instead of the bundled container:

1. Comment out or remove the `db` service in `docker-compose.yml`
2. Set `DATABASE_URL` in your `.env` file:

```bash
DATABASE_URL=postgresql://username:password@your-db-host:5432/tales_db
```

### Persistent Data

Database data is stored in a Docker volume named `tales_postgres_data`. This persists across container restarts.

To back up the database:

```bash
docker compose exec db pg_dump -U tales tales > backup.sql
```

To restore:

```bash
docker compose exec -T db psql -U tales tales < backup.sql
```

---

## Initial Admin Setup

The initial admin is created using a CLI script that runs inside the container.

### Running the Setup Script

```bash
docker compose exec app python scripts/admin/setup_initial_admin.py
```

The script will:
1. Verify database connection
2. Check for existing admin users
3. Prompt for admin email, name, and organization
4. Generate a secure temporary password
5. Create the admin user
6. Display the credentials (one time only)

### What the Admin Can Do

Once logged in, the admin can:
- **Configure Site Settings** - Set your organization's URL and contact email for notifications (Admin Menu > Site Settings)
- **Configure LLM Providers** - Set up which AI platforms to query (Admin Menu > LLM Configuration)
- Access the Admin Panel to manage users
- Invite new users (they will receive credentials to log in)
- Create and manage brands to monitor
- Run data collection queries
- View analytics and generate reports

---

## Site Settings Configuration

After initial setup, configure site-wide settings to customize email notifications and branding for your organization.

### Accessing Site Settings

1. Log in as an admin
2. Click your profile icon in the top right
3. Select **Site Settings** from the dropdown menu

### Configurable Settings

| Setting | Description | Default Behavior |
|---------|-------------|------------------|
| **Site URL** | Base URL for all email links (e.g., `https://mycompany.com/tales`) | Falls back to `FRONTEND_URL` environment variable |
| **Admin Email** | Contact email shown in notification emails | Falls back to `FROM_EMAIL` environment variable |
| **Site Name** | Application name used in email subjects and headers | Defaults to "TALES" |

### When to Configure

Configure these settings:
- **Before inviting users** - so invitation emails contain correct URLs
- **After changing domains** - if you move to a new URL
- **For white-labeling** - to customize the application name in emails

---

## Authentication

Tales supports multiple authentication methods. **Email/password authentication works out of the box with no additional setup.**

The login page dynamically adapts based on your configuration. It shows only the authentication methods you have enabled, in any combination:

- **Email/password only** (default) - a simple email and password form
- **OAuth only** - Google and/or Microsoft sign-in buttons
- **Both** - OAuth buttons at the top, an "or" divider, then the email/password form below

### Default: Email/Password

This is the simplest option and requires no additional configuration:

1. Create the initial admin using the setup script (see above)
2. Admin logs in with the generated email/password credentials
3. Admin invites users via the Admin Panel
4. New users receive credentials (via email if Resend is configured, or manually shared)

### Optional: OIDC (Microsoft Entra ID)

For enterprise single sign-on, configure OIDC:

```bash
OIDC_CLIENT_ID=<from-IT>
OIDC_CLIENT_SECRET=<from-IT>
ENABLE_MICROSOFT_AUTH=true  # enabled by default

# Optional: For tenant-specific authentication
OIDC_DISCOVERY_URL=https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration
```

| Auth Method | Setup Required | Best For |
|-------------|----------------|----------|
| Email/Password | None (works immediately) | Quick deployments, small teams |
| Microsoft/Entra ID | OIDC credentials from IT | Organizations using Microsoft 365 |
| Google OAuth | Google Cloud Console setup | Organizations using Google Workspace |
| Multiple methods | Configure each individually | Maximum flexibility for users |

### How Login Methods Are Controlled

Each authentication method requires two things to appear on the login page:

1. **Enable flag** set to `true` in your `.env` file
2. **Credentials configured** (client ID for OAuth methods)

| Method | Enable Flag | Also Requires |
|--------|------------|---------------|
| Email/Password | `ENABLE_LOCAL_AUTH=true` | Nothing else (works immediately) |
| Google | `ENABLE_GOOGLE_AUTH=true` | `GOOGLE_CLIENT_ID` set |
| Microsoft | `ENABLE_MICROSOFT_AUTH=true` | `OIDC_CLIENT_ID` or `MICROSOFT_CLIENT_ID` set |

If all methods are disabled or no credentials are provided, the login page displays: "No authentication methods configured. Please contact your administrator."

---

## LLM Provider Configuration

Tales supports up to 6 LLM providers: 4 default providers (ChatGPT, Claude, Gemini, Perplexity) plus up to 2 custom providers.

### Important: Two-Part Setup Required

Setting up each LLM provider requires completing BOTH parts:

| Part | Where | What |
|------|-------|------|
| **Part 1** | Server `.env` file | Add the API key (e.g., `GEMINI_API_KEY=AIzaSy...`) |
| **Part 2** | Admin UI | Configure display settings (name, model, color) |

**The Admin UI does NOT have an API key input field.** API keys are read from environment variables only. Both parts must be completed for a provider to work.

### Step-by-Step: Adding an LLM Provider

**Part 1: Configure API Key in Environment**

Add the API key to your `.env` file:

```bash
# Example: Adding Gemini
GEMINI_API_KEY=AIzaSy...your-key-here

# Example: Adding Claude
ANTHROPIC_API_KEY=sk-ant-...your-key-here
```

**Restart the Application** (required after `.env` changes):

```bash
docker compose restart app
```

**Part 2: Add LLM in Admin UI**

1. Log in as an admin
2. Go to LLM Configuration (profile menu > LLM Configuration)
3. Click "Add LLM"
4. Fill in the form fields (NO API key field exists):
   - **Display Name** - Human-readable name (e.g., "Gemini", "Claude")
   - **Provider Key** - Auto-generated unique ID (e.g., "gemini", "claude")
   - **API Type** - Select: OpenAI, Anthropic, Google, or OpenAI Compatible
   - **Model Name** - Model identifier (e.g., "gemini-2.0-flash", "claude-3-haiku-20240307")
   - **Chart Color** - Color for analytics charts
5. Configure options (Enabled, Use for Analysis, Supports Web Search)
6. Click "Add LLM"
7. Click "Test" to verify the connection works

### Environment Variable Mapping

Each API type reads from a specific environment variable:

| API Type | Environment Variable | Example Providers |
|----------|---------------------|-------------------|
| OpenAI | `OPENAI_API_KEY` | ChatGPT (gpt-4o, gpt-3.5-turbo) |
| Anthropic | `ANTHROPIC_API_KEY` | Claude (claude-3-haiku, claude-3-sonnet) |
| Google | `GEMINI_API_KEY` | Gemini (gemini-2.0-flash, gemini-pro) |
| OpenAI Compatible | `PERPLEXITY_API_KEY` | Perplexity (sonar) |

Only providers whose environment variable is set will work. If an API key is missing, the "Test" button will show an error.

### Recommended Provider Configuration

**We recommend configuring at least one of the following providers: Google Gemini or Perplexity (or both).**

**Why?** Tales reports include a "State of the LLMs" section that provides current information about changes and updates to major AI platforms. This section requires **live web search capability** to gather fresh information. Only Gemini (with Google Search grounding) and Perplexity (with built-in web search) support this feature.

| Provider | Web Search | Recommendation |
|----------|------------|----------------|
| Google Gemini | Yes (Google Search grounding) | **Highly recommended** - Excellent for analysis and web search |
| Perplexity | Yes (built-in search via sonar model) | **Recommended** - Good alternative for web search |
| OpenAI (ChatGPT) | No | Good for data collection, not for web search |
| Anthropic (Claude) | No | Good for data collection, not for web search |

If neither Gemini nor Perplexity is configured, the "State of the LLMs" section will be omitted from generated reports. All other report sections will work normally.

---

## Verification

After deployment, verify everything is working:

### 1. Check Container Status

```bash
docker compose ps
```

Both `app` and `db` should show as "Up".

### 2. Check Application Logs

```bash
docker compose logs app
```

Look for: `Uvicorn running on http://0.0.0.0:8000`

### 3. Test the API

```bash
curl http://localhost:8080/
```

Should return a JSON response.

### 4. Test Login

1. Open `http://localhost:8080` in a browser
2. Verify the login page shows the expected authentication methods (email/password form, OAuth buttons, or both, depending on your configuration)
3. Log in with the admin credentials created in the setup step
4. Verify you can access the dashboard

### 5. Test Data Collection

1. Create a brand in the dashboard
2. Add a test query
3. Run collection for one platform
4. Verify responses are recorded

---

## Optional: OAuth Configuration

Tales supports Google and Microsoft OAuth for user authentication. This is optional; email/password login is always available when `ENABLE_LOCAL_AUTH=true` (the default).

For each OAuth provider, you need to: (1) set the enable flag, (2) add the credentials, and (3) rebuild the container so the frontend picks up the client IDs.

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new OAuth 2.0 Client ID (Application type: Web application)
3. Set authorized JavaScript origins: `http://your-tales-url` (e.g., `http://localhost:8080`)
4. Set authorized redirect URIs: `http://your-tales-url` (same as origins)
5. Add to your `.env`:

```bash
# Enable Google login
ENABLE_GOOGLE_AUTH=true

# Google OAuth credentials
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-secret
```

### Microsoft OAuth Setup

1. Go to [Azure Portal App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Create a new App Registration
3. Under "Authentication", add a Single-page application redirect URI: `http://your-tales-url` (e.g., `http://localhost:8080`)
4. Create a client secret under Certificates & secrets
5. Add to your `.env`:

```bash
# Enable Microsoft login (enabled by default)
ENABLE_MICROSOFT_AUTH=true

# Microsoft OAuth credentials (OIDC naming)
OIDC_CLIENT_ID=your-app-client-id
OIDC_CLIENT_SECRET=your-secret
```

### After Adding OAuth Credentials

Rebuild the container so the frontend is built with the OAuth client IDs:

```bash
docker compose up -d --build
```

After rebuilding, the login page will automatically show the new OAuth sign-in buttons alongside (or instead of) the email/password form, depending on your enable flags.

---

## Security

Tales includes built-in security hardening that requires no additional configuration.

### Security Headers

All responses include the following security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | Nonce-based policy | Prevents XSS by restricting script and style sources |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Enforces HTTPS connections (HSTS) |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer information |
| `X-XSS-Protection` | `1; mode=block` | XSS protection for older browsers |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Restricts browser feature access |

### Additional Protections

- **Content Security Policy (CSP)**: Nonce-based CSP for style-src, compatible with MUI/Material-UI
- **Path traversal protection**: Frontend file serving validates paths stay within the expected directory
- **Cloud metadata blocking**: Requests to cloud provider metadata endpoints (AWS, GCP, Azure) are blocked
- **Self-hosted fonts**: All fonts are served locally, eliminating external CDN dependencies
- **Rate limiting**: API endpoints are rate-limited to prevent abuse

---

## Maintenance

### Updating Tales

```bash
# Pull latest image
docker compose pull

# Restart with new image
docker compose up -d
```

### Viewing Logs

```bash
# All logs
docker compose logs

# Just application logs
docker compose logs app

# Follow logs in real-time
docker compose logs -f app
```

### Restarting Services

```bash
# Restart everything
docker compose restart

# Restart just the app
docker compose restart app
```

### Stopping Tales

```bash
# Stop but keep data
docker compose down

# Stop and remove data (WARNING: deletes database)
docker compose down -v
```

---

## Troubleshooting

### Container won't start

Check logs for errors:
```bash
docker compose logs app
```

Common issues:
- Missing required environment variables
- Database connection failed
- Port already in use

### Database connection errors

Verify the database is running:
```bash
docker compose ps db
docker compose logs db
```

### "Account is not active" error

The user needs to be activated by an admin. Log in as admin and activate the user in the Admin Panel.

### OAuth buttons not showing on login page

For an OAuth button to appear, both conditions must be met:
1. The enable flag is set (e.g., `ENABLE_GOOGLE_AUTH=true`)
2. The client ID is configured (e.g., `GOOGLE_CLIENT_ID=...`)

After changing OAuth settings in `.env`, you must rebuild the container:
```bash
docker compose up -d --build
```

### Login page shows "No authentication methods configured"

This means no authentication methods are available. Check that at least one of the following is true:
- `ENABLE_LOCAL_AUTH=true` (default)
- `ENABLE_GOOGLE_AUTH=true` with `GOOGLE_CLIENT_ID` set
- `ENABLE_MICROSOFT_AUTH=true` with `OIDC_CLIENT_ID` or `MICROSOFT_CLIENT_ID` set

### Forgot admin password

Create a new admin user:
```bash
docker compose exec app python scripts/admin/setup_initial_admin.py
```

### LLM API errors

1. Check that API keys are correctly set in `.env`
2. Verify environment variables are loaded (restart the container after `.env` changes)
3. Use the "Test" button in Admin > LLM Configuration to verify connections
4. Ensure you have billing/credits set up with each provider

### Performance issues

Consider:
- Increasing Docker memory allocation
- Using an external PostgreSQL database
- Adding Redis for caching (set `REDIS_URL` in `.env`)

---

## Support

For issues or questions:
- Check the [User Guide](USER_GUIDE.md) for usage help
- Review `.env.template` for configuration options
- Contact your Tales administrator
