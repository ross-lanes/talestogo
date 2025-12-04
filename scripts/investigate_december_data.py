#!/usr/bin/env python3
"""
Script to investigate why December has 176 data points instead of 88.
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models
from sqlalchemy import func

def investigate():
    db = SessionLocal()
    try:
        # Get all December 2025 batches
        print("=== December 2025 Collection Batches ===")
        december_batches = db.query(models.CollectionBatch).filter(
            func.extract('month', models.CollectionBatch.started_at) == 12,
            func.extract('year', models.CollectionBatch.started_at) == 2025
        ).order_by(models.CollectionBatch.started_at).all()

        print(f"Found {len(december_batches)} December batches:\n")

        total_december_responses = 0
        for batch in december_batches:
            # Count responses for this batch
            response_count = db.query(func.count(models.Response.id)).filter(
                models.Response.batch_id == batch.id
            ).scalar()

            total_december_responses += response_count

            print(f"Batch ID: {batch.id}")
            print(f"  Name: {batch.batch_name}")
            print(f"  User ID: {batch.user_id}")
            print(f"  Started: {batch.started_at}")
            print(f"  Completed: {batch.completed_at}")
            print(f"  Status: {batch.status}")
            print(f"  Response Count: {response_count}")
            print()

        print(f"TOTAL December responses: {total_december_responses}")

        # Check for duplicate prompts within December
        print("\n=== Checking for duplicate prompts in December ===")

        # Get all December batch IDs
        december_batch_ids = [b.id for b in december_batches]

        if december_batch_ids:
            # Find prompts that appear more than once
            duplicate_check = db.query(
                models.Response.prompt_id,
                models.Response.platform,
                func.count(models.Response.id).label('count')
            ).filter(
                models.Response.batch_id.in_(december_batch_ids)
            ).group_by(
                models.Response.prompt_id,
                models.Response.platform
            ).having(
                func.count(models.Response.id) > 1
            ).all()

            if duplicate_check:
                print(f"Found {len(duplicate_check)} prompt/platform combinations with duplicates:")
                for dup in duplicate_check[:10]:  # Show first 10
                    prompt = db.query(models.Prompt).filter(models.Prompt.id == dup.prompt_id).first()
                    print(f"  Prompt ID {dup.prompt_id} ({prompt.category if prompt else 'Unknown'}), Platform: {dup.platform}, Count: {dup.count}")
            else:
                print("No duplicate prompt/platform combinations found within December batches.")

        # Compare with November to understand expected count
        print("\n=== November 2025 Comparison ===")
        november_batches = db.query(models.CollectionBatch).filter(
            func.extract('month', models.CollectionBatch.started_at) == 11,
            func.extract('year', models.CollectionBatch.started_at) == 2025
        ).order_by(models.CollectionBatch.started_at).all()

        print(f"Found {len(november_batches)} November batches:\n")

        total_november_responses = 0
        for batch in november_batches:
            response_count = db.query(func.count(models.Response.id)).filter(
                models.Response.batch_id == batch.id
            ).scalar()
            total_november_responses += response_count
            print(f"Batch ID: {batch.id}")
            print(f"  Name: {batch.batch_name}")
            print(f"  Response Count: {response_count}")
            print()

        print(f"TOTAL November responses: {total_november_responses}")

        # Check unique prompts and platforms
        print("\n=== Prompt and Platform Breakdown ===")
        for batch in december_batches:
            unique_prompts = db.query(func.count(func.distinct(models.Response.prompt_id))).filter(
                models.Response.batch_id == batch.id
            ).scalar()

            unique_platforms = db.query(func.distinct(models.Response.platform)).filter(
                models.Response.batch_id == batch.id
            ).all()

            platforms = [p[0] for p in unique_platforms]

            print(f"Batch {batch.id} ({batch.batch_name}):")
            print(f"  Unique prompts: {unique_prompts}")
            print(f"  Platforms: {platforms}")
            print(f"  Expected (prompts × platforms): {unique_prompts * len(platforms)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    investigate()
