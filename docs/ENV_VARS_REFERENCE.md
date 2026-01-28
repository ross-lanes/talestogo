# Tales Environment Variables Reference

This document lists all environment variables used by Tales. Variables marked as **Required** must be set for the application to function.

## Quick Start (Minimum Required)

For a basic deployment, you need at minimum:

```bash
JWT_SECRET_KEY=<random-string>
ENCRYPTION_KEY=<random-string>
DATABASE_URL=postgresql://user:pass@host:port/database

# Optional: LLM keys can be configured via Admin UI after deployment
# GEMINI_API_KEY=<your-gemini-key>
```

**Note:** LLM API keys are optional in the .env file. You can configure them through the Admin UI (Admin Menu > LLM Configuration) after deployment instead.

---

## Security Configuration

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `JWT_SECRET_KEY` | **Yes** | Secret key for signing JWT authentication tokens. Must be a secure random string. | `Abc123XyzSecureRandomString` |
| `ENCRYPTION_KEY` | **Yes** | Key for encrypting sensitive data (API keys) at rest. Must be a secure random string. | `DefGhi456AnotherSecureString` |

**Generate secure keys:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Security Notes:**
- Never commit these values to version control
- Use different values for each environment (dev, staging, production)
- Rotate keys periodically for enhanced security

---

## Database Configuration

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | **Yes** | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/tales` |
| `DB_POOL_SIZE` | No | Database connection pool size (default: 5) | `10` |
| `DB_MAX_OVERFLOW` | No | Maximum overflow connections (default: 10) | `20` |

**Connection String Format:**
```
postgresql://username:password@host:port/database_name
```

**Notes:**
- PostgreSQL is recommended for production
- SQLite (`sqlite:///./tales.db`) works for development only
- The application auto-converts `postgres://` URLs to `postgresql://` format

---

## LLM API Keys

**Important:** LLM providers can also be configured through the Admin UI (recommended). Environment variables serve as a fallback when no providers are configured in the database.

| Variable | Required | Description | Get Key From |
|----------|----------|-------------|--------------|
| `GEMINI_API_KEY` | No* | Google Gemini API key (analysis + web search) | https://makersuite.google.com/app/apikey |
| `OPENAI_API_KEY` | No | OpenAI API key (for ChatGPT queries) | https://platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` | No | Anthropic API key (for Claude queries) | https://console.anthropic.com/settings/keys |
| `PERPLEXITY_API_KEY` | No | Perplexity API key (queries + web search) | https://www.perplexity.ai/settings/api |

*At minimum, one LLM with analysis capability (Gemini recommended) should be configured either via environment variables or the Admin UI.

**Admin UI Configuration (Recommended):**
After deployment, configure LLM providers via Admin Menu > LLM Configuration. This allows:
- Adding/removing providers without restarting the application
- Testing API connections before saving
- Customizing chart colors per provider
- Designating which LLM to use for analysis
- Enabling web search capability (for "State of the LLMs" report section)

**Environment Variable Behavior:**
When environment variables are set but no database providers exist, Tales automatically creates providers from these keys on startup. Once providers are configured in the database, environment variables are ignored.

**Key Formats:**
- OpenAI: `sk-proj-...` or `sk-...`
- Anthropic: `sk-ant-api03-...`
- Gemini: Alphanumeric string
- Perplexity: `pplx-...`

---

## OAuth Configuration (Optional)

OAuth is optional. Users can always log in with email/password created by the admin.

### Google OAuth

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CLIENT_ID` | No | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | Google OAuth client secret |
| `VITE_GOOGLE_CLIENT_ID` | No | Same as GOOGLE_CLIENT_ID (for frontend build) |

**Setup:** https://console.cloud.google.com/apis/credentials

### Microsoft OAuth

| Variable | Required | Description |
|----------|----------|-------------|
| `MICROSOFT_CLIENT_ID` | No | Azure AD application client ID |
| `MICROSOFT_CLIENT_SECRET` | No | Azure AD application secret |
| `VITE_MICROSOFT_CLIENT_ID` | No | Same as MICROSOFT_CLIENT_ID (for frontend build) |

**Setup:** https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade

---

## Email Configuration (Optional)

Email is used for sending user invitations. If not configured, admins can share credentials directly.

### Resend (Recommended)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `RESEND_API_KEY` | No | Resend API key | `re_abc123...` |
| `FROM_EMAIL` | No | Sender email address | `admin@yourdomain.com` |

**Setup:** https://resend.com

### SMTP (Alternative)

| Variable | Required | Description |
|----------|----------|-------------|
| `SMTP_HOST` | No | SMTP server hostname |
| `SMTP_PORT` | No | SMTP server port (usually 587) |
| `SMTP_USER` | No | SMTP username |
| `SMTP_PASSWORD` | No | SMTP password |

**Note:** SMTP may not work on some cloud platforms (ports blocked). Resend is recommended.

---

## Application Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ENVIRONMENT` | No | Environment name | `development` |
| `FRONTEND_URL` | No | Frontend URL for CORS | `http://localhost:5173` |
| `ADMIN_EMAIL` | No | Bootstrap admin email (OAuth only) | `robotrachel@gmail.com` |
| `PORT` | No | Application port | `8000` |

---

## Redis Configuration (Optional)

Redis enables caching for improved performance. Not required for basic operation.

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `REDIS_URL` | No | Redis connection URL | `redis://localhost:6379/0` |
| `REDIS_CACHE_TTL_DASHBOARD` | No | Dashboard cache TTL (seconds) | `900` (15 min) |
| `REDIS_CACHE_TTL_TRENDS` | No | Trends cache TTL (seconds) | `3600` (1 hour) |
| `REDIS_CACHE_TTL_BATCH` | No | Batch cache TTL (seconds) | `86400` (24 hours) |

---

## Scheduler Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ENABLE_SCHEDULER` | No | Enable background task scheduler | `false` |

**Note:** Only set to `true` in production. Running multiple instances with scheduler enabled can cause duplicate tasks.

---

## Analytics Configuration

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ANALYTICS_DEFAULT_LOOKBACK_DAYS` | No | Default date range for analytics | `180` |

---

## Frontend Build Variables

These are only needed when building the frontend (during Docker build).

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL for frontend |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `VITE_MICROSOFT_CLIENT_ID` | Microsoft OAuth client ID |

---

## Example .env File

```bash
# Security (REQUIRED - generate unique values)
JWT_SECRET_KEY=your-secure-random-jwt-key-here
ENCRYPTION_KEY=your-secure-random-encryption-key-here

# Database (REQUIRED)
DATABASE_URL=postgresql://tales:password@db:5432/tales

# LLM API Keys (at least Gemini required)
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
PERPLEXITY_API_KEY=your-perplexity-api-key

# Optional: OAuth (for Google/Microsoft login)
# GOOGLE_CLIENT_ID=your-google-client-id
# GOOGLE_CLIENT_SECRET=your-google-secret
# MICROSOFT_CLIENT_ID=your-microsoft-client-id
# MICROSOFT_CLIENT_SECRET=your-microsoft-secret

# Optional: Email (for sending invitations)
# RESEND_API_KEY=re_your-resend-key
# FROM_EMAIL=admin@yourdomain.com

# Optional: Performance
# REDIS_URL=redis://localhost:6379/0

# Environment
ENVIRONMENT=production
FRONTEND_URL=http://localhost:8080
```

---

## Troubleshooting

### "JWT_SECRET_KEY not set"
Generate a secure key: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### "Database connection failed"
- Verify DATABASE_URL format: `postgresql://user:pass@host:port/database`
- Check that the database server is running and accessible
- Verify credentials are correct

### "API key invalid"
- Verify the key is copied correctly (no extra spaces)
- Check that billing/credits are set up with the provider
- Ensure the key has the necessary permissions

### "CORS error"
- Add your frontend URL to FRONTEND_URL
- Restart the application after changing the value
