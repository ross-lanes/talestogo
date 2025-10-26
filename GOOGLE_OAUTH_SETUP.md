# Google OAuth Setup Guide for AIRO

This guide will walk you through setting up Google OAuth authentication for the AIRO application.

## Overview

The AIRO application now supports two authentication methods:
1. **Traditional Email/Password** - Users register with email and password
2. **Google OAuth** - Users sign in with their Google account (recommended)

Google OAuth users are automatically activated upon first login, while email/password users require admin approval.

## Prerequisites

- A Google Cloud Platform account
- Access to the Google Cloud Console

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "AIRO Authentication")
5. Click "Create"

## Step 2: Enable Google+ API

1. In your Google Cloud project, navigate to "APIs & Services" > "Library"
2. Search for "Google+ API"
3. Click on it and press "Enable"

## Step 3: Configure OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen"
2. Select "External" (or "Internal" if using Google Workspace)
3. Click "Create"
4. Fill in the required information:
   - **App name**: AIRO
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click "Save and Continue"
6. On the "Scopes" page, you can skip adding scopes (default profile and email are included)
7. Click "Save and Continue"
8. On "Test users" (if External), add your email for testing
9. Click "Save and Continue"

## Step 4: Create OAuth Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Configure the following:

   **Name**: AIRO Web Client

   **Authorized JavaScript origins**:
   - `http://localhost:5173` (for development)
   - `http://localhost:3000` (alternative dev port)
   - `https://yourdomain.com` (for production)

   **Authorized redirect URIs**:
   - `http://localhost:5173` (for development)
   - `https://yourdomain.com` (for production)

5. Click "Create"
6. **Important**: Copy the Client ID and Client Secret

## Step 5: Configure Backend Environment

1. Create a `.env` file in the project root (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Add your Google OAuth credentials:
   ```env
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   JWT_SECRET_KEY=generate-a-random-secret-key
   ```

3. Generate a secure JWT secret key:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## Step 6: Configure Frontend Environment

1. Create a `.env` file in the `frontend/` directory:
   ```bash
   cd frontend
   cp .env.example .env
   ```

2. Add your Google Client ID:
   ```env
   VITE_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   VITE_API_URL=http://localhost:8000
   ```

## Step 7: Install Dependencies

### Backend
```bash
pip install -r requirements.txt
```

### Frontend
```bash
cd frontend
npm install
```

## Step 8: Update Database Schema

The User model has been updated to support OAuth. You need to update your database:

```bash
# If using SQLite (development)
# The tables will be automatically created/updated on app start

# If using PostgreSQL (production)
# You may need to run migrations or update the schema manually
```

### Manual Database Update (if needed)

If you're using an existing database, run these SQL commands:

```sql
ALTER TABLE users
ADD COLUMN google_id VARCHAR(255) UNIQUE,
ADD COLUMN oauth_provider VARCHAR(50),
ADD COLUMN picture_url VARCHAR(500),
ALTER COLUMN hashed_password DROP NOT NULL;

CREATE INDEX idx_users_google_id ON users(google_id);
```

## Step 9: Start the Application

### Start Backend
```bash
uvicorn app.main:app --reload
```

### Start Frontend
```bash
cd frontend
npm run dev
```

## Step 10: Test Google OAuth

1. Navigate to `http://localhost:5173/login`
2. Click "Continue with Google"
3. Select your Google account
4. Grant permissions
5. You should be redirected to the dashboard

## Authentication Flow

### Google OAuth Flow
1. User clicks "Continue with Google" on login page
2. Google OAuth popup appears
3. User selects account and grants permissions
4. Google returns an ID token to the frontend
5. Frontend sends the ID token to backend `/auth/google` endpoint
6. Backend verifies the token with Google
7. Backend creates or retrieves user from database
8. Backend generates a JWT token
9. Frontend stores JWT token and user data
10. User is logged in

### Traditional Email/Password Flow
1. User enters email and password
2. Frontend sends credentials to `/auth/login`
3. Backend verifies password hash
4. Backend checks if user is active
5. Backend generates JWT token
6. Frontend stores JWT token and user data
7. User is logged in

## User Management

### OAuth Users
- Automatically activated upon first login
- No password stored (password field is NULL)
- Can be identified by `oauth_provider` field = 'google'
- Profile picture URL stored in `picture_url` field

### Email/Password Users
- Require admin approval (`is_active` = False by default)
- Have hashed password stored
- Can be converted to OAuth by logging in with Google using the same email

## Security Considerations

1. **Never commit `.env` files** - They contain sensitive credentials
2. **Use HTTPS in production** - Required for OAuth
3. **Rotate JWT secrets regularly** - Especially if compromised
4. **Keep dependencies updated** - Run `pip install --upgrade` and `npm update`
5. **Monitor Google Cloud Console** - Check for suspicious activity

## Troubleshooting

### "Invalid Google token" Error
- Check that `GOOGLE_CLIENT_ID` matches in both backend and frontend
- Ensure JavaScript origins are correctly configured in Google Cloud Console
- Verify the ID token hasn't expired

### "Redirect URI mismatch" Error
- Add your current URL to "Authorized redirect URIs" in Google Cloud Console
- Make sure there are no trailing slashes

### Users Can't Log In After Migration
- Existing email/password users can continue using their passwords
- They can also link their Google account by logging in with Google using the same email
- Admin can activate users from the User Management page

## Production Deployment

1. Update authorized origins/redirects in Google Cloud Console
2. Use environment variables (not `.env` files) in production
3. Enable HTTPS/SSL
4. Use a production-grade database (PostgreSQL)
5. Set up proper logging and monitoring
6. Configure CORS to only allow your production domain

## API Endpoints

### New Endpoint
- `POST /auth/google` - Google OAuth login
  - Request body: `{ "token": "google-id-token" }`
  - Response: `{ "access_token": "jwt-token", "token_type": "bearer" }`

### Existing Endpoints
- `POST /auth/login` - Email/password login
- `POST /auth/register` - Email/password registration
- `GET /auth/me` - Get current user info

## Support

For issues or questions:
1. Check the Google Cloud Console for error messages
2. Review backend logs for authentication errors
3. Check browser console for frontend errors
4. Verify environment variables are set correctly
