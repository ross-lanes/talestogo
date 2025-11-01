"""
Database migration to add brand_shares table for multi-user brand collaboration.

This migration creates the brand_shares table to track which users have access
to which brands, enabling collaborative editing of brand data.
Run this script manually when ready to update the production database.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Create brand_shares table for brand collaboration"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("Creating brand_shares table...")

        # Check if table already exists
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name='brand_shares'
        """)

        if cursor.fetchone():
            print("✓ Table 'brand_shares' already exists (migration already run)")
            cursor.close()
            conn.close()
            return True

        # Create brand_shares table
        cursor.execute("""
            CREATE TABLE brand_shares (
                id SERIAL PRIMARY KEY,
                brand_id INTEGER NOT NULL REFERENCES brand_info(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                shared_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                permission_level VARCHAR(20) DEFAULT 'edit',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(brand_id, user_id)
            )
        """)

        # Create indexes for efficient lookups
        cursor.execute("""
            CREATE INDEX idx_brand_shares_brand_id ON brand_shares(brand_id)
        """)
        cursor.execute("""
            CREATE INDEX idx_brand_shares_user_id ON brand_shares(user_id)
        """)

        conn.commit()
        print("✓ Successfully created brand_shares table with indexes")

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
    print("MIGRATION: Add brand_shares table for collaboration")
    print("=" * 60)
    success = run_migration()
    if success:
        print("\n✓ Migration completed successfully")
    else:
        print("\n✗ Migration failed")
    print("=" * 60)
