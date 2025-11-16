"""Send email notification to sl40 about completed report"""
import os
import sys
import asyncio
from datetime import datetime

PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"
os.environ['DATABASE_URL'] = PROD_DATABASE_URL

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, BrandInfo, Report, CollectionBatch
from app.email import send_email

engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def send_notification():
    db = SessionLocal()

    try:
        # Find sl40
        user = db.query(User).filter_by(email="sl40@princeton.edu").first()
        brand = db.query(BrandInfo).filter_by(user_id=user.id, brand_name="Princeton Engineering").first()

        # Get latest batch
        batch = db.query(CollectionBatch).filter(
            CollectionBatch.user_id == user.id,
            CollectionBatch.brand_id == brand.id
        ).order_by(CollectionBatch.started_at.desc()).first()

        # Get latest report
        report = db.query(Report).filter(
            Report.user_id == user.id,
            Report.brand_id == brand.id
        ).order_by(Report.created_at.desc()).first()

        print(f"\n{'='*80}")
        print(f"SENDING EMAIL NOTIFICATION TO sl40@princeton.edu")
        print(f"{'='*80}\n")

        subject = f"TALES Monthly Report - {brand.brand_name}"

        body = f"""Your scheduled monthly data collection and analysis has completed successfully!

Brand: {brand.brand_name}
Collection Date: {batch.started_at.strftime('%B %d, %Y')}
Responses Collected: {batch.total_responses}
Responses Analyzed: {batch.total_responses}

View your results: https://tales.robotrachel.com/analytics

Next scheduled run: December 1, 2025 at 3:30 AM

--
TALES - AI Reputation Intelligence & Optimization
"""

        print(f"To: {user.email}")
        print(f"Subject: {subject}")
        print(f"\nBody:\n{body}\n")

        await send_email(user.email, subject, body)

        print(f"\n✅ Email sent successfully to {user.email}")

    finally:
        db.close()

# Run the async function
asyncio.run(send_notification())
