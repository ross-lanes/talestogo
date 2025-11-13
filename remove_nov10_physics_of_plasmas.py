"""
Script to remove all data from November 10, 2025 for the "Physics of Plasmas" brand.

This script will:
1. Find the brand_id for "Physics of Plasmas"
2. Delete all responses from November 10, 2025 for that brand
3. Delete collection batches that were created on November 10, 2025
4. Delete batch analytics for those batches
5. Print a summary of deleted records

Usage:
    python remove_nov10_physics_of_plasmas.py
"""

import os
import sys
from datetime import datetime, date
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import DATABASE_URL
from app.models import BrandInfo, Response, CollectionBatch, BatchAnalytics

def main():
    """Remove all data from November 10, 2025 for Physics of Plasmas brand."""

    # Create database connection
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("=" * 70)
        print("PHYSICS OF PLASMAS - NOVEMBER 10, 2025 DATA REMOVAL")
        print("=" * 70)
        print()

        # Step 1: Find the brand
        print("Step 1: Finding 'Physics of Plasmas' brand...")
        brand = db.query(BrandInfo).filter(
            BrandInfo.brand_name == "Physics of Plasmas"
        ).first()

        if not brand:
            print("ERROR: Brand 'Physics of Plasmas' not found in database!")
            print("\nAvailable brands:")
            brands = db.query(BrandInfo).all()
            for b in brands:
                print(f"  - {b.brand_name} (ID: {b.id})")
            return

        print(f"✓ Found brand: {brand.brand_name} (ID: {brand.id})")
        print()

        # Define the target date (November 10, 2025)
        target_date = date(2025, 11, 10)

        # Step 2: Find collection batches from November 10, 2025
        print("Step 2: Finding collection batches from November 10, 2025...")
        batches = db.query(CollectionBatch).filter(
            and_(
                CollectionBatch.brand_id == brand.id,
                func.date(CollectionBatch.started_at) == target_date
            )
        ).all()

        print(f"✓ Found {len(batches)} collection batch(es) from November 10, 2025")
        if batches:
            for batch in batches:
                print(f"  - {batch.batch_name} (ID: {batch.id}, Started: {batch.started_at})")
        print()

        # Step 3: Count responses to be deleted
        print("Step 3: Counting responses from November 10, 2025...")
        response_count = db.query(Response).filter(
            and_(
                Response.brand_id == brand.id,
                func.date(Response.timestamp) == target_date
            )
        ).count()

        print(f"✓ Found {response_count} response(s) from November 10, 2025")
        print()

        # Step 4: Count batch analytics to be deleted
        batch_ids = [b.id for b in batches]
        analytics_count = 0
        if batch_ids:
            analytics_count = db.query(BatchAnalytics).filter(
                BatchAnalytics.batch_id.in_(batch_ids)
            ).count()
            print(f"✓ Found {analytics_count} batch analytics record(s) to delete")
        print()

        # Confirm deletion
        print("=" * 70)
        print("DELETION SUMMARY")
        print("=" * 70)
        print(f"Brand: {brand.brand_name} (ID: {brand.id})")
        print(f"Target Date: November 10, 2025")
        print(f"Responses to delete: {response_count}")
        print(f"Collection batches to delete: {len(batches)}")
        print(f"Batch analytics to delete: {analytics_count}")
        print()

        confirmation = input("Are you sure you want to delete this data? Type 'YES' to confirm: ")

        if confirmation != "YES":
            print("\nDeletion cancelled. No data was removed.")
            return

        print("\nProceeding with deletion...")
        print()

        # Step 5: Delete batch analytics
        if batch_ids:
            print("Deleting batch analytics...")
            deleted_analytics = db.query(BatchAnalytics).filter(
                BatchAnalytics.batch_id.in_(batch_ids)
            ).delete(synchronize_session=False)
            print(f"✓ Deleted {deleted_analytics} batch analytics record(s)")

        # Step 6: Delete responses
        print("Deleting responses...")
        deleted_responses = db.query(Response).filter(
            and_(
                Response.brand_id == brand.id,
                func.date(Response.timestamp) == target_date
            )
        ).delete(synchronize_session=False)
        print(f"✓ Deleted {deleted_responses} response(s)")

        # Step 7: Delete collection batches
        print("Deleting collection batches...")
        deleted_batches = db.query(CollectionBatch).filter(
            and_(
                CollectionBatch.brand_id == brand.id,
                func.date(CollectionBatch.started_at) == target_date
            )
        ).delete(synchronize_session=False)
        print(f"✓ Deleted {deleted_batches} collection batch(es)")

        # Commit the changes
        db.commit()

        print()
        print("=" * 70)
        print("DELETION COMPLETE")
        print("=" * 70)
        print(f"Successfully removed all data from November 10, 2025")
        print(f"for the '{brand.brand_name}' brand.")
        print()

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("Rolling back changes...")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    main()
