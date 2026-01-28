"""
Test script to generate a slideshow for Princeton Engineering
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.report_slideshow import generate_slideshow
from app import models

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_slideshow():
    db = SessionLocal()
    try:
        # Get Princeton Engineering brand (brand_id=14)
        brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == 14).first()
        if not brand:
            print("Brand not found!")
            return

        print(f"Found brand: {brand.brand_name} (ID: {brand.id}, Owner: {brand.user_id})")

        # Get the most recent report for this brand
        report = db.query(models.Report).filter(
            models.Report.user_id == brand.user_id
        ).order_by(models.Report.created_at.desc()).first()

        if not report:
            print("No reports found!")
            return

        print(f"Found report: {report.title} (ID: {report.id})")
        print(f"Generating slideshow with actual website images...")

        # Generate slideshow
        slideshow_bytes = generate_slideshow(
            markdown_content=report.report_content,
            title=report.title,
            db=db,
            user_id=brand.user_id,
            brand_id=brand.id
        )

        # Save to Downloads folder
        output_path = os.path.expanduser("~/Downloads/Princeton_Engineering_Slideshow_TEST.pptx")
        with open(output_path, 'wb') as f:
            f.write(slideshow_bytes.read())

        print(f"\n✅ Slideshow saved to: {output_path}")
        print(f"This slideshow uses the ACTUAL images from the website (from frontend/public/report_charts/)")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_slideshow()
