# Step-by-Step: Configure OAuth Consent Screen

## 📋 Overview

The OAuth consent screen is what users see when they click "Sign in with Google". You need to configure it once before creating OAuth credentials.

**Time needed:** 5 minutes
**Cost:** FREE

---

## 🚀 Step-by-Step Instructions

### Step 1: Access Google Cloud Console

1. Go to: **https://console.cloud.google.com/**
2. Sign in with your Google account
3. If you haven't created a project yet, you'll see a welcome screen

### Step 2: Create a Project (if needed)

1. Click the **project dropdown** at the top left (next to "Google Cloud")
2. Click **"NEW PROJECT"** button (top right)
3. Fill in:
   - **Project name**: `AIRO` (or `AIRO Authentication`)
   - **Organization**: Leave as "No organization" (unless you have a Google Workspace)
   - **Location**: Leave default
4. Click **"CREATE"**
5. Wait 10-20 seconds for project creation
6. Click **"SELECT PROJECT"** when it appears

### Step 3: Navigate to OAuth Consent Screen

1. In the left sidebar, click **"APIs & Services"**
   - If you don't see the sidebar, click the ☰ (hamburger menu) at top left
2. Click **"OAuth consent screen"**
3. You'll see two options: **Internal** or **External**

### Step 4: Choose User Type

**Choose "External"** (unless you have Google Workspace)

| User Type | When to Use | Cost |
|-----------|-------------|------|
| **Internal** | Only if you have Google Workspace and want to restrict to your organization | Free |
| **External** | For everyone else (most common) | Free |

✅ **Select "External"** → Click **"CREATE"**

---

## 📝 Step 5: Fill Out OAuth Consent Screen

You'll see a form with 4 pages. Here's exactly what to enter:

### **Page 1: OAuth consent screen** (Required fields only)

#### App Information

**App name** (Required)
```
AIRO
```

**User support email** (Required - dropdown)
```
[Select your email address from dropdown]
```

**App logo** (Optional - skip for now)
```
[Leave empty]
```

#### App Domain (All Optional - you can skip these)

**Application home page**
```
[Leave empty for now]
```

**Application privacy policy link**
```
[Leave empty for now]
```

**Application terms of service link**
```
[Leave empty for now]
```

#### Authorized domains (Optional - skip for now)
```
[Leave empty - you'll add your production domain here later]
```

#### Developer contact information (Required)

**Email addresses**
```
[Type your email address]
```

✅ Click **"SAVE AND CONTINUE"** at the bottom

---

### **Page 2: Scopes** (Can skip entirely)

This page asks what data you want to access from users.

**What to do**: Just click **"SAVE AND CONTINUE"**

Why? The default scopes (email, profile, openid) are already included automatically. You don't need to add anything here for basic authentication.

✅ Click **"SAVE AND CONTINUE"**

---

### **Page 3: Test users** (Optional but recommended)

This page lets you add test users who can sign in while your app is in "Testing" mode.

**What to do**:

#### Option A: Skip Testing Mode (Recommended for now)
- Just click **"SAVE AND CONTINUE"**
- You can add yourself as a test user once you get to the summary

#### Option B: Add Test Users Now
1. Click **"+ ADD USERS"**
2. Enter your email address (and any other testers)
3. Click **"ADD"**
4. Click **"SAVE AND CONTINUE"**

✅ Click **"SAVE AND CONTINUE"**

---

### **Page 4: Summary**

Review your settings. You should see:

```
✓ App name: AIRO
✓ User support email: [your email]
✓ Developer contact: [your email]
✓ Publishing status: Testing
```

**Publishing Status will be "Testing"** - This is normal!

#### What "Testing" Mode Means:
- ✅ You and test users can sign in
- ✅ Up to 100 test users allowed
- ✅ Perfect for development and small teams
- ⚠️ Non-test users will see a warning screen

#### Do You Need to Publish?

**For Development & Small Teams**: No, stay in Testing mode
- You can add up to 100 test users
- No verification required
- Perfect for internal use

**For Public Launch**: Yes, submit for verification
- Allows anyone to sign in
- Requires Google review (1-2 weeks)
- Needed only if you want unlimited public users

✅ Click **"BACK TO DASHBOARD"**

---

## ✅ You're Done with OAuth Consent Screen!

You should now see a dashboard showing:
```
Publishing status: Testing
User type: External
```

---

## 🎯 Next Step: Create OAuth Credentials

Now that consent screen is configured, create your OAuth credentials:

### Quick Steps:

1. In the left sidebar: **"APIs & Services"** → **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"**
4. Choose **"Web application"**
5. Configure:
   - **Name**: `AIRO Web Client`
   - **Authorized JavaScript origins**:
     ```
     http://localhost:5173
     ```
   - **Authorized redirect URIs**:
     ```
     http://localhost:5173
     ```
6. Click **"CREATE"**
7. **Copy your credentials:**
   - **Client ID**: `xxxxx.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-xxxxx`

---

## 🎨 What Users Will See

### In Testing Mode (Current)
When users click "Sign in with Google", they'll see:

```
┌─────────────────────────────────────┐
│  Google                        [X]  │
├─────────────────────────────────────┤
│                                     │
│  ⚠️  This app isn't verified       │
│                                     │
│  AIRO wants to access your Google  │
│  Account                            │
│                                     │
│  [email address]                    │
│                                     │
│  This will allow AIRO to:          │
│  • See your email address          │
│  • See your personal info          │
│                                     │
│  [ Continue ]  [ Cancel ]          │
│                                     │
└─────────────────────────────────────┘
```

**This is normal for Testing mode!** Test users can still sign in by clicking "Continue".

### After Publishing (Optional)
The warning goes away, and users see a cleaner screen.

---

## 🔧 Adding Test Users (After Setup)

If you need to add test users later:

1. Go to **APIs & Services** → **OAuth consent screen**
2. Scroll to **"Test users"** section
3. Click **"+ ADD USERS"**
4. Enter email addresses (one per line)
5. Click **"SAVE"**

Test users can sign in even though app is in Testing mode.

---

## 🆘 Troubleshooting

### "This app isn't verified" Warning

**Cause**: Your app is in Testing mode
**Solution**: This is expected! Test users can click "Continue" to proceed
**To remove**: Submit app for verification (only needed for public launch)

### Can't Find OAuth Consent Screen

**Solution**:
1. Make sure you've selected your project (top left dropdown)
2. Click ☰ menu → APIs & Services → OAuth consent screen

### "Access blocked: This app's request is invalid"

**Cause**: Haven't configured consent screen yet
**Solution**: Complete the OAuth consent screen setup above

### Email Not Showing in Dropdown

**Cause**: Not signed in with right account
**Solution**: Sign out and sign in with the Google account you want to use

---

## 📋 Quick Checklist

After completing this guide, you should have:

- [x] Created Google Cloud project
- [x] Configured OAuth consent screen
- [x] App name: AIRO
- [x] User support email: Added
- [x] Developer contact: Added
- [x] Publishing status: Testing
- [ ] OAuth credentials created (Next step)
- [ ] Added Client ID/Secret to `.env` files (After credentials)

---

## 🎯 What's Next?

1. **Create OAuth Credentials** (see Quick Steps above)
2. **Update `.env` files** with your Client ID and Secret
3. **Start your servers** and test login

See [QUICK_START.md](QUICK_START.md) for complete instructions!

---

## 💡 Tips

- **Stay in Testing mode** for development - it's easier
- **Add yourself as a test user** if you see verification warnings
- **No need to publish** unless you want unlimited public users
- **You can edit** the consent screen anytime from the dashboard

---

**Done?** Proceed to creating OAuth credentials! 🚀
