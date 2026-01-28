# Tales Application Login System Investigation Report

## Executive Summary
This report provides a comprehensive analysis of the login authentication system in the Tales application, a full-stack web application built with:
- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **Frontend**: React with TypeScript
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT tokens, Google OAuth, Microsoft OAuth

---

## 1. BACKEND AUTHENTICATION ENDPOINTS

### Authentication Router (`/app/routers/auth.py`)

#### 1.1 Email/Password Login
```
POST /auth/login
Request Body:
  - email (string): User email
  - password (string): User password

Response:
  - access_token (JWT): Valid for 7 days (604,800 minutes)
  - token_type: "bearer"

Status Codes:
  - 200 OK: Successful login
  - 401 UNAUTHORIZED: Invalid credentials or user doesn't exist
  - 403 FORBIDDEN: User account is inactive (pending admin approval)
```

#### 1.2 Google OAuth Login
```
POST /auth/google
Request Body:
  - token (string): Google ID token from frontend

Response:
  - access_token (JWT): Valid for 7 days
  - token_type: "bearer"

Status Codes:
  - 200 OK: Successful login or user created
  - 400 BAD_REQUEST: Email not verified with Google
  - 401 UNAUTHORIZED: Invalid Google token
  - 403 FORBIDDEN: User account inactive
```

#### 1.3 Microsoft OAuth Login
```
POST /auth/microsoft
Request Body:
  - token (string): Microsoft ID token from frontend

Response:
  - access_token (JWT): Valid for 7 days
  - token_type: "bearer"

Status Codes:
  - 200 OK: Successful login or user created
  - 400 BAD_REQUEST: Email not verified with Microsoft
  - 401 UNAUTHORIZED: Invalid Microsoft token
  - 403 FORBIDDEN: User account inactive
```

#### 1.4 User Registration (Email/Password)
```
POST /auth/register
Request Body:
  - email (string): User email
  - password (string): Password
  - full_name (optional): User's full name
  - organization (optional): Organization name

Response:
  - User object (id, email, full_name, etc.)

Status Codes:
  - 201 CREATED: User created (inactive - pending admin approval)
  - 400 BAD_REQUEST: Email already registered

Note: Newly registered users are INACTIVE by default (is_active=False)
Admin must approve users before they can access the system
```

#### 1.5 Get Current User Info
```
GET /auth/me
Authorization: Bearer {jwt_token}

Response:
  - Full User object (including admin status, active status, tenant_id)

Status Codes:
  - 200 OK: User info retrieved
  - 401 UNAUTHORIZED: Invalid or expired token
  - 403 FORBIDDEN: User account inactive
```

#### 1.6 Update User Profile
```
PUT /auth/me
Authorization: Bearer {jwt_token}
Request Body:
  - full_name (optional)
  - organization (optional)
  - openai_api_key (optional, encrypted)
  - anthropic_api_key (optional, encrypted)
  - gemini_api_key (optional, encrypted)
  - perplexity_api_key (optional, encrypted)

Response:
  - Updated User object

Status Codes:
  - 200 OK: Profile updated
  - 404 NOT_FOUND: User not found
  - 401 UNAUTHORIZED: Invalid token
```

---

## 2. AUTHENTICATION UTILITIES & MIDDLEWARE

### Core Auth Functions (`/app/auth.py`)

#### 2.1 JWT Token Management
- **create_access_token()**: Creates JWT tokens valid for 7 days
  - Uses HS256 algorithm
  - Payload: `{"sub": user_id, "exp": expiration_time}`
- **verify_token()**: Validates JWT signature and expiration
- **get_current_user()**: FastAPI dependency for protected routes
  - Validates JWT token
  - Checks if user is active
  - Returns User object or raises 401/403 exceptions

#### 2.2 Password Handling
- **get_password_hash()**: Uses bcrypt for secure hashing
- **verify_password()**: Compares plain password with bcrypt hash
- **authenticate_user()**: Validates email/password combination

#### 2.3 OAuth Token Verification
- **verify_google_token()**: 
  - Verifies Google ID token using google.oauth2 library
  - Checks email verification status
  - Returns: {email, name, picture, google_id, email_verified}
  
- **verify_microsoft_token()**:
  - Validates Microsoft ID token signature using RSA keys
  - Fetches public keys from Microsoft's discovery endpoint
  - Returns: {email, name, microsoft_id, email_verified}

#### 2.4 OAuth User Management
- **get_or_create_oauth_user()**:
  - Looks up user by OAuth provider ID
  - Links OAuth account to existing email account if found
  - Creates new user if needed
  - **Auto-activation logic**: Only the admin email is auto-activated
  - Other users require admin approval

#### 2.5 Tenant Assignment
- **get_tenant_id_for_email()**:
  - Determines tenant based on email domain
  - Domain mapping: `solsticehc.net` → Solstice Health Communications
  - Default: "RobotRachel" tenant for unmatched domains
  - Creates tenant if it doesn't exist

### Security Middleware
- **HTTPBearer**: Validates Bearer token format in Authorization header
- **CORS Configuration**: Allows requests from:
  - `http://localhost:5173` (local development)
  - `https://tales.robotrachel.com` (production)
  - `https://*.robotrachel.com` (all subdomains)
- Credentials enabled for cross-origin requests

---

## 3. FRONTEND AUTHENTICATION COMPONENTS

### Login Component (`/frontend/src/pages/auth/Login.tsx`)

**Features**:
- Google Login button (using @react-oauth/google)
- Microsoft Login button (using @azure/msal-browser)
- Error handling and loading states
- Responsive Material-UI design

**Flow**:
1. User clicks Google or Microsoft button
2. OAuth provider popup appears
3. User authenticates with provider
4. Frontend receives ID token
5. Sends token to backend (`POST /auth/google` or `/auth/microsoft`)
6. Receives JWT access token
7. Redirects to dashboard (`/`)

**Environment Variables**:
- `VITE_GOOGLE_CLIENT_ID`: Google OAuth client ID
- `VITE_MICROSOFT_CLIENT_ID`: Microsoft OAuth client ID (required for MSAL)

### AuthContext (`/frontend/src/contexts/AuthContext.tsx`)

**State Management**:
- `user`: Current authenticated user object
- `loading`: Initial auth check in progress
- `isAuthenticated`: Boolean based on token existence
- `isAdmin`: Boolean from user.is_admin

**Methods**:
- `login(email, password)`: Email/password login
- `googleLogin(googleToken)`: Google OAuth flow
- `microsoftLogin(microsoftToken)`: Microsoft OAuth flow
- `register(email, password, full_name, organization)`: New user registration
- `logout()`: Clear auth data
- `refreshUser()`: Fetch fresh user data from server

**Token Storage**:
- Token stored in localStorage with key `tales_access_token`
- User data stored in localStorage with key `tales_user`
- Tokens automatically included in all API requests via axios interceptor

### API Service (`/frontend/src/services/api.ts`)

**Configuration**:
- Base URL: `import.meta.env.VITE_API_URL` (default: `http://localhost:8000`)
- Axios instance with custom interceptors

**Request Interceptor**:
- Automatically adds `Authorization: Bearer {token}` header to all requests

**Response Interceptor**:
- Handles 401 responses by clearing auth and redirecting to `/login`
- Logs all errors to console

**Auth API Functions**:
- `login(email, password)`: Email/password authentication
- `googleLogin(googleToken)`: Google OAuth
- `microsoftLogin(microsoftToken)`: Microsoft OAuth
- `register()`: New user registration
- `getCurrentUser()`: Fetch user profile
- `updateProfile()`: Update user settings
- `logout()`: Clear local auth data
- `getStoredUser()`: Retrieve from localStorage
- `getStoredToken()`: Retrieve from localStorage
- `isAuthenticated()`: Check if token exists

### Protected Route Component (`/frontend/src/components/ProtectedRoute.tsx`)

**Functionality**:
- Wraps routes requiring authentication
- Redirects unauthenticated users to `/login`
- Redirects non-admin users away from admin routes
- Shows loading spinner during auth check

**Props**:
- `children`: Content to render if authenticated
- `requireAdmin`: If true, only admins can access

---

## 4. DATABASE MODELS

### User Model (`/app/models.py`)

```python
class User(Base):
    __tablename__ = "users"
    
    # Identification
    id: Integer (primary key)
    email: String(255, unique, indexed)
    full_name: String(200)
    organization: String(200)
    
    # Tenant (multi-tenancy)
    tenant_id: Integer (ForeignKey to tenants.id)
    
    # Authentication
    hashed_password: String(255) - nullable for OAuth users
    
    # Status
    is_admin: Boolean (default False)
    is_active: Boolean (default False) - must be approved by admin
    is_invited: Boolean (default False) - received invite email
    
    # OAuth Integration
    google_id: String(255, unique, nullable)
    microsoft_id: String(255, unique, nullable)
    oauth_provider: String(50) - 'google', 'microsoft', etc.
    picture_url: String(500) - profile picture from OAuth
    
    # Invitation System
    invitation_token: String(500, unique, nullable)
    invitation_expires_at: DateTime(nullable)
    
    # API Key Storage (encrypted)
    openai_api_key_encrypted: Text(nullable)
    anthropic_api_key_encrypted: Text(nullable)
    gemini_api_key_encrypted: Text(nullable)
    perplexity_api_key_encrypted: Text(nullable)
    
    # Timestamps
    created_at: DateTime
    updated_at: DateTime
```

### Tenant Model (`/app/models.py`)

```python
class Tenant(Base):
    __tablename__ = "tenants"
    
    id: Integer (primary key)
    tenant_name: String(200) - e.g., "RobotRachel", "Solstice Health Communications"
    subdomain: String(100, unique, nullable)
    logo_url: Text(nullable)
    primary_color: String(7) - hex color (default '#75C9C8')
    secondary_color: String(7) - hex color (default '#665775')
    custom_domain: String(255, nullable)
    created_at: DateTime
    updated_at: DateTime
```

---

## 5. USER SCHEMAS (Data Validation)

### UserCreate (Registration)
```python
- email: str (EmailStr)
- password: str
- full_name: Optional[str]
- organization: Optional[str]
```

### UserLogin (Email/Password Auth)
```python
- email: str (EmailStr)
- password: str
```

### GoogleLogin
```python
- token: str (Google ID token)
```

### MicrosoftLogin
```python
- token: str (Microsoft ID token)
```

### User (Response)
```python
- id: int
- email: str
- full_name: Optional[str]
- organization: Optional[str]
- is_admin: bool
- is_active: bool
- is_invited: bool
- created_at: datetime
- updated_at: datetime
```

### Token (OAuth Response)
```python
- access_token: str (JWT)
- token_type: str ("bearer")
```

---

## 6. ENVIRONMENT CONFIGURATION

### Backend (.env)

```bash
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ENCRYPTION_KEY=your-encryption-key-for-api-keys

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Admin Configuration
ADMIN_EMAIL=robotrachel@gmail.com

# Database
DATABASE_URL=sqlite:///./tales.db (or postgresql://...)

# Email (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=admin@example.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=admin@robotrachel.com
```

### Frontend (.env)

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# Google OAuth
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# Microsoft OAuth
VITE_MICROSOFT_CLIENT_ID=your-microsoft-client-id
```

---

## 7. CRITICAL AUTHENTICATION FLOW DIAGRAMS

### Email/Password Login Flow
```
Frontend (Login.tsx)
  ↓ (POST /auth/login with email, password)
Backend (auth.py router)
  ↓ authenticate_user()
  ├─ Query User by email
  ├─ Verify password with bcrypt
  └─ Check if user is active
  ↓ create_access_token()
  ├─ Create JWT with user.id
  └─ Return token
Frontend (AuthContext)
  ↓
  ├─ Store token in localStorage
  ├─ Fetch /auth/me for user data
  └─ Store user in localStorage
Frontend
  ↓ Navigate to dashboard
```

### OAuth (Google/Microsoft) Login Flow
```
Frontend (Login.tsx)
  ↓ (User clicks OAuth button)
  ├─ OAuth provider popup
  └─ User authenticates
  ↓ (Receive ID token)
  ↓ (POST /auth/google or /auth/microsoft)
Backend (auth.py)
  ↓ verify_google_token() OR verify_microsoft_token()
  ├─ Validate token signature
  └─ Extract user info
  ↓ get_or_create_oauth_user()
  ├─ Check if user exists by OAuth ID
  ├─ Check if user exists by email
  ├─ Create new user if needed
  └─ Link OAuth ID to user
  ↓ create_access_token()
Frontend (AuthContext)
  ↓
  ├─ Store token in localStorage
  ├─ Fetch /auth/me for user data
  └─ Store user in localStorage
Frontend
  ↓ Navigate to dashboard
```

### Protected Route Access
```
Frontend Router
  ↓ (User accesses protected route)
  ↓ ProtectedRoute component checks:
  ├─ Is user authenticated? (check localStorage token)
  ├─ If no token → redirect to /login
  └─ If admin required → check is_admin flag
  ↓ Request API endpoint
API Request Interceptor
  ↓ Add Authorization header: "Bearer {token}"
Backend Route Dependency
  ↓ get_current_user() dependency:
  ├─ Extract token from Authorization header
  ├─ Verify JWT signature
  ├─ Check expiration
  ├─ Query User by user_id from token
  └─ Check if user is active
  ↓ If all checks pass → proceed with endpoint
  ↓ If any check fails → return 401 or 403
Response Interceptor
  ↓ If 401 response:
  ├─ Clear localStorage
  └─ Redirect to /login
```

---

## 8. COMMON LOGIN ISSUES & TROUBLESHOOTING

### Issue 1: "Account is not active" Error (403)
**Cause**: User registered but hasn't been approved by admin yet
**Solution**: 
- User must wait for admin approval
- Admin should go to Admin panel → User Management
- Admin clicks on user and sets `is_active = true`

### Issue 2: "Incorrect email or password" (401)
**Possible Causes**:
- Email/password combination is wrong
- User doesn't exist
- User is OAuth-only (no password set, must use Google/Microsoft)

**Debug**:
- Check database: `SELECT * FROM users WHERE email = 'user@example.com'`
- Check `hashed_password` is NOT NULL for password-based users
- Check `oauth_provider` for OAuth-only users

### Issue 3: "Email not verified with Google/Microsoft" (400)
**Cause**: User authenticated with provider but email isn't marked as verified by that provider
**Solution**:
- User should verify email in their Google/Microsoft account
- Re-attempt login

### Issue 4: "Could not validate credentials" (401)
**Possible Causes**:
- JWT token expired (7 day expiration)
- Token signature invalid
- Token tampered with
- JWT_SECRET_KEY not set or mismatched between backend deployments

**Solution**:
- Clear browser localStorage
- Log out and log back in
- Check backend JWT_SECRET_KEY configuration

### Issue 5: OAuth Token Errors
**Google token errors**:
- Check `GOOGLE_CLIENT_ID` environment variable
- Verify localhost/domain in Google OAuth credentials
- Verify token issuer is `accounts.google.com`

**Microsoft token errors**:
- Check `MICROSOFT_CLIENT_ID` environment variable
- Verify Authority URL: `https://login.microsoftonline.com/common`
- Verify client app registration in Azure

### Issue 6: Token Stored but Redirects to Login
**Possible Causes**:
- Token expired (check localStorage expiration timestamp)
- API base URL misconfigured (VITE_API_URL)
- CORS issues preventing token validation request

**Debug**:
- Check browser Network tab: is `/auth/me` returning 200?
- Check browser Storage → localStorage for `tales_access_token`
- Check Frontend console for CORS errors

### Issue 7: CORS Errors During Login
**Cause**: Frontend origin not in CORS whitelist
**Current CORS whitelist**:
- `http://localhost:5173` (local dev)
- `https://tales.robotrachel.com`
- `https://*.robotrachel.com`

**Solution**:
- If deploying to new domain, update `CORSMiddleware` in `/app/main.py`
- Add domain to `allow_origins` list

---

## 9. ADMIN USER MANAGEMENT ENDPOINTS

### List All Users
```
GET /admin/users
Authorization: Bearer {admin_token}
Response: List[User]
```

### Invite User (create with temp password)
```
POST /admin/users/invite
Authorization: Bearer {admin_token}
Body: {email, full_name, organization}
Response: User (is_active=true)
```

### Create OAuth-only Invite
```
POST /admin/users/create-invite
Authorization: Bearer {admin_token}
Body: {email, full_name, organization, tenant_id}
Response: InvitationResponse
```

### Update User Status
```
PUT /admin/users/{user_id}
Authorization: Bearer {admin_token}
Body: {is_active, is_admin}
Response: User
```

### Delete User
```
DELETE /admin/users/{user_id}
Authorization: Bearer {admin_token}
Response: User (deleted)
```

---

## 10. KEY SECURITY CONSIDERATIONS

1. **Password Hashing**: Uses bcrypt with automatic salt generation
2. **JWT Secrets**: Stored in environment variables (not in code)
3. **Token Expiration**: 7-day expiration (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
4. **API Key Encryption**: User-provided API keys encrypted with Fernet (symmetric encryption)
5. **HTTPS Required**: Production deployments should enforce HTTPS
6. **CORS Whitelist**: Explicitly configured origins
7. **Admin Email Protection**: Only configured admin email is auto-activated for OAuth
8. **Tenant Isolation**: Users isolated by tenant_id in database queries
9. **OAuth Email Verification**: Requires email_verified flag from OAuth provider
10. **No Passwords in Logs**: Error messages don't expose sensitive info

---

## 11. LIKELY CAUSES OF CURRENT LOGIN ISSUE

Based on code analysis, here are the most probable causes of users unable to login:

1. **Database Not Initialized**
   - Tenants table might not exist or be empty
   - `get_tenant_id_for_email()` might fail if default tenant not created

2. **JWT_SECRET_KEY Not Set**
   - If environment variable missing, defaults to weak key
   - Token creation/verification will fail inconsistently

3. **CORS Configuration Mismatch**
   - Frontend domain not in `allow_origins` list in main.py
   - `/auth/me` request fails with CORS error after login

4. **OAuth Configuration Incomplete**
   - Google/Microsoft client IDs/secrets not configured
   - Tokens can't be verified, OAuth login fails

5. **User Account Status**
   - New users created with `is_active=False` by default
   - Admin must manually approve users before they can login

6. **Token Storage/Retrieval Issue**
   - Frontend not storing token in localStorage
   - API interceptor not adding Authorization header
   - Token validation request failing

7. **Database Connection Issues**
   - DATABASE_URL not configured for production
   - SQLite file permissions issue in production
   - PostgreSQL connection string incorrect

8. **Tenant Assignment Logic**
   - `get_tenant_id_for_email()` tries to create tenant on first login
   - If database transaction fails, user creation fails

---

## 12. FILES REFERENCED IN THIS REPORT

### Backend Authentication Files
- `/app/routers/auth.py` - Login endpoints
- `/app/auth.py` - Authentication utilities
- `/app/routers/users.py` - Admin user management
- `/app/models.py` - Database models
- `/app/schemas.py` - Data validation schemas
- `/app/database.py` - Database configuration
- `/app/crud.py` - User CRUD operations
- `/app/main.py` - FastAPI app setup with CORS

### Frontend Authentication Files
- `/frontend/src/pages/auth/Login.tsx` - Login component
- `/frontend/src/contexts/AuthContext.tsx` - Auth state management
- `/frontend/src/services/api.ts` - API client with interceptors
- `/frontend/src/components/ProtectedRoute.tsx` - Route protection
- `/frontend/src/pages/auth/Register.tsx` - Registration component

### Configuration Files
- `/.env` - Backend environment variables
- `/.env.example` - Backend environment template
- `/frontend/.env` - Frontend environment variables
- `/frontend/.env.example` - Frontend environment template

---

**Report Generated**: November 9, 2025
**Application**: Tales (Multi-tenant LLM Analytics)
**Version**: See recent commits (mainly using Google/Microsoft OAuth)
