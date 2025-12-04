#!/usr/bin/env python3
"""
Add is_data_reviewer role to users table.

This migration adds a new boolean column to support data reviewer role
for NSTXView - users who can review outliers and manage thresholds
without having full admin privileges.
"""

import os
import sys
from sqlalchemy import create_engine, text

def run_migration(database_url: str, dry_run: bool = False):
    """Run the migration."""
    print(f"🔧 Adding is_data_reviewer column to users table...")
    print(f"📊 Database: {database_url.split('@')[1].split('/')[0]}")
    print(f"🧪 Dry run: {dry_run}\n")

    engine = create_engine(database_url)

    migration_sql = """
    -- Add is_data_reviewer column to users table
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_data_reviewer BOOLEAN DEFAULT FALSE;

    -- Create index for performance
    CREATE INDEX IF NOT EXISTS idx_users_data_reviewer
    ON users(is_data_reviewer) WHERE is_data_reviewer = TRUE;
    """

    with engine.connect() as conn:
        print(f"📝 Adding is_data_reviewer column...")
        if dry_run:
            print(f"   [DRY RUN] Would execute:\n{migration_sql}")
        else:
            try:
                conn.execute(text(migration_sql))
                conn.commit()
                print(f"   ✅ Success")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                conn.rollback()
                raise

    if not dry_run:
        # Verify changes
        print("\n🔍 Verifying schema changes...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'users'
                AND column_name = 'is_data_reviewer'
            """))
            col = result.fetchone()
            if col:
                print(f"   ✅ Column added: {col[0]} ({col[1]}, default: {col[2]})")
            else:
                print(f"   ❌ Column not found!")

    print("\n✅ Migration complete!")
    return True

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Add is_data_reviewer role to users')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--prod', action='store_true', help='Run on PRODUCTION database (use with caution!)')
    args = parser.parse_args()

    # Get database URL
    if args.prod:
        db_url = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway"
        if not args.dry_run:
            confirm = input("⚠️  WARNING: This will modify PRODUCTION database. Type 'yes' to continue: ")
            if confirm.lower() != 'yes':
                print("❌ Aborted")
                return 1
    else:
        db_url = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway"

    try:
        run_migration(db_url, dry_run=args.dry_run)
        return 0
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
