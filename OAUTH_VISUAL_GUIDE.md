# 🎨 Visual Guide: OAuth Consent Screen Setup

## 🗺️ Navigation Map

Here's exactly where to click in Google Cloud Console:

```
Google Cloud Console (console.cloud.google.com)
│
├── 1️⃣ Create Project (if needed)
│   └── Click: Project dropdown → NEW PROJECT → Name: "AIRO" → CREATE
│
├── 2️⃣ Navigate to OAuth
│   └── Click: ☰ Menu → APIs & Services → OAuth consent screen
│
├── 3️⃣ Choose User Type
│   └── Click: External → CREATE
│
├── 4️⃣ Fill Form (4 pages)
│   ├── Page 1: App info ✍️
│   ├── Page 2: Scopes (skip) ⏭️
│   ├── Page 3: Test users (skip) ⏭️
│   └── Page 4: Summary ✅
│
└── 5️⃣ Create Credentials
    └── Click: Credentials → CREATE CREDENTIALS → OAuth client ID
```

---

## 📸 Screenshot Reference

### Screen 1: Project Selection
```
┌─────────────────────────────────────────┐
│ [≡] Google Cloud    [My Project ▼]  👤 │ ← Click dropdown here
├─────────────────────────────────────────┤
│                                         │
│  Select a project:                      │
│  ┌───────────────────────────────────┐ │
│  │ 🔍 Search projects               │ │
│  ├───────────────────────────────────┤ │
│  │ My First Project                  │ │
│  │ Other Project                     │ │
│  ├───────────────────────────────────┤ │
│  │ [+ NEW PROJECT]  ← Click this     │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Screen 2: Left Sidebar Menu
```
┌────────────────────────┐
│ [≡] Google Cloud       │
├────────────────────────┤
│ 🏠 Dashboard           │
│                        │
│ 📊 APIs & Services  ← Click this
│   ├─ Dashboard         │
│   ├─ Library           │
│   ├─ Credentials       │
│   └─ OAuth consent  ← Then this
│                        │
│ ☁️ Compute Engine      │
│ 💾 Storage             │
└────────────────────────┘
```

### Screen 3: OAuth Consent Screen Page
```
┌─────────────────────────────────────────────────┐
│ OAuth consent screen                            │
├─────────────────────────────────────────────────┤
│                                                 │
│  Configure the consent screen users see        │
│  when your app requests access to their data   │
│                                                 │
│  User Type                                      │
│  ┌─────────────────┐  ┌─────────────────┐     │
│  │   ○ Internal    │  │   ● External    │  ← Choose this
│  │                 │  │                 │     │
│  │ Only users in   │  │ Available to    │     │
│  │ your org        │  │ any Google user │     │
│  └─────────────────┘  └─────────────────┘     │
│                                                 │
│  [CREATE] ← Click                               │
└─────────────────────────────────────────────────┘
```

### Screen 4: Form - Page 1 (App Information)
```
┌─────────────────────────────────────────────────┐
│ OAuth consent screen                      1/4   │
├─────────────────────────────────────────────────┤
│                                                 │
│ App information                                 │
│                                                 │
│ App name *                                      │
│ ┌─────────────────────────────────────────┐    │
│ │ AIRO                              ← Type│    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ User support email *                            │
│ ┌─────────────────────────────────────────┐    │
│ │ your.email@gmail.com    ▼         ← Pick│    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ App logo (optional) - Skip this                 │
│ ┌─────────────────────────────────────────┐    │
│ │ [Upload logo]                            │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ App domain (optional) - Skip this               │
│ • Application home page                         │
│ • Application privacy policy link               │
│ • Application terms of service link             │
│                                                 │
│ Authorized domains (optional) - Skip            │
│                                                 │
│ Developer contact information *                 │
│ ┌─────────────────────────────────────────┐    │
│ │ your.email@gmail.com              ← Type│    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│              [SAVE AND CONTINUE] ← Click        │
└─────────────────────────────────────────────────┘
```

### Screen 5: Form - Page 2 (Scopes)
```
┌─────────────────────────────────────────────────┐
│ OAuth consent screen                      2/4   │
├─────────────────────────────────────────────────┤
│                                                 │
│ Scopes                                          │
│                                                 │
│ Tell users what data your app can access       │
│                                                 │
│ Default scopes (automatically included):        │
│ ✓ email                                         │
│ ✓ profile                                       │
│ ✓ openid                                        │
│                                                 │
│ These are perfect for authentication!           │
│ No need to add anything.                        │
│                                                 │
│ [ADD OR REMOVE SCOPES] ← Don't click this      │
│                                                 │
│              [SAVE AND CONTINUE] ← Click        │
└─────────────────────────────────────────────────┘
```

### Screen 6: Form - Page 3 (Test Users)
```
┌─────────────────────────────────────────────────┐
│ OAuth consent screen                      3/4   │
├─────────────────────────────────────────────────┤
│                                                 │
│ Test users                                      │
│                                                 │
│ Add trusted testers (up to 100)                 │
│                                                 │
│ Test users can access your app while it's      │
│ in Testing mode (unpublished)                   │
│                                                 │
│ ┌─────────────────────────────────────────┐    │
│ │ [+ ADD USERS] ← Optional: add yourself │    │
│ └─────────────────────────────────────────┘    │
│                                                 │
│ You can skip this and add yourself later        │
│                                                 │
│              [SAVE AND CONTINUE] ← Click        │
└─────────────────────────────────────────────────┘
```

### Screen 7: Form - Page 4 (Summary)
```
┌─────────────────────────────────────────────────┐
│ OAuth consent screen                      4/4   │
├─────────────────────────────────────────────────┤
│                                                 │
│ Summary                                         │
│                                                 │
│ Review your OAuth consent screen:               │
│                                                 │
│ App name:         AIRO                          │
│ User type:        External                      │
│ Publishing status: Testing                      │
│ User support:     your.email@gmail.com          │
│ Developer:        your.email@gmail.com          │
│                                                 │
│ ✓ Everything looks good!                        │
│                                                 │
│ [BACK TO DASHBOARD] ← Click                     │
└─────────────────────────────────────────────────┘
```

---

## ✅ Success! What You Should See

After completing, your dashboard should show:

```
┌─────────────────────────────────────────────────┐
│ OAuth consent screen                            │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📱 AIRO                                         │
│                                                 │
│ Publishing status: 🟡 Testing                   │
│ User type: External                             │
│                                                 │
│ [EDIT APP REGISTRATION]                         │
│                                                 │
│ Test users:                                     │
│ • your.email@gmail.com                          │
│ [+ ADD USERS]                                   │
│                                                 │
│ Note: Your app is in Testing mode.             │
│ Only test users can access it.                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

✅ **You're done with OAuth Consent Screen!**

---

## 🎯 Next: Create OAuth Credentials

Now click on **Credentials** in the left sidebar:

```
┌────────────────────────┐
│ APIs & Services        │
│ ├─ Dashboard           │
│ ├─ Library             │
│ ├─ Credentials      ← Click here
│ └─ OAuth consent       │
└────────────────────────┘
```

Then follow the credentials guide in [QUICK_START.md](QUICK_START.md#step-4-create-oauth-credentials)

---

## 🕐 Time Estimate

| Step | Time |
|------|------|
| Create project | 1 min |
| Navigate to OAuth | 30 sec |
| Choose External | 10 sec |
| Fill form page 1 | 2 min |
| Skip pages 2-3 | 20 sec |
| Review summary | 30 sec |
| **Total** | **~5 minutes** |

---

## 📝 Copy-Paste Ready Values

Use these exact values:

**App name:**
```
AIRO
```

**User support email:**
```
[Your Google email from the dropdown]
```

**Developer contact:**
```
[Your Google email - type it]
```

**Everything else:** Leave blank/skip

---

## 🆘 Common Issues

### Issue: "Can't find OAuth consent screen"

**Solution:**
1. Make sure you created/selected a project (top left dropdown)
2. Click the ☰ hamburger menu
3. Scroll down to "APIs & Services"
4. Click "OAuth consent screen"

### Issue: "Internal option is grayed out"

**Solution:**
This means you don't have Google Workspace. Just choose "External" - it works great for AIRO!

### Issue: "Need to verify my app?"

**Solution:**
No! In Testing mode, you can have up to 100 test users without verification. Perfect for development and small teams.

---

## 💡 Pro Tips

1. **Add yourself as a test user** to avoid the "unverified app" warning
2. **Stay in Testing mode** - no need to publish unless you want 1000+ public users
3. **Save emails** - you can use the same Google Cloud project for other apps too
4. **Bookmark the console** - you'll need it to add test users later

---

**Ready?** Start at Google Cloud Console: https://console.cloud.google.com/ 🚀

Next guide: [Creating OAuth Credentials →](QUICK_START.md#step-4-create-oauth-credentials)
