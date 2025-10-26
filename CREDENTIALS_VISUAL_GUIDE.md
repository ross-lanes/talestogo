# 🎨 Visual Guide: Create OAuth Credentials

## 📸 Screen-by-Screen Walkthrough

### Screen 1: Credentials Page
```
┌─────────────────────────────────────────────────────────────┐
│ Credentials                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [+ CREATE CREDENTIALS ▼]  [Filter]  [Refresh]  ← Click here│
│                                                             │
│ Credentials List (might be empty):                         │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ No credentials yet                                  │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Action:** Click **"+ CREATE CREDENTIALS"** button

---

### Screen 2: Dropdown Menu
```
┌─────────────────────────────────────────────────────────────┐
│ Credentials                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ [+ CREATE CREDENTIALS ▼] ← Clicked                         │
│ ┌──────────────────────────────────┐                       │
│ │ API key                          │                       │
│ │ OAuth client ID          ← Pick  │                       │
│ │ Service account key              │                       │
│ └──────────────────────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Action:** Select **"OAuth client ID"**

---

### Screen 3: Application Type Selection
```
┌─────────────────────────────────────────────────────────────┐
│ Create OAuth client ID                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Application type *                                          │
│                                                             │
│ Select the application type for your OAuth client ID       │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ ○ Android                                           │   │
│ │ ○ Chrome app                                        │   │
│ │ ○ Desktop app                                       │   │
│ │ ○ iOS                                               │   │
│ │ ○ TVs and Limited Input devices                     │   │
│ │ ○ Universal Windows Platform (UWP)                  │   │
│ │ ● Web application                    ← Select this! │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Action:** Click **"Web application"** radio button

---

### Screen 4: Configuration Form (Initial)
```
┌─────────────────────────────────────────────────────────────┐
│ Create OAuth client ID                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Name *                                                      │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ Web client 1                    [Clear]  ← Change this│ │
│ └───────────────────────────────────────────────────────┘ │
│                                                             │
│ Authorized JavaScript origins                               │
│ For use with requests from a browser                        │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ [+ ADD URI]                                    ← Click│ │
│ └───────────────────────────────────────────────────────┘ │
│                                                             │
│ Authorized redirect URIs                                    │
│ For use with requests from a web server                     │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ [+ ADD URI]                                    ← Click│ │
│ └───────────────────────────────────────────────────────┘ │
│                                                             │
│ [CREATE]                                                    │
└─────────────────────────────────────────────────────────────┘
```

**Action:** Now fill out the form...

---

### Screen 5: Name Field
```
┌─────────────────────────────────────────────────────────────┐
│ Name *                                                      │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ AIRO Web Client                          ← Type this  │ │
│ └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Type:** `AIRO Web Client`

---

### Screen 6: Add JavaScript Origins
```
┌─────────────────────────────────────────────────────────────┐
│ Authorized JavaScript origins                               │
│ For use with requests from a browser                        │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ [+ ADD URI]                                 ← Click   │ │
│ └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Click:** [+ ADD URI]

After clicking, a text field appears:
```
┌─────────────────────────────────────────────────────────────┐
│ Authorized JavaScript origins                               │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ URIs 1  http://localhost:5173              [×] ← Type│ │
│ └───────────────────────────────────────────────────────┘ │
│ [+ ADD URI]                                    ← Click   │ │
└─────────────────────────────────────────────────────────────┘
```

**Type:** `http://localhost:5173`

**Then:** Click [+ ADD URI] again to add: `http://localhost:3000`

---

### Screen 7: Add Redirect URIs
```
┌─────────────────────────────────────────────────────────────┐
│ Authorized redirect URIs                                    │
│ For use with requests from a web server                     │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ [+ ADD URI]                                 ← Click   │ │
│ └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Click:** [+ ADD URI]

After clicking:
```
┌─────────────────────────────────────────────────────────────┐
│ Authorized redirect URIs                                    │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ URIs 1  http://localhost:5173              [×] ← Type│ │
│ └───────────────────────────────────────────────────────┘ │
│ [+ ADD URI]                                    ← Click   │ │
└─────────────────────────────────────────────────────────────┘
```

**Type:** `http://localhost:5173`

**Then:** Click [+ ADD URI] again to add: `http://localhost:3000`

---

### Screen 8: Complete Form
```
┌─────────────────────────────────────────────────────────────┐
│ Create OAuth client ID                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Name *                                                      │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ AIRO Web Client                                  ✓    │ │
│ └───────────────────────────────────────────────────────┘ │
│                                                             │
│ Authorized JavaScript origins                               │
│ URIs 1  http://localhost:5173                     [×]  ✓   │
│ URIs 2  http://localhost:3000                     [×]  ✓   │
│ [+ ADD URI]                                                 │
│                                                             │
│ Authorized redirect URIs                                    │
│ URIs 1  http://localhost:5173                     [×]  ✓   │
│ URIs 2  http://localhost:3000                     [×]  ✓   │
│ [+ ADD URI]                                                 │
│                                                             │
│ [CREATE]                                        ← Click!    │
└─────────────────────────────────────────────────────────────┘
```

**Action:** Click **[CREATE]** button

---

### Screen 9: Credentials Created! 🎉
```
┌─────────────────────────────────────────────────────────────┐
│ OAuth client created                                   [×]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Here's your client ID and secret. Keep them secure!        │
│                                                             │
│ Your Client ID                                              │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ 123456789012-abc123xyz.apps.googleusercontent.com     │📋│ ← Copy!
│ └───────────────────────────────────────────────────────┘ │
│                                                             │
│ Your Client Secret                                          │
│ ┌───────────────────────────────────────────────────────┐ │
│ │ GOCSPX-ABCDEFGHijklmnop1234567                        │📋│ ← Copy!
│ └───────────────────────────────────────────────────────┘ │
│                                                             │
│ ⚠️ Keep your client secret private!                        │
│                                                             │
│ [DOWNLOAD JSON]  [OK]                                       │
└─────────────────────────────────────────────────────────────┘
```

**Action:**
1. Click 📋 to copy **Client ID**
2. Click 📋 to copy **Client Secret**
3. Save both somewhere safe!

---

## 📝 What to Copy Where

### Backend `.env` File

Location: `/Users/rachelkremen/Documents/Code/airo_project/.env`

```env
# Before:
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# After (with YOUR actual values):
GOOGLE_CLIENT_ID=123456789012-abc123xyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-ABCDEFGHijklmnop1234567
```

### Frontend `.env` File

Location: `/Users/rachelkremen/Documents/Code/airo_project/frontend/.env`

```env
# Before:
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# After (with YOUR actual Client ID - SAME as backend):
VITE_GOOGLE_CLIENT_ID=123456789012-abc123xyz.apps.googleusercontent.com
```

---

## ✅ Checklist

Follow these steps in order:

```
□ Navigate to Credentials page
□ Click "+ CREATE CREDENTIALS"
□ Select "OAuth client ID"
□ Choose "Web application"
□ Name: "AIRO Web Client"
□ Add JavaScript origin: http://localhost:5173
□ Add JavaScript origin: http://localhost:3000
□ Add Redirect URI: http://localhost:5173
□ Add Redirect URI: http://localhost:3000
□ Click "CREATE"
□ Copy Client ID
□ Copy Client Secret
□ Paste Client ID → Backend .env
□ Paste Client Secret → Backend .env
□ Paste Client ID → Frontend .env
□ Ready to test!
```

---

## 🎯 Quick Reference Table

| Field | Value | Where |
|-------|-------|-------|
| **Name** | `AIRO Web Client` | Credentials form |
| **App Type** | Web application | Credentials form |
| **JS Origins** | `http://localhost:5173`<br>`http://localhost:3000` | Credentials form |
| **Redirect URIs** | `http://localhost:5173`<br>`http://localhost:3000` | Credentials form |
| **Client ID** | Copy from popup | Backend + Frontend `.env` |
| **Client Secret** | Copy from popup | Backend `.env` only |

---

## 🆘 Common Mistakes

### ❌ Wrong: Using https for localhost
```
https://localhost:5173  ← Wrong!
```

### ✅ Correct: Using http for localhost
```
http://localhost:5173  ← Correct!
```

### ❌ Wrong: Adding trailing slash
```
http://localhost:5173/  ← Wrong!
```

### ✅ Correct: No trailing slash
```
http://localhost:5173  ← Correct!
```

### ❌ Wrong: Different Client IDs in frontend/backend
```
Backend:  123-abc.apps.googleusercontent.com
Frontend: 456-xyz.apps.googleusercontent.com  ← Wrong!
```

### ✅ Correct: Same Client ID in both
```
Backend:  123-abc.apps.googleusercontent.com
Frontend: 123-abc.apps.googleusercontent.com  ← Correct!
```

---

## 🚀 After Setup

Once you've updated your `.env` files, start the servers:

### Terminal 1 - Backend
```bash
cd /Users/rachelkremen/Documents/Code/airo_project
python3 -m uvicorn app.main:app --reload
```

### Terminal 2 - Frontend
```bash
cd /Users/rachelkremen/Documents/Code/airo_project/frontend
npm run dev
```

### Browser
```
http://localhost:5173/login
```

You should see the Google "Sign in" button! 🎉

---

**Next:** [Test your Google OAuth login →](QUICK_START.md)

**Need help?** See [CREATE_OAUTH_CREDENTIALS.md](CREATE_OAUTH_CREDENTIALS.md) for detailed troubleshooting
