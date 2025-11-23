#!/usr/bin/env python3
"""
Smart migration that handles schema differences between localhost and Railway
"""
from sqlalchemy import create_engine, text, MetaData, inspect
import sys

# Source: localhost PostgreSQL
SOURCE_URL = "postgresql://localhost/tales_db"

# Destination: Railway PostgreSQL
DEST_URL = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway"

def get_common_columns(source_inspector, dest_inspector, table_name):
    """Get columns that exist in both source and destination"""
    try:
        source_cols = {col['name'] for col in source_inspector.get_columns(table_name)}
        dest_cols = {col['name'] for col in dest_inspector.get_columns(table_name)}
        common = source_cols & dest_cols
        return sorted(list(common))
    except Exception as e:
        print(f"Error getting columns for {table_name}: {e}")
        return []

def migrate_database():
    """Migrate all data from localhost to Railway"""

    print("=" * 60)
    print("SMART DATABASE MIGRATION: localhost -> Railway")
    print("=" * 60)

    # Connect to both databases
    print("\n[1/6] Connecting to source database (localhost)...")
    try:
        source_engine = create_engine(SOURCE_URL)
        source_conn = source_engine.connect()
        source_inspector = inspect(source_engine)
        print("✅ Connected to localhost PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to localhost: {e}")
        return False

    print("\n[2/6] Connecting to destination database (Railway)...")
    try:
        dest_engine = create_engine(DEST_URL)
        dest_conn = dest_engine.connect()
        dest_inspector = inspect(dest_engine)
        print("✅ Connected to Railway PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to Railway: {e}")
        return False

    # Create tables in destination if needed
    print("\n[3/6] Ensuring tables exist in Railway database...")
    try:
        from app.database import Base
        from app import models
        Base.metadata.bind = dest_engine
        Base.metadata.create_all(dest_engine)
        print("✅ Tables ready in Railway database")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

    # Migration order
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

    print("\n[4/6] Migrating data...")
    migrated_count = 0

    for table_name in migration_order:
        # Check if table exists in both databases
        try:
            source_tables = source_inspector.get_table_names()
            dest_tables = dest_inspector.get_table_names()

            if table_name not in source_tables:
                continue
            if table_name not in dest_tables:
                print(f"  ⊘ {table_name}: not in destination (skipped)")
                continue

            # Get common columns
            common_cols = get_common_columns(source_inspector, dest_inspector, table_name)

            if not common_cols:
                print(f"  ⊘ {table_name}: no common columns (skipped)")
                continue

            # Get row count
            count_result = source_conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = count_result.scalar()

            if row_count == 0:
                print(f"  ⊘ {table_name}: 0 rows (skipped)")
                continue

            # Read data - only common columns
            cols_str = ', '.join(common_cols)
            result = source_conn.execute(text(f"SELECT {cols_str} FROM {table_name}"))
            rows = result.fetchall()

            if rows:
                # Build insert statement with only common columns
                placeholders = ', '.join([f':{col}' for col in common_cols])
                insert_sql = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"

                # Convert rows to dicts
                data = [dict(zip(common_cols, row)) for row in rows]

                # Insert in batches to avoid memory issues
                batch_size = 100
                for i in range(0, len(data), batch_size):
                    batch = data[i:i+batch_size]
                    dest_conn.execute(text(insert_sql), batch)
                dest_conn.commit()

                print(f"  ✅ {table_name}: {len(rows)} rows migrated ({len(common_cols)} columns)")
                migrated_count += 1

        except Exception as e:
            print(f"  ⚠️  {table_name}: Error - {str(e)[:100]}")
            dest_conn.rollback()  # Rollback this table's transaction
            continue

    # Update sequences
    print("\n[5/6] Updating ID sequences...")
    tables_with_ids = ['users', 'brand_info', 'queries', 'target_descriptors',
                       'competitors', 'responses', 'analyses', 'reports', 'task_status',
                       'collection_batches', 'scheduled_tasks', 'tenants', 'trends']

    for table_name in tables_with_ids:
        try:
            source_tables = source_inspector.get_table_names()
            if table_name not in source_tables:
                continue

            # Get max ID from source
            max_id_result = source_conn.execute(text(f"SELECT MAX(id) FROM {table_name}"))
            max_id = max_id_result.scalar()

            if max_id:
                # Update sequence in destination
                dest_conn.execute(text(f"SELECT setval('{table_name}_id_seq', {max_id}, true)"))
                dest_conn.commit()
                print(f"  ✅ {table_name}_id_seq -> {max_id}")
        except Exception as e:
            print(f"  ⚠️  {table_name}: {str(e)[:80]}")

    # Verify migration
    print("\n[6/6] Verifying migration...")
    try:
        result = dest_conn.execute(text("""
            SELECT bi.id, bi.brand_name, u.email
            FROM brand_info bi
            JOIN users u ON bi.user_id = u.id
            WHERE u.email = 'robotrachel@gmail.com'
        """))
        brands = result.fetchall()
        print(f"  ✅ Found {len(brands)} brands for robotrachel@gmail.com in Railway:")
        for brand in brands:
            print(f"     - {brand[1]} (ID: {brand[0]})")
    except Exception as e:
        print(f"  ⚠️  Verification failed: {e}")

    # Close connections
    source_conn.close()
    dest_conn.close()

    print("\n" + "=" * 60)
    print(f"✅ MIGRATION COMPLETE!")
    print(f"   Migrated {migrated_count} tables successfully")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
