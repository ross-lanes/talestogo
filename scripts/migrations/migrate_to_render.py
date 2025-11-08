#!/usr/bin/env python3
"""
Database Migration Script - SQLite to PostgreSQL (Render)
Migrates all data from local SQLite database to Render PostgreSQL database.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base
from app import models


def migrate_database(source_db_url: str, target_db_url: str):
    """
    Migrate data from source database to target database.

    Args:
        source_db_url: SQLite database URL (e.g., sqlite:///tales.db)
        target_db_url: PostgreSQL database URL (from Render)
    """
    print("="*60)
    print("TALES Database Migration Tool")
    print("="*60)
    print(f"\nSource: {source_db_url}")
    print(f"Target: {target_db_url[:50]}...")
    print()

    # Create engines
    print("Connecting to databases...")
    source_engine = create_engine(source_db_url)
    target_engine = create_engine(target_db_url)

    # Create sessions
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)

    source_session = SourceSession()
    target_session = TargetSession()

    try:
        # Create all tables in target database
        print("Creating tables in target database...")
        Base.metadata.create_all(target_engine)
        print("✓ Tables created")

        # Define migration order (respecting foreign key constraints)
        migration_order = [
            (models.User, "Users"),
            (models.BrandInfo, "Brand Information"),
            (models.BrandShare, "Brand Shares"),
            (models.Query, "Queries"),
            (models.Competitor, "Competitors"),
            (models.TargetDescriptor, "Target Descriptors"),
            (models.CollectionBatch, "Collection Batches"),
            (models.Response, "Responses"),
            (models.BatchAnalytics, "Batch Analytics"),
            (models.Campaign, "Campaigns"),
            (models.CitedSource, "Cited Sources"),
            (models.Report, "Reports"),
            (models.AnalysisHistory, "Analysis History"),
            (models.Trend, "Trends"),
            (models.Configuration, "Configurations"),
            (models.ScheduledTask, "Scheduled Tasks"),
            (models.ScheduledTaskHistory, "Scheduled Task History"),
            (models.TaskStatus, "Task Statuses"),
        ]

        stats = {}

        print("\nMigrating data...")
        print("-"*60)

        for model_class, display_name in migration_order:
            try:
                # Get all records from source
                source_records = source_session.query(model_class).all()
                count = len(source_records)

                if count == 0:
                    print(f"  {display_name}: 0 records (skipped)")
                    stats[display_name] = 0
                    continue

                print(f"  {display_name}: Migrating {count} records...", end=" ", flush=True)

                # Insert into target
                for record in source_records:
                    # Create dict of all columns
                    record_dict = {}
                    for column in model_class.__table__.columns:
                        record_dict[column.name] = getattr(record, column.name)

                    # Create new object in target
                    new_record = model_class(**record_dict)
                    target_session.add(new_record)

                target_session.commit()
                print(f"✓ {count} records")
                stats[display_name] = count

            except Exception as e:
                print(f"✗ Error: {e}")
                target_session.rollback()
                stats[display_name] = f"Error: {str(e)[:50]}"

        print("-"*60)
        print("\nMigration Summary:")
        print("="*60)

        total_records = 0
        for name, count in stats.items():
            if isinstance(count, int):
                total_records += count
                status = "✓" if count > 0 else " "
                print(f"  {status} {name}: {count}")
            else:
                print(f"  ✗ {name}: {count}")

        print("="*60)
        print(f"\nTotal records migrated: {total_records}")
        print("\n✅ Migration complete!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        target_session.rollback()

    finally:
        source_session.close()
        target_session.close()


def main():
    """Main migration function."""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate SQLite database to PostgreSQL')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("\n🚀 TALES Database Migration to Render\n")

    # Source database (local SQLite)
    source_db = os.path.join(os.path.dirname(__file__), "tales.db")
    if not os.path.exists(source_db):
        print(f"❌ Source database not found: {source_db}")
        print("\nPlease ensure tales.db exists in the project root.")
        sys.exit(1)

    source_db_url = f"sqlite:///{source_db}"

    # Target database (Render PostgreSQL)
    # You can pass the Render DATABASE_URL as an environment variable or argument
    target_db_url = os.getenv("RENDER_DATABASE_URL")

    if not target_db_url:
        print("❌ RENDER_DATABASE_URL environment variable not set!")
        print("\nTo migrate your database:")
        print("1. Go to your Render dashboard")
        print("2. Find your PostgreSQL database")
        print("3. Copy the 'External Database URL'")
        print("4. Run:")
        print("   export RENDER_DATABASE_URL='your-postgres-url'")
        print("   python3 migrate_to_render.py --yes")
        print("\nOr pass it directly:")
        print("   RENDER_DATABASE_URL='your-url' python3 migrate_to_render.py --yes")
        sys.exit(1)

    # Confirm before migration
    print(f"Source database: {source_db}")
    print(f"Target database: {target_db_url[:50]}...")
    print("\n⚠️  WARNING: This will ADD data to the target database.")
    print("If you want a clean migration, clear the target database first.")

    if not args.yes:
        response = input("\nProceed with migration? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            sys.exit(0)
    else:
        print("\nAuto-confirmed with --yes flag. Proceeding with migration...")

    # Run migration
    migrate_database(source_db_url, target_db_url)


if __name__ == "__main__":
    main()
