# Tales Authentication System - Visual Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TALES APPLICATION                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────┐      ┌────────────────────────────────────┐
│       FRONTEND (React)           │      │     BACKEND (FastAPI)              │
│  /frontend/src                   │      │     /app                           │
├────────────────────────────────┤      ├────────────────────────────────────┤
│                                 │      │                                     │
│ Login.tsx                        │      │ routers/auth.py                    │
│ ├─ Google OAuth button           │  →   │ ├─ POST /auth/login               │
│ └─ Microsoft OAuth button        │  →   │ ├─ POST /auth/google              │
│                                 │  →   │ ├─ POST /auth/microsoft            │
│ AuthContext.tsx                 │      │ ├─ POST /auth/register             │
│ ├─ State: user, token            │      │ ├─ GET /auth/me                    │
│ └─ Methods: login, logout        │      │ └─ PUT /auth/me                    │
│                                 │      │                                     │
│ api.ts (axios)                   │      │ auth.py (Core Auth)                │
│ ├─ Request interceptor           │  ←   │ ├─ create_access_token()           │
│ │  └─ Add Authorization header   │      │ ├─ verify_token()                  │
│ └─ Response interceptor          │      │ ├─ authenticate_user()             │
│    └─ Handle 401 errors          │      │ ├─ get_current_user()              │
│                                 │      │ ├─ verify_google_token()           │
│ localStorage                     │      │ ├─ verify_microsoft_token()        │
│ ├─ tales_access_token            │      │ └─ get_or_create_oauth_user()     │
│ └─ tales_user                    │      │                                     │
│                                 │      │ models.py                           │
│                                 │      │ ├─ User model                      │
│                                 │      │ └─ Tenant model                    │
└────────────────────────────────┘      └────────────────────────────────────┘
         (Vite)                                   (Python)
```

## Authentication Flow - Email/Password

```
User enters email & password
            ↓
    [Login.tsx]
            ↓
    POST /auth/login
            ↓
    [auth.py router]
    authenticate_user()
            ↓
    Query user by email
            ↓
    Verify password (bcrypt)
            ↓
    Check is_active
            ├─ false → 403 Forbidden
            └─ true → continue
            ↓
    create_access_token()
    (JWT, 7 day expiration)
            ↓
    Return {access_token, token_type}
            ↓
    [AuthContext]
    Store token in localStorage
            ↓
    GET /auth/me (get user profile)
            ↓
    Store user in localStorage
            ↓
    Navigate to dashboard
```

## Authentication Flow - OAuth (Google/Microsoft)

```
User clicks "Sign in with Google/Microsoft"
            ↓
    [Login.tsx]
    OAuth provider popup
            ↓
    User authenticates with provider
            ↓
    Provider returns ID token
            ↓
    POST /auth/google (or /auth/microsoft)
            ↓
    [auth.py router]
    verify_google_token() OR verify_microsoft_token()
            ├─ Validate token signature
            └─ Extract user info (email, name, picture)
            ↓
    get_or_create_oauth_user()
            ├─ Look up by OAuth ID
            ├─ Look up by email
            ├─ Link to existing user OR
            └─ Create new user
            ↓
    get_tenant_id_for_email()
    (Assign tenant based on domain)
            ↓
    Check is_active
            ├─ false → 403 Forbidden (unless admin)
            └─ true → continue
            ↓
    create_access_token()
            ↓
    Return {access_token, token_type}
            ↓
    [AuthContext]
    Store token & user in localStorage
            ↓
    Navigate to dashboard
```

## Protected Route Access

```
Frontend accesses /dashboard
            ↓
    [ProtectedRoute]
    Check localStorage for token
            ├─ No token → Redirect to /login
            └─ Token exists → Continue
            ↓
    Make API request to /api/endpoint
            ↓
    [Request Interceptor]
    Add Authorization header
    "Authorization: Bearer {token}"
            ↓
    Backend receives request
            ↓
    [get_current_user() dependency]
    Extract token from header
            ↓
    verify_token()
    ├─ Check signature (uses JWT_SECRET_KEY)
    └─ Check expiration
            ↓
    Query user from database
            ↓
    Check is_active
            ├─ false → 403 Forbidden
            └─ true → Return user object
            ↓
    Endpoint executes with user context
            ↓
    Response to frontend
            ↓
    [Response Interceptor]
    Check status code
            ├─ 401 → Clear localStorage, redirect to /login
            └─ Other → Return response
```

## Database Schema - Key Tables

```
┌─────────────────────────────────────────────────────────────┐
│                      TENANTS TABLE                            │
├─────────────────────────────────────────────────────────────┤
│ id (PK)           │ Primary Key                               │
│ tenant_name       │ e.g., "Default", "Example Lab"           │
│ primary_color     │ Hex color (e.g., #75C9C8)                │
│ secondary_color   │ Hex color (e.g., #665775)                │
│ logo_url          │ Tenant branding                           │
│ created_at        │ Timestamp                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        USERS TABLE                            │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                   │ Primary Key                       │
│ tenant_id (FK)            │ Foreign Key to tenants.id        │
│ email (UNIQUE, INDEX)     │ User email address               │
│ hashed_password           │ bcrypt hash (NULL for OAuth)     │
│ full_name                 │ User's name                      │
│ organization              │ Organization they track          │
├─────────────────────────────────────────────────────────────┤
│ OAuth Fields:                                                 │
│ google_id (UNIQUE)        │ Google account ID                │
│ microsoft_id (UNIQUE)     │ Microsoft account ID             │
│ oauth_provider            │ 'google', 'microsoft', etc.      │
│ picture_url               │ Profile picture                  │
├─────────────────────────────────────────────────────────────┤
│ Status Fields:                                                │
│ is_active                 │ User can login? (default FALSE)  │
│ is_admin                  │ Admin privileges? (default FALSE)│
│ is_invited                │ Received invite? (default FALSE) │
├─────────────────────────────────────────────────────────────┤
│ Encrypted API Keys:                                           │
│ openai_api_key_encrypted  │ User's OpenAI key (Fernet)       │
│ anthropic_api_key_encrypted│ User's Anthropic key            │
│ gemini_api_key_encrypted  │ User's Gemini key                │
│ perplexity_api_key_encrypted│ User's Perplexity key          │
├─────────────────────────────────────────────────────────────┤
│ Timestamps:                                                   │
│ created_at                │ User registration time           │
│ updated_at                │ Last update time                 │
└─────────────────────────────────────────────────────────────┘
```

## User Activation Status States

```
┌──────────────────────────────────────────────────────────────┐
│ User Creation/Registration                                    │
└──────────────────────────────────────────────────────────────┘
            ↓
        is_active = false
        (CANNOT LOGIN)
            ↓
┌──────────────────────────────────────────────────────────────┐
│ Waiting for Admin Approval                                    │
│ User sees: "Account is not active. Contact admin for approval"│
└──────────────────────────────────────────────────────────────┘
            ↓ (Admin approves)
        PUT /admin/users/{user_id}
        Body: {is_active: true}
            ↓
        is_active = true
            ↓
┌──────────────────────────────────────────────────────────────┐
│ Active User (Can login)                                       │
│ Can access all endpoints with their user_id                  │
└──────────────────────────────────────────────────────────────┘
```

## Token Lifecycle

```
Token Creation:
  access_token = create_access_token(data={"sub": user.id})
  Token payload:
  {
    "sub": 42,              // User ID
    "exp": 1699...         // Expiration timestamp (7 days from now)
    "iat": 1699...         // Issued at timestamp
  }
  Signed with: JWT_SECRET_KEY using HS256 algorithm

Token Storage (Frontend):
  localStorage.setItem('tales_access_token', access_token)

Token Usage:
  Authorization: Bearer {access_token}
  Added to all API requests via axios interceptor

Token Validation (Backend):
  1. Extract token from Authorization header
  2. Verify signature (using JWT_SECRET_KEY)
  3. Decode payload
  4. Check expiration (now < token.exp)
  5. Extract user_id from token.sub
  6. Query user from database
  7. Check is_active status
  8. Return user object or raise 401/403

Token Expiration:
  After 7 days:
    - Token becomes invalid
    - Backend returns 401 Unauthorized
    - Frontend response interceptor clears localStorage
    - User redirected to /login
    - User must login again
```

## Environment Variables Required

```
BACKEND (.env)
──────────────────────────────────────────────────────────────
JWT_SECRET_KEY                      ← Secret for token signing
GOOGLE_CLIENT_ID                    ← Google OAuth client ID
GOOGLE_CLIENT_SECRET                ← Google OAuth secret
MICROSOFT_CLIENT_ID                 ← Microsoft OAuth client ID
MICROSOFT_CLIENT_SECRET             ← Microsoft OAuth secret
ADMIN_EMAIL                         ← Email auto-activated as admin
ENCRYPTION_KEY                      ← For API key encryption
DATABASE_URL                        ← Database connection (SQLite/PostgreSQL)

FRONTEND (.env)
──────────────────────────────────────────────────────────────
VITE_API_URL                        ← Backend API base URL
VITE_GOOGLE_CLIENT_ID               ← Google OAuth client ID
VITE_MICROSOFT_CLIENT_ID            ← Microsoft OAuth client ID
```

## Common Error Messages

```
╔══════════════════════════════════════════════════════════════╗
║                    ERROR MESSAGES                             ║
╠══════════════════════════════════════════════════════════════╣
║ 401 Unauthorized                                              ║
║ Detail: "Incorrect email or password"                        ║
║ Cause: Wrong credentials or user doesn't exist              ║
╠──────────────────────────────────────────────────────────────╣
║ 403 Forbidden                                                 ║
║ Detail: "Account is not active..."                           ║
║ Cause: User created but not approved by admin               ║
╠──────────────────────────────────────────────────────────────╣
║ 400 Bad Request                                               ║
║ Detail: "Email not verified with Google"                    ║
║ Cause: Google account email not verified                    ║
╠──────────────────────────────────────────────────────────────╣
║ 401 Unauthorized                                              ║
║ Detail: "Invalid Google token"                              ║
║ Cause: Token expired, tampered, or client ID wrong         ║
╠──────────────────────────────────────────────────────────────╣
║ 401 Unauthorized                                              ║
║ Detail: "Could not validate credentials"                    ║
║ Cause: JWT invalid, expired, or JWT_SECRET_KEY wrong       ║
╚══════════════════════════════════════════════════════════════╝
```

## Key Authentication Constants

```
Token Expiration:
  ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 = 10,080 minutes = 7 days

JWT Algorithm:
  ALGORITHM = "HS256"

Default Admin Email:
  ADMIN_EMAIL = "admin@yourlab.gov"  # configured per deployment; empty by default

Default Tenant:
  tenant_name = "Default"
  primary_color = "#003e60"
  secondary_color = "#75c9c8"

Tenant Domain Mapping:
  (none by default — admins can add lab-specific email-domain → tenant
   mappings in app/auth.py:get_tenant_id_for_email().
   Unmatched domains fall back to the "Default" tenant.)

Token Storage Keys (localStorage):
  "tales_access_token" → JWT token
  "tales_user" → User object (JSON)
```

## Security Features

```
PASSWORD SECURITY
  ├─ Uses bcrypt hashing
  ├─ Automatic salt generation
  ├─ Never stored in plaintext
  └─ Time-safe comparison (prevents timing attacks)

JWT SECURITY
  ├─ Signed with JWT_SECRET_KEY
  ├─ HS256 algorithm
  ├─ Expiration enforced (7 days)
  ├─ Stored in HTTP-only recommended (currently localStorage)
  └─ Bearer token format in Authorization header

OAUTH SECURITY
  ├─ Token signature verification
  ├─ Email verification required
  ├─ Issuer validation
  ├─ Automatic user creation/linking
  └─ Only admin auto-activated

USER ISOLATION
  ├─ All data filtered by user_id
  ├─ Multi-tenant isolation by tenant_id
  ├─ API keys encrypted with Fernet
  └─ User status (is_active) enforced

CORS SECURITY
  ├─ Whitelist of allowed origins
  ├─ Credentials enabled for valid origins
  └─ Only pre-approved domains can access API

ADMIN PROTECTION
  ├─ Only one email auto-activated as admin
  ├─ get_current_admin_user() dependency for admin routes
  └─ Users can't delete their own account
```

## Related Documentation

See the other documentation files in this directory:
- **LOGIN_SYSTEM_INVESTIGATION.md** - Complete detailed reference
- **LOGIN_SYSTEM_FILE_INDEX.md** - File paths and structure
- **LOGIN_SYSTEM_QUICK_REFERENCE.md** - Developer quick guide

---

Generated: November 9, 2025
Tales Application - Authentication System
