#!/usr/bin/env python3
"""
Migration: Add LLM Providers Table

This migration creates the llm_providers table for configurable LLM support.
Allows each tenant (or Lab deployment) to configure their own LLM API keys
for data collection, analysis, and report generation.

Run with: python migrations/add_llm_providers.py

Uses SQLAlchemy ORM for database-agnostic table creation (works with both
SQLite and PostgreSQL).
"""

import sys
import os
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from app.database import engine, Base
from app.models import LLMProvider  # Import the model to register it


def run_migration():
    """Run the LLM providers migration using SQLAlchemy ORM."""

    print("Starting LLM Providers migration...")
    print()

    # Check if table already exists
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if 'llm_providers' in existing_tables:
        print("Table 'llm_providers' already exists.")
        print()

        # Show existing columns
        columns = inspector.get_columns('llm_providers')
        print("Existing columns:")
        for col in columns:
            nullable = "nullable" if col.get('nullable', True) else "not null"
            print(f"   - {col['name']}: {col['type']} ({nullable})")
        print()
        print("Migration skipped (table already exists).")
        return

    # Step 1: Create the llm_providers table using SQLAlchemy ORM
    print("1. Creating llm_providers table...")

    # Create only the llm_providers table (not all tables)
    LLMProvider.__table__.create(engine, checkfirst=True)

    print("   ✓ llm_providers table created")
    print()

    # Step 2: Verify the table was created
    print("2. Verifying table structure...")
    inspector = inspect(engine)

    if 'llm_providers' in inspector.get_table_names():
        columns = inspector.get_columns('llm_providers')
        print("   Table columns:")
        for col in columns:
            nullable = "nullable" if col.get('nullable', True) else "not null"
            print(f"      - {col['name']}: {col['type']} ({nullable})")
        print("   ✓ Table structure verified")
    else:
        print("   ⚠️  Table creation may have failed")
    print()

    print("="*60)
    print("LLM Providers migration completed successfully!")
    print()
    print("Next steps:")
    print("1. Configure LLM providers via the Admin UI at /settings/llm-configuration")
    print("2. Or use the API: POST /api/admin/llm-providers")
    print("3. For existing deployments, environment variables continue to work as fallback")
    print("="*60)


def rollback_migration():
    """Rollback the LLM providers migration."""

    print("Rolling back LLM Providers migration...")
    print()

    inspector = inspect(engine)

    if 'llm_providers' not in inspector.get_table_names():
        print("Table 'llm_providers' does not exist. Nothing to rollback.")
        return

    # Drop the table using SQLAlchemy ORM
    print("1. Dropping llm_providers table...")
    LLMProvider.__table__.drop(engine, checkfirst=True)
    print("   ✓ Table dropped")
    print()

    print("Rollback completed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='LLM Providers Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
