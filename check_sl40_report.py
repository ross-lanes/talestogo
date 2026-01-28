"""Check if sl40 has a report generated"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.models import User, BrandInfo, Report

engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()

try:
    # Find sl40
    user = db.query(User).filter_by(email="sl40@princeton.edu").first()
    brand = db.query(BrandInfo).filter_by(user_id=user.id, brand_name="Princeton Engineering").first()

    print(f"\n{'='*80}")
    print(f"REPORTS FOR sl40@princeton.edu - Princeton Engineering")
    print(f"{'='*80}\n")

    # Get all reports for this user/brand
    reports = db.query(Report).filter(
        Report.user_id == user.id,
        Report.brand_id == brand.id
    ).order_by(Report.created_at.desc()).limit(5).all()

    if not reports:
        print("❌ No reports found")
    else:
        print(f"Found {len(reports)} report(s):\n")
        for i, report in enumerate(reports, 1):
            print(f"Report {i}:")
            print(f"  ID: {report.id}")
            print(f"  Created: {report.created_at}")
            print(f"  Report Date: {report.report_date}")
            print(f"  Total Responses: {report.total_responses}")
            print(f"  Has Markdown: {'Yes' if report.markdown_content else 'No'}")
            print(f"  Has Word Doc: {'Yes' if report.word_doc_path else 'No'}")
            if report.word_doc_path:
                print(f"  Word Doc Path: {report.word_doc_path}")
            print()

finally:
    db.close()
