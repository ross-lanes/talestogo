# Step-by-Step: Create OAuth Credentials

## 📋 Overview

After configuring your OAuth consent screen, you need to create OAuth credentials (Client ID and Client Secret) to enable Google login in AIRO.

**Time needed:** 3 minutes
**Prerequisites:** OAuth consent screen configured ✓

---

## 🚀 Step-by-Step Instructions

### Step 1: Navigate to Credentials

1. Go to **https://console.cloud.google.com/**
2. Make sure your project is selected (top left dropdown should show "AIRO")
3. In the left sidebar, click **"APIs & Services"**
4. Click **"Credentials"**

```
Left Sidebar:
┌────────────────────────┐
│ [≡] Google Cloud       │
├────────────────────────┤
│ 📊 APIs & Services     │
│   ├─ Dashboard         │
│   ├─ Library           │
│   ├─ Credentials    ← Click here!
│   └─ OAuth consent    │
└────────────────────────┘
```

### Step 2: Create Credentials

You'll see the Credentials page:

```
┌─────────────────────────────────────────────────┐
│ Credentials                                     │
├─────────────────────────────────────────────────┤
│ [+ CREATE CREDENTIALS ▼] ← Click this button   │
│                                                 │
│ Dropdown appears:                               │
│ • API key                                       │
│ • OAuth client ID      ← Select this           │
│ • Service account key                           │
└─────────────────────────────────────────────────┘
```

1. Click **"+ CREATE CREDENTIALS"** button at the top
2. From dropdown, select **"OAuth client ID"**

### Step 3: Choose Application Type

You'll see "Create OAuth client ID" page:

```
┌─────────────────────────────────────────────────┐
│ Create OAuth client ID                          │
├─────────────────────────────────────────────────┤
│                                                 │
│ Application type *                              │
│                                                 │
│ ⚪ Android                                      │
│ ⚪ Chrome app                                   │
│ ⚪ Desktop app                                  │
│ ⚪ iOS                                          │
│ ⚪ TVs and Limited Input devices                │
│ ⚪ Universal Windows Platform (UWP)             │
│ 🔘 Web application     ← Select this!          │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Select:** ✅ **Web application**

### Step 4: Configure Web Application

Now you'll see a form. Here's exactly what to enter:

```
┌─────────────────────────────────────────────────┐
│ Create OAuth client ID                          │
├─────────────────────────────────────────────────┤
│                                                 │
│ Name *                                          │
│ ┌─────────────────────────────────────────┐    │
│ │ AIRO Web Client                   ← Type│    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ Authorized JavaScript origins                   │
│ ┌─────────────────────────────────────────┐    │
│ │ [+ ADD URI]                        ← Click   │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ Authorized redirect URIs                        │
│ ┌─────────────────────────────────────────┐    │
│ │ [+ ADD URI]                        ← Click   │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ [CREATE]                                        │
└─────────────────────────────────────────────────┘
```

#### Fill in these fields:

**Name:**
```
AIRO Web Client
```

**Authorized JavaScript origins:**

Click **"+ ADD URI"** and enter:
```
http://localhost:5173
```

Click **"+ ADD URI"** again (optional) and add:
```
http://localhost:3000
```
*(Backup port if 5173 is in use)*

**Authorized redirect URIs:**

Click **"+ ADD URI"** and enter:
```
http://localhost:5173
```

Click **"+ ADD URI"** again (optional) and add:
```
http://localhost:3000
```

### Visual Example:
```
┌─────────────────────────────────────────────────┐
│ Name *                                          │
│ ┌─────────────────────────────────────────┐    │
│ │ AIRO Web Client                          │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ Authorized JavaScript origins                   │
│ URIs 1  http://localhost:5173           [×]    │
│ URIs 2  http://localhost:3000           [×]    │
│ [+ ADD URI]                                     │
│                                                 │
│ Authorized redirect URIs                        │
│ URIs 1  http://localhost:5173           [×]    │
│ URIs 2  http://localhost:3000           [×]    │
│ [+ ADD URI]                                     │
│                                                 │
│ [CREATE] ← Click when done                      │
└─────────────────────────────────────────────────┘
```

### Step 5: Click CREATE

After filling everything out, click the **[CREATE]** button at the bottom.

---

## 🎉 Step 6: Copy Your Credentials

A popup will appear with your credentials:

```
┌─────────────────────────────────────────────────┐
│ OAuth client created                       [×]  │
├─────────────────────────────────────────────────┤
│                                                 │
│ Your Client ID                                  │
│ ┌─────────────────────────────────────────┐    │
│ │ 123456789-abc.apps.googleusercontent... │ 📋 │ ← Click to copy
│ └─────────────────────────────────────────┘    │
│                                                 │
│ Your Client Secret                              │
│ ┌─────────────────────────────────────────┐    │
│ │ GOCSPX-abcdefghijklmnop...             │ 📋 │ ← Click to copy
│ └─────────────────────────────────────────┘    │
│                                                 │
│ [DOWNLOAD JSON]  [OK]                           │
└─────────────────────────────────────────────────┘
```

### 🔴 IMPORTANT: Copy Both Values!

**Client ID** - Looks like:
```
123456789012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com
```

**Client Secret** - Looks like:
```
GOCSPX-ABCdefGHIjklMNOpqrSTUvwxYZ
```

**Ways to copy:**
1. Click the 📋 copy icon next to each
2. Select the text and press Cmd+C (Mac) or Ctrl+C (Windows)
3. Click "DOWNLOAD JSON" to save them to a file

**⚠️ Warning:** The Client Secret is only shown once! If you lose it, you'll need to generate a new one.

---

## 💾 Step 7: Save Your Credentials

Now update your AIRO `.env` files with these credentials:

### Backend: `.env`

Open: `/Users/rachelkremen/Documents/Code/airo_project/.env`

Find these lines:
```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

Replace with YOUR values:
```env
GOOGLE_CLIENT_ID=123456789012-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-ABCdefGHIjklMNOpqrSTU
```

### Frontend: `frontend/.env`

Open: `/Users/rachelkremen/Documents/Code/airo_project/frontend/.env`

Find this line:
```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

Replace with YOUR Client ID (same as backend):
```env
VITE_GOOGLE_CLIENT_ID=123456789012-abcdefghijklmnop.apps.googleusercontent.com
```

**💡 Note:** Use the SAME Client ID in both files!

---

## ✅ Verification

After updating, your files should look like:

### `.env` (Backend)
```env
# JWT Configuration
JWT_SECRET_KEY=ww5mWOvftMjsaBAU8LldpfMUGrxteJ9mpopHb9DuQ1Q
ENCRYPTION_KEY=p-u0Bk36udBIes--zCK85PHeM-_cpkxugPYSAPvdoiE

# Google OAuth Configuration
GOOGLE_CLIENT_ID=123456789012-abc.apps.googleusercontent.com  ✓
GOOGLE_CLIENT_SECRET=GOCSPX-ABCdefGHIjklMNO  ✓
```

### `frontend/.env` (Frontend)
```env
# API Base URL
VITE_API_URL=http://localhost:8000

# Google OAuth Client ID
VITE_GOOGLE_CLIENT_ID=123456789012-abc.apps.googleusercontent.com  ✓
```

---

## 🎯 You're Ready to Test!

Now you can start your servers and test Google login:

### Terminal 1 - Backend:
```bash
cd /Users/rachelkremen/Documents/Code/airo_project
python3 -m uvicorn app.main:app --reload
```

### Terminal 2 - Frontend:
```bash
cd /Users/rachelkremen/Documents/Code/airo_project/frontend
npm run dev
```

### Test in Browser:
1. Open: **http://localhost:5173/login**
2. You should see the Google "Sign in" button
3. Click it and sign in with your Google account
4. You should be redirected to the dashboard! 🎉

---

## 🔧 Managing Your Credentials

### View Your Credentials Later

1. Go to: **APIs & Services** → **Credentials**
2. You'll see your credentials listed under "OAuth 2.0 Client IDs"
3. Click the pencil icon (✏️) to view/edit

### If You Lose Your Client Secret

1. Go to **Credentials** page
2. Click on your "AIRO Web Client"
3. Scroll to "Client secrets"
4. Click **"+ ADD SECRET"**
5. Copy the new secret
6. Update your `.env` file

### Adding Production URLs Later

When you deploy to production:

1. Go to **Credentials** page
2. Click your "AIRO Web Client" credential
3. Under "Authorized JavaScript origins", click **"+ ADD URI"**
4. Add your production domain: `https://yourdomain.com`
5. Under "Authorized redirect URIs", add: `https://yourdomain.com`
6. Click **"SAVE"**

---

## 🆘 Troubleshooting

### Error: "Redirect URI mismatch"

**Cause:** The URL you're accessing doesn't match your authorized URIs

**Solution:**
1. Go back to Credentials → Click your OAuth client
2. Make sure you added: `http://localhost:5173`
3. Check for typos (http vs https, trailing slashes, etc.)
4. Save changes
5. **Restart your frontend** after updating

### Error: "Invalid client"

**Cause:** Client ID in frontend doesn't match Google Cloud Console

**Solution:**
1. Double-check `VITE_GOOGLE_CLIENT_ID` in `frontend/.env`
2. Compare with Client ID in Google Cloud Console
3. Make sure there are no extra spaces or quotes
4. Restart frontend: `npm run dev`

### Can't Find Credentials Page

**Solution:**
1. Click ☰ hamburger menu
2. APIs & Services → Credentials
3. Make sure project "AIRO" is selected (top left)

### "This app isn't verified" Warning

**Cause:** Your app is in Testing mode

**Solution:**
- This is normal! Click "Continue" or "Advanced" → "Go to AIRO (unsafe)"
- Better: Add yourself as a test user in OAuth consent screen

---

## 📋 Quick Copy-Paste Values

Use these exact values when creating credentials:

**Name:**
```
AIRO Web Client
```

**Authorized JavaScript origins:**
```
http://localhost:5173
http://localhost:3000
```

**Authorized redirect URIs:**
```
http://localhost:5173
http://localhost:3000
```

---

## 🔒 Security Best Practices

✅ **DO:**
- Keep Client Secret private (don't commit to git)
- Use environment variables (`.env` files)
- Add `.env` to `.gitignore`
- Rotate secrets if compromised

❌ **DON'T:**
- Share Client Secret publicly
- Commit `.env` files to GitHub
- Use same credentials for dev and production
- Hard-code credentials in source code

---

## 📊 Credentials Checklist

After completing this guide:

- [x] OAuth consent screen configured
- [x] OAuth client ID created
- [x] Client ID copied
- [x] Client Secret copied
- [x] Backend `.env` updated with both credentials
- [x] Frontend `.env` updated with Client ID
- [ ] Servers started (next step)
- [ ] Google login tested (next step)

---

## 🎯 What's Next?

You're ready to test! Follow these steps:

1. **Start Backend** - See Terminal 1 command above
2. **Start Frontend** - See Terminal 2 command above
3. **Test Login** - Go to http://localhost:5173/login
4. **Sign in with Google** - Click the button and authenticate

See [QUICK_START.md](QUICK_START.md) for complete testing instructions!

---

**Done?** Start your servers and test Google login! 🚀

**Need help?** Check the troubleshooting section above or [QUICK_START.md](QUICK_START.md)
