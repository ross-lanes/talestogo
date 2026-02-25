"""
Manually compute batch analytics for all completed batches in Render database.
This is needed because automatic analysis wasn't running after data collection.
"""
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models
from app.services.batch_analytics import compute_batch_analytics

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

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

        for batch in batches:
            print(f"\nProcessing batch {batch.id}:")
            print(f"  User ID: {batch.user_id}")
            print(f"  Brand ID: {batch.brand_id}")
            print(f"  Created: {batch.created_at}")

            # Check if analytics already exist
            existing = db.query(models.BatchAnalytics).filter(
                models.BatchAnalytics.batch_id == batch.id
            ).first()

            if existing:
                print(f"  ✓ Analytics already exist (id={existing.id})")
                continue

            # Compute analytics
            analytics = compute_batch_analytics(
                db=db,
                batch_id=batch.id,
                user_id=batch.user_id,
                brand_id=batch.brand_id
            )

            if analytics:
                db.commit()
                print(f"  ✓ Created analytics (id={analytics.id})")
                print(f"    Mention rate: {analytics.mention_rate}%")
                print(f"    Total responses: {analytics.total_responses}")
            else:
                print(f"  ✗ No responses found for this batch")

        print(f"\n✓ Done! Computed analytics for all batches.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
