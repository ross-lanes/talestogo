#!/usr/bin/env python3
"""
Migration Script: Add tenant_id to all tables
Purpose: Add tenant_id column to all tables that need multi-tenant support

This script should be run once on production after the initial tenant migration.

Usage:
    python migrations/add_tenant_to_all_tables.py
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


def add_tenant_columns():
    """Add tenant_id column to all tables that need it."""

    # List of tables that need tenant_id column
    tables_needing_tenant = [
        'brand_info',
        'queries',
        'responses',
        'competitors',
        'descriptors',
        'reports',
        'batches',
        'batch_responses'
    ]

    print("\n" + "="*60)
    print("Adding tenant_id columns to tables")
    print("="*60)

    with engine.connect() as conn:
        trans = conn.begin()

        try:
            for table in tables_needing_tenant:
                # Check if table exists
                table_check = conn.execute(text(f"""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_name='{table}'
                """))

                if not table_check.fetchone():
                    print(f"⊘ {table} table does not exist, skipping")
                    continue

                # Check if column already exists
                result = conn.execute(text(f"""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='{table}' AND column_name='tenant_id'
                """))

                if result.fetchone():
                    print(f"✓ {table}.tenant_id already exists")
                else:
                    print(f"Adding tenant_id to {table}...")
                    conn.execute(text(f"""
                        ALTER TABLE {table}
                        ADD COLUMN tenant_id INTEGER REFERENCES tenants(id)
                    """))

                    # Create index
                    conn.execute(text(f"""
                        CREATE INDEX IF NOT EXISTS idx_{table}_tenant_id ON {table}(tenant_id)
                    """))
                    print(f"✓ {table}.tenant_id added with index")

            trans.commit()
            print("\n" + "="*60)
            print("Migration Complete!")
            print("="*60)
            return True

        except Exception as e:
            trans.rollback()
            print(f"\n✗ Error: {e}")
            return False


if __name__ == "__main__":
    print("\nStarting tenant column migration...\n")
    success = add_tenant_columns()
    sys.exit(0 if success else 1)
