# Scripts Directory

This directory contains all utility and administrative scripts for the TALES project, organized by purpose.

## Directory Structure

### `/admin/`
Production administration and operational scripts:
- `analyze_responses.py` - Analyze collected AI responses for brand mentions
- `collect_responses.py` - Collect responses from AI platforms
- `generate_report.py` - Generate monthly brand analysis reports
- `compute_batch_analytics_render.py` - Compute batch analytics on Render
- `check_recommendations.py` - Validate recommendation data
- `check_server_db.py` - Check database server status
- `debug_dashboard.py` - Debug dashboard data issues
- `debug_leadership.py` - Debug leadership data issues

### `/migrations/`
Database migration and data transfer scripts:
- `add_invitation_fields.py` - Add invitation tracking fields
- `add_microsoft_id_column.py` - Add Microsoft OAuth ID column
- `export_data.py` - Export database data
- `fix_user_sequence.py` - Fix user ID sequence
- `import_to_postgres.py` - Import data to PostgreSQL
- `migrate_oauth.py` - Migrate OAuth authentication
- `migrate_production.py` - Migrate to production environment
- `migrate_tales_to_render.py` - Migrate TALES brand to Render
- `migrate_to_multiuser.py` - Migrate to multi-user setup
- `migrate_to_render.py` - General Render migration

### `/data/`
Data seeding, import, and export scripts:
- `export_sqlite_data.py` - Export SQLite database data
- `export_user_data.py` - Export user data (v1)
- `export_user_data_v2.py` - Export user data (v2)
- `import_competitors.py` - Import competitor data
- `import_descriptors.py` - Import brand descriptors
- `seed.py` - Seed initial database data
- `seed_historical_data.py` - Seed historical analytics data
- `upload_pppl_data.py` - Upload PPPL-specific data

### `/testing/`
Testing and debugging scripts:
- `test_analytics.py` - Test analytics endpoints
- `test_api_reports.py` - Test report API
- `test_api_responses.py` - Test response API
- `test_db_connection.py` - Test database connection
- `test_endpoints.py` - Test API endpoints
- `test_recommendations_api.py` - Test recommendations API

### `/archive/`
Deprecated or rarely-used cleanup scripts:
- `delete_all_responses.py` - Delete all collected responses
- `delete_today_responses.py` - Delete today's responses
- `keep_first_88_responses.py` - Keep only first 88 responses

## Usage

All scripts should be run from the project root directory:

```bash
# Example: Run data collection
python scripts/admin/collect_responses.py

# Example: Seed historical data
python scripts/data/seed_historical_data.py

# Example: Test database connection
python scripts/testing/test_db_connection.py
```

Most scripts require environment variables to be set (especially `DATABASE_URL`). Check each script for specific requirements.
