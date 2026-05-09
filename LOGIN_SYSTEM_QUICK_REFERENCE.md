# Tales Login System - Quick Reference Guide

## Quick Navigation

- **Main Investigation Report**: See `LOGIN_SYSTEM_INVESTIGATION.md` for complete details
- **File Index**: See `LOGIN_SYSTEM_FILE_INDEX.md` for all authentication files

---

## 1. LOGIN ENDPOINTS - QUICK REFERENCE

### Email/Password Login
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

# Error: Invalid credentials
401 Unauthorized
{
  "detail": "Incorrect email or password"
}

# Error: User not approved
403 Forbidden
{
  "detail": "Account is not active. Please contact admin for approval."
}
```

### Google OAuth Login
```bash
POST /auth/google
Content-Type: application/json

{
  "token": "{GOOGLE_ID_TOKEN}"
}

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Microsoft OAuth Login
```bash
POST /auth/microsoft
Content-Type: application/json

{
  "token": "{MICROSOFT_ID_TOKEN}"
}

# Response (200 OK)
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### User Registration
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePassword123",
  "full_name": "John Doe",
  "organization": "Acme Corp"
}

# Response (201 Created)
{
  "id": 42,
  "email": "newuser@example.com",
  "full_name": "John Doe",
  "is_active": false,
  "is_admin": false,
  ...
}

# Note: is_active=false means user needs admin approval!
```

### Get Current User
```bash
GET /auth/me
Authorization: Bearer {access_token}

# Response (200 OK)
{
  "id": 42,
  "email": "user@example.com",
  "full_name": "John Doe",
  "organization": "Acme Corp",
  "is_admin": false,
  "is_active": true,
  "is_invited": false,
  "tenant_id": 1,
  "created_at": "2025-11-09T12:00:00",
  "updated_at": "2025-11-09T12:00:00"
}
```

---

## 2. KEY CODE LOCATIONS

### Backend Authentication
- **Main Auth Module**: `/app/auth.py` (395 lines)
  - JWT creation/verification
  - Password hashing
  - OAuth token verification
  - User creation/linking

- **Auth Routes**: `/app/routers/auth.py` (174 lines)
  - All 6 authentication endpoints

- **User CRUD**: `/app/crud.py` (lines 613-680)
  - User database operations

### Frontend Authentication
- **Login Page**: `/frontend/src/pages/auth/Login.tsx` (217 lines)
  - Google OAuth button
  - Microsoft OAuth button

- **Auth Context**: `/frontend/src/contexts/AuthContext.tsx` (144 lines)
  - State management for user and token

- **API Client**: `/frontend/src/services/api.ts` (341 lines)
  - Axios interceptors
  - Request/response handling

---

## 3. AUTHENTICATION FLOW - QUICK DIAGRAM

### OAuth (Google/Microsoft) Flow
```
User clicks "Sign in with Google/Microsoft"
        ↓
Provider popup opens
        ↓
User authenticates with provider
        ↓
Frontend receives ID token
        ↓
POST /auth/google (or /auth/microsoft) with token
        ↓
Backend verifies token signature
        ↓
Backend checks/creates user in database
        ↓
Backend returns JWT access_token
        ↓
Frontend stores token in localStorage
        ↓
Frontend fetches GET /auth/me to get user profile
        ↓
Frontend stores user data in localStorage
        ↓
User redirected to dashboard
```

### Protected API Call Flow
```
Frontend makes request to /api/some-endpoint
        ↓
Request Interceptor adds: Authorization: Bearer {token}
        ↓
Backend receives request
        ↓
get_current_user() dependency validates token:
  - Extract token from header
  - Verify JWT signature
  - Check expiration
  - Query user from database
  - Check is_active status
        ↓
If valid → proceed with endpoint
If invalid → return 401 or 403
        ↓
If 401 response → Response Interceptor clears localStorage
        ↓
Frontend redirected to /login
```

---

## 4. ENVIRONMENT VARIABLES NEEDED

### Backend (.env)
```bash
# REQUIRED FOR AUTHENTICATION
JWT_SECRET_KEY=your-super-secret-key-at-least-32-chars
ENCRYPTION_KEY=your-encryption-key

# For Google OAuth
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx

# For Microsoft OAuth  
MICROSOFT_CLIENT_ID=xxxxx-xxxxx-xxxxx
MICROSOFT_CLIENT_SECRET=xxxxx

# Database (defaults to SQLite)
DATABASE_URL=sqlite:///./tales.db
# Or PostgreSQL:
DATABASE_URL=postgresql://user:password@localhost/dbname

# Admin email (auto-activated on first OAuth login)
ADMIN_EMAIL=admin@yourlab.gov
```

### Frontend (.env)
```bash
# Backend URL
VITE_API_URL=http://localhost:8000

# For Google OAuth
VITE_GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com

# For Microsoft OAuth
VITE_MICROSOFT_CLIENT_ID=xxxxx-xxxxx-xxxxx
```

---

## 5. DEBUGGING LOGIN ISSUES

### Check if user is in database
```python
# In backend Python shell
from app import models
from app.database import SessionLocal

db = SessionLocal()
user = db.query(models.User).filter(models.User.email == "user@example.com").first()

if user:
    print(f"User ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Active: {user.is_active}")
    print(f"Admin: {user.is_admin}")
    print(f"Tenant ID: {user.tenant_id}")
    print(f"Has password: {user.hashed_password is not None}")
    print(f"OAuth Provider: {user.oauth_provider}")
```

### Check tokens in browser
```javascript
// In browser console
localStorage.getItem('tales_access_token')  // Get JWT token
localStorage.getItem('tales_user')          // Get user data
JSON.parse(localStorage.getItem('tales_user')) // Parse user object
```

### Check database connections
```bash
# For SQLite
ls -la tales.db
file tales.db

# For PostgreSQL
psql -U user -d dbname -c "SELECT COUNT(*) FROM users;"
```

### Monitor API requests
1. Open browser DevTools (F12)
2. Go to Network tab
3. Try to login
4. Look for POST requests to `/auth/login`, `/auth/google`, `/auth/microsoft`
5. Check response status codes and error messages

---

## 6. USER STATUS MEANINGS

| Field | Value | Meaning |
|-------|-------|---------|
| `is_active` | false | User hasn't been approved by admin yet - cannot login |
| `is_active` | true | User can login |
| `is_admin` | false | Regular user |
| `is_admin` | true | Admin user (can manage other users) |
| `is_invited` | false | User registered or created by admin |
| `is_invited` | true | User was sent an invitation email |
| `hashed_password` | NULL | OAuth-only user (no password) |
| `hashed_password` | (value) | Email/password user |
| `oauth_provider` | NULL | Email/password only |
| `oauth_provider` | "google" | Can use Google OAuth |
| `oauth_provider` | "microsoft" | Can use Microsoft OAuth |

---

## 7. TOKEN EXPIRATION & REFRESH

### JWT Token Lifetime
- **Expiration**: 7 days (604,800 minutes)
- **Algorithm**: HS256
- **Key**: JWT_SECRET_KEY environment variable
- **Payload**: `{"sub": user_id, "exp": expiration_time}`

### How Tokens Expire
```javascript
// Token created with expiration timestamp
const exp = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60)

// When token used, backend checks:
const now = Math.floor(Date.now() / 1000)
if (now > token.exp) {
  // Token expired
  return 401 Unauthorized
}
```

### What to do when token expires
1. User gets 401 Unauthorized
2. Response interceptor clears localStorage
3. Frontend redirects to /login
4. User must login again

**No automatic refresh!** Users must login again after 7 days.

---

## 8. IMPORTANT CONFIGURATION DETAILS

### CORS Configuration (Backend)
```python
# In /app/main.py
allow_origins=[
    "http://localhost:5173",        # Local dev
    # Production origins are configured via FRONTEND_URL and the
    # ALLOWED_ORIGINS env var (comma-separated), not hardcoded here.
]
```

If deploying to a new domain, this list needs to be updated!

### Tenant Assignment Logic
```python
# From /app/auth.py get_tenant_id_for_email()
domain_to_tenant = {
    # Add lab-specific mappings here, e.g.:
    # 'mylab.gov': 'My Lab',
}

# If email domain not found, use default "Default" tenant.
# Creates tenant automatically if doesn't exist.
```

### Admin Email
```python
# From /app/auth.py
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

# Only this email is auto-activated on first OAuth login
# All other new users require admin approval
```

---

## 9. MOST COMMON LOGIN PROBLEMS

### Problem 1: "Account is not active" (403)
**Cause**: User exists but `is_active=false`
**Fix**: Admin must approve user
```python
# Admin in backend
from app import crud, schemas
db = SessionLocal()
admin_update = schemas.UserAdminUpdate(is_active=True)
crud.admin_update_user(db, user_id=user.id, user_update=admin_update)
```

### Problem 2: "Incorrect email or password" (401)
**Cause**: Wrong credentials or OAuth user trying password login
**Debug**:
```python
# Check if user exists
user = db.query(models.User).filter(models.User.email == email).first()
# Check if they have a password
print(user.hashed_password is not None)
# Check OAuth provider
print(user.oauth_provider)
```

### Problem 3: Login succeeds but redirects back to /login
**Cause**: Token stored but GET /auth/me failing
**Debug**:
1. Check Network tab: is GET /auth/me returning 200?
2. Check if token in localStorage: `localStorage.getItem('tales_access_token')`
3. Check for CORS errors in console
4. Check if frontend domain is in CORS whitelist

### Problem 4: CORS error "Access-Control-Allow-Origin"
**Cause**: Frontend domain not in backend CORS whitelist
**Fix**: Update `allow_origins` in `/app/main.py`

### Problem 5: "Invalid Google token" or "Invalid Microsoft token"
**Cause**: Client ID/secret misconfigured or wrong issuer
**Debug**:
```python
# In backend, check the verify functions in /app/auth.py
# Make sure GOOGLE_CLIENT_ID and MICROSOFT_CLIENT_ID are set
print(os.getenv("GOOGLE_CLIENT_ID"))
print(os.getenv("MICROSOFT_CLIENT_ID"))
```

---

## 10. ADMIN USER MANAGEMENT ENDPOINTS

### List All Users
```bash
GET /admin/users
Authorization: Bearer {admin_token}
```

### Approve a User
```bash
PUT /admin/users/{user_id}
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "is_active": true
}
```

### Delete a User
```bash
DELETE /admin/users/{user_id}
Authorization: Bearer {admin_token}
```

### Invite User with Temp Password
```bash
POST /admin/users/invite
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "email": "newuser@example.com",
  "full_name": "New User",
  "organization": "Company"
}

# Returns user with is_active=true and temporary password
```

---

**Last Updated**: November 9, 2025
**Quick Reference for**: Tales Login System Investigation
