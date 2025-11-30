#!/usr/bin/env python3
"""
Migration: Add allowed_products column to users table

This migration:
1. Adds allowed_products column to users table (TEXT for JSON storage)
2. Sets full access for existing admins and skremen@solsticehc.net
3. Leaves other users with NULL (defaults to Tales only via code)
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def run_migration():
    """Run the allowed_products migration"""

    with engine.connect() as conn:
        print("Starting allowed_products migration...")
        print()

        # Step 1: Check if column exists
        print("1. Checking if allowed_products column exists...")
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'allowed_products'
        """))
        if result.fetchone():
            print("   ⚠️  Column already exists, skipping creation")
        else:
            # Add the column
            print("   Adding allowed_products column...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN allowed_products TEXT
            """))
            print("   ✅ allowed_products column added")

        # Step 2: Set full access for admins
        print("2. Setting full access for admin users...")
        result = conn.execute(text("""
            UPDATE users
            SET allowed_products = '["tales", "heads", "canon"]'
            WHERE is_admin = true
        """))
        print(f"   ✅ Updated {result.rowcount} admin users")

        # Step 3: Set full access for skremen@solsticehc.net
        print("3. Setting full access for skremen@solsticehc.net...")
        result = conn.execute(text("""
            UPDATE users
            SET allowed_products = '["tales", "heads", "canon"]'
            WHERE LOWER(email) = 'skremen@solsticehc.net'
        """))
        print(f"   ✅ Updated {result.rowcount} user(s)")

        conn.commit()
        print()
        print("✅ Migration completed successfully!")
        print()
        print("Product access is now controlled by the allowed_products column:")
        print("  - NULL/empty = Tales only (default)")
        print("  - Admins bypass this check (always see all products)")
        print("  - skremen@solsticehc.net has special full access")


def rollback_migration():
    """Rollback the allowed_products migration"""

    with engine.connect() as conn:
        print("Rolling back allowed_products migration...")
        print()

        # Check if column exists before dropping
        print("1. Checking if allowed_products column exists...")
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users' AND column_name = 'allowed_products'
        """))
        if not result.fetchone():
            print("   ⚠️  Column does not exist, nothing to rollback")
        else:
            print("   Dropping allowed_products column...")
            conn.execute(text("""
                ALTER TABLE users
                DROP COLUMN allowed_products
            """))
            print("   ✅ Column dropped")

        conn.commit()
        print()
        print("✅ Rollback completed successfully!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        run_migration()
