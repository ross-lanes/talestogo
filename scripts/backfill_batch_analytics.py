"""
Backfill batch analytics for existing collection batches.

This script computes and caches analytics for all batches that don't
have cached analytics yet.
"""
import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models
from app.services.batch_analytics import backfill_all_batch_analytics


def main():
    db = SessionLocal()

    try:
        # Get all brands with batches
        brands = db.query(models.BrandInfo).all()

        print(f"Found {len(brands)} brands\n")

        total_processed = 0
        for brand in brands:
            print(f"\nProcessing brand: {brand.brand_name} (ID: {brand.id})")
            print(f"  User ID: {brand.user_id}")

            # Get batch count
            batch_count = db.query(models.CollectionBatch).filter(
                models.CollectionBatch.brand_id == brand.id,
                models.CollectionBatch.status == 'completed'
            ).count()

            print(f"  Completed batches: {batch_count}")

            if batch_count > 0:
                processed = backfill_all_batch_analytics(db, brand.user_id, brand.id)
                print(f"  ✓ Cached analytics for {processed} batches")
                total_processed += processed
            else:
                print(f"  (No completed batches to process)")

        print(f"\n{'='*60}")
        print(f"Total batches processed: {total_processed}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
