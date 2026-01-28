# PostgreSQL Migration Guide for Render Deployment

This guide will help you migrate your TALES project from SQLite to PostgreSQL for production deployment on Render.

## What's Been Prepared

✅ **Code Changes Complete:**
- Added `psycopg2-binary` to `requirements.txt`
- Updated `app/database.py` to support both SQLite (local) and PostgreSQL (production)
- Created `export_sqlite_data.py` - Exports your SQLite data to JSON
- Created `import_to_postgres.py` - Imports JSON data into PostgreSQL
- Exported your current data to `sqlite_export.json` (2 users, 88 responses, 22 queries, etc.)

## Step-by-Step Migration Process

### Step 1: Create PostgreSQL Database on Render

1. Log into your [Render Dashboard](https://dashboard.render.com/)

2. Click **"New +"** and select **"PostgreSQL"**

3. Configure the database:
   - **Name**: `tales-database` (or your choice)
   - **Database**: `tales`
   - **User**: (auto-generated)
   - **Region**: Select same region as your web service
   - **PostgreSQL Version**: 16 (latest)
   - **Plan**: Choose based on your needs
     - **Free**: Good for testing (expires after 90 days, limited storage)
     - **Starter**: $7/month (recommended for production)

4. Click **"Create Database"**

5. Wait for the database to be created (takes 1-2 minutes)

6. Once created, go to the database's **Info** tab and copy the **Internal Database URL**
   - It will look like: `postgres://user:password@dpg-xxxxx/tales`

### Step 2: Configure Your Backend Service on Render

1. Go to your backend web service in Render

2. Click on **"Environment"** in the left sidebar

3. Add a new environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Paste the **Internal Database URL** you copied (the one starting with `postgres://`)

4. Click **"Save Changes"**

**Important**: Do NOT deploy yet! We need to import your data first.

### Step 3: Import Your Data to PostgreSQL

You have two options for importing your data:

#### Option A: Import Locally (Recommended for Testing)

1. Open a terminal on your local machine

2. Set the DATABASE_URL environment variable to your PostgreSQL connection string:
   ```bash
   export DATABASE_URL="postgresql://user:password@dpg-xxxxx/tales"
   ```
   Replace with your actual connection string (use the **External Database URL** from Render for local access)

3. Run the import script:
   ```bash
   cd "/Users/rachelkremen/Library/Mobile Documents/com~apple~CloudDocs/Documents/Code/tales_project"
   python3 import_to_postgres.py
   ```

4. Verify the import was successful - you should see:
   ```
   ✓ Data import completed successfully!
     - Users: 2
     - Brand Info: 1
     - Queries: 22
     - Responses: 88
     ...
   ```

#### Option B: Import via Render Shell

1. First, deploy your updated code to Render (with the new database.py changes)

2. Once deployed, open a Shell in your Render service:
   - Go to your backend service in Render
   - Click **"Shell"** in the top right
   - This opens a terminal in your deployed environment

3. Upload your export file:
   ```bash
   # First, you'll need to upload sqlite_export.json to your service
   # You can do this via the Render file manager or by including it in your repo temporarily
   ```

4. Run the import script:
   ```bash
   python import_to_postgres.py
   ```

### Step 4: Deploy Your Application

1. **Commit your changes** (if not already done):
   ```bash
   cd "/Users/rachelkremen/Library/Mobile Documents/com~apple~CloudDocs/Documents/Code/tales_project"
   git add requirements.txt app/database.py
   git commit -m "Add PostgreSQL support for production deployment"
   git push origin main
   ```

2. Render will automatically deploy your changes

3. Monitor the deploy logs to ensure everything works correctly

### Step 5: Verify the Migration

1. Visit your deployed application: `https://tales-tzgj.onrender.com`

2. Try logging in with Google OAuth

3. Check that your data is present:
   - Go to Dashboard - should show your metrics
   - Check Analytics pages - should show your responses
   - Verify Competitors and Queries are still there

## Troubleshooting

### Issue: "relation does not exist" error

**Solution**: The tables weren't created. The import script creates them automatically, but if you deployed before importing, you may need to:
1. Open Render Shell
2. Run: `python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"`

### Issue: OAuth still not working

**Solution**: Double-check Google Cloud Console:
1. **Authorized JavaScript origins**: `https://tales-tzgj.onrender.com`
2. **Authorized redirect URIs**: `https://tales-tzgj.onrender.com/auth/google/callback`

### Issue: Database connection timeout

**Solution**:
- Make sure you're using the **Internal Database URL** (starts with `postgres://`) in your Render environment variables
- Internal URLs are faster and don't count against external connection limits

### Issue: Data didn't import correctly

**Solution**:
1. Check the Render logs for errors
2. Verify DATABASE_URL is set correctly
3. Try re-running the import script
4. Check that `sqlite_export.json` has your data

## Important Notes

### Local Development
- Your local environment will continue to use SQLite (`tales.db`)
- Only production (Render) will use PostgreSQL
- This is handled automatically by the updated `database.py`

### Data Backup
- Keep `sqlite_export.json` as a backup
- Render provides automatic daily backups for paid PostgreSQL plans
- For free plans, periodically export your data

### Environment Variables Summary

**Backend Service on Render needs:**
- `DATABASE_URL` - PostgreSQL connection string from Render
- `GOOGLE_CLIENT_ID` - Your Google OAuth Client ID
- `GOOGLE_CLIENT_SECRET` - Your Google OAuth Client Secret
- `SECRET_KEY` - Your application secret key

**Frontend Service on Render needs:**
- `VITE_API_URL` - Your backend URL (e.g., `https://your-backend.onrender.com`)
- `VITE_GOOGLE_CLIENT_ID` - Your Google OAuth Client ID

## Next Steps

Once migration is complete:

1. ✅ Test all functionality thoroughly
2. ✅ Monitor application performance
3. ✅ Set up regular database backups (if on paid plan)
4. ✅ Remove `sqlite_export.json` and migration scripts from your repo (optional)

## Need Help?

If you encounter issues:
1. Check Render deploy logs
2. Check Render service logs
3. Verify all environment variables are set correctly
4. Ensure PostgreSQL database is running
5. Test database connection with a simple script

---

**Status**: Your local data has been exported and is ready for import. Follow the steps above to complete the migration.
