# Migration Guide: Fixing Login & Data Leakage Issues

This guide walks you through fixing the double login popup and data leakage issues in the Tales project.

## Issues Fixed

1. **Double Login Popup** - Removed Google One Tap to show single login prompt
2. **Data Leakage** - Removed orphaned PPPL data visible to all users
3. **Future Prevention** - Added database constraints to prevent orphaned records

## Quick Summary of Changes

### Frontend Changes
- **Login.tsx** - Removed `useOneTap` prop from GoogleLogin component
- **AuthContext.tsx** - Added clarifying comments to auth flow

### Backend Changes
- **seed_db.py** - DELETED (was creating orphaned data)
- **Database migrations** - Created scripts to clean up orphaned data and add constraints
- **Test script** - Added user isolation verification tests

### Database Changes
- Orphaned records removed (queries, descriptors, competitors without user_id)
- NOT NULL constraints added to user_id columns
- Migration tracking table added

## Pre-Migration Checklist

Before running migrations, ensure:

- [ ] **Backup your database** (migrations do this automatically, but better safe than sorry)
- [ ] **Stop the application** (both frontend and backend)
- [ ] **You have Python 3 installed** (for migration scripts)
- [ ] **You're on the correct database** (local for testing, production for deployment)

## Step-by-Step Migration Process

### Step 1: Test Frontend Changes Locally

1. **Start the frontend** to see the single login:
   ```bash
   cd frontend
   npm run dev
   ```

2. **Test login flow**:
   - Navigate to login page
   - Should see ONLY ONE Google login button (no auto-popup)
   - Click "Sign in with Google"
   - Complete authentication
   - Should redirect to dashboard

3. **Expected result**: Single login popup, no duplicate prompts

### Step 2: Backup Database

Even though migrations auto-backup, create a manual backup:

```bash
cd /Users/rachelkremen/Documents/Code/tales_project
cp tales.db tales.db.MANUAL_BACKUP_$(date +%Y%m%d_%H%M%S)
```

### Step 3: Run Migrations (DRY RUN FIRST)

Test what the migration will do WITHOUT actually doing it:

```bash
cd app/migrations
python run_migrations.py --dry-run
```

**Review the output** to understand what will change.

### Step 4: Run Migrations (FOR REAL)

Now run the actual migrations:

```bash
python run_migrations.py
```

**Expected output:**
```
============================================================
TALES PROJECT - DATABASE MIGRATION TOOL
============================================================
Database: /Users/rachelkremen/Documents/Code/tales_project/tales.db
Mode: EXECUTE
============================================================
Creating backup: tales.db.backup_20251031_123456
✓ Backup created successfully

Found 2 migration(s) to process:
  • Pending: 001_cleanup_orphaned_data.sql
  • Pending: 002_add_not_null_constraints.sql

Running migration: 001_cleanup_orphaned_data.sql
✓ Migration 001_cleanup_orphaned_data.sql applied successfully

Running migration: 002_add_not_null_constraints.sql
✓ Migration 002_add_not_null_constraints.sql applied successfully

============================================================
VERIFICATION: Checking for orphaned data...
============================================================
✓ queries: No orphaned records
✓ responses: No orphaned records
✓ competitors: No orphaned records
✓ target_descriptors: No orphaned records
✓ campaigns: No orphaned records
✓ cited_sources: No orphaned records
✓ reports: No orphaned records
✓ task_status: No orphaned records
✓ trends: No orphaned records
✓ analyses: No orphaned records

✓ All tables are clean - no orphaned data found!

============================================================
✓ Migration complete!
============================================================
```

### Step 5: Verify Database

Run the verification script:

```bash
cd /Users/rachelkremen/Documents/Code/tales_project/app
python test_user_isolation.py
```

**Expected output:**
```
============================================================
USER ISOLATION VERIFICATION TESTS
============================================================

============================================================
TEST 4: No orphaned data (NULL user_id)
============================================================
✓ queries: No orphaned records
✓ responses: No orphaned records
✓ competitors: No orphaned records
✓ target_descriptors: No orphaned records
... (all tables clean)
✓ TEST PASSED: No orphaned data found

... (more tests)

============================================================
✓ ALL TESTS PASSED!
============================================================

User isolation is working correctly:
  ✓ No orphaned data in database
  ✓ New users start with empty data
  ✓ Users cannot see each other's data
  ✓ Brand data is properly isolated
```

### Step 6: Start Backend and Test

1. **Start the backend**:
   ```bash
   cd /Users/rachelkremen/Documents/Code/tales_project
   # Activate virtual environment if using one
   # source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. **Test as existing user (robotrachel@gmail.com)**:
   - Login with your Google account
   - Verify your existing data is still there
   - Check queries, descriptors, competitors

3. **Test as new user**:
   - Login with a different Google account (or create test account)
   - Dashboard should be EMPTY
   - No queries, no descriptors, no competitors
   - No PPPL data visible
   - Prompted to create first brand

### Step 7: Test Creating New Data

As a new user:

1. **Create a brand**:
   - Go to brand management
   - Create "My Test Brand"
   - Set as active

2. **Create some queries**:
   - Add a few test queries
   - Verify they appear in your list

3. **Logout and login as different user**:
   - Should NOT see the other user's data
   - Should have empty dashboard again

### Step 8: Deploy to Production

Once local testing is complete:

1. **Deploy frontend changes**:
   ```bash
   cd frontend
   npm run build
   # Deploy to Render or your hosting service
   ```

2. **Deploy backend changes and run migrations**:
   ```bash
   # On your production server:
   cd /path/to/tales_project

   # Backup production database
   cp tales.db tales.db.PROD_BACKUP_$(date +%Y%m%d_%H%M%S)

   # Pull latest code
   git pull

   # Run migrations
   cd app/migrations
   python run_migrations.py

   # Verify
   python run_migrations.py --verify-only

   # Restart application
   # (depends on your deployment method - e.g., systemctl restart tales, etc.)
   ```

## Verification Checklist

After deployment, verify:

### Login Flow
- [ ] Single Google login popup (not two)
- [ ] Login completes successfully
- [ ] Redirects to dashboard after login
- [ ] No console errors

### Data Isolation
- [ ] Existing users see their own data
- [ ] New users see empty dashboard
- [ ] New users are NOT shown PPPL data
- [ ] Users cannot see each other's data

### Functionality
- [ ] Can create brands
- [ ] Can create queries
- [ ] Can create descriptors
- [ ] Can create competitors
- [ ] Can switch between brands
- [ ] Brand filtering works correctly

## Troubleshooting

### Migration Fails

**Problem:** Migration script errors out

**Solution:**
1. Check the error message
2. Restore from backup: `cp tales.db.backup_YYYYMMDD_HHMMSS tales.db`
3. Fix the issue
4. Try again

### Still See Double Login

**Problem:** Two Google popups still appear

**Solution:**
1. Clear browser cache and cookies
2. Clear localStorage: Open browser console, run `localStorage.clear()`
3. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
4. Try incognito/private window

### New Users Still See PPPL Data

**Problem:** New users see PPPL queries/descriptors

**Solution:**
1. Migration didn't run or failed
2. Run: `python run_migrations.py --verify-only`
3. Look for orphaned records
4. If found, re-run migration 001:
   ```bash
   python run_migrations.py --migration 001
   ```

### "NOT NULL constraint failed" Error

**Problem:** Can't create new records

**Solution:**
1. This means code is trying to create records without user_id
2. Check the CRUD function being called
3. Ensure user_id is passed to all create functions
4. Example fix:
   ```python
   # WRONG:
   crud.create_query(db, query=query_data)

   # CORRECT:
   crud.create_query(db, query=query_data, user_id=current_user.id)
   ```

### Database Locked Error

**Problem:** "Database is locked" during migration

**Solution:**
1. Stop the Tales application (backend)
2. Make sure no other processes are using the database
3. Run migration again

## Rollback Plan

If something goes catastrophically wrong:

### Rollback Frontend
```bash
cd frontend
git checkout HEAD~1 src/pages/auth/Login.tsx
git checkout HEAD~1 src/contexts/AuthContext.tsx
npm run build
# Redeploy
```

### Rollback Database
```bash
# Stop application
# Restore from backup
cp tales.db.MANUAL_BACKUP_YYYYMMDD_HHMMSS tales.db
# Restart application
```

### Rollback Backend
```bash
# Restore seed_db.py if needed (from git history)
git checkout HEAD~1 app/seed_db.py
```

## Files Changed

### Modified Files
- `frontend/src/pages/auth/Login.tsx` - Removed useOneTap
- `frontend/src/contexts/AuthContext.tsx` - Added comments

### Deleted Files
- `app/seed_db.py` - Removed entirely

### New Files
- `app/migrations/001_cleanup_orphaned_data.sql` - Cleanup migration
- `app/migrations/002_add_not_null_constraints.sql` - Constraint migration
- `app/migrations/run_migrations.py` - Migration runner
- `app/migrations/README.md` - Migration documentation
- `app/test_user_isolation.py` - Verification tests
- `MIGRATION_GUIDE.md` - This file

### Database Changes
- Deleted orphaned records (queries, descriptors, competitors with NULL user_id)
- Added NOT NULL constraints to user_id columns in all data tables
- Added schema_migrations table for tracking

## Post-Migration Monitoring

After deployment, monitor:

1. **User logins** - Should be smooth, single popup
2. **New user signups** - Dashboard should be empty
3. **Error logs** - Watch for "NOT NULL constraint" errors (indicates code bug)
4. **User feedback** - Ask users if they see any other users' data

## Support

If issues arise:

1. Check migration logs
2. Run verification tests: `python test_user_isolation.py`
3. Check application logs for errors
4. Restore from backup if needed
5. Review this guide for troubleshooting steps

## Success Criteria

Migration is successful when:

- ✓ Single login popup on login page
- ✓ New users see empty dashboard
- ✓ No PPPL data visible to new users
- ✓ Users cannot see each other's data
- ✓ All verification tests pass
- ✓ No orphaned records in database
- ✓ Application functions normally

---

**Migration created:** 2025-10-31
**Author:** Claude (AI Assistant)
**Review status:** Ready for deployment
