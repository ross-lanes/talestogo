"""
Database migration to add process_id column to task_status table.

This migration adds a process_id column to track subprocess PIDs for running tasks,
enabling the ability to stop/cancel running tasks.
Run this script manually when ready to update the database.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Add process_id column to task_status table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("Adding process_id column to task_status table...")

        # Check if column already exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='task_status' AND column_name='process_id'
        """)

        if cursor.fetchone():
            print("✓ Column 'process_id' already exists (migration already run)")
            cursor.close()
            conn.close()
            return True

        # Add process_id column
        cursor.execute("""
            ALTER TABLE task_status
            ADD COLUMN process_id INTEGER NULL
        """)

        conn.commit()
        print("✓ Successfully added process_id column to task_status table")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Add process_id to task_status table")
    print("=" * 60)
    success = run_migration()
    if success:
        print("\n✓ Migration completed successfully")
    else:
        print("\n✗ Migration failed")
    print("=" * 60)
