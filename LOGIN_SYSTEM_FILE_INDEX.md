# Tales Login System - Complete File Index

## BACKEND AUTHENTICATION FILES

### Core Authentication Module
1. `/Users/rachelkremen/Documents/Code/tales_project/app/auth.py`
   - JWT token creation and verification
   - Password hashing (bcrypt)
   - Google OAuth token verification
   - Microsoft OAuth token verification
   - User creation/linking logic for OAuth
   - Tenant assignment by email domain
   - Current user dependency for protected routes

2. `/Users/rachelkremen/Documents/Code/tales_project/app/routers/auth.py`
   - POST /auth/register - User registration
   - POST /auth/login - Email/password login
   - POST /auth/google - Google OAuth login
   - POST /auth/microsoft - Microsoft OAuth login
   - GET /auth/me - Get current user info
   - PUT /auth/me - Update user profile

### Admin User Management
3. `/Users/rachelkremen/Documents/Code/tales_project/app/routers/users.py`
   - Admin user management endpoints
   - User invitations with temporary passwords
   - OAuth-only user creation
   - User status updates (activate/deactivate)
   - User deletion

### Database & ORM
4. `/Users/rachelkremen/Documents/Code/tales_project/app/models.py`
   - User model with OAuth fields, tenant assignment, password fields
   - Tenant model for multi-tenancy
   - All other data models (Query, Response, etc.)

5. `/Users/rachelkremen/Documents/Code/tales_project/app/database.py`
   - SQLAlchemy engine configuration
   - SQLite/PostgreSQL database URL handling
   - SessionLocal for database sessions
   - get_db() dependency function

6. `/Users/rachelkremen/Documents/Code/tales_project/app/crud.py`
   - User CRUD operations:
     - get_user_by_email()
     - get_user_by_id()
     - create_user()
     - update_user()
     - admin_update_user()

### Data Validation
7. `/Users/rachelkremen/Documents/Code/tales_project/app/schemas.py`
   - User schema definitions
   - OAuth login schemas (GoogleLogin, MicrosoftLogin)
   - Token response schema
   - Admin update schema

### Application Setup
8. `/Users/rachelkremen/Documents/Code/tales_project/app/main.py`
   - FastAPI app initialization
   - CORS configuration with origin whitelist
   - Router includes for auth endpoints

---

## FRONTEND AUTHENTICATION FILES

### Authentication Pages
1. `/Users/rachelkremen/Documents/Code/tales_project/frontend/src/pages/auth/Login.tsx`
   - Google OAuth login button
   - Microsoft OAuth login button
   - Error handling and loading states
   - Responsive UI with Material-UI

2. `/Users/rachelkremen/Documents/Code/tales_project/frontend/src/pages/auth/Register.tsx`
   - Email/password registration form
   - Form validation
   - Success/error messages
   - Redirect to login after registration

3. `/Users/rachelkremen/Documents/Code/tales_project/frontend/src/pages/auth/InviteAccept.tsx`
   - Invitation acceptance flow (if implemented)

### State Management & Contexts
4. `/Users/rachelkremen/Documents/Code/tales_project/frontend/src/contexts/AuthContext.tsx`
   - AuthProvider component
   - useAuth() hook
   - User state management
   - Auth methods: login, googleLogin, microsoftLogin, register, logout, refreshUser
   - Token and user storage/retrieval from localStorage

### API Client
5. `/Users/rachelkremen/Documents/Code/tales_project/frontend/src/services/api.ts`
   - Axios instance configuration
   - Request interceptor (adds Authorization header)
   - Response interceptor (handles 401 errors)
   - authAPI object with methods:
     - login()
     - googleLogin()
     - microsoftLogin()
     - register()
     - getCurrentUser()
     - updateProfile()
     - logout()
     - getStoredUser()
     - getStoredToken()
     - isAuthenticated()

### Route Protection
6. `/Users/rachelkremen/Documents/Code/tales_project/frontend/src/components/ProtectedRoute.tsx`
   - Redirects unauthenticated users to /login
   - Redirects non-admin users from admin routes
   - Shows loading spinner during auth check

---

## CONFIGURATION FILES

### Backend Configuration
1. `/Users/rachelkremen/Documents/Code/tales_project/.env`
   - JWT_SECRET_KEY - Secret for signing JWT tokens
   - GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET - Google OAuth credentials
   - MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET - Microsoft OAuth credentials
   - ADMIN_EMAIL - Email that becomes admin on first OAuth login
   - DATABASE_URL - Database connection string
   - ENCRYPTION_KEY - For API key encryption
   - SMTP configuration - For sending emails
   - Redis and analytics settings

2. `/Users/rachelkremen/Documents/Code/tales_project/.env.example`
   - Template for backend environment variables

### Frontend Configuration
3. `/Users/rachelkremen/Documents/Code/tales_project/frontend/.env`
   - VITE_API_URL - Backend API base URL
   - VITE_GOOGLE_CLIENT_ID - Google OAuth client ID
   - VITE_MICROSOFT_CLIENT_ID - Microsoft OAuth client ID

4. `/Users/rachelkremen/Documents/Code/tales_project/frontend/.env.example`
   - Template for frontend environment variables

---

## KEY CONFIGURATION CONSTANTS

### Backend Auth Configuration (`app/auth.py`)
- SECRET_KEY (from JWT_SECRET_KEY env var)
- ALGORITHM: "HS256"
- ACCESS_TOKEN_EXPIRE_MINUTES: 60 * 24 * 7 (1 week / 604,800 minutes)
- GOOGLE_CLIENT_ID (from env)
- GOOGLE_CLIENT_SECRET (from env)
- MICROSOFT_CLIENT_ID (from env)
- MICROSOFT_CLIENT_SECRET (from env)
- ADMIN_EMAIL: e.g. "admin@yourlab.gov" (from env; empty by default)
- ENCRYPTION_KEY (from env, auto-generated if missing)

### Frontend Configuration (`services/api.ts`)
- API_BASE_URL: import.meta.env.VITE_API_URL or 'http://localhost:8000'
- TOKEN_KEY: 'tales_access_token'
- USER_KEY: 'tales_user'

### Microsoft OAuth Configuration (`pages/auth/Login.tsx`)
- clientId: VITE_MICROSOFT_CLIENT_ID
- authority: 'https://login.microsoftonline.com/common'
- redirectUri: window.location.origin
- cacheLocation: 'localStorage'

---

## DATABASE INITIALIZATION

The application auto-creates tables on startup via:
```
models.Base.metadata.create_all(bind=engine)
```

This is called in `app/main.py` and ensures all models are available before the app starts.

---

## CRITICAL ENDPOINTS SUMMARY

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| /auth/register | POST | No | New user registration |
| /auth/login | POST | No | Email/password authentication |
| /auth/google | POST | No | Google OAuth authentication |
| /auth/microsoft | POST | No | Microsoft OAuth authentication |
| /auth/me | GET | Yes | Get current user profile |
| /auth/me | PUT | Yes | Update user profile |
| /admin/users | GET | Yes (Admin) | List all users |
| /admin/users/invite | POST | Yes (Admin) | Invite user with temp password |
| /admin/users/create-invite | POST | Yes (Admin) | Create OAuth-only user invite |
| /admin/users/{user_id} | PUT | Yes (Admin) | Update user status |
| /admin/users/{user_id} | DELETE | Yes (Admin) | Delete user |

---

## AUTHENTICATION TOKEN FLOW

### Token Storage (Frontend)
- Key: `tales_access_token` in localStorage
- Key: `tales_user` in localStorage for user object
- Cleared on logout or 401 response

### Token Usage (Frontend)
- Added to all API requests via axios interceptor
- Header format: `Authorization: Bearer {token}`

### Token Validation (Backend)
- Extracted from Authorization header
- Verified using JWT_SECRET_KEY
- Checked for expiration (7 days)
- Used to look up current user in database

---

## TENANT SYSTEM

### Multi-Tenancy Architecture
- All users assigned to a tenant via `user.tenant_id`
- Tenants created on first login based on email domain
- Domain mapping in `get_tenant_id_for_email()`:
  - Lab-specific email-domain → tenant mappings (configurable, none by default)
  - All others → "Default" tenant
- Users isolated by tenant_id in all queries

### Default Tenant
- Name: "Default"
- Primary Color: #75C9C8 (teal)
- Secondary Color: #665775 (purple)
- Created automatically if doesn't exist

---

**Report Generated**: November 9, 2025
**Scope**: Complete login/authentication system analysis
