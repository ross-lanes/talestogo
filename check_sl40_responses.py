"""Check if sl40's responses were collected"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.models import Response, User, BrandInfo, CollectionBatch

engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

try:
    # Find sl40
    user = db.query(User).filter_by(email="sl40@princeton.edu").first()
    brand = db.query(BrandInfo).filter_by(user_id=user.id, brand_name="Princeton Engineering").first()

    print(f"\n{'='*80}")
    print(f"RESPONSES FOR sl40@princeton.edu - Princeton Engineering")
    print(f"{'='*80}\n")

    # Get responses from last hour
    cutoff = datetime.utcnow() - timedelta(hours=1)
    recent_responses = db.query(Response).filter(
        Response.user_id == user.id,
        Response.brand_id == brand.id,
        Response.timestamp >= cutoff
    ).order_by(Response.timestamp.desc()).all()

    print(f"Found {len(recent_responses)} responses collected in the last hour\n")

    # Check latest batch
    latest_batch = db.query(CollectionBatch).filter(
        CollectionBatch.user_id == user.id,
        CollectionBatch.brand_id == brand.id
    ).order_by(CollectionBatch.started_at.desc()).first()

    if latest_batch:
        print(f"Latest Batch:")
        print(f"  ID: {latest_batch.id}")
        print(f"  Name: {latest_batch.batch_name}")
        print(f"  Started: {latest_batch.started_at}")
        print(f"  Status: {latest_batch.status}")
        print(f"  Total Responses: {latest_batch.total_responses}")
        print(f"  Platforms: {latest_batch.platforms}")

        # Check how many are analyzed
        analyzed_count = db.query(Response).filter(
            Response.user_id == user.id,
            Response.brand_id == brand.id,
            Response.batch_id == latest_batch.id,
            Response.analyzed_at.isnot(None)
        ).count()

        print(f"  Analyzed: {analyzed_count}/{latest_batch.total_responses}")

finally:
    db.close()
