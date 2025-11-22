# AWS App Runner Migration Guide

## Overview
AWS App Runner is a fully managed service that automatically builds and deploys web applications from source code. It's like Render, but actually works reliably.

**Benefits:**
- ✅ Auto-deploy from GitHub (push to deploy)
- ✅ AWS infrastructure reliability
- ✅ No server management needed
- ✅ Pay only for usage (~$10-20/month)
- ✅ Automatic scaling
- ✅ Built-in SSL certificates
- ✅ Environment variables in console

**Cost Estimate:**
- Backend (FastAPI): ~$10-15/month
- Frontend (Static): ~$1-2/month (via S3 + CloudFront)
- Database: Keep existing Render PostgreSQL OR migrate to AWS RDS
- **Total: ~$11-17/month** (vs current Render costs)

---

## Architecture

```
tales.robotrachel.com (CloudFront + S3)
    ↓
    Frontend (React/Vite static files)

api.tales.robotrachel.com (App Runner)
    ↓
    Backend (FastAPI + Python)
    ↓
    PostgreSQL (Render DB or AWS RDS)
```

---

## Prerequisites

1. **AWS Account** - Create at https://aws.amazon.com
2. **GitHub Personal Access Token** - App Runner needs this to access your repo
3. **Domain DNS Access** - To point tales.robotrachel.com to AWS

---

## Part 1: Backend Deployment (AWS App Runner)

### Step 1: Create App Runner Configuration File

Create `apprunner.yaml` in your project root:

```yaml
version: 1.0
runtime: python3
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  runtime-version: 3.11
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  network:
    port: 8000
  env:
    - name: PYTHONPATH
      value: /app
```

### Step 2: Deploy Backend to App Runner

1. **Go to AWS Console** → Search "App Runner"
2. **Click "Create service"**
3. **Source:**
   - Repository type: Source code repository
   - Connect to GitHub (authorize AWS to access your repo)
   - Select: `rtwodeetwo/tales_project`
   - Branch: `main`
   - Configuration: Use configuration file → `apprunner.yaml`

4. **Service settings:**
   - Service name: `tales-backend`
   - Virtual CPU: 1 vCPU
   - Memory: 2 GB
   - Port: 8000

5. **Environment variables** (click "Add environment variable"):
   ```
   SECRET_KEY=<generate-new-key>
   ENCRYPTION_KEY=<generate-new-key>
   GOOGLE_CLIENT_ID=<your-value>
   GOOGLE_CLIENT_SECRET=<your-value>
   MICROSOFT_CLIENT_ID=<your-value>
   MICROSOFT_CLIENT_SECRET=<your-value>
   GEMINI_API_KEY=<your-value>
   PERPLEXITY_API_KEY=<your-value>
   DATABASE_URL=postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3
   FRONTEND_URL=https://tales.robotrachel.com
   ```

6. **Click "Create & Deploy"**
7. **Wait 5-10 minutes** for initial deployment
8. **Copy the App Runner URL** (looks like: `https://abc123.us-east-1.awsapprunner.com`)

### Step 3: Test Backend

Visit `https://abc123.us-east-1.awsapprunner.com/docs` to see the API documentation.

---

## Part 2: Frontend Deployment (S3 + CloudFront)

### Step 1: Build Frontend Locally

```bash
cd frontend
npm install
npm run build
# Creates frontend/dist/ folder
```

### Step 2: Create S3 Bucket

1. **Go to AWS Console** → Search "S3"
2. **Click "Create bucket"**
3. **Settings:**
   - Bucket name: `tales-frontend-<random>` (must be globally unique)
   - Region: US East (N. Virginia) - us-east-1
   - Block all public access: **UNCHECK** (we need public read)
   - Acknowledge the warning
4. **Click "Create bucket"**

### Step 3: Enable Static Website Hosting

1. Click on your bucket
2. Go to **Properties** tab
3. Scroll to **Static website hosting** → Click Edit
4. Enable: **Enable**
5. Index document: `index.html`
6. Error document: `index.html` (for React Router)
7. Save changes
8. **Copy the endpoint URL** (e.g., `http://tales-frontend-xyz.s3-website-us-east-1.amazonaws.com`)

### Step 4: Upload Frontend Files

```bash
# Install AWS CLI if not already installed
# brew install awscli  (Mac)
# or download from https://aws.amazon.com/cli/

# Configure AWS CLI (one-time setup)
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json

# Upload frontend files
cd frontend
aws s3 sync dist/ s3://tales-frontend-<your-bucket-name>/ --delete

# Make files publicly readable
aws s3 website s3://tales-frontend-<your-bucket-name>/ --index-document index.html --error-document index.html
```

### Step 5: Create CloudFront Distribution (CDN + SSL)

1. **Go to AWS Console** → Search "CloudFront"
2. **Click "Create distribution"**
3. **Origin settings:**
   - Origin domain: Paste your S3 website endpoint (from Step 3)
   - Protocol: HTTP only
   - Name: tales-frontend

4. **Default cache behavior:**
   - Viewer protocol policy: Redirect HTTP to HTTPS
   - Allowed HTTP methods: GET, HEAD, OPTIONS
   - Cache policy: CachingOptimized

5. **Settings:**
   - Alternate domain names (CNAMEs): `tales.robotrachel.com`
   - Custom SSL certificate: **Request certificate** (opens new tab)
     - In new tab: Request public certificate
     - Domain: `tales.robotrachel.com`
     - Validation: DNS validation
     - **Follow AWS instructions to add CNAME to your DNS**
     - Wait for validation (~5 minutes)
   - Back to CloudFront: Select your new certificate

6. **Click "Create distribution"**
7. **Wait 15-20 minutes** for CloudFront to deploy globally
8. **Copy the CloudFront domain** (e.g., `d1234abcd.cloudfront.net`)

---

## Part 3: DNS Configuration

### Update DNS Records (at your domain registrar):

1. **tales.robotrachel.com** (Frontend)
   - Type: CNAME
   - Name: tales
   - Value: `d1234abcd.cloudfront.net` (your CloudFront domain)

2. **api.tales.robotrachel.com** (Backend)
   - Type: CNAME
   - Name: api.tales
   - Value: `abc123.us-east-1.awsapprunner.com` (your App Runner domain)

**Wait 5-60 minutes for DNS propagation.**

---

## Part 4: Update Frontend Environment Variables

Update `frontend/.env.production`:

```env
VITE_API_URL=https://api.tales.robotrachel.com
VITE_GOOGLE_CLIENT_ID=<your-value>
VITE_MICROSOFT_CLIENT_ID=<your-value>
```

Rebuild and redeploy frontend:

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://tales-frontend-<your-bucket-name>/ --delete

# Invalidate CloudFront cache to see changes immediately
aws cloudfront create-invalidation --distribution-id <your-cloudfront-id> --paths "/*"
```

---

## Part 5: Set Up Automated Deployments

### Backend (Automatic via App Runner)
✅ Already done! App Runner auto-deploys when you push to GitHub.

### Frontend (GitHub Actions)

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend to S3

on:
  push:
    branches: [main]
    paths:
      - 'frontend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: cd frontend && npm install

      - name: Build
        run: cd frontend && npm run build

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Deploy to S3
        run: |
          aws s3 sync frontend/dist/ s3://tales-frontend-<your-bucket-name>/ --delete
          aws cloudfront create-invalidation --distribution-id <your-cloudfront-id> --paths "/*"
```

**Add GitHub Secrets:**
1. Go to GitHub → Settings → Secrets and variables → Actions
2. Add:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_S3_BUCKET`: tales-frontend-xyz
   - `AWS_CLOUDFRONT_DISTRIBUTION_ID`: E1234ABCD

---

## Cost Breakdown

**Monthly Costs:**
- App Runner (Backend): ~$10-15
  - 1 vCPU, 2GB RAM, always running
  - Auto-scales with traffic
- S3 (Frontend Storage): ~$0.10
  - Minimal storage for static files
- CloudFront (CDN): ~$1-2
  - First 1TB free tier, then $0.085/GB
- Data Transfer: ~$1-3
- **Total: $12-20/month**

**Compare to Render:**
- Render: ~$21/month (backend + frontend)
- AWS App Runner: ~$12-20/month
- **Savings: ~$1-9/month** + better reliability

---

## Migration Checklist

- [ ] Create AWS account
- [ ] Create `apprunner.yaml` config file
- [ ] Deploy backend to App Runner
- [ ] Test backend API
- [ ] Create S3 bucket
- [ ] Build and upload frontend
- [ ] Create CloudFront distribution
- [ ] Request SSL certificate
- [ ] Update DNS records
- [ ] Wait for DNS propagation
- [ ] Update frontend API URL
- [ ] Test full application
- [ ] Set up GitHub Actions for frontend auto-deploy
- [ ] Add AWS credentials to GitHub Secrets
- [ ] Delete Render services
- [ ] Cancel Render subscription

---

## Rollback Plan

If something goes wrong:
1. Update DNS back to Render domains
2. Wait for propagation
3. Debug AWS issues without downtime

---

## Support

**AWS Documentation:**
- App Runner: https://docs.aws.amazon.com/apprunner/
- S3: https://docs.aws.amazon.com/s3/
- CloudFront: https://docs.aws.amazon.com/cloudfront/

**AWS Support:**
- Free tier: Community forums
- Developer: $29/month (optional, for support tickets)
