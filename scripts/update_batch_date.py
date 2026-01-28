#!/usr/bin/env python3
"""
Script to update a collection batch date.
Updates Princeton Plasma Physics Laboratory batch from Oct 25 to Nov 1, 2025.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models

def update_batch_date():
    db = SessionLocal()
    try:
        # Find the batch - looking for PPPL batch from Oct 25, 2025
        batches = db.query(models.CollectionBatch).filter(
            models.CollectionBatch.batch_name.ilike('%Princeton Plasma Physics%')
        ).all()

        print(f"Found {len(batches)} matching batches:")
        for batch in batches:
            print(f"  ID: {batch.id}, Name: {batch.batch_name}, Started: {batch.started_at}")

        if not batches:
            print("\nNo matching batches found. Let me search more broadly...")
            # Try searching by date range
            all_batches = db.query(models.CollectionBatch).order_by(
                models.CollectionBatch.started_at.desc()
            ).limit(20).all()
            print("\nRecent batches:")
            for batch in all_batches:
                print(f"  ID: {batch.id}, Name: {batch.batch_name}, Started: {batch.started_at}")
            return

        # Find the specific batch from Oct 25
        target_batch = None
        for batch in batches:
            if batch.started_at and batch.started_at.month == 10 and batch.started_at.day == 25:
                target_batch = batch
                break

        if not target_batch and batches:
            # Just use the first one if no exact match
            target_batch = batches[0]
            print(f"\nNo exact Oct 25 match, using first match: {target_batch.batch_name}")

        if target_batch:
            old_date = target_batch.started_at
            # New date: Nov 1, 2025 at 11:25 PM (same time zone as original)
            new_date = datetime(2025, 11, 1, 23, 25, 0)

            print(f"\nUpdating batch ID {target_batch.id}:")
            print(f"  Old started_at: {old_date}")
            print(f"  New started_at: {new_date}")

            target_batch.started_at = new_date

            # Also update completed_at if it exists (shift by same delta)
            if target_batch.completed_at:
                delta = new_date - old_date
                target_batch.completed_at = target_batch.completed_at + delta
                print(f"  New completed_at: {target_batch.completed_at}")

            db.commit()
            print("\nBatch date updated successfully!")

            # Also update BatchAnalytics if it exists
            batch_analytics = db.query(models.BatchAnalytics).filter(
                models.BatchAnalytics.batch_id == target_batch.id
            ).first()

            if batch_analytics:
                batch_analytics.collection_date = new_date
                db.commit()
                print("BatchAnalytics collection_date also updated!")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_batch_date()
