#!/usr/bin/env python3
"""
Check status of Oak Ridge National Laboratory data
"""

import sys
from app.database import SessionLocal
from app.models import User, BrandInfo, Response, CollectionBatch, Report
from sqlalchemy import func

def main():
    db = SessionLocal()

    try:
        # Find user
        user = db.query(User).filter(User.email == "robotrachel@gmail.com").first()
        if not user:
            print("❌ User robotrachel@gmail.com not found")
            return

        print(f"✓ User found: {user.email} (ID: {user.id})")
        print()

        # Find ORNL brand
        ornl = db.query(BrandInfo).filter(
            BrandInfo.user_id == user.id,
            BrandInfo.brand_name.ilike("%oak ridge%")
        ).first()

        if not ornl:
            print("❌ Oak Ridge National Laboratory brand not found")
            print("\n📋 All brands for this user:")
            brands = db.query(BrandInfo).filter(BrandInfo.user_id == user.id).all()
            for brand in brands:
                print(f"  • {brand.brand_name} (ID: {brand.id}, Active: {brand.is_active})")
            return

        print(f"✓ Brand found: {ornl.brand_name}")
        print(f"  Brand ID: {ornl.id}")
        print(f"  Active: {ornl.is_active}")
        print()

        # Check collection batches
        batches = db.query(CollectionBatch).filter(
            CollectionBatch.user_id == user.id,
            CollectionBatch.brand_id == ornl.id
        ).order_by(CollectionBatch.started_at.desc()).all()

        print(f"📊 Collection Batches: {len(batches)}")
        if batches:
            for batch in batches:
                print(f"  • Batch {batch.id}: {batch.batch_name}")
                print(f"    Status: {batch.status}")
                print(f"    Started: {batch.started_at}")
                print(f"    Completed: {batch.completed_at}")
                print()
        else:
            print("  ⚠️  No collection batches found")
            print()

        # Check responses
        total_responses = db.query(func.count(Response.id)).filter(
            Response.user_id == user.id,
            Response.brand_id == ornl.id
        ).scalar()

        analyzed_responses = db.query(func.count(Response.id)).filter(
            Response.user_id == user.id,
            Response.brand_id == ornl.id,
            Response.analyzed_at.isnot(None)
        ).scalar()

        unanalyzed = total_responses - analyzed_responses

        print(f"📝 Responses:")
        print(f"  Total collected: {total_responses}")
        print(f"  Analyzed: {analyzed_responses}")
        print(f"  Unanalyzed: {unanalyzed}")
        print()

        if total_responses > 0:
            # Show sample response
            sample = db.query(Response).filter(
                Response.user_id == user.id,
                Response.brand_id == ornl.id
            ).first()
            print(f"📄 Sample Response:")
            print(f"  Platform: {sample.platform}")
            print(f"  Query: {sample.query_text[:80]}...")
            print(f"  Timestamp: {sample.timestamp}")
            print(f"  Analyzed at: {sample.analyzed_at}")
            if sample.analyzed_at:
                print(f"  Brand mentioned: {sample.brand_mentioned}")
                print(f"  Position: {sample.brand_position}")
                print(f"  Sentiment: {sample.sentiment}")
            print()

        # Check reports
        reports = db.query(Report).filter(
            Report.user_id == user.id,
            Report.brand_id == ornl.id
        ).order_by(Report.generated_at.desc()).all()

        print(f"📑 Reports: {len(reports)}")
        if reports:
            for report in reports[:3]:  # Show last 3 reports
                print(f"  • Report generated at {report.generated_at}")
                print(f"    Report type: {report.report_type}")
        else:
            print("  ⚠️  No reports found")
        print()

        # Diagnosis
        print("=" * 60)
        print("🔍 DIAGNOSIS:")
        print("=" * 60)

        if total_responses == 0:
            print("❌ ISSUE: No data collected for Oak Ridge National Laboratory")
            print("   → Run data collection for this brand")
        elif unanalyzed > 0:
            print(f"⚠️  ISSUE: {unanalyzed} responses need to be analyzed")
            print("   → Run: railway run python scripts/admin/analyze_responses.py --brand-name 'Oak Ridge National Laboratory'")
        elif analyzed_responses > 0 and len(reports) == 0:
            print("⚠️  ISSUE: Data is analyzed but no report generated")
            print("   → Run: railway run python scripts/admin/generate_report.py --brand-name 'Oak Ridge National Laboratory'")
        elif analyzed_responses > 0 and len(reports) > 0:
            print("✓ Data looks good!")
            print("  → If analytics pages show no data, check:")
            print("     1. Is Oak Ridge National Laboratory the active/selected brand in the UI?")
            print("     2. Is the correct batch selected in the batch filter?")

    finally:
        db.close()

if __name__ == "__main__":
    main()
