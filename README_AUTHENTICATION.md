# Tales Application Authentication Investigation

## Overview

This directory contains a comprehensive investigation and documentation of the Tales application's login and authentication system. If you're experiencing login issues or need to understand how authentication works in this application, start here.

## Documentation Files

### 1. Start Here: AUTHENTICATION_SYSTEM_OVERVIEW.md
**Best for**: Getting a visual understanding of the system
- System architecture diagrams
- Authentication flow diagrams (Email/Password and OAuth)
- Database schema diagrams
- Token lifecycle
- Error messages reference

**When to read**: First time understanding the system

---

### 2. For Developers: LOGIN_SYSTEM_QUICK_REFERENCE.md
**Best for**: Quick lookup while developing or debugging
- Endpoint reference with examples
- Debugging commands
- Common problems and solutions
- Code locations
- Environment variables

**When to read**: While debugging login issues or making changes

---

### 3. For Details: LOGIN_SYSTEM_INVESTIGATION.md
**Best for**: Comprehensive technical reference
- Complete endpoint documentation
- Authentication utilities explained
- Frontend components detailed
- Database models documented
- Troubleshooting guide
- Security considerations

**When to read**: Need complete technical details

---

### 4. For Navigation: LOGIN_SYSTEM_FILE_INDEX.md
**Best for**: Finding where things are in the codebase
- All authentication files listed
- File paths and purposes
- Configuration constants
- Endpoint summary table

**When to read**: Looking for a specific file or endpoint

---

## Quick Start

### If users cannot login:

1. **Check error message**
   - Look at the exact error in the browser console
   - Go to LOGIN_SYSTEM_QUICK_REFERENCE.md Section 9

2. **Most common cause**
   - New users are created with `is_active=false`
   - Admin must approve users in the admin panel
   - See "Problem 1: Account is not active" in quick reference

3. **Check environment variables**
   - JWT_SECRET_KEY must be set
   - GOOGLE_CLIENT_ID/SECRET or MICROSOFT_CLIENT_ID/SECRET
   - DATABASE_URL for database connection
   - See Environment Variables section in quick reference

4. **Check database**
   - Is users table created?
   - Do users have is_active=true?
   - Is there a default tenant?

---

## System Architecture

```
FRONTEND (React/TypeScript)          BACKEND (FastAPI/Python)
├─ Login.tsx                         ├─ routers/auth.py
├─ AuthContext.tsx                   ├─ auth.py
├─ api.ts (axios)                    ├─ models.py
└─ ProtectedRoute.tsx                └─ database.py

                 ↔ JWT Tokens
                 ↔ API Requests

DATABASE (SQLite/PostgreSQL)
├─ users table
├─ tenants table
└─ other tables
```

---

## Key Authentication Concepts

### User Activation Status
```
New User Created
    ↓
is_active = false (cannot login)
    ↓
Admin Approval Needed
    ↓
Admin sets is_active = true
    ↓
User can now login
```

### Token Flow
```
User logs in → Backend creates JWT token → Frontend stores in localStorage
              ↓
              Token sent with every API request
              ↓
              Backend validates token (signature, expiration, user status)
              ↓
              Endpoint executed with current user context
```

### Multi-Tenancy
```
User registers/logs in with email
              ↓
System extracts email domain
              ↓
Maps domain to tenant or uses default "Default"
              ↓
User assigned to that tenant
              ↓
All user data isolated by tenant_id
```

---

## Main Authentication Endpoints

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | /auth/register | No | Email/password registration |
| POST | /auth/login | No | Email/password login |
| POST | /auth/google | No | Google OAuth login |
| POST | /auth/microsoft | No | Microsoft OAuth login |
| GET | /auth/me | Yes | Get current user |
| PUT | /auth/me | Yes | Update user profile |
| GET | /admin/users | Admin | List all users |
| PUT | /admin/users/{id} | Admin | Update user status |

---

## Environment Variables Checklist

Before deploying, ensure these are set:

### Backend (.env)
- [ ] JWT_SECRET_KEY - Secret key for signing tokens
- [ ] ENCRYPTION_KEY - For encrypting stored API keys
- [ ] GOOGLE_CLIENT_ID - From Google Cloud Console
- [ ] GOOGLE_CLIENT_SECRET - From Google Cloud Console
- [ ] MICROSOFT_CLIENT_ID - From Azure App Registration
- [ ] MICROSOFT_CLIENT_SECRET - From Azure App Registration
- [ ] ADMIN_EMAIL - Email to auto-activate as admin
- [ ] DATABASE_URL - Database connection string (or leave blank for SQLite)

### Frontend (.env)
- [ ] VITE_API_URL - Backend API URL
- [ ] VITE_GOOGLE_CLIENT_ID - From Google Cloud Console
- [ ] VITE_MICROSOFT_CLIENT_ID - From Azure App Registration

---

## Code Locations Quick Reference

**Backend**
- Core auth: `/app/auth.py` (395 lines)
- Routes: `/app/routers/auth.py` (174 lines)
- Models: `/app/models.py` (User, Tenant)
- Database: `/app/database.py`
- CRUD: `/app/crud.py` (User operations)

**Frontend**
- Login page: `/frontend/src/pages/auth/Login.tsx`
- State: `/frontend/src/contexts/AuthContext.tsx`
- API: `/frontend/src/services/api.ts`
- Route guard: `/frontend/src/components/ProtectedRoute.tsx`

---

## Troubleshooting Checklist

### Symptom: 401 Unauthorized "Incorrect email or password"
- [ ] User exists in database
- [ ] User has a password (not OAuth-only)
- [ ] Password is correct
- [ ] User is not trying OAuth-only account with password

### Symptom: 403 Forbidden "Account is not active"
- [ ] User is_active is true in database
- [ ] Admin approved the user
- [ ] User is not new/just registered

### Symptom: Login succeeds but redirects to /login
- [ ] Token saved in localStorage
- [ ] GET /auth/me request returns 200
- [ ] No CORS errors in console
- [ ] Frontend domain in CORS whitelist
- [ ] JWT_SECRET_KEY matches between deployments

### Symptom: OAuth fails with "Invalid token"
- [ ] Client ID/Secret are correct
- [ ] Email verified with provider
- [ ] Token not expired
- [ ] Correct issuer validation

### Symptom: CORS error
- [ ] Frontend domain in allow_origins in main.py
- [ ] For new domains, update app/main.py

---

## Security Notes

1. **Passwords** - Hashed with bcrypt, never stored plaintext
2. **Tokens** - JWT with 7-day expiration, signed with JWT_SECRET_KEY
3. **API Keys** - Encrypted with Fernet cipher
4. **User Isolation** - All data filtered by user_id and tenant_id
5. **Admin Protection** - Only configured admin email auto-activated
6. **OAuth** - Signature verification and email verification required

---

## Related Files

- `TEST_LOGIN_FIXES.md` - Previous login issue fixes (October 2025)
- `MULTIUSER_AUTH_STATUS.md` - Multi-user authentication implementation
- `ENV_SETUP_GUIDE.md` - Environment setup instructions

---

## When to Use Each Document

| Task | Document |
|------|----------|
| Understand system overall | AUTHENTICATION_SYSTEM_OVERVIEW.md |
| Debug a specific issue | LOGIN_SYSTEM_QUICK_REFERENCE.md |
| Find exact code locations | LOGIN_SYSTEM_FILE_INDEX.md |
| Get complete technical details | LOGIN_SYSTEM_INVESTIGATION.md |
| Setup environment | .env.example files |

---

## Contact & Maintenance

These documents were generated on November 9, 2025 through analysis of:
- Backend authentication code (395 lines)
- Frontend components (600+ lines)
- Database models and schemas
- Environment configuration

All code is current as of the latest commit on the main branch.

---

**Last Updated**: November 9, 2025
**Scope**: Complete authentication system investigation
**Status**: Ready for troubleshooting and development
