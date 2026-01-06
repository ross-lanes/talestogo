"""
Recompute batch analytics for all completed batches to use organic-only queries.

This script forces recomputation of all BatchAnalytics records to apply the new
logic that only counts organic queries (brand_in_query=False) for brand mention
metrics. This ensures accurate visibility metrics that measure true organic brand
mentions rather than mentions when users explicitly ask about the brand.

Usage:
    DATABASE_URL="postgresql://..." python3 scripts/admin/recompute_batch_analytics_organic.py
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models
from app.services.batch_analytics import compute_batch_analytics

# Get database URL from environment or use production URL
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    print("Usage: DATABASE_URL='postgresql://...' python3 scripts/admin/recompute_batch_analytics_organic.py")
    sys.exit(1)

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def main():
    db = SessionLocal()

    try:
        # Get all completed collection batches
        batches = db.query(models.CollectionBatch).filter(
            models.CollectionBatch.status == 'completed'
        ).all()

        print(f"Found {len(batches)} completed collection batches")
        print("Recomputing all batch analytics to use organic-only queries...\n")

        recomputed = 0
        for batch in batches:
            print(f"Processing batch {batch.id}:")
            print(f"  User ID: {batch.user_id}")
            print(f"  Brand ID: {batch.brand_id}")
            print(f"  Name: {batch.batch_name}")

            # Check if analytics already exist
            existing = db.query(models.BatchAnalytics).filter(
                models.BatchAnalytics.batch_id == batch.id
            ).first()

            old_mention_rate = None
            old_total = None
            if existing:
                old_mention_rate = existing.mention_rate
                old_total = existing.total_responses
                print(f"  Old: {old_mention_rate}% mention rate ({old_total} responses)")

            # Force recompute analytics (compute_batch_analytics will update existing records)
            analytics = compute_batch_analytics(
                db=db,
                batch_id=batch.id,
                user_id=batch.user_id,
                brand_id=batch.brand_id
            )

            if analytics:
                db.commit()
                print(f"  New: {analytics.mention_rate}% mention rate ({analytics.total_responses} organic responses)")
                if old_mention_rate is not None:
                    diff = analytics.mention_rate - old_mention_rate
                    diff_total = analytics.total_responses - old_total
                    print(f"  Change: {diff:+}% mention rate, {diff_total:+} responses")
                recomputed += 1
            else:
                print(f"  No responses found for this batch")

            print()

        print(f"Done! Recomputed analytics for {recomputed} batches.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
