#!/usr/bin/env python3
"""
Add outlier detection schema to NSTXView database.

This migration adds:
1. Outlier tracking columns to nstx_parameters
2. parameter_thresholds table for threshold configuration
3. threshold_history table for audit trail
4. ingestion_batches table for batch tracking
5. Indexes for performance

Run on DEV first, then PROD after testing.
"""

import os
import sys
from sqlalchemy import create_engine, text

def run_migration(database_url: str, dry_run: bool = False):
    """Run the migration."""
    print(f"🔧 Adding outlier detection schema...")
    print(f"📊 Database: {database_url.split('@')[1].split('/')[0]}")
    print(f"🧪 Dry run: {dry_run}\n")

    engine = create_engine(database_url)

    migrations = []

    # Migration 1: Add outlier tracking columns to nstx_parameters
    migrations.append(("Add outlier tracking columns to nstx_parameters", """
    -- Add outlier tracking columns
    ALTER TABLE nstx_parameters
    ADD COLUMN IF NOT EXISTS is_outlier BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS outlier_reason TEXT,
    ADD COLUMN IF NOT EXISTS flagged_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS flagged_by_threshold_id INTEGER,
    ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS reviewed_by INTEGER,
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS review_action VARCHAR(20),
    ADD COLUMN IF NOT EXISTS review_notes TEXT,
    ADD COLUMN IF NOT EXISTS corrected_value DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS corrected_unit VARCHAR(50);

    -- Add batch tracking
    ALTER TABLE nstx_parameters
    ADD COLUMN IF NOT EXISTS batch_id INTEGER DEFAULT 1;

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_nstx_parameters_outlier
    ON nstx_parameters(is_outlier) WHERE is_outlier = TRUE;

    CREATE INDEX IF NOT EXISTS idx_nstx_parameters_batch
    ON nstx_parameters(batch_id);

    CREATE INDEX IF NOT EXISTS idx_nstx_parameters_reviewed
    ON nstx_parameters(reviewed) WHERE reviewed = FALSE;
    """))

    # Migration 2: Create parameter_thresholds table
    migrations.append(("Create parameter_thresholds table", """
    CREATE TABLE IF NOT EXISTS parameter_thresholds (
        id SERIAL PRIMARY KEY,
        parameter_name VARCHAR(100) NOT NULL,
        parameter_pattern VARCHAR(200),
        min_value DOUBLE PRECISION,
        max_value DOUBLE PRECISION,
        expected_unit VARCHAR(50),
        category VARCHAR(50),
        reason_below TEXT,
        reason_above TEXT,
        flag_all BOOLEAN DEFAULT FALSE,
        special_case VARCHAR(50),
        source VARCHAR(200),
        active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW(),
        created_by INTEGER,
        notes TEXT
    );

    -- Create unique constraint for active thresholds
    CREATE UNIQUE INDEX IF NOT EXISTS idx_param_threshold_active
    ON parameter_thresholds(parameter_name)
    WHERE active = TRUE;
    """))

    # Migration 3: Create threshold_history table
    migrations.append(("Create threshold_history table", """
    CREATE TABLE IF NOT EXISTS threshold_history (
        id SERIAL PRIMARY KEY,
        parameter_name VARCHAR(100) NOT NULL,
        old_min DOUBLE PRECISION,
        old_max DOUBLE PRECISION,
        new_min DOUBLE PRECISION,
        new_max DOUBLE PRECISION,
        changed_by INTEGER NOT NULL,
        changed_at TIMESTAMP DEFAULT NOW(),
        reason TEXT,
        reprocessing_triggered BOOLEAN DEFAULT FALSE
    );

    CREATE INDEX IF NOT EXISTS idx_threshold_history_param
    ON threshold_history(parameter_name);

    CREATE INDEX IF NOT EXISTS idx_threshold_history_date
    ON threshold_history(changed_at DESC);
    """))

    # Migration 4: Create ingestion_batches table
    migrations.append(("Create ingestion_batches table", """
    CREATE TABLE IF NOT EXISTS ingestion_batches (
        id SERIAL PRIMARY KEY,
        batch_name VARCHAR(100),
        papers_processed INTEGER DEFAULT 0,
        measurements_extracted INTEGER DEFAULT 0,
        outliers_flagged INTEGER DEFAULT 0,
        started_at TIMESTAMP DEFAULT NOW(),
        completed_at TIMESTAMP,
        status VARCHAR(20) DEFAULT 'processing',
        error_message TEXT,
        triggered_by INTEGER,
        notes TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_ingestion_batches_status
    ON ingestion_batches(status);

    CREATE INDEX IF NOT EXISTS idx_ingestion_batches_date
    ON ingestion_batches(started_at DESC);
    """))

    # Migration 5: Create initial batch record
    migrations.append(("Create initial batch record", """
    INSERT INTO ingestion_batches (id, batch_name, papers_processed, started_at, completed_at, status, notes)
    SELECT 1, 'Initial Historical Data', COUNT(DISTINCT paper_id), MIN(created_at), MAX(created_at), 'completed',
           'All papers processed before outlier detection system was implemented'
    FROM nstx_parameters
    WHERE NOT EXISTS (SELECT 1 FROM ingestion_batches WHERE id = 1);
    """))

    # Execute migrations
    with engine.connect() as conn:
        for name, sql in migrations:
            print(f"📝 {name}...")
            if dry_run:
                print(f"   [DRY RUN] Would execute:\n{sql[:200]}...")
            else:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"   ✅ Success")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    conn.rollback()
                    raise

    if not dry_run:
        # Verify changes
        print("\n🔍 Verifying schema changes...")
        with engine.connect() as conn:
            # Check columns added
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'nstx_parameters'
                AND column_name IN ('is_outlier', 'batch_id', 'outlier_reason')
            """))
            cols = [row[0] for row in result]
            print(f"   ✅ Added columns to nstx_parameters: {', '.join(cols)}")

            # Check tables created
            result = conn.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_name IN ('parameter_thresholds', 'threshold_history', 'ingestion_batches')
                AND table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"   ✅ Created tables: {', '.join(tables)}")

            # Check batch record
            result = conn.execute(text("SELECT COUNT(*) FROM ingestion_batches"))
            count = result.fetchone()[0]
            print(f"   ✅ Batch records: {count}")

    print("\n✅ Migration complete!")
    return True

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Add outlier detection schema')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--prod', action='store_true', help='Run on PRODUCTION database (use with caution!)')
    args = parser.parse_args()

    # Get database URL
    if args.prod:
        db_url = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway"
        if not args.dry_run:
            confirm = input("⚠️  WARNING: This will modify PRODUCTION database. Type 'yes' to continue: ")
            if confirm.lower() != 'yes':
                print("❌ Aborted")
                return 1
    else:
        db_url = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway"

    try:
        run_migration(db_url, dry_run=args.dry_run)
        return 0
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
