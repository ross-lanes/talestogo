"""
Database Migration: Add tenant_id column to users table

This script adds the tenant_id column to the users table and creates
the tenants table if it doesn't exist.

Run this script with:
    python migrations/add_tenant_column.py
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def run_migration():
    """Add tenant_id column to users table and create tenants table."""

    with engine.connect() as conn:
        print("=" * 60)
        print("Database Migration: Adding Tenant Support")
        print("=" * 60)
        print()

        # Start transaction
        trans = conn.begin()

        try:
            # Create tenants table if it doesn't exist
            print("Creating tenants table if it doesn't exist...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id SERIAL PRIMARY KEY,
                    tenant_name VARCHAR(200) NOT NULL UNIQUE,
                    subdomain VARCHAR(100),
                    logo_url VARCHAR(500),
                    primary_color VARCHAR(20) DEFAULT '#75C9C8',
                    secondary_color VARCHAR(20) DEFAULT '#665775',
                    custom_domain VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✓ Tenants table ready")

            # Check if tenant_id column exists
            print("\nChecking if tenant_id column exists in users table...")
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='tenant_id'
            """))

            if result.fetchone():
                print("✓ tenant_id column already exists")
            else:
                print("Adding tenant_id column to users table...")
                conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)
                """))
                print("✓ tenant_id column added")

            # Create index on tenant_id if it doesn't exist
            print("\nCreating index on tenant_id...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)
            """))
            print("✓ Index created")

            # Commit transaction
            trans.commit()
            print()
            print("=" * 60)
            print("Migration Complete!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("1. Run: python migrations/assign_existing_users_to_tenant.py")
            print("   This will assign all existing users to the Default tenant")

        except Exception as e:
            trans.rollback()
            print(f"\n✗ Error: {e}")
            raise


if __name__ == "__main__":
    run_migration()
