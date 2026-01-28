# Quick Start Guide - Google OAuth Setup

## Current Status ✓

Your TALES project has been successfully configured for Google OAuth! Here's what's been done:

### Completed Steps ✓

1. **Backend Configuration**
   - ✓ OAuth columns added to database (`google_id`, `oauth_provider`, `picture_url`)
   - ✓ JWT secret keys generated and configured
   - ✓ Google OAuth endpoints created
   - ✓ Dependencies installed (`google-auth`, `authlib`)
   - ✓ Backend imports successfully

2. **Frontend Configuration**
   - ✓ Google OAuth library installed (`@react-oauth/google`)
   - ✓ Login page updated with Google login button
   - ✓ Environment file created

3. **Database Migration**
   - ✓ OAuth columns added to existing database
   - ✓ Indexes created for performance

## Next Steps - Get Your Google OAuth Credentials

### Step 1: Create Google Cloud Project (5 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown at the top → "New Project"
3. Name: "TALES Authentication" → Click "Create"
4. Wait for project creation (usually instant)

### Step 2: Configure OAuth Consent Screen (3 minutes)

1. In your new project, go to: **APIs & Services** → **OAuth consent screen**
2. Select **External** → Click "Create"
3. Fill in required fields:
   - **App name**: TALES
   - **User support email**: [Your email]
   - **Developer contact**: [Your email]
4. Click "Save and Continue" (3 times to skip optional sections)
5. Click "Back to Dashboard"

### Step 3: Create OAuth Credentials (2 minutes)

1. Go to: **APIs & Services** → **Credentials**
2. Click **"+ Create Credentials"** → **"OAuth client ID"**
3. Application type: **Web application**
4. Name: **TALES Web Client**
5. **Authorized JavaScript origins**: Add these URLs:
   ```
   http://localhost:5173
   http://localhost:3000
   ```
6. **Authorized redirect URIs**: Add these URLs:
   ```
   http://localhost:5173
   http://localhost:3000
   ```
7. Click **"Create"**
8. **IMPORTANT**: Copy both:
   - Client ID (looks like: `xxxxx.apps.googleusercontent.com`)
   - Client Secret (looks like: `GOCSPX-xxxxx`)

### Step 4: Configure Environment Files (1 minute)

#### Backend (.env)
Open `/Users/rachelkremen/Documents/Code/tales_project/.env` and update:

```env
GOOGLE_CLIENT_ID=paste-your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=paste-your-client-secret-here
```

#### Frontend (frontend/.env)
Open `/Users/rachelkremen/Documents/Code/tales_project/frontend/.env` and update:

```env
VITE_GOOGLE_CLIENT_ID=paste-your-client-id-here.apps.googleusercontent.com
```

**Note**: Use the SAME Client ID in both files!

### Step 5: Start the Application

Open two terminal windows:

#### Terminal 1 - Backend
```bash
cd /Users/rachelkremen/Documents/Code/tales_project
python3 -m uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

#### Terminal 2 - Frontend
```bash
cd /Users/rachelkremen/Documents/Code/tales_project/frontend
npm run dev
```

You should see:
```
  VITE v... ready in ...ms

  ➜  Local:   http://localhost:5173/
```

### Step 6: Test Google OAuth

1. Open browser: http://localhost:5173/login
2. You should see:
   - Email/Password login fields
   - "OR" divider
   - **"Sign in with Google"** button
3. Click the Google button
4. Select your Google account
5. Grant permissions
6. You should be logged in and redirected to the dashboard!

## Troubleshooting

### Error: "Invalid client ID"
- Check that `VITE_GOOGLE_CLIENT_ID` in `frontend/.env` matches your Google Cloud Console Client ID
- Restart the frontend server after updating `.env`

### Error: "Redirect URI mismatch"
- Add `http://localhost:5173` to both:
  - Authorized JavaScript origins
  - Authorized redirect URIs
- In Google Cloud Console

### Error: "Google login failed"
- Check browser console for detailed errors
- Verify backend is running on port 8000
- Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in backend `.env`

### Backend won't start
```bash
# Install missing dependencies
pip install -r requirements.txt

# Check for errors
python3 -c "from app.main import app; print('OK')"
```

### Frontend won't start
```bash
cd frontend
npm install
npm run dev
```

## Verification Checklist

- [ ] Google Cloud project created
- [ ] OAuth consent screen configured
- [ ] OAuth credentials created (Client ID + Secret)
- [ ] Backend `.env` updated with Google credentials
- [ ] Frontend `.env` updated with Google Client ID
- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173
- [ ] Can see Google login button on login page
- [ ] Successfully logged in with Google account

## What's Different?

### For New Users
- Can now sign in with Google (instant activation)
- No need to wait for admin approval
- Profile picture automatically imported

### For Existing Users
- Can continue using email/password login
- Can link Google account by logging in with Google (using same email)
- Once linked, can use either method

### For Admins
- New users via Google OAuth are auto-activated
- Email/password users still require manual activation
- Can see OAuth provider in user management

## Security Notes

✓ **OAuth users are auto-activated** - They've been verified by Google
✓ **Existing users protected** - Email/password users still require admin approval
✓ **Account linking** - Users can link their Google account to existing email/password account
✓ **Secure tokens** - JWT secrets have been randomly generated
✓ **Data isolation** - Each user's data remains separated

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review browser console for errors (F12)
3. Check backend terminal for error messages
4. Verify all environment variables are set correctly

## Production Deployment

When deploying to production:
1. Add your production domain to Google OAuth authorized origins/redirects
2. Update `.env` files with production URLs
3. Use environment variables (not `.env` files) in production
4. Enable HTTPS (required for OAuth)

---

**Ready to test?** Follow Step 5 above to start your servers and test Google OAuth!
