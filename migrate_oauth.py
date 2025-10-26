#!/usr/bin/env python3
"""
Migration script to add Google OAuth fields to the users table.
Run this once to update your existing database.
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path='airo.db'):
    """Add OAuth columns to the users table."""

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]

        migrations_needed = []

        if 'google_id' not in columns:
            migrations_needed.append(
                "ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"
            )

        if 'oauth_provider' not in columns:
            migrations_needed.append(
                "ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(50)"
            )

        if 'picture_url' not in columns:
            migrations_needed.append(
                "ALTER TABLE users ADD COLUMN picture_url VARCHAR(500)"
            )

        if not migrations_needed:
            print("✓ Database is already up to date. No migrations needed.")
            return True

        # Execute migrations
        print(f"Running {len(migrations_needed)} migrations...")
        for i, sql in enumerate(migrations_needed, 1):
            print(f"  [{i}/{len(migrations_needed)}] {sql}")
            cursor.execute(sql)

        # Make hashed_password nullable (SQLite doesn't support ALTER COLUMN directly)
        # We'll handle this in the application logic instead

        # Create index on google_id for faster lookups
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)")
            print("  [+] Created index on google_id")
        except Exception as e:
            print(f"  [!] Index creation skipped: {e}")

        # Commit changes
        conn.commit()
        print("\n✓ Migration completed successfully!")
        print("\nNew columns added:")
        print("  - google_id: Stores Google OAuth user ID")
        print("  - oauth_provider: Tracks authentication method (e.g., 'google')")
        print("  - picture_url: Stores user's profile picture URL from OAuth")

        return True

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}", file=sys.stderr)
        return False

    finally:
        conn.close()


if __name__ == "__main__":
    # Check if database exists
    db_path = Path("airo.db")
    if not db_path.exists():
        print("✗ Database file 'airo.db' not found.")
        print("  The database will be created automatically when you start the backend.")
        sys.exit(1)

    # Run migration
    print("=" * 60)
    print("AIRO Database Migration: Adding Google OAuth Support")
    print("=" * 60)
    print()

    success = migrate_database(str(db_path))
    sys.exit(0 if success else 1)
