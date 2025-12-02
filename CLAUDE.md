# Tales Project

Tales is an AI reputation monitoring platform that tracks how brands are represented across major AI platforms (ChatGPT, Claude, Gemini, Perplexity).

## Tech Stack

- **Backend**: Python/FastAPI with SQLAlchemy ORM
- **Frontend**: React/TypeScript with Vite, Material-UI
- **Database**: PostgreSQL (hosted on Render)
- **Hosting**: Railway (separate frontend/backend services)
- **Auth**: Google OAuth + JWT tokens

## Project Structure

```
tales_project/
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
├── Procfile               # Railway start command
└── nixpacks.toml          # Railway build config
```

## LLM Configuration

Current LLM usage (as of Nov 2025):
- **Data Collection**: Queries sent to ChatGPT, Claude, Gemini, Perplexity
- **Response Analysis**: Gemini 2.5 Pro (`analyze_raw_response` in llm_service.py)
- **Report Writing**: Gemini 2.5 Pro (generate_report.py)
## Development Commands

```bash
# Start backend locally
python3 -m uvicorn app.main:app --reload --port 8000

# Start frontend locally
cd frontend && npm run dev

# Run both (from project root)
./start_local.sh
```

## Deployment

### Environments

**Development** (dev branch):
- Frontend: https://tales-frontend-development.up.railway.app
- Backend: https://tales-backend-development.up.railway.app
- Database: `postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway`

**Production** (main branch):
- Frontend: https://apps.robotrachel.com
- Backend: https://apps.robotrachel.com
- Database: `postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway`

### Deploy to Production
```bash
git checkout main
git merge dev
git push
```

### Deploy to Development
```bash
git checkout dev
git push origin dev
```

Railway auto-deploys when changes are pushed to the respective branches.

## Environment Variables

Required on Railway backend:
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - For authentication tokens
- `ENCRYPTION_KEY` - Fernet key for API key storage
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth
- `PERPLEXITY_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`
- `FRONTEND_URL` - For CORS (e.g., https://tales.robotrachel.com)
- `RESEND_API_KEY` - For sending invitation emails (see Email Configuration below)
- `FROM_EMAIL` - Email address for sending (e.g., admin@robotrachel.com)

## Email Configuration

Tales uses **Resend** for sending invitation emails. Railway blocks SMTP ports, so Resend's HTTP-based API is the recommended solution.

### Initial Setup (One-time)

1. **Create Resend Account**
   - Go to https://resend.com
   - Sign up with your admin email
   - Verify your email address

2. **Add and Verify Domain**
   - In Resend dashboard, go to "Domains"
   - Click "Add Domain" and enter your domain (e.g., `robotrachel.com`)
   - Resend will provide DNS records to add

3. **Add DNS Records to DreamHost**

   **For DreamHost users:** Navigate to Panel → Domains → Manage Domains → DNS

   Add these 3 custom DNS records:

   **Record 1 - DKIM (TXT):**
   ```
   Name: resend._domainkey.robotrachel.com
   Type: TXT
   Value: [Copy exact value from Resend dashboard]
   ```

   **Record 2 - Send MX:**
   ```
   Name: send.robotrachel.com
   Type: MX
   Priority: 10
   Value: feedback-smtp.us-east-1.amazonses.com
   ```

   **Record 3 - Send SPF (TXT):**
   ```
   Name: send.robotrachel.com
   Type: TXT
   Value: v=spf1 include:amazonses.com ~all
   ```

   ⚠️ **Do NOT add the "Enable Receiving" MX record** if you already receive email at your domain (e.g., via Google Workspace) - it will break existing email!

   ⏱️ **DNS propagation takes 4-6 hours on DreamHost** (sometimes up to 24 hours)

4. **Generate API Keys**
   - In Resend dashboard, go to "API Keys"
   - Create two API keys:
     - `tales-production` (for production Railway)
     - `tales-development` (for development Railway)
   - Copy each key immediately (starts with `re_`) - you can't see it again!

### Railway Configuration

**Production Backend:**
1. Open Railway dashboard → Production backend service
2. Go to Variables tab
3. Add:
   - `RESEND_API_KEY` = `re_xxxxx` (production API key)
   - `FROM_EMAIL` = `admin@robotrachel.com`
4. Save (Railway auto-redeploys)

**Development Backend:**
1. Open Railway dashboard → Development backend service
2. Go to Variables tab
3. Add:
   - `RESEND_API_KEY` = `re_xxxxx` (development API key)
   - `FROM_EMAIL` = `admin@robotrachel.com`
4. Save (Railway auto-redeploys)

### Testing

Once DNS is verified (check in Resend dashboard):
1. In admin panel, invite a test user
2. Click "Send Invitation Email"
3. Check Resend dashboard → "Logs" to confirm send
4. Check recipient inbox to verify delivery
5. Check Railway logs for: `"Email sent via Resend to ..."`

### Troubleshooting

**"Domain not verified" error:**
- Wait longer for DNS propagation (up to 24 hours)
- Verify DNS records are correct in DreamHost
- Click "Verify DNS Records" in Resend dashboard

**Emails not sending:**
- Check Railway logs for errors
- Check Resend dashboard → Logs for failed sends
- Verify `RESEND_API_KEY` is set in Railway
- Verify `FROM_EMAIL=admin@robotrachel.com` matches verified domain

**Emails going to spam:**
- Ensure all DNS records (SPF, DKIM) are properly configured
- Check Resend domain verification shows all green checkmarks

### Code Reference

Email sending is implemented in `app/email.py`:
- Uses Resend API if `RESEND_API_KEY` is set (recommended)
- Falls back to SMTP if configured
- Logs only if no email service configured

## Key Features

- Multi-brand support (users can track up to 20 brands)
- Brand sharing between users
- Automated data collection with scheduling
- Response analysis extracting: mentions, sentiment, positioning, competitors, descriptors
- Report generation with AI-written summaries
- Analytics dashboard with charts
