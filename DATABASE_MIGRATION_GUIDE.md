# Database Migration Guide - Local to Render

This guide will help you migrate your local SQLite database (with all your TALES data and analysis) to your Render PostgreSQL database.

## Prerequisites

- Local `tales.db` file with your data
- Access to your Render dashboard
- Python environment with all dependencies installed

## Step-by-Step Migration Process

### Step 1: Get Your Render Database URL

1. Go to https://dashboard.render.com
2. Navigate to your **PostgreSQL database** service (not the backend web service)
3. Click on the database service
4. Look for **"External Database URL"** or **"Connection String"**
5. Copy the full URL (it looks like: `postgresql://user:password@host/database`)

**Important:** This is different from your backend web service. Make sure you're looking at the PostgreSQL database service.

### Step 2: Set the Environment Variable

In your terminal, set the database URL as an environment variable:

```bash
export RENDER_DATABASE_URL='postgresql://user:password@host/database'
```

Replace with your actual database URL from Step 1.

### Step 3: Run the Migration Script

```bash
python3 migrate_to_render.py
```

The script will:
1. Connect to both databases
2. Show you what will be migrated
3. Ask for confirmation
4. Migrate all tables in the correct order (respecting foreign keys)
5. Show a summary of migrated records

### Step 4: Verify the Migration

After migration completes, verify your data:

1. Go to https://tales.robotrachel.com
2. Log in with your credentials
3. Check that:
   - Your brand information appears
   - Your queries are present
   - Your collected responses are there
   - Your analysis results are available
   - Your reports exist

## What Gets Migrated

The script migrates all tables in this order:

1. **Users** - Your user accounts
2. **Brand Information** - Your brand profiles
3. **Brand Shares** - Shared brand access
4. **Queries** - All your data collection queries
5. **Competitors** - Competitor information
6. **Descriptors** - Brand descriptors
7. **Collection Batches** - Data collection batch metadata
8. **Responses** - All AI platform responses
9. **Analysis Results** - Analyzed response data
10. **Reports** - Generated reports
11. **Scheduled Tasks** - Monthly automation schedules
12. **Scheduled Task History** - Task execution history
13. **Task Statuses** - Current and recent task statuses

## Alternative: Direct PostgreSQL Connection

If you prefer a more manual approach:

### Option A: Using pg_dump (if you already have PostgreSQL locally)

```bash
# Export local data to SQL file
sqlite3 tales.db .dump > local_data.sql

# Convert SQLite SQL to PostgreSQL format (manual editing required)
# Then import to Render
psql $RENDER_DATABASE_URL < local_data_converted.sql
```

### Option B: Using DBeaver or pgAdmin

1. Install [DBeaver](https://dbeaver.io/) (free database tool)
2. Connect to your local SQLite database
3. Connect to your Render PostgreSQL database
4. Use DBeaver's data transfer wizard to migrate tables

## Troubleshooting

### Error: "RENDER_DATABASE_URL not set"

Make sure you've exported the environment variable:
```bash
export RENDER_DATABASE_URL='your-database-url'
```

### Error: "Connection refused" or "Authentication failed"

- Verify the database URL is correct
- Check that you copied the **External Database URL** (not internal)
- Ensure your IP is allowed (Render PostgreSQL accepts connections from anywhere by default)

### Error: "Duplicate key" or "Unique constraint violation"

This means data already exists in the target database. Options:
1. Clear the target database first (be careful!)
2. Modify the script to skip existing records
3. Start with a fresh Render database

### Migration runs but no data appears on site

1. Check if migration completed successfully (look for "✅ Migration complete!")
2. Verify you're logged in with the same credentials
3. Check Render backend logs for errors
4. Ensure the backend is using the correct DATABASE_URL

## Post-Migration

After successful migration:

1. **Test thoroughly** - Try all features on the production site
2. **Keep your local backup** - Don't delete `tales.db` yet
3. **Update scheduled tasks** - Verify they're working in production
4. **Check email notifications** - Ensure SMTP is configured in Render

## Need Help?

If you encounter issues:

1. Check the migration script output for specific errors
2. Check Render backend logs: Dashboard → tales-backend → Logs
3. Verify database connection: Dashboard → PostgreSQL database → Connections

## Database Management Tips

### Creating Backups on Render

Render PostgreSQL includes automatic daily backups (on paid plans), but you can also:

1. Use `pg_dump` to create manual backups:
```bash
pg_dump $RENDER_DATABASE_URL > backup_$(date +%Y%m%d).sql
```

2. Download backups from Render dashboard

### Viewing Database Contents

Use the Render dashboard's built-in SQL console:
1. Go to your PostgreSQL database service
2. Click "Access Console"
3. Run SQL queries to inspect data

Example queries:
```sql
-- Count users
SELECT COUNT(*) FROM users;

-- Count responses
SELECT COUNT(*) FROM responses;

-- View latest analysis results
SELECT * FROM analysis_results ORDER BY created_at DESC LIMIT 10;
```

## Security Notes

- **Never commit** your Render database URL to git
- Use environment variables for all sensitive credentials
- The migration script shows only the first 50 characters of the URL for security
- Keep your local `tales.db` as a backup until you're confident in the migration
