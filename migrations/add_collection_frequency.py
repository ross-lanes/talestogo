#!/usr/bin/env python3
"""
Migration: Add collection frequency and analysis tracking fields

This migration updates the scheduling system to support:
- Weekly or monthly data collection
- Separate tracking for monthly, quarterly, and annual analysis runs
- Period labels for reports

Changes:
1. ScheduledTask table:
   - Add collection_frequency ('weekly' or 'monthly')
   - Add last_collection_at, next_collection_at (replacing last_run_at, next_run_at)
   - Add last_monthly_analysis_at, last_quarterly_analysis_at, last_annual_analysis_at
   - Keep schedule_type for backward compatibility (will be deprecated)

2. Report table:
   - Add period_label for display (e.g., "Q1 2026", "January 2026")

Usage:
    DATABASE_URL="your_db_url" python3 migrations/add_collection_frequency.py
"""

import os
import sys
from sqlalchemy import create_engine, text


def run_migration(database_url: str):
    """Run the migration to add collection frequency fields."""

    engine = create_engine(database_url)

    print("="*70)
    print("MIGRATION: Add collection frequency and analysis tracking")
    print("="*70)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    print("="*70 + "\n")

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # Step 1: Add collection_frequency column
            print("Step 1: Adding collection_frequency column to scheduled_tasks...")
            conn.execute(text("""
                ALTER TABLE scheduled_tasks
                ADD COLUMN IF NOT EXISTS collection_frequency VARCHAR(20) DEFAULT 'monthly' NOT NULL
            """))
            print("  Added collection_frequency column with default 'monthly'\n")

            # Step 2: Add collection tracking columns
            print("Step 2: Adding collection tracking columns...")
            conn.execute(text("""
                ALTER TABLE scheduled_tasks
                ADD COLUMN IF NOT EXISTS last_collection_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS next_collection_at TIMESTAMP
            """))
            print("  Added last_collection_at and next_collection_at columns\n")

            # Step 3: Add analysis tracking columns
            print("Step 3: Adding analysis tracking columns...")
            conn.execute(text("""
                ALTER TABLE scheduled_tasks
                ADD COLUMN IF NOT EXISTS last_monthly_analysis_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS last_quarterly_analysis_at TIMESTAMP,
                ADD COLUMN IF NOT EXISTS last_annual_analysis_at TIMESTAMP
            """))
            print("  Added last_monthly_analysis_at, last_quarterly_analysis_at, last_annual_analysis_at columns\n")

            # Step 4: Add index on next_collection_at
            print("Step 4: Adding index on next_collection_at...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_collection
                ON scheduled_tasks(next_collection_at)
            """))
            print("  Added index idx_scheduled_tasks_next_collection\n")

            # Step 5: Migrate existing data from legacy columns
            print("Step 5: Migrating existing schedule data...")
            result = conn.execute(text("""
                UPDATE scheduled_tasks
                SET
                    last_collection_at = last_run_at,
                    next_collection_at = next_run_at
                WHERE last_run_at IS NOT NULL OR next_run_at IS NOT NULL
            """))
            print(f"  Migrated {result.rowcount} existing scheduled tasks\n")

            # Step 6: Add period_label column to reports
            print("Step 6: Adding period_label column to reports table...")
            conn.execute(text("""
                ALTER TABLE reports
                ADD COLUMN IF NOT EXISTS period_label VARCHAR(100)
            """))
            print("  Added period_label column\n")

            # Step 7: Update existing reports with period labels based on report_type
            print("Step 7: Updating existing reports with period labels...")
            # For monthly reports, set label based on start_date
            conn.execute(text("""
                UPDATE reports
                SET period_label = TO_CHAR(start_date, 'FMMonth YYYY')
                WHERE report_type = 'monthly'
                  AND start_date IS NOT NULL
                  AND period_label IS NULL
            """))
            # For all_data reports, set a generic label
            conn.execute(text("""
                UPDATE reports
                SET period_label = 'All Data Report'
                WHERE report_type = 'all_data'
                  AND period_label IS NULL
            """))
            print("  Updated existing reports with period labels\n")

            # Commit transaction
            trans.commit()

            print("="*70)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("="*70)
            print("\nChanges made to scheduled_tasks:")
            print("  - Added 'collection_frequency' column (default: 'monthly')")
            print("  - Added 'last_collection_at' column")
            print("  - Added 'next_collection_at' column (indexed)")
            print("  - Added 'last_monthly_analysis_at' column")
            print("  - Added 'last_quarterly_analysis_at' column")
            print("  - Added 'last_annual_analysis_at' column")
            print("  - Migrated data from legacy last_run_at/next_run_at columns")
            print("\nChanges made to reports:")
            print("  - Added 'period_label' column")
            print("  - Updated existing reports with period labels")
            print("\nNOTE: Legacy columns (schedule_type, last_run_at, next_run_at)")
            print("      are preserved for rollback capability.")
            print()

        except Exception as e:
            trans.rollback()
            print(f"\nERROR: {str(e)}")
            print("Migration rolled back - no changes made")
            raise


def run_rollback(database_url: str):
    """Rollback the migration (remove new columns)."""

    engine = create_engine(database_url)

    print("="*70)
    print("ROLLBACK: Removing collection frequency fields")
    print("="*70)

    with engine.connect() as conn:
        trans = conn.begin()

        try:
            # Remove new columns from scheduled_tasks
            conn.execute(text("""
                ALTER TABLE scheduled_tasks
                DROP COLUMN IF EXISTS collection_frequency,
                DROP COLUMN IF EXISTS last_collection_at,
                DROP COLUMN IF EXISTS next_collection_at,
                DROP COLUMN IF EXISTS last_monthly_analysis_at,
                DROP COLUMN IF EXISTS last_quarterly_analysis_at,
                DROP COLUMN IF EXISTS last_annual_analysis_at
            """))

            # Remove index
            conn.execute(text("""
                DROP INDEX IF EXISTS idx_scheduled_tasks_next_collection
            """))

            # Remove period_label from reports
            conn.execute(text("""
                ALTER TABLE reports
                DROP COLUMN IF EXISTS period_label
            """))

            trans.commit()
            print("Rollback completed successfully")

        except Exception as e:
            trans.rollback()
            print(f"Rollback failed: {str(e)}")
            raise


if __name__ == '__main__':
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("\nUsage:")
        print('  DATABASE_URL="postgresql://user:pass@host/db" python3 migrations/add_collection_frequency.py')
        print('  DATABASE_URL="..." python3 migrations/add_collection_frequency.py --rollback')
        sys.exit(1)

    # Check for rollback flag
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        print("\nThis will ROLLBACK the migration and remove:")
        print("  - collection_frequency, last_collection_at, next_collection_at")
        print("  - last_monthly_analysis_at, last_quarterly_analysis_at, last_annual_analysis_at")
        print("  - period_label from reports")
        print()
        response = input("Continue with rollback? [y/N]: ")
        if response.lower() != 'y':
            print("Rollback cancelled")
            sys.exit(0)
        run_rollback(database_url)
    else:
        # Confirm before running
        print("\nThis migration will:")
        print("  1. Add collection_frequency column to scheduled_tasks")
        print("  2. Add collection tracking columns (last_collection_at, next_collection_at)")
        print("  3. Add analysis tracking columns (last_monthly/quarterly/annual_analysis_at)")
        print("  4. Add period_label column to reports")
        print("  5. Migrate existing schedule data to new columns")
        print()

        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Migration cancelled")
            sys.exit(0)

        run_migration(database_url)
