# Database Migrations

This directory contains SQL migration scripts to update the Tales database schema and fix data issues.

## Migration Files

- **001_cleanup_orphaned_data.sql** - Removes records without user_id (fixes data leakage)
- **002_add_not_null_constraints.sql** - Adds NOT NULL constraints to user_id columns (prevents future data leakage)

## Running Migrations

### Prerequisites

1. **BACKUP YOUR DATABASE FIRST!** (The script does this automatically, but you can also do it manually)
   ```bash
   cp tales.db tales.db.backup_$(date +%Y%m%d_%H%M%S)
   ```

### Quick Start

Run all pending migrations:
```bash
cd app/migrations
python run_migrations.py
```

### Options

**Dry run** (see what would happen without executing):
```bash
python run_migrations.py --dry-run
```

**Run specific migration**:
```bash
python run_migrations.py --migration 001
```

**Specify database path**:
```bash
python run_migrations.py --db-path /path/to/tales.db
```

**Verify database only** (no migrations):
```bash
python run_migrations.py --verify-only
```

**Skip automatic backup**:
```bash
python run_migrations.py --no-backup
```

## Migration Order

**IMPORTANT:** Migrations must be run in order:

1. **001_cleanup_orphaned_data.sql** - MUST run first to remove NULL user_id records
2. **002_add_not_null_constraints.sql** - MUST run after 001 (will fail if NULL values exist)

The migration runner automatically tracks which migrations have been applied and runs them in the correct order.

## What Each Migration Does

### 001_cleanup_orphaned_data.sql

**Purpose:** Fix data leakage by removing orphaned records

**What it does:**
- Deletes all records from data tables where `user_id IS NULL`
- These orphaned records were created by the old seed_db.py script
- Affects tables: queries, responses, competitors, target_descriptors, campaigns, cited_sources, reports, task_status, trends, analyses

**Why it's needed:**
- Orphaned records appear to all users, causing data leakage
- New users were seeing PPPL-specific data (queries, descriptors, competitors)
- Violates multi-tenant isolation requirements

**What gets deleted:**
- PPPL-specific seed data (22 queries, 14 descriptors, 6 competitors)
- Any other records without proper user association

### 002_add_not_null_constraints.sql

**Purpose:** Prevent future orphaned records

**What it does:**
- Adds `NOT NULL` constraint to `user_id` column in all data tables
- Uses SQLite table recreation method (create new → copy data → drop old → rename)
- Recreates all indexes after table migration

**Why it's needed:**
- Database will reject attempts to create records without user_id
- Prevents future data leakage bugs at the schema level
- Enforces multi-tenant data isolation

**Tables affected:**
- queries, responses, competitors, target_descriptors, campaigns, cited_sources, reports, task_status, trends, analyses

## Verification

After migrations complete, the script automatically verifies:
- ✓ No orphaned records remain (user_id IS NULL)
- ✓ All tables have proper constraints
- ✓ Indexes are recreated correctly

You can also manually verify:

```bash
# Check for orphaned records
python run_migrations.py --verify-only

# Or use SQLite directly
sqlite3 tales.db "SELECT COUNT(*) FROM queries WHERE user_id IS NULL;"
sqlite3 tales.db "SELECT COUNT(*) FROM competitors WHERE user_id IS NULL;"
sqlite3 tales.db "SELECT COUNT(*) FROM target_descriptors WHERE user_id IS NULL;"
```

All counts should be 0.

## Rollback

If something goes wrong:

1. **Stop the application**
2. **Restore from backup:**
   ```bash
   cp tales.db.backup_YYYYMMDD_HHMMSS tales.db
   ```
3. **Investigate the error**
4. **Fix the migration script if needed**
5. **Try again**

## Migration Tracking

The migration runner creates a `schema_migrations` table to track which migrations have been applied:

```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

You can check migration status:
```bash
sqlite3 tales.db "SELECT * FROM schema_migrations;"
```

## Adding New Migrations

To add a new migration:

1. Create a new SQL file with the next number: `003_description.sql`
2. Follow the format of existing migrations (include comments, transaction, verification queries)
3. Test with `--dry-run` first
4. Run on local database before production

## Safety Checklist

Before running migrations on production:

- [ ] Backup database manually
- [ ] Test on local development database first
- [ ] Run with `--dry-run` to review changes
- [ ] Stop the application during migration
- [ ] Run migrations: `python run_migrations.py`
- [ ] Verify results: `python run_migrations.py --verify-only`
- [ ] Test application functionality
- [ ] If any issues, restore from backup

## Troubleshooting

**Migration fails with "table already exists":**
- The migration may have partially completed
- Check `schema_migrations` table to see what was applied
- Restore from backup and try again

**Migration fails with "NOT NULL constraint failed":**
- You tried to run 002 before 001
- Run 001 first to clean up NULL values
- Then run 002

**Verification shows orphaned records after migration:**
- Migration 001 may not have run successfully
- Check the migration log for errors
- Run migration 001 again manually

**"Database is locked" error:**
- Stop the Tales application (both frontend and backend)
- Make sure no other processes are accessing the database
- Run migration again

## Questions?

See the main project documentation or contact the development team.
