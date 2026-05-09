#!/usr/bin/env python3
"""
Tales Database Initialization Script

Creates all database tables required by Tales. Does not create any users,
brands, or tenants. Run this script to prepare a fresh database before
first use.

Usage:
    # With DATABASE_URL in environment or .env file:
    python scripts/admin/init_database.py

    # Or specify DATABASE_URL directly:
    DATABASE_URL=postgresql://user:pass@host:port/db python scripts/admin/init_database.py

    # Inside Docker container:
    docker compose exec app python scripts/admin/init_database.py
"""

import os
import sys

# Preserve DATABASE_URL if explicitly set before loading .env
# This allows: DATABASE_URL=... python script.py
_explicit_db_url = os.environ.get('DATABASE_URL')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)

# Restore explicit DATABASE_URL if it was set
if _explicit_db_url:
    os.environ['DATABASE_URL'] = _explicit_db_url

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy import text, inspect
from app.database import SessionLocal, engine, Base
from app import models  # noqa: F401 - imports register models with Base


def check_database_connection() -> bool:
    """Verify database connection works."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        print(f"\nError: Cannot connect to database.")
        print(f"Details: {e}")
        print("\nMake sure DATABASE_URL is set correctly in your environment or .env file.")
        return False


def get_existing_tables() -> list:
    """Get list of tables that already exist in the database."""
    inspector = inspect(engine)
    return inspector.get_table_names()


def create_tables() -> tuple[int, int]:
    """
    Create all database tables defined in models.

    Returns:
        Tuple of (tables_created, tables_existing)
    """
    # Get tables before creation
    existing_before = set(get_existing_tables())

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Get tables after creation
    existing_after = set(get_existing_tables())

    # Calculate new tables
    new_tables = existing_after - existing_before

    return len(new_tables), len(existing_before)


def main():
    print("=" * 60)
    print("TALES Database Initialization")
    print("=" * 60)
    print()

    # Show which database we're connecting to
    from app.database import DATABASE_URL
    if "sqlite" in DATABASE_URL:
        print(f"Database: SQLite (local development)")
    else:
        # Mask password in URL for display
        display_url = DATABASE_URL
        if "@" in display_url:
            # postgresql://user:password@host:port/db
            parts = display_url.split("@")
            prefix = parts[0].rsplit(":", 1)[0]  # everything before password
            display_url = f"{prefix}:****@{parts[1]}"
        print(f"Database: {display_url}")
    print()

    # Check database connection
    print("Checking database connection...")
    if not check_database_connection():
        sys.exit(1)
    print("Database connection OK.")
    print()

    # Create tables
    print("Creating database tables...")
    tables_created, tables_existing = create_tables()

    if tables_created > 0:
        print(f"Created {tables_created} new table(s).")

    if tables_existing > 0:
        print(f"Found {tables_existing} existing table(s).")

    # List all tables
    all_tables = sorted(get_existing_tables())
    print()
    print(f"Total tables in database: {len(all_tables)}")
    print()

    print("=" * 60)
    print("SUCCESS! Database initialized.")
    print("=" * 60)
    print()
    print("Tables created:")
    for table in all_tables:
        print(f"  - {table}")
    print()
    print("Next steps:")
    print("1. Run setup_initial_admin.py to create the first admin user")
    print("2. Configure LLM API keys in your environment")
    print("3. Start the application")
    print()


if __name__ == "__main__":
    main()
