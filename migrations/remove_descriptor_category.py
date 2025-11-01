"""
Database migration to remove category column from target_descriptors table.

This migration removes the unused category field from descriptors.
Run this script manually when ready to update the production database.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Remove category column from target_descriptors table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("Removing category column from target_descriptors table...")

        # Check if column exists first
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='target_descriptors' AND column_name='category'
        """)

        if cursor.fetchone():
            # Column exists, drop it
            cursor.execute("""
                ALTER TABLE target_descriptors
                DROP COLUMN IF EXISTS category
            """)
            conn.commit()
            print("✓ Successfully removed category column from target_descriptors table")
        else:
            print("✓ Column 'category' does not exist in target_descriptors table (already removed)")

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
    print("MIGRATION: Remove category column from target_descriptors")
    print("=" * 60)
    success = run_migration()
    if success:
        print("\n✓ Migration completed successfully")
    else:
        print("\n✗ Migration failed")
    print("=" * 60)
