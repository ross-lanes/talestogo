#!/usr/bin/env python3
"""
Migration: Add collection batches table and batch_id to responses

This migration adds:
1. A new 'collection_batches' table to track data collection runs
2. A 'batch_id' column to the responses table to link responses to batches
3. Automatically creates a batch for existing responses based on their timestamp

Usage:
    DATABASE_URL="your_db_url" python3 migrations/add_collection_batches.py
"""

import os
import sys
import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import sessionmaker

def run_migration(database_url: str):
    """Run the migration to add collection batches."""

    engine = create_engine(database_url)

    print("="*70)
    print("MIGRATION: Add Collection Batches")
    print("="*70)
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    print("="*70 + "\n")

    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()

        try:
            # Step 1: Create collection_batches table
            print("Step 1: Creating collection_batches table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS collection_batches (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    brand_id INTEGER REFERENCES brand_info(id),
                    batch_name VARCHAR(200) NOT NULL,
                    description TEXT,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'in_progress',
                    total_queries INTEGER DEFAULT 0,
                    total_responses INTEGER DEFAULT 0,
                    platforms TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            print("✓ Created collection_batches table\n")

            # Step 2: Add indexes to collection_batches
            print("Step 2: Adding indexes to collection_batches...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_collection_batches_user_id
                ON collection_batches(user_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_collection_batches_brand_id
                ON collection_batches(brand_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_collection_batches_started_at
                ON collection_batches(started_at)
            """))
            print("✓ Created indexes\n")

            # Step 3: Add batch_id column to responses table
            print("Step 3: Adding batch_id column to responses...")
            conn.execute(text("""
                ALTER TABLE responses
                ADD COLUMN IF NOT EXISTS batch_id INTEGER
                REFERENCES collection_batches(id)
            """))
            print("✓ Added batch_id column to responses\n")

            # Step 4: Create index on responses.batch_id
            print("Step 4: Creating index on responses.batch_id...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_responses_batch_id
                ON responses(batch_id)
            """))
            print("✓ Created index\n")

            # Step 5: Group existing responses into batches by date and user
            print("Step 5: Creating batches for existing responses...")

            # Get distinct dates with responses
            result = conn.execute(text("""
                SELECT
                    user_id,
                    brand_id,
                    DATE(timestamp) as collection_date,
                    MIN(timestamp) as started_at,
                    MAX(timestamp) as completed_at,
                    COUNT(*) as response_count,
                    COUNT(DISTINCT query_id) as query_count,
                    STRING_AGG(DISTINCT platform, ', ' ORDER BY platform) as platforms
                FROM responses
                WHERE batch_id IS NULL
                GROUP BY user_id, brand_id, DATE(timestamp)
                ORDER BY user_id, brand_id, collection_date
            """))

            existing_collections = result.fetchall()

            if len(existing_collections) > 0:
                print(f"  Found {len(existing_collections)} existing collection dates to batch\n")

                for row in existing_collections:
                    user_id = row[0]
                    brand_id = row[1]
                    collection_date = row[2]
                    started_at = row[3]
                    completed_at = row[4]
                    response_count = row[5]
                    query_count = row[6]
                    platforms = row[7]

                    # Create batch name
                    batch_name = f"Collection {collection_date.strftime('%Y-%m-%d')}"

                    # Insert batch record
                    insert_result = conn.execute(text("""
                        INSERT INTO collection_batches
                        (user_id, brand_id, batch_name, started_at, completed_at,
                         status, total_queries, total_responses, platforms,
                         description, created_at)
                        VALUES
                        (:user_id, :brand_id, :batch_name, :started_at, :completed_at,
                         'completed', :total_queries, :total_responses, :platforms,
                         'Auto-generated batch from existing responses', NOW())
                        RETURNING id
                    """), {
                        'user_id': user_id,
                        'brand_id': brand_id,
                        'batch_name': batch_name,
                        'started_at': started_at,
                        'completed_at': completed_at,
                        'total_queries': query_count,
                        'total_responses': response_count,
                        'platforms': platforms
                    })

                    batch_id = insert_result.fetchone()[0]

                    # Update responses with batch_id
                    conn.execute(text("""
                        UPDATE responses
                        SET batch_id = :batch_id
                        WHERE user_id = :user_id
                        AND brand_id = :brand_id
                        AND DATE(timestamp) = :collection_date
                        AND batch_id IS NULL
                    """), {
                        'batch_id': batch_id,
                        'user_id': user_id,
                        'brand_id': brand_id,
                        'collection_date': collection_date
                    })

                    print(f"  ✓ Created batch '{batch_name}' (ID: {batch_id}) with {response_count} responses")

                print(f"\n✓ Successfully created {len(existing_collections)} batches\n")
            else:
                print("  No existing responses to batch\n")

            # Commit transaction
            trans.commit()

            print("="*70)
            print("✓ MIGRATION COMPLETED SUCCESSFULLY")
            print("="*70)
            print("\nNext steps:")
            print("1. Update your collection API to create batch records")
            print("2. Add batch selection UI to analysis/reporting pages")
            print("3. Update analytics functions to filter by batch_id")
            print()

        except Exception as e:
            trans.rollback()
            print(f"\n✗ ERROR: {str(e)}")
            print("Migration rolled back - no changes made")
            raise


if __name__ == '__main__':
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("\nUsage:")
        print('  DATABASE_URL="postgresql://user:pass@host/db" python3 migrations/add_collection_batches.py')
        sys.exit(1)

    # Confirm before running
    print("\nThis migration will:")
    print("  1. Create a new 'collection_batches' table")
    print("  2. Add 'batch_id' column to responses table")
    print("  3. Create batches for existing responses grouped by date")
    print()

    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Migration cancelled")
        sys.exit(0)

    run_migration(database_url)
