# Tales IT Deployment Guide

This guide is for IT teams deploying Tales at their organization. Tales is an AI reputation monitoring platform that tracks how your organization is represented across major AI platforms (ChatGPT, Claude, Gemini, Perplexity).

## Table of Contents

1. [PPPL National Lab Deployment](#pppl-national-lab-deployment)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Initial Admin Setup](#initial-admin-setup)
6. [Verification](#verification)
7. [Optional: OAuth Configuration](#optional-oauth-configuration)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)

---

## PPPL National Lab Deployment

This section covers deployment specifics for national labs following the PPPL Internal Developer Guide standards.

### PPPL Compliance Features

Tales includes the following PPPL-compliant features:

- **Multi-stage Dockerfile**: Uses `node:20-alpine` and `python:3.11-slim` base images with build tools removed from final image
- **GitLab CI/CD**: Automatic container builds with proper tagging (`:latest` for main, version tags, branch names)
- **OIDC Authentication**: Supports Entra ID via standard OIDC variable naming
- **Environment Variables**: All secrets managed via environment variables (never hardcoded)
- **Docker Compose**: Defines app and database services with proper networking

### PPPL Environment Variables

Tales supports both PPPL standard naming and legacy variable names for backwards compatibility:

| PPPL Standard | Legacy Name | Description |
|---------------|-------------|-------------|
| `APP_SECRET` | `JWT_SECRET_KEY` | JWT signing secret |
| `OIDC_CLIENT_ID` | `MICROSOFT_CLIENT_ID` | Azure AD client ID |
| `OIDC_CLIENT_SECRET` | `MICROSOFT_CLIENT_SECRET` | Azure AD client secret |
| `OIDC_DISCOVERY_URL` | (new) | OIDC discovery endpoint |

### Authentication Enable/Disable Flags

Labs can control which authentication methods are available:

```bash
# Enable/disable authentication methods
ENABLE_LOCAL_AUTH=true      # Email/password login
ENABLE_MICROSOFT_AUTH=true  # Microsoft/Entra ID login
ENABLE_GOOGLE_AUTH=false    # Google login (disabled by default)
```

### Lab-Specific Branding

Customize the appearance for your organization:

```bash
SITE_NAME=PPPL Tales              # Your lab's name
SITE_LOGO_URL=https://...         # URL to your logo
SITE_PRIMARY_COLOR=#003e60        # Primary theme color
SITE_SECONDARY_COLOR=#75c9c8      # Secondary theme color
```

### OIDC Configuration for Entra ID

IT will provide OIDC credentials during app registration:

```bash
# Standard PPPL OIDC variables
OIDC_CLIENT_ID=<from-IT>
OIDC_CLIENT_SECRET=<from-IT>

# Optional: For tenant-specific authentication
OIDC_DISCOVERY_URL=https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration
```

### GitLab CI/CD Setup

1. Push your code to PPPL's GitLab server
2. The included `.gitlab-ci.yml` will automatically:
   - Build the Docker image on push
   - Tag as `:latest` for main branch
   - Tag with version for git tags (e.g., `v1.0.0`)
   - Push to GitLab Container Registry

### Deployment Checklist

1. Repository created on PPPL GitLab Server
2. Code pushed to repository
3. `.env` file created with PPPL variables
4. Container builds successfully in GitLab Pipeline
5. IT has provided OIDC credentials
6. OIDC_CLIENT_ID and OIDC_CLIENT_SECRET configured
7. Admin user created via setup script

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

### 1. Clone the Repository

```bash
git clone <repository-url> tales
cd tales
```

### 2. Create Environment File

Copy the template and edit with your values:

```bash
cp .env.template .env
nano .env  # or use your preferred editor
```

**Minimum required variables:**

```bash
# Security (generate unique values for your deployment)
JWT_SECRET_KEY=<generate-random-string>
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
# Run this twice to generate JWT_SECRET_KEY and ENCRYPTION_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Start the Application

```bash
docker compose up -d
```

This will:
- Build the Tales application container
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

See [ENV_VARS_REFERENCE.md](ENV_VARS_REFERENCE.md) for a complete list of environment variables.

### Changing the Port

To run on a different port, edit `docker-compose.yml`:

```yaml
services:
  app:
    ports:
      - "YOUR_PORT:8000"  # Change YOUR_PORT to desired port
```

Or set it via environment variable:

```bash
PORT=3000 docker compose up -d
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

### Testing Your Configuration

After saving settings:
1. Invite a test user (or yourself at a different email)
2. Check the invitation email for:
   - Correct URL in the login link
   - Correct admin contact email
   - Your organization's site name in the subject/header

### Notes

- If settings are left empty, the system uses environment variables as fallbacks
- Changes take effect immediately for new emails
- Existing emails (already sent) are not affected

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

### Optional: OAuth (Google/Microsoft)

If your organization prefers single sign-on, you can optionally configure OAuth. See [Optional: OAuth Configuration](#optional-oauth-configuration) below.

| Auth Method | Setup Required | Best For |
|-------------|----------------|----------|
| Email/Password | None (works immediately) | Quick deployments, small teams |
| Google OAuth | Google Cloud Console setup | Organizations using Google Workspace |
| Microsoft OAuth | Azure Portal setup | Organizations using Microsoft 365 |
| Multiple methods | Configure each individually | Maximum flexibility for users |

### How Login Methods Are Controlled

Each authentication method requires two things to appear on the login page:

1. **Enable flag** set to `true` in your `.env` file
2. **Credentials configured** (client ID for OAuth methods)

| Method | Enable Flag | Also Requires |
|--------|------------|---------------|
| Email/Password | `ENABLE_LOCAL_AUTH=true` | Nothing else (works immediately) |
| Google | `ENABLE_GOOGLE_AUTH=true` | `GOOGLE_CLIENT_ID` set |
| Microsoft | `ENABLE_MICROSOFT_AUTH=true` | `MICROSOFT_CLIENT_ID` or `OIDC_CLIENT_ID` set |

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
# or for local development:
# restart the uvicorn server
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

### Editing Provider Settings

Click on an existing provider card to modify its settings. You can change the display name, model name, color, and enable/disable options.

### Adding Custom Providers

For providers beyond the 4 defaults (e.g., Mistral, DeepSeek), you can add up to 2 custom providers:

1. Add the API key to `.env` with a custom variable name:
   ```bash
   MISTRAL_API_KEY=your-mistral-key
   ```

2. Restart the application

3. In Admin UI, click "Add LLM" and fill in:
   - **Display Name** - "Mistral"
   - **API Type** - "OpenAI Compatible" (most custom providers use this)
   - **Model Name** - The model ID (e.g., "mistral-large-latest")
   - **Environment Variable Name** - "MISTRAL_API_KEY" (must match your `.env`)
   - **API Endpoint** - The provider's API URL (e.g., "https://api.mistral.ai")

4. Click "Add LLM" and test the connection

### Supported API Types

| API Type | Description | Example Providers |
|----------|-------------|-------------------|
| OpenAI | OpenAI API | ChatGPT (GPT-4, GPT-3.5) |
| Anthropic | Anthropic API | Claude models |
| Google | Google GenAI API | Gemini models |
| OpenAI Compatible | Any OpenAI-compatible API | Perplexity, Mistral, Azure OpenAI, local LLMs |

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

# Microsoft OAuth credentials
MICROSOFT_CLIENT_ID=your-app-client-id
MICROSOFT_CLIENT_SECRET=your-secret
```

For PPPL/national lab deployments using OIDC naming:
```bash
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
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer information |
| `X-XSS-Protection` | `1; mode=block` | XSS protection for older browsers |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Restricts browser feature access |

### Content Security Policy (CSP)

Tales uses a nonce-based CSP for style-src, which allows MUI/Material-UI styles while blocking unauthorized inline styles. A unique nonce is generated per request and injected into the HTML response. No configuration is needed; this works automatically.

### Additional Protections

- **Path traversal protection**: The frontend catch-all route validates file paths stay within the expected directory
- **Cloud metadata blocking**: Requests to cloud provider metadata endpoints (AWS, GCP, Azure) are blocked to prevent SSRF attacks
- **Self-hosted fonts**: All fonts are served from the application itself, eliminating external CDN dependencies
- **Password validation**: Login password fields enforce a maximum length of 128 characters

---

## Maintenance

### Updating Tales

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build
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

A simple `docker compose restart` is not enough because OAuth client IDs are embedded in the frontend during the build step.

### Login page shows "No authentication methods configured"

This means no authentication methods are available. Check that at least one of the following is true:
- `ENABLE_LOCAL_AUTH=true` (default)
- `ENABLE_GOOGLE_AUTH=true` with `GOOGLE_CLIENT_ID` set
- `ENABLE_MICROSOFT_AUTH=true` with `MICROSOFT_CLIENT_ID` or `OIDC_CLIENT_ID` set

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
- Review [ENV_VARS_REFERENCE.md](ENV_VARS_REFERENCE.md) for configuration options
- Contact your Tales administrator
