# Tales Deployment Guide for PPPL (tales.pppl.gov)

## Current Issue
The login page shows "No authentication methods configured" because the frontend is trying to reach `http://localhost:8080` instead of `https://tales.pppl.gov`. This is because the Docker image was built without the correct `VITE_API_URL`.

---

## Complete Deployment Setup

### Step 1: Configure GitLab CI/CD Variables

In your GitLab repository (https://git.pppl.gov/rkremen/talestogo), go to:
**Settings > CI/CD > Variables**

Add these variables:

| Variable | Value | Protected | Masked |
|----------|-------|-----------|---------|
| `VITE_API_URL` | `https://tales.pppl.gov` | ✓ | ✗ |
| `VITE_MICROSOFT_CLIENT_ID` | `<your-entra-client-id>` | ✓ | ✗ |

These are used at **build time** to bake the correct URLs into the frontend code.

---

### Step 2: Configure Portainer Environment Variables

In Portainer (https://portainer.pppl.gov/#!/7/docker/stacks/tales), add/update these environment variables:

#### Required for Entra ID

```bash
# Entra ID Authentication (PPPL Standard Naming)
OIDC_CLIENT_ID=<your-azure-app-client-id>
OIDC_CLIENT_SECRET=<your-azure-app-client-secret>
OIDC_DISCOVERY_URL=https://login.microsoftonline.com/<pppl-tenant-id>/v2.0/.well-known/openid-configuration

# Enable Microsoft Auth (already default to true)
ENABLE_MICROSOFT_AUTH=true

# Disable local password auth if SSO-only (optional)
ENABLE_LOCAL_AUTH=false
```

#### Security Keys (Already Required)

```bash
# JWT signing secret (PPPL standard name)
APP_SECRET=<generate-random-string>

# Encryption key for storing API keys
ENCRYPTION_KEY=<generate-random-string>
```

Generate secure keys:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Database (Already Configured)

```bash
DB_PASSWORD=<your-db-password>
```

#### LLM API Keys (Already Configured via Admin UI)

These are optional in `.env` since you can configure them via Admin UI:
```bash
GEMINI_API_KEY=<optional>
OPENAI_API_KEY=<optional>
ANTHROPIC_API_KEY=<optional>
PERPLEXITY_API_KEY=<optional>
```

---

### Step 3: Azure/Entra ID App Registration

In the Azure/Entra portal for PPPL:

#### 3.1 Create App Registration

1. Go to **Azure Active Directory > App registrations > New registration**
2. Name: `Tales PPPL`
3. Supported account types: **Accounts in this organizational directory only (PPPL)**
4. Redirect URI:
   - Type: **Single-page application (SPA)**
   - URL: `https://tales.pppl.gov`

#### 3.2 Configure Authentication

1. Go to **Authentication** in your app registration
2. Under **Implicit grant and hybrid flows**, enable:
   - ✓ **ID tokens** (used for hybrid flows and implicit flows)
3. Under **Advanced settings**:
   - Allow public client flows: **No**

#### 3.3 API Permissions

1. Go to **API permissions**
2. Ensure these Microsoft Graph permissions are granted:
   - `openid` (Sign users in)
   - `profile` (View users' basic profile)
   - `email` (View users' email address)
3. Click **Grant admin consent for PPPL**

#### 3.4 Get Client Credentials

1. **Client ID**: Copy from the Overview page (use for `OIDC_CLIENT_ID`)
2. **Client Secret**:
   - Go to **Certificates & secrets**
   - Click **New client secret**
   - Description: `Tales Production`
   - Expires: Choose duration (e.g., 24 months)
   - Copy the **Value** (use for `OIDC_CLIENT_SECRET`)
   - ⚠️ **Important**: Copy immediately - you won't be able to see it again!
3. **Tenant ID**: Copy from the Overview page (use in `OIDC_DISCOVERY_URL`)

---

### Step 4: Deploy the Updated Image

#### Option A: Push to GitLab (Automatic Build)

1. Commit the Dockerfile and GitLab CI changes:
   ```bash
   git add Dockerfile .gitlab-ci.yml
   git commit -m "Add VITE_MICROSOFT_CLIENT_ID build arg for Entra ID"
   git push origin main
   ```

2. GitLab CI will automatically:
   - Build with `VITE_API_URL=https://tales.pppl.gov`
   - Build with `VITE_MICROSOFT_CLIENT_ID=<from-gitlab-vars>`
   - Push to `git.pppl.gov:5050/rkremen/talestogo:latest`

3. In Portainer:
   - Click **Update the stack**
   - Check **Re-pull image**
   - Click **Update**

#### Option B: Manual Build (If Needed)

If you need to build locally:

```bash
# Get the Entra client ID from Azure portal
ENTRA_CLIENT_ID="<your-client-id>"

# Build the image
docker build \
  --build-arg VITE_API_URL=https://tales.pppl.gov \
  --build-arg VITE_MICROSOFT_CLIENT_ID=$ENTRA_CLIENT_ID \
  -t git.pppl.gov:5050/rkremen/talestogo:latest .

# Login to GitLab registry
docker login git.pppl.gov:5050

# Push
docker push git.pppl.gov:5050/rkremen/talestogo:latest
```

Then update in Portainer as above.

---

### Step 5: Verify Deployment

1. **Check the login page**: https://tales.pppl.gov/login
   - Should show "Sign in with Microsoft" button
   - Should NOT show CORS errors in console

2. **Test Microsoft login**:
   - Click "Sign in with Microsoft"
   - Should redirect to PPPL Entra login
   - After login, should create user account in Tales

3. **Create initial admin** (if needed):
   ```bash
   docker compose exec app python scripts/admin/setup_initial_admin.py
   ```

4. **Check backend health**:
   ```bash
   curl https://tales.pppl.gov/health
   # Should return: {"status":"healthy"}
   ```

---

## Troubleshooting

### CORS Errors

**Symptom**: Console shows `Access to XMLHttpRequest at 'http://localhost:8080/...' has been blocked by CORS`

**Cause**: Frontend was built with wrong `VITE_API_URL`

**Fix**: Rebuild Docker image with correct `VITE_API_URL` (see Step 4)

---

### "No authentication methods configured"

**Symptom**: Login page shows this message

**Causes**:
1. Frontend can't reach backend (CORS issue - see above)
2. `OIDC_CLIENT_ID` not set in Portainer environment variables

**Fix**:
1. Rebuild with correct `VITE_API_URL`
2. Add `OIDC_CLIENT_ID` and `OIDC_CLIENT_SECRET` to Portainer

---

### Microsoft login button missing

**Symptom**: Only "Email/Password" fields shown, no Microsoft button

**Causes**:
1. `VITE_MICROSOFT_CLIENT_ID` not set at build time
2. `OIDC_CLIENT_ID` not set at runtime

**Fix**:
1. Set `VITE_MICROSOFT_CLIENT_ID` in GitLab CI variables
2. Set `OIDC_CLIENT_ID` in Portainer environment
3. Rebuild and redeploy

---

### "Invalid token" after Microsoft login

**Symptom**: Login redirects back but shows error

**Causes**:
1. `OIDC_DISCOVERY_URL` incorrect or missing tenant ID
2. Client secret expired
3. Redirect URI mismatch in Azure

**Fix**:
1. Verify `OIDC_DISCOVERY_URL` has correct PPPL tenant ID
2. Generate new client secret in Azure
3. Verify redirect URI is exactly `https://tales.pppl.gov` (no trailing slash)

---

## Summary: What Changed

1. **Dockerfile**: Added `VITE_MICROSOFT_CLIENT_ID` build arg
2. **.gitlab-ci.yml**: Passes `VITE_MICROSOFT_CLIENT_ID` during build
3. **Environment Variables**: Need to set in both GitLab CI (build time) and Portainer (runtime)

The key issue was that the frontend code needs the backend URL and OAuth client ID baked in at build time, not runtime.

---

## Quick Reference: All Environment Variables

### GitLab CI/CD Variables (Build Time)
```
VITE_API_URL=https://tales.pppl.gov
VITE_MICROSOFT_CLIENT_ID=<azure-client-id>
```

### Portainer Environment Variables (Runtime)
```
# Security
APP_SECRET=<random-string>
ENCRYPTION_KEY=<random-string>
DB_PASSWORD=<db-password>

# Entra ID
OIDC_CLIENT_ID=<azure-client-id>
OIDC_CLIENT_SECRET=<azure-client-secret>
OIDC_DISCOVERY_URL=https://login.microsoftonline.com/<pppl-tenant-id>/v2.0/.well-known/openid-configuration

# Auth Flags
ENABLE_MICROSOFT_AUTH=true
ENABLE_LOCAL_AUTH=false  # Set to false for SSO-only

# Application
ENVIRONMENT=production
FRONTEND_URL=https://tales.pppl.gov
ENABLE_SCHEDULER=true

# Optional: LLM Keys (can configure via Admin UI instead)
GEMINI_API_KEY=<optional>
```
