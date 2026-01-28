#!/usr/bin/env python3
"""
Database Migration Runner for Tales Project

This script runs SQL migration files in order to update the database schema
and clean up orphaned data.

Usage:
    python run_migrations.py [--db-path path/to/tales.db] [--migration 001]

Options:
    --db-path: Path to SQLite database file (default: ../tales.db)
    --migration: Specific migration to run (e.g., 001, 002). If not specified, runs all.
    --dry-run: Show what would be executed without actually running it
    --backup: Create backup before running (default: True, use --no-backup to disable)

Examples:
    # Run all migrations with automatic backup
    python run_migrations.py

    # Run specific migration
    python run_migrations.py --migration 001

    # Run on specific database file
    python run_migrations.py --db-path /path/to/database.db

    # Dry run to see what would happen
    python run_migrations.py --dry-run
"""

import sqlite3
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path
import shutil

# Migration tracking table
MIGRATION_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

def get_db_path(custom_path=None):
    """Get the database file path."""
    if custom_path:
        return Path(custom_path)

    # Default: look for tales.db in parent directory
    script_dir = Path(__file__).parent
    return script_dir.parent / "tales.db"

def backup_database(db_path):
    """Create a backup of the database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}.backup_{timestamp}{db_path.suffix}"

    print(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created successfully")
    return backup_path

def get_migration_files():
    """Get all SQL migration files in order."""
    migrations_dir = Path(__file__).parent
    migration_files = sorted(migrations_dir.glob("*.sql"))
    return migration_files

def has_migration_been_applied(conn, migration_name):
    """Check if a migration has already been applied."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = ?",
        (migration_name,)
    )
    count = cursor.fetchone()[0]
    return count > 0

def mark_migration_applied(conn, migration_name):
    """Mark a migration as applied."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO schema_migrations (migration_name) VALUES (?)",
        (migration_name,)
    )
    conn.commit()

def run_migration_file(conn, migration_file, dry_run=False):
    """Run a single migration file."""
    migration_name = migration_file.name

    # Check if already applied
    if has_migration_been_applied(conn, migration_name):
        print(f"⊘ Skipping {migration_name} (already applied)")
        return True

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Running migration: {migration_name}")

    # Read migration SQL
    with open(migration_file, 'r') as f:
        sql = f.read()

    if dry_run:
        print(f"Would execute SQL from: {migration_file}")
        print(f"Preview (first 500 chars):\n{sql[:500]}...")
        return True

    try:
        # Execute the SQL
        cursor = conn.cursor()
        cursor.executescript(sql)

        # Mark as applied
        mark_migration_applied(conn, migration_name)

        print(f"✓ Migration {migration_name} applied successfully")
        return True

    except Exception as e:
        print(f"✗ Migration {migration_name} failed: {e}")
        return False

def verify_database(conn):
    """Verify database integrity after migrations."""
    print("\n" + "="*60)
    print("VERIFICATION: Checking for orphaned data...")
    print("="*60)

    cursor = conn.cursor()

    tables_to_check = [
        'queries', 'responses', 'competitors', 'target_descriptors',
        'campaigns', 'cited_sources', 'reports', 'task_status',
        'trends', 'analyses'
    ]

    all_clean = True
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id IS NULL")
            count = cursor.fetchone()[0]

            if count > 0:
                print(f"⚠ WARNING: {table} has {count} records with NULL user_id")
                all_clean = False
            else:
                print(f"✓ {table}: No orphaned records")
        except sqlite3.OperationalError:
            # Table might not exist yet
            print(f"⊘ {table}: Table does not exist (skipped)")

    if all_clean:
        print("\n✓ All tables are clean - no orphaned data found!")
    else:
        print("\n⚠ Some tables still have orphaned data. Check warnings above.")

    return all_clean

def main():
    parser = argparse.ArgumentParser(
        description="Run database migrations for Tales project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--db-path',
        help='Path to SQLite database file (default: ../tales.db)'
    )
    parser.add_argument(
        '--migration',
        help='Specific migration number to run (e.g., 001)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be executed without running it'
    )
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip database backup before migration'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify database, do not run migrations'
    )

    args = parser.parse_args()

    # Get database path
    db_path = get_db_path(args.db_path)

    if not db_path.exists():
        print(f"✗ Database file not found: {db_path}")
        print(f"  Please specify correct path with --db-path")
        return 1

    print("="*60)
    print("TALES PROJECT - DATABASE MIGRATION TOOL")
    print("="*60)
    print(f"Database: {db_path}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'EXECUTE'}")
    print("="*60)

    # Connect to database
    conn = sqlite3.connect(db_path)

    # Create migration tracking table
    conn.executescript(MIGRATION_TABLE_SQL)

    # Verify only mode
    if args.verify_only:
        verify_database(conn)
        conn.close()
        return 0

    # Create backup (unless disabled or dry run)
    if not args.no_backup and not args.dry_run:
        backup_path = backup_database(db_path)
        print(f"Backup saved to: {backup_path}")

    # Get migration files
    migration_files = get_migration_files()

    if not migration_files:
        print("No migration files found in migrations directory")
        return 1

    # Filter to specific migration if requested
    if args.migration:
        migration_files = [
            f for f in migration_files
            if f.name.startswith(args.migration)
        ]
        if not migration_files:
            print(f"✗ Migration {args.migration} not found")
            return 1

    print(f"\nFound {len(migration_files)} migration(s) to process:")
    for mf in migration_files:
        status = "✓ Applied" if has_migration_been_applied(conn, mf.name) else "• Pending"
        print(f"  {status}: {mf.name}")

    # Run migrations
    success = True
    for migration_file in migration_files:
        if not run_migration_file(conn, migration_file, dry_run=args.dry_run):
            success = False
            break

    # Verify database after migrations
    if not args.dry_run and success:
        verify_database(conn)

    # Close connection
    conn.close()

    if success:
        print("\n" + "="*60)
        print("✓ Migration complete!")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print("✗ Migration failed - database may be in inconsistent state")
        print("  Restore from backup and investigate the error")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
