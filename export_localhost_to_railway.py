#!/usr/bin/env python3
"""
Export data from localhost PostgreSQL and import to Railway PostgreSQL.
This will migrate all your data to the production database.
"""
from sqlalchemy import create_engine, text, MetaData, Table
from sqlalchemy.orm import sessionmaker
import sys

# Source: localhost PostgreSQL
SOURCE_URL = "postgresql://localhost/tales_db"

# Destination: Railway PostgreSQL (public URL)
DEST_URL = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway"

def migrate_database():
    """Migrate all data from localhost to Railway"""

    print("=" * 60)
    print("DATABASE MIGRATION: localhost -> Railway")
    print("=" * 60)

    # Connect to both databases
    print("\n[1/5] Connecting to source database (localhost)...")
    try:
        source_engine = create_engine(SOURCE_URL)
        source_conn = source_engine.connect()
        print("✅ Connected to localhost PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to localhost: {e}")
        return False

    print("\n[2/5] Connecting to destination database (Railway)...")
    try:
        dest_engine = create_engine(DEST_URL)
        dest_conn = dest_engine.connect()
        print("✅ Connected to Railway PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to Railway: {e}")
        return False

    # Get table structure from source
    print("\n[3/5] Reading source database schema...")
    source_metadata = MetaData()
    source_metadata.reflect(bind=source_engine)
    tables = source_metadata.sorted_tables
    print(f"✅ Found {len(tables)} tables to migrate")

    # Create tables in destination
    print("\n[4/5] Creating tables in Railway database...")
    try:
        # Import models to create schema
        from app.database import Base, engine as app_engine
        from app import models

        # Point Base to Railway database
        Base.metadata.bind = dest_engine
        Base.metadata.create_all(dest_engine)
        print("✅ Tables created in Railway database")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

    # Migrate data table by table (in dependency order)
    print("\n[5/5] Migrating data...")

    # Define migration order (respecting foreign key dependencies)
    migration_order = [
        'tenants',
        'users',
        'brand_info',
        'queries',
        'target_descriptors',
        'competitors',
        'personas',
        'campaigns',
        'collection_batches',
        'responses',
        'cited_sources',
        'analyses',
        'reports',
        'trends',
        'batch_analytics',
        'task_status',
        'scheduled_tasks',
        'scheduled_task_history',
        'brand_shares',
        'persona_generations',
    ]

    migrated_count = 0

    for table_name in migration_order:
        if table_name not in source_metadata.tables:
            continue

        try:
            # Get row count
            count_result = source_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = count_result.scalar()

            if row_count == 0:
                print(f"  ⊘ {table_name}: 0 rows (skipped)")
                continue

            # Read all data from source
            result = source_conn.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            columns = result.keys()

            # Insert into destination
            if rows:
                # Build insert statement
                cols = ', '.join(columns)
                placeholders = ', '.join([f':{col}' for col in columns])
                insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"

                # Convert rows to dicts
                data = [dict(zip(columns, row)) for row in rows]

                dest_conn.execute(text(insert_sql), data)
                dest_conn.commit()

                print(f"  ✅ {table_name}: {len(rows)} rows migrated")
                migrated_count += 1

        except Exception as e:
            print(f"  ⚠️  {table_name}: Error - {e}")
            continue

    # Update sequences for auto-increment columns
    print("\n[6/5] Updating sequences...")
    try:
        tables_with_ids = ['users', 'brand_info', 'queries', 'target_descriptors',
                           'competitors', 'responses', 'analyses', 'reports', 'task_status']

        for table_name in tables_with_ids:
            if table_name not in source_metadata.tables:
                continue
            try:
                # Get max ID from source
                max_id_result = source_conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
                max_id = max_id_result.scalar()

                if max_id:
                    # Update sequence in destination
                    dest_conn.execute(text(f"SELECT setval('{table_name}_id_seq', {max_id}, true)"))
                    dest_conn.commit()
                    print(f"  ✅ Updated sequence for {table_name} to {max_id}")
            except Exception as e:
                print(f"  ⚠️  Sequence update failed for {table_name}: {e}")
    except Exception as e:
        print(f"  ⚠️  Error updating sequences: {e}")

    # Close connections
    source_conn.close()
    dest_conn.close()

    print("\n" + "=" * 60)
    print(f"✅ MIGRATION COMPLETE!")
    print(f"   Migrated {migrated_count} tables")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
