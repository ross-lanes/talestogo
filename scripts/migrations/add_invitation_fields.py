#!/usr/bin/env python3
"""
Migration script to add invitation fields to users table.
Run this once to update the database schema.
"""
from dotenv import load_dotenv
load_dotenv(override=True)  # Load .env file first

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

# Verify we're using PostgreSQL
print(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")

def add_invitation_fields():
    """Add invitation_token and invitation_expires_at fields to users table."""
    print("Adding invitation fields to users table...")

    with engine.connect() as conn:
        try:
            # Add invitation_token column
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS invitation_token VARCHAR(500) UNIQUE
            """))
            conn.commit()
            print("✓ Added invitation_token column")

            # Add invitation_expires_at column
            conn.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS invitation_expires_at TIMESTAMP
            """))
            conn.commit()
            print("✓ Added invitation_expires_at column")

            # Create index on invitation_token
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_invitation_token
                ON users(invitation_token)
            """))
            conn.commit()
            print("✓ Created index on invitation_token")

            print("\n✅ Migration completed successfully!")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_invitation_fields()
