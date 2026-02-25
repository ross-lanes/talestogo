#!/usr/bin/env python3
"""
Run migration on PRODUCTION database.
This adds invitation_token and invitation_expires_at columns to the users table.
"""
from dotenv import load_dotenv
load_dotenv(override=True)

import sys
import os
from sqlalchemy import create_engine, text

# Production database URL from environment
PRODUCTION_DB_URL = os.getenv("DATABASE_URL")
if not PRODUCTION_DB_URL:
    print("❌ DATABASE_URL environment variable is not set")
    sys.exit(1)

def add_invitation_fields():
    """Add invitation fields to production users table."""
    print(f"Connecting to production database...")
    print(f"Database: {PRODUCTION_DB_URL[:50]}...")

    engine = create_engine(PRODUCTION_DB_URL)

    with engine.connect() as conn:
        try:
            # Add invitation_token column
            print("\nAdding invitation_token column...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS invitation_token VARCHAR(500) UNIQUE
            """))
            conn.commit()
            print("✓ Added invitation_token column")

            # Add invitation_expires_at column
            print("Adding invitation_expires_at column...")
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS invitation_expires_at TIMESTAMP
            """))
            conn.commit()
            print("✓ Added invitation_expires_at column")

            # Create index on invitation_token
            print("Creating index on invitation_token...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_invitation_token
                ON users(invitation_token)
            """))
            conn.commit()
            print("✓ Created index on invitation_token")

            print("\n✅ Production migration completed successfully!")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    response = input("This will modify the PRODUCTION database. Are you sure? (yes/no): ")
    if response.lower() == 'yes':
        add_invitation_fields()
    else:
        print("Migration cancelled.")
