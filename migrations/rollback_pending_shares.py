"""
Rollback Migration: Remove pending_email and is_pending columns from brand_shares table

This script undoes the pending shares feature by:
1. Removing pending_email column
2. Removing is_pending column
3. Making user_id NOT NULL again
4. Deleting any pending shares (where user_id is NULL)

Usage:
    python migrations/rollback_pending_shares.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, SessionLocal


def run_rollback():
    """Remove pending shares columns and restore original schema"""

    print("Starting rollback: Remove pending shares feature...")

    db = SessionLocal()

    try:
        # Check if columns exist
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'brand_shares'
            AND column_name IN ('pending_email', 'is_pending')
        """))

        existing_columns = [row[0] for row in result]

        if not existing_columns:
            print("✅ Columns already removed. Rollback not needed.")
            return

        print("Rolling back database changes...")

        # Step 1: Delete any pending shares (where user_id is NULL)
        print("  - Removing pending shares (where user_id is NULL)...")
        result = db.execute(text("""
            DELETE FROM brand_shares WHERE user_id IS NULL
        """))
        deleted_count = result.rowcount
        print(f"    ✓ Deleted {deleted_count} pending share(s)")

        # Step 2: Make user_id NOT NULL again
        print("  - Making user_id column NOT NULL...")
        db.execute(text("""
            ALTER TABLE brand_shares
            ALTER COLUMN user_id SET NOT NULL
        """))
        print("    ✓ user_id is now NOT NULL")

        # Step 3: Drop pending_email column if it exists
        if 'pending_email' in existing_columns:
            print("  - Dropping pending_email column...")
            db.execute(text("""
                DROP INDEX IF EXISTS ix_brand_shares_pending_email
            """))
            db.execute(text("""
                ALTER TABLE brand_shares
                DROP COLUMN IF EXISTS pending_email
            """))
            print("    ✓ Removed pending_email column and index")

        # Step 4: Drop is_pending column if it exists
        if 'is_pending' in existing_columns:
            print("  - Dropping is_pending column...")
            db.execute(text("""
                DROP INDEX IF EXISTS ix_brand_shares_is_pending
            """))
            db.execute(text("""
                ALTER TABLE brand_shares
                DROP COLUMN IF EXISTS is_pending
            """))
            print("    ✓ Removed is_pending column and index")

        db.commit()

        print("\n✅ Rollback completed successfully!")
        print("\nThe brand_shares table has been restored to its original schema.")
        print("All pending shares have been removed.")

    except Exception as e:
        print(f"\n❌ Rollback failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE ROLLBACK: Remove Pending Shares Feature")
    print("=" * 60)
    print()
    print("⚠️  WARNING: This will:")
    print("  - Delete all pending shares (shares without a user_id)")
    print("  - Remove pending_email and is_pending columns")
    print("  - Make user_id required again (NOT NULL)")
    print()

    # Confirm before proceeding
    response = input("Are you sure you want to proceed? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Rollback cancelled.")
        sys.exit(0)

    print()
    run_rollback()
