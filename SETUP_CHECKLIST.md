# Google OAuth Setup Checklist

## ✓ Completed Automatically

- [x] Database migrated with OAuth columns
- [x] Backend dependencies installed
- [x] Frontend dependencies installed
- [x] Environment files created (.env)
- [x] JWT secret keys generated
- [x] Encryption keys generated
- [x] Backend code updated
- [x] Frontend code updated
- [x] API endpoints created
- [x] Login page updated with Google button

## → Your Action Items

### 1. Get Google OAuth Credentials (10 minutes)

Follow these steps in [Google Cloud Console](https://console.cloud.google.com/):

- [ ] Create new Google Cloud project named "AIRO"
- [ ] Configure OAuth consent screen (External)
- [ ] Create OAuth 2.0 Client ID (Web application)
- [ ] Add authorized JavaScript origins:
  - `http://localhost:5173`
  - `http://localhost:3000`
- [ ] Add authorized redirect URIs:
  - `http://localhost:5173`
  - `http://localhost:3000`
- [ ] Copy Client ID and Client Secret

### 2. Update Environment Files (2 minutes)

#### Backend: `.env`
```bash
# Open this file and update these two lines:
GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-actual-client-secret
```

#### Frontend: `frontend/.env`
```bash
# Open this file and update this line:
VITE_GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
```

**Important**: Use the SAME Client ID in both files!

### 3. Start the Servers

#### Terminal 1 - Backend
```bash
cd /Users/rachelkremen/Documents/Code/airo_project
python3 -m uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### Terminal 2 - Frontend
```bash
cd /Users/rachelkremen/Documents/Code/airo_project/frontend
npm run dev
```

Expected output:
```
➜  Local:   http://localhost:5173/
```

### 4. Test Google Login

- [ ] Open http://localhost:5173/login in browser
- [ ] Verify you see "Sign in with Google" button
- [ ] Click the Google button
- [ ] Complete Google sign-in flow
- [ ] Confirm you're logged into the dashboard

## Files Modified/Created

### Backend
- `app/models.py` - Added OAuth fields to User model
- `app/auth.py` - Added Google OAuth verification
- `app/main.py` - Added `/auth/google` endpoint
- `app/schemas.py` - Added GoogleLogin schema
- `requirements.txt` - Added dependencies
- `.env` - Created with secrets

### Frontend
- `frontend/src/App.tsx` - Wrapped with GoogleOAuthProvider
- `frontend/src/contexts/AuthContext.tsx` - Added googleLogin method
- `frontend/src/services/api.ts` - Added googleLogin API call
- `frontend/src/pages/auth/Login.tsx` - Added Google login button
- `frontend/package.json` - Added @react-oauth/google
- `frontend/.env` - Created with Google Client ID

### Documentation
- `GOOGLE_OAUTH_SETUP.md` - Detailed setup guide
- `QUICK_START.md` - Quick start instructions
- `SETUP_CHECKLIST.md` - This file
- `.env.example` - Backend environment template
- `frontend/.env.example` - Frontend environment template
- `migrate_oauth.py` - Database migration script

### Database
- `airo.db` - Migrated with new columns:
  - `google_id` - Google user ID
  - `oauth_provider` - OAuth provider name
  - `picture_url` - Profile picture URL

## Current Configuration Status

```
✓ Database: Migrated
✓ Backend Dependencies: Installed
✓ Frontend Dependencies: Installed
✓ Environment Files: Created
✓ JWT Secrets: Generated
✓ Migration Script: Executed

⚠ Google Credentials: NEEDS YOUR INPUT
⚠ .env Files: NEED YOUR GOOGLE CREDENTIALS
```

## Quick Commands Reference

```bash
# Test backend imports
python3 -c "from app.main import app; print('Backend OK')"

# Start backend
python3 -m uvicorn app.main:app --reload

# Start frontend
cd frontend && npm run dev

# View database schema
sqlite3 airo.db "PRAGMA table_info(users);"

# Check environment variables
cat .env | grep GOOGLE
cat frontend/.env | grep GOOGLE
```

## Need Help?

1. **Backend won't start**: Check `pip install -r requirements.txt`
2. **Frontend won't start**: Check `cd frontend && npm install`
3. **Can't see Google button**: Verify `VITE_GOOGLE_CLIENT_ID` in `frontend/.env`
4. **Google login fails**: Check browser console (F12) for errors
5. **Redirect URI error**: Add localhost:5173 to authorized origins in Google Console

## Next Steps After Setup

Once Google OAuth is working:

1. Test with multiple Google accounts
2. Test linking existing email/password account
3. Update production authorized origins (when deploying)
4. Consider adding other OAuth providers (GitHub, Microsoft)
5. Configure user roles and permissions

---

**Current Status**: Ready for Google OAuth credentials!
See [QUICK_START.md](QUICK_START.md) for detailed setup instructions.
