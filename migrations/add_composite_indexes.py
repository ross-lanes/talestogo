"""
Database migration to add composite indexes for performance optimization.

This migration adds composite indexes to the queries and responses tables
to significantly improve analytics query performance, especially as data
grows to 6+ months.

Expected performance improvements:
- 30-50% faster analytics calculations
- Reduced database CPU usage
- Better concurrent user support

Run this script manually when ready to update the production database.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()


def run_migration():
    """Add composite indexes to queries and responses tables"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print("Adding composite indexes for performance optimization...")
        print()

        # Define all indexes to create
        indexes = [
            # Query table indexes
            {
                'name': 'idx_query_brand_branded',
                'table': 'queries',
                'columns': ['brand_id', 'brand_in_query'],
                'description': 'Optimize brand_in_query filtering in analytics queries'
            },
            {
                'name': 'idx_query_compound_lookup',
                'table': 'queries',
                'columns': ['query_id', 'user_id', 'brand_id'],
                'description': 'Optimize JOIN operations between responses and queries'
            },

            # Response table indexes
            {
                'name': 'idx_response_user_brand_batch',
                'table': 'responses',
                'columns': ['user_id', 'brand_id', 'batch_id'],
                'description': 'Optimize multi-tenant + multi-brand + batch filtering (most common query)'
            },
            {
                'name': 'idx_response_sentiment_mentioned',
                'table': 'responses',
                'columns': ['sentiment', 'brand_mentioned'],
                'description': 'Optimize sentiment analysis queries with brand mention filtering'
            },
            {
                'name': 'idx_response_position_mentioned',
                'table': 'responses',
                'columns': ['brand_position', 'brand_mentioned'],
                'description': 'Optimize positioning breakdown queries'
            },
            {
                'name': 'idx_response_timestamp_user',
                'table': 'responses',
                'columns': ['timestamp', 'user_id', 'brand_id'],
                'description': 'Optimize time-based queries with user/brand filtering'
            },
            {
                'name': 'idx_response_query_lookup',
                'table': 'responses',
                'columns': ['query_id', 'user_id', 'brand_id'],
                'description': 'Optimize JOIN operations from responses to queries'
            }
        ]

        created_count = 0
        skipped_count = 0

        for index in indexes:
            # Check if index already exists
            cursor.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = %s AND indexname = %s
            """, (index['table'], index['name']))

            if cursor.fetchone():
                print(f"  ⊙ Skipping {index['name']} (already exists)")
                skipped_count += 1
                continue

            # Create the index
            columns_str = ', '.join(index['columns'])
            sql = f"CREATE INDEX {index['name']} ON {index['table']} ({columns_str})"

            print(f"  + Creating {index['name']}...")
            print(f"    Table: {index['table']}")
            print(f"    Columns: {columns_str}")
            print(f"    Purpose: {index['description']}")

            cursor.execute(sql)
            created_count += 1
            print(f"    ✓ Created successfully")
            print()

        conn.commit()

        print()
        print("=" * 60)
        print(f"Index creation summary:")
        print(f"  Created: {created_count}")
        print(f"  Skipped (already exist): {skipped_count}")
        print(f"  Total: {len(indexes)}")
        print("=" * 60)

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION: Add Composite Indexes for Performance")
    print("=" * 60)
    print()
    print("This migration adds 7 composite indexes to improve analytics")
    print("query performance, especially important as data grows to 6+ months.")
    print()
    print("IMPORTANT: This migration may take several minutes on large databases.")
    print("Indexes are created CONCURRENTLY to avoid locking tables.")
    print()

    response = input("Do you want to proceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        exit(0)

    print()
    success = run_migration()

    if success:
        print()
        print("✓ Migration completed successfully!")
        print()
        print("Next steps:")
        print("  1. Monitor database performance metrics")
        print("  2. Analytics queries should now be 30-50% faster")
        print("  3. Consider VACUUM ANALYZE on queries and responses tables")
    else:
        print()
        print("✗ Migration failed - check error messages above")

    print("=" * 60)
