#!/usr/bin/env python3
"""
Migration: Add report_type field to reports table

This migration adds a report_type column to the reports table to distinguish
between monthly reports (focused on latest month) and all-data reports
(comprehensive analysis of all historical data).

Values:
- 'monthly': Default, focuses on latest month with historical context
- 'all_data': Comprehensive report using all data to date

Usage:
    DATABASE_URL="your_db_url" python3 migrations/add_report_type_field.py
"""

import os
import sys
from sqlalchemy import create_engine, text


def run_migration(database_url: str):
    """Run the migration to add report_type field."""

    engine = create_engine(database_url)

    print("="*70)
    print("MIGRATION: Add report_type field to reports")
    print("="*70)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    print("="*70 + "\n")

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # Step 1: Add report_type column
            print("Step 1: Adding report_type column to reports table...")
            conn.execute(text("""
                ALTER TABLE reports
                ADD COLUMN IF NOT EXISTS report_type VARCHAR(20) DEFAULT 'monthly' NOT NULL
            """))
            print("  Added report_type column with default 'monthly'\n")

            # Step 2: Update existing reports to have 'all_data' type
            # (since existing reports were generated with all historical data)
            print("Step 2: Updating existing reports to 'all_data' type...")
            result = conn.execute(text("""
                UPDATE reports
                SET report_type = 'all_data'
                WHERE report_type = 'monthly'
            """))
            print(f"  Updated {result.rowcount} existing reports to 'all_data' type\n")

            # Commit transaction
            trans.commit()

            print("="*70)
            print("MIGRATION COMPLETED SUCCESSFULLY")
            print("="*70)
            print("\nChanges made:")
            print("  - Added 'report_type' column to reports table")
            print("  - Existing reports marked as 'all_data' type")
            print("  - New reports will default to 'monthly' type")
            print()

        except Exception as e:
            trans.rollback()
            print(f"\nERROR: {str(e)}")
            print("Migration rolled back - no changes made")
            raise


if __name__ == '__main__':
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("\nUsage:")
        print('  DATABASE_URL="postgresql://user:pass@host/db" python3 migrations/add_report_type_field.py')
        sys.exit(1)

    # Confirm before running
    print("\nThis migration will:")
    print("  1. Add 'report_type' column to reports table")
    print("  2. Set existing reports to 'all_data' type")
    print()

    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Migration cancelled")
        sys.exit(0)

    run_migration(database_url)
