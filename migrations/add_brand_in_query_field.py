"""
Database migration to add brand_in_query field to queries table.

This field indicates whether the brand name is explicitly mentioned in the query.
Queries with brand_in_query=True should be excluded from mentions, positioning,
share of voice, and threats metrics, but still counted for sentiment and descriptors.

Run this script manually when ready to update the production database.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Add brand_in_query column to queries table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("Adding brand_in_query column to queries table...")

        # Check if column already exists
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='queries' AND column_name='brand_in_query'
        """)

        if cursor.fetchone():
            print("✓ Column 'brand_in_query' already exists in queries table")
            cursor.close()
            conn.close()
            return True

        # Add the column with default value False
        cursor.execute("""
            ALTER TABLE queries
            ADD COLUMN brand_in_query BOOLEAN DEFAULT FALSE
        """)

        conn.commit()
        print("✓ Successfully added brand_in_query column to queries table")

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
    print("MIGRATION: Add brand_in_query column to queries table")
    print("=" * 60)
    success = run_migration()
    if success:
        print("\n✓ Migration completed successfully")
    else:
        print("\n✗ Migration failed")
    print("=" * 60)
