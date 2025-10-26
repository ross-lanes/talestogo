# .env Files Setup Guide

I've created comprehensive `.env` files for you! Here's how to fill them out.

## 📁 Files Created

1. **`.env`** (Backend) - Located in project root
2. **`frontend/.env`** (Frontend) - Located in frontend folder

Both files have detailed comments and checklists to help you configure them.

---

## 🔑 What You Need to Get

### 1. Google OAuth Credentials (REQUIRED for login)

**Get from:** [Google Cloud Console](https://console.cloud.google.com/apis/credentials)

**What you need:**
- ✅ **Client ID** (looks like: `123456789012-abc.apps.googleusercontent.com`)
- ✅ **Client Secret** (looks like: `GOCSPX-ABCDEFGHijklmnop`)

**Where to put them:**
- **Backend `.env`**:
  - `GOOGLE_CLIENT_ID=` (paste Client ID)
  - `GOOGLE_CLIENT_SECRET=` (paste Client Secret)
- **Frontend `frontend/.env`**:
  - `VITE_GOOGLE_CLIENT_ID=` (paste Client ID - same as backend)

**How to get:** See [CREATE_OAUTH_CREDENTIALS.md](CREATE_OAUTH_CREDENTIALS.md)

---

### 2. LLM API Keys (At least ONE required for AIRO features)

AIRO uses LLM APIs to analyze responses. You need at least one of these:

#### Option A: Google Gemini (RECOMMENDED - Cheapest!)

**Get from:** https://makersuite.google.com/app/apikey

**Cost:** ~$0.001-0.01 per query (10x cheaper than others)

**Where to put it:**
```env
GEMINI_API_KEY=AIzaSy-your-key-here
```

#### Option B: OpenAI (ChatGPT)

**Get from:** https://platform.openai.com/api-keys

**Cost:** ~$0.03-0.06 per query

**Where to put it:**
```env
OPENAI_API_KEY=sk-proj-your-key-here
```

#### Option C: Anthropic (Claude)

**Get from:** https://console.anthropic.com/settings/keys

**Cost:** ~$0.01-0.03 per query

**Where to put it:**
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

#### Option D: Perplexity (Optional)

**Get from:** https://www.perplexity.ai/settings/api

**Where to put it:**
```env
PERPLEXITY_API_KEY=pplx-your-key-here
```

**💡 Recommendation:** Start with **Gemini** - it's the cheapest and works great!

---

## 📋 Quick Setup Steps

### Step 1: Open Backend `.env`

Location: `/Users/rachelkremen/Documents/Code/airo_project/.env`

**Find these lines and update:**

```env
# Line 24-25: Add your Google OAuth credentials
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

**Replace with your actual values:**
```env
GOOGLE_CLIENT_ID=123456789012-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-ABCDEFGHijklmnop
```

**Then add at least ONE LLM API key:**

```env
# Line 50: Add Gemini key (recommended)
GEMINI_API_KEY=AIzaSy-your-actual-key-here

# OR Line 42: Add OpenAI key
OPENAI_API_KEY=sk-proj-your-actual-key-here

# OR Line 46: Add Anthropic key
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

### Step 2: Open Frontend `.env`

Location: `/Users/rachelkremen/Documents/Code/airo_project/frontend/.env`

**Find this line and update:**

```env
# Line 22: Add your Google OAuth Client ID
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

**Replace with the SAME Client ID from backend:**
```env
VITE_GOOGLE_CLIENT_ID=123456789012-abc.apps.googleusercontent.com
```

**⚠️ Important:** Use the **SAME** Client ID in both files!

---

## ✅ Verification Checklist

After filling out your `.env` files:

### Backend `.env`
- [ ] `JWT_SECRET_KEY` has a value (already set ✓)
- [ ] `ENCRYPTION_KEY` has a value (already set ✓)
- [ ] `GOOGLE_CLIENT_ID` updated with your Client ID
- [ ] `GOOGLE_CLIENT_SECRET` updated with your Client Secret
- [ ] At least ONE of these has a real API key:
  - [ ] `GEMINI_API_KEY` (recommended)
  - [ ] `OPENAI_API_KEY`
  - [ ] `ANTHROPIC_API_KEY`

### Frontend `.env`
- [ ] `VITE_API_URL` is set to `http://localhost:8000` ✓
- [ ] `VITE_GOOGLE_CLIENT_ID` updated with your Client ID
- [ ] `VITE_GOOGLE_CLIENT_ID` matches backend `GOOGLE_CLIENT_ID`

---

## 🧪 Test Your Configuration

### 1. Test Backend Starts

```bash
cd /Users/rachelkremen/Documents/Code/airo_project
python3 -m uvicorn app.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**If you see errors about missing credentials:**
- Check that your Google credentials are set correctly
- Verify there are no extra spaces or quotes

### 2. Test Frontend Starts

```bash
cd /Users/rachelkremen/Documents/Code/airo_project/frontend
npm run dev
```

**Expected output:**
```
  VITE v... ready in ...ms
  ➜  Local:   http://localhost:5173/
```

### 3. Test Google Login Button

1. Open: http://localhost:5173/login
2. You should see: "Sign in with Google" button
3. Click it - Google OAuth popup should appear

**If the button doesn't appear:**
- Check that `VITE_GOOGLE_CLIENT_ID` is set in `frontend/.env`
- Restart the frontend server after updating `.env`

---

## 🔍 What Each Variable Does

### Backend `.env`

| Variable | Purpose | Required? |
|----------|---------|-----------|
| `JWT_SECRET_KEY` | Secures user sessions | ✅ Yes (already set) |
| `ENCRYPTION_KEY` | Encrypts stored API keys | ✅ Yes (already set) |
| `GOOGLE_CLIENT_ID` | Google OAuth authentication | ✅ Yes (you need to add) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth authentication | ✅ Yes (you need to add) |
| `GEMINI_API_KEY` | For Gemini AI analysis | ⚠️ One LLM key required |
| `OPENAI_API_KEY` | For ChatGPT analysis | ⚠️ One LLM key required |
| `ANTHROPIC_API_KEY` | For Claude analysis | ⚠️ One LLM key required |
| `PERPLEXITY_API_KEY` | For Perplexity analysis | ❌ Optional |
| `DATABASE_URL` | PostgreSQL connection | ❌ Optional (SQLite used by default) |
| `REDIS_URL` | Redis for background tasks | ❌ Optional |

### Frontend `.env`

| Variable | Purpose | Required? |
|----------|---------|-----------|
| `VITE_API_URL` | Backend API endpoint | ✅ Yes (already set) |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth in browser | ✅ Yes (you need to add) |

---

## 🆘 Common Issues

### Error: "Invalid Google token"

**Cause:** Google credentials not set or incorrect

**Solution:**
1. Check `GOOGLE_CLIENT_ID` in backend `.env`
2. Check `VITE_GOOGLE_CLIENT_ID` in frontend `.env`
3. Make sure they match
4. Verify no extra spaces or quotes

### Error: "Could not validate credentials"

**Cause:** JWT secret key issue

**Solution:**
- This shouldn't happen - `JWT_SECRET_KEY` is already set correctly
- Don't change this value unless necessary

### Google Login Button Not Showing

**Cause:** Frontend environment variable not set

**Solution:**
1. Open `frontend/.env`
2. Verify `VITE_GOOGLE_CLIENT_ID` is set
3. Restart frontend: `npm run dev`
4. Clear browser cache and reload

### LLM Features Not Working

**Cause:** No LLM API keys configured

**Solution:**
1. Get at least one LLM API key (recommend Gemini)
2. Add it to backend `.env`
3. Restart backend server

---

## 🔒 Security Reminders

✅ **DO:**
- Keep both `.env` files secure and private
- Add `.env` to `.gitignore` (already done)
- Use different credentials for development vs production
- Rotate secrets if compromised

❌ **DON'T:**
- Commit `.env` files to GitHub
- Share your `.env` files
- Put secrets in the frontend `.env` (except Client ID which is safe)
- Hard-code credentials in source files

---

## 📊 Configuration Summary

### ✅ Already Configured (No Action Needed)
- JWT secret keys (secure, auto-generated)
- Encryption keys (secure, auto-generated)
- API URLs (correctly configured for localhost)
- Database (SQLite, works automatically)

### ⚠️ You Need to Add
1. **Google OAuth Credentials** (2 values)
   - Client ID (goes in both `.env` files)
   - Client Secret (goes in backend `.env` only)

2. **At Least One LLM API Key**
   - Gemini (recommended - cheapest)
   - OR OpenAI
   - OR Anthropic

**Total time to set up:** ~10-15 minutes

---

## 🎯 Next Steps

After configuring your `.env` files:

1. ✅ Get Google OAuth credentials → [CREATE_OAUTH_CREDENTIALS.md](CREATE_OAUTH_CREDENTIALS.md)
2. ✅ Get at least one LLM API key (Gemini recommended)
3. ✅ Update both `.env` files
4. ✅ Start backend and frontend servers
5. ✅ Test login at http://localhost:5173/login

**Need help?** See [QUICK_START.md](QUICK_START.md) for complete instructions!

---

## 📝 Quick Reference: Where to Get Keys

| What | Where |
|------|-------|
| **Google OAuth** | https://console.cloud.google.com/apis/credentials |
| **Gemini API** | https://makersuite.google.com/app/apikey |
| **OpenAI API** | https://platform.openai.com/api-keys |
| **Anthropic API** | https://console.anthropic.com/settings/keys |
| **Perplexity API** | https://www.perplexity.ai/settings/api |

---

**Your `.env` files are ready!** Just add your credentials and you're good to go! 🚀
