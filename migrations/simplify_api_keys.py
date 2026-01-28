#!/usr/bin/env python3
"""
Migration: Simplify API Key Infrastructure

This migration removes API key storage from the database and moves to environment
variables only. Changes:

1. LLM Providers table:
   - Add env_var_name column (for custom providers to specify their env var)
   - Remove api_key_encrypted column (API keys now read from environment only)

2. Users table:
   - Remove openai_api_key_encrypted column
   - Remove anthropic_api_key_encrypted column
   - Remove gemini_api_key_encrypted column
   - Remove perplexity_api_key_encrypted column

After this migration:
- All API keys are read from environment variables (.env file)
- Default providers use standard env vars (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
- Custom providers specify their env var via the env_var_name column

Usage:
    # For development database:
    DATABASE_URL="postgresql://..." python -m migrations.simplify_api_keys

    # Or set the environment variable first:
    export DATABASE_URL="postgresql://..."
    python -m migrations.simplify_api_keys

    # To rollback:
    python -m migrations.simplify_api_keys --rollback
"""

import os
import sys
from sqlalchemy import create_engine, text


def get_database_url():
    """Get database URL from environment variable."""
    url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PUBLIC_URL')

    if not url:
        print("ERROR: No database URL found!")
        print("")
        print("Please set the DATABASE_URL environment variable.")
        print("")
        print("For Railway, you can get this from:")
        print("  1. Go to Railway dashboard")
        print("  2. Click on your Postgres database")
        print("  3. Go to 'Variables' tab")
        print("  4. Copy DATABASE_PUBLIC_URL (use PUBLIC for running from local machine)")
        print("")
        print("Then run:")
        print('  DATABASE_URL="your_url_here" python -m migrations.simplify_api_keys')
        sys.exit(1)

    return url


def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table."""
    result = conn.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = :table_name AND column_name = :column_name
    """), {"table_name": table_name, "column_name": column_name})
    return result.fetchone() is not None


def run_migration():
    """Run the API key simplification migration."""
    database_url = get_database_url()

    # Mask password in URL for display
    display_url = database_url
    if '@' in display_url:
        parts = display_url.split('@')
        if ':' in parts[0]:
            creds = parts[0].rsplit(':', 1)
            display_url = f"{creds[0]}:****@{parts[1]}"

    print(f"Connecting to database: {display_url}")
    print()

    engine = create_engine(database_url)

    with engine.connect() as conn:
        print("=" * 60)
        print("SIMPLIFY API KEYS MIGRATION")
        print("=" * 60)
        print()

        # Step 1: Add env_var_name column to llm_providers
        print("1. LLM Providers Table")
        print("-" * 40)

        if column_exists(conn, 'llm_providers', 'env_var_name'):
            print("   env_var_name column already exists")
        else:
            print("   Adding env_var_name column...")
            conn.execute(text("""
                ALTER TABLE llm_providers
                ADD COLUMN env_var_name VARCHAR(100)
            """))
            conn.commit()
            print("   + env_var_name column added")

        # Remove api_key_encrypted from llm_providers
        if column_exists(conn, 'llm_providers', 'api_key_encrypted'):
            print("   Removing api_key_encrypted column...")
            conn.execute(text("""
                ALTER TABLE llm_providers
                DROP COLUMN api_key_encrypted
            """))
            conn.commit()
            print("   - api_key_encrypted column removed")
        else:
            print("   api_key_encrypted column already removed")

        print()

        # Step 2: Remove API key columns from users table
        print("2. Users Table")
        print("-" * 40)

        api_key_columns = [
            'openai_api_key_encrypted',
            'anthropic_api_key_encrypted',
            'gemini_api_key_encrypted',
            'perplexity_api_key_encrypted'
        ]

        for col in api_key_columns:
            if column_exists(conn, 'users', col):
                print(f"   Removing {col}...")
                conn.execute(text(f"ALTER TABLE users DROP COLUMN {col}"))
                conn.commit()
                print(f"   - {col} removed")
            else:
                print(f"   {col} already removed")

        print()
        print("=" * 60)
        print("MIGRATION COMPLETE!")
        print("=" * 60)
        print()
        print("API keys are now read from environment variables only:")
        print("  - OPENAI_API_KEY      (ChatGPT)")
        print("  - ANTHROPIC_API_KEY   (Claude)")
        print("  - GEMINI_API_KEY      (Gemini)")
        print("  - PERPLEXITY_API_KEY  (Perplexity)")
        print()
        print("Custom providers can specify their env var via env_var_name column.")
        print()


def rollback_migration():
    """Rollback the API key simplification migration."""
    database_url = get_database_url()

    # Mask password in URL for display
    display_url = database_url
    if '@' in display_url:
        parts = display_url.split('@')
        if ':' in parts[0]:
            creds = parts[0].rsplit(':', 1)
            display_url = f"{creds[0]}:****@{parts[1]}"

    print(f"Connecting to database: {display_url}")
    print()

    engine = create_engine(database_url)

    with engine.connect() as conn:
        print("=" * 60)
        print("ROLLBACK: SIMPLIFY API KEYS MIGRATION")
        print("=" * 60)
        print()
        print("WARNING: This will restore API key columns but data will be lost!")
        print()

        # Step 1: Restore api_key_encrypted to llm_providers
        print("1. LLM Providers Table")
        print("-" * 40)

        if not column_exists(conn, 'llm_providers', 'api_key_encrypted'):
            print("   Restoring api_key_encrypted column...")
            conn.execute(text("""
                ALTER TABLE llm_providers
                ADD COLUMN api_key_encrypted TEXT
            """))
            conn.commit()
            print("   + api_key_encrypted column restored (empty)")
        else:
            print("   api_key_encrypted column already exists")

        # Optionally remove env_var_name
        if column_exists(conn, 'llm_providers', 'env_var_name'):
            print("   Removing env_var_name column...")
            conn.execute(text("""
                ALTER TABLE llm_providers
                DROP COLUMN env_var_name
            """))
            conn.commit()
            print("   - env_var_name column removed")
        else:
            print("   env_var_name column already removed")

        print()

        # Step 2: Restore API key columns to users table
        print("2. Users Table")
        print("-" * 40)

        api_key_columns = [
            'openai_api_key_encrypted',
            'anthropic_api_key_encrypted',
            'gemini_api_key_encrypted',
            'perplexity_api_key_encrypted'
        ]

        for col in api_key_columns:
            if not column_exists(conn, 'users', col):
                print(f"   Restoring {col}...")
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} TEXT"))
                conn.commit()
                print(f"   + {col} restored (empty)")
            else:
                print(f"   {col} already exists")

        print()
        print("=" * 60)
        print("ROLLBACK COMPLETE!")
        print("=" * 60)
        print()
        print("NOTE: API key data cannot be recovered.")
        print("Users will need to re-enter their API keys.")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Simplify API Keys Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()

    if args.rollback:
        rollback_migration()
    else:
        run_migration()
