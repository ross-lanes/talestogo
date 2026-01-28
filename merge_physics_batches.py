"""
Merge Physics of Plasmas batches that were split at midnight UTC.

This script merges Batch 2 and Batch 3 into a single batch, fixing the
midnight-crossing issue caused by the migration script.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys

# Production database URL
PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

def merge_batches():
    """Merge Batch 2 and Batch 3 into a single batch."""
    engine = create_engine(PROD_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("MERGING PHYSICS OF PLASMAS BATCHES")
        print("="*80)

        # Get info about both batches
        result = db.execute(text("""
            SELECT
                id,
                batch_name,
                started_at,
                completed_at,
                total_responses,
                total_queries
            FROM collection_batches
            WHERE id IN (2, 3)
            ORDER BY id
        """))

        batches = result.fetchall()

        if len(batches) != 2:
            print(f"\n❌ ERROR: Expected 2 batches, found {len(batches)}")
            return

        batch_2 = batches[0]
        batch_3 = batches[1]

        print(f"\nBatch 2: {batch_2[1]}")
        print(f"  Started: {batch_2[2]}")
        print(f"  Responses: {batch_2[4]}")

        print(f"\nBatch 3: {batch_3[1]}")
        print(f"  Started: {batch_3[2]}")
        print(f"  Responses: {batch_3[4]}")

        total_responses = batch_2[4] + batch_3[4]
        print(f"\n📊 Combined total: {total_responses} responses")

        # Confirm merge
        print(f"\n{'='*80}")
        print("MERGE PLAN:")
        print("  1. Move all responses from Batch 3 → Batch 2")
        print("  2. Update Batch 2 with combined totals")
        print("  3. Update Batch 2 completed_at to Batch 3's completed_at")
        print("  4. Delete Batch 3")
        print(f"{'='*80}\n")

        # Auto-confirm for non-interactive execution
        print("✅ Auto-proceeding with merge...\n")

        print("🔄 Merging batches...")

        # Step 1: Move all responses from Batch 3 to Batch 2
        result = db.execute(text("""
            UPDATE responses
            SET batch_id = 2
            WHERE batch_id = 3
        """))

        moved_count = result.rowcount
        print(f"  ✓ Moved {moved_count} responses from Batch 3 → Batch 2")

        # Step 2: Update Batch 2 with combined statistics
        db.execute(text("""
            UPDATE collection_batches
            SET
                total_responses = :total_responses,
                total_queries = :total_queries,
                completed_at = :completed_at,
                batch_name = 'Collection 2025-11-01 23:55:41'
            WHERE id = 2
        """), {
            'total_responses': total_responses,
            'total_queries': batch_2[5] + batch_3[5],
            'completed_at': batch_3[3]  # Use Batch 3's completed_at (end of collection)
        })

        print(f"  ✓ Updated Batch 2 with combined totals")

        # Step 3: Delete batch_analytics for Batch 3 (foreign key constraint)
        db.execute(text("""
            DELETE FROM batch_analytics
            WHERE batch_id = 3
        """))

        print(f"  ✓ Deleted batch_analytics for Batch 3")

        # Step 4: Delete Batch 3
        db.execute(text("""
            DELETE FROM collection_batches
            WHERE id = 3
        """))

        print(f"  ✓ Deleted Batch 3")

        # Commit all changes
        db.commit()

        print(f"\n{'='*80}")
        print("✅ MERGE COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")

        # Show final result
        result = db.execute(text("""
            SELECT
                id,
                batch_name,
                started_at,
                completed_at,
                total_responses,
                total_queries
            FROM collection_batches
            WHERE id = 2
        """))

        merged_batch = result.fetchone()

        print(f"\n📦 Merged Batch:")
        print(f"  ID: {merged_batch[0]}")
        print(f"  Name: {merged_batch[1]}")
        print(f"  Started: {merged_batch[2]}")
        print(f"  Completed: {merged_batch[3]}")
        print(f"  Total Responses: {merged_batch[4]}")
        print(f"  Total Queries: {merged_batch[5]}")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    merge_batches()
