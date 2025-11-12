"""
Copy Virelyxa demo brand and all its data to Solstice tenant user.

This script:
- Finds the source Virelyxa brand (robotrachel@gmail.com)
- Finds the target Solstice user (skremen@solsticehc.net)
- Copies the brand and all associated data:
  - Collection batches
  - Responses
  - Batch analytics
  - Reports
- Sets the copied brand as active for the Solstice user
"""
import os
import sys
from datetime import datetime

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models

def main():
    """
    Copy Virelyxa brand and data to Solstice tenant user.
    """
    print("=" * 60)
    print("Copy Virelyxa Demo Data to Solstice Tenant")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 1. Find source user (robotrachel)
        source_user = db.query(models.User).filter(
            models.User.email == "robotrachel@gmail.com"
        ).first()

        if not source_user:
            print("❌ ERROR: Source user robotrachel@gmail.com not found!")
            return

        print(f"\n✓ Source user: {source_user.email} (ID: {source_user.id})")

        # 2. Find target user (Solstice)
        target_user = db.query(models.User).filter(
            models.User.email == "skremen@solsticehc.net"
        ).first()

        if not target_user:
            print("❌ ERROR: Target user skremen@solsticehc.net not found!")
            return

        print(f"✓ Target user: {target_user.email} (ID: {target_user.id})")
        print(f"  Tenant: {target_user.tenant_id}")

        # 3. Find source Virelyxa brand
        source_brand = db.query(models.BrandInfo).filter(
            models.BrandInfo.brand_name == "Virelyxa",
            models.BrandInfo.user_id == source_user.id
        ).first()

        if not source_brand:
            print("❌ ERROR: Source Virelyxa brand not found!")
            return

        print(f"\n✓ Source Virelyxa brand found (ID: {source_brand.id})")

        # 4. Check if target already has Virelyxa
        existing_brand = db.query(models.BrandInfo).filter(
            models.BrandInfo.brand_name == "Virelyxa",
            models.BrandInfo.user_id == target_user.id
        ).first()

        if existing_brand:
            print(f"\n⚠️  Target user already has Virelyxa brand (ID: {existing_brand.id})")
            response = input("Delete existing Virelyxa and recreate? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                return

            # Delete existing data
            print("\nDeleting existing Virelyxa data for target user...")
            db.query(models.Report).filter(models.Report.brand_id == existing_brand.id).delete()
            db.query(models.BatchAnalytics).filter(models.BatchAnalytics.brand_id == existing_brand.id).delete()
            db.query(models.Response).filter(models.Response.brand_id == existing_brand.id).delete()
            db.query(models.CollectionBatch).filter(models.CollectionBatch.brand_id == existing_brand.id).delete()
            db.query(models.BrandInfo).filter(models.BrandInfo.id == existing_brand.id).delete()
            db.commit()
            print("  ✓ Existing data deleted")

        # 5. Copy the brand
        print("\nCopying Virelyxa brand...")
        new_brand = models.BrandInfo(
            user_id=target_user.id,
            tenant_id=target_user.tenant_id,
            brand_name=source_brand.brand_name,
            website_url=source_brand.website_url,
            industry=source_brand.industry,
            description=source_brand.description,
            strategic_messages=source_brand.strategic_messages,
            is_active=True,
            created_at=datetime.utcnow()
        )
        db.add(new_brand)
        db.commit()
        db.refresh(new_brand)
        print(f"  ✓ Brand copied (New ID: {new_brand.id})")

        # 6. Get all collection batches for source brand
        source_batches = db.query(models.CollectionBatch).filter(
            models.CollectionBatch.brand_id == source_brand.id
        ).order_by(models.CollectionBatch.started_at).all()

        print(f"\n✓ Found {len(source_batches)} collection batches to copy")

        batch_id_mapping = {}  # Maps old batch_id to new batch_id

        for i, source_batch in enumerate(source_batches, 1):
            print(f"\nCopying batch {i}/{len(source_batches)}...")

            # Copy batch
            new_batch = models.CollectionBatch(
                user_id=target_user.id,
                brand_id=new_brand.id,
                tenant_id=target_user.tenant_id,
                started_at=source_batch.started_at,
                completed_at=source_batch.completed_at,
                status=source_batch.status,
                total_queries=source_batch.total_queries,
                queries_completed=source_batch.queries_completed,
                total_responses=source_batch.total_responses
            )
            db.add(new_batch)
            db.commit()
            db.refresh(new_batch)

            batch_id_mapping[source_batch.id] = new_batch.id
            print(f"  ✓ Batch copied (Old ID: {source_batch.id} → New ID: {new_batch.id})")

            # Copy responses for this batch
            source_responses = db.query(models.Response).filter(
                models.Response.batch_id == source_batch.id
            ).all()

            for source_response in source_responses:
                new_response = models.Response(
                    user_id=target_user.id,
                    brand_id=new_brand.id,
                    batch_id=new_batch.id,
                    tenant_id=target_user.tenant_id,
                    query_id=source_response.query_id,
                    query_text=source_response.query_text,
                    platform=source_response.platform,
                    response_text=source_response.response_text,
                    brand_mentioned=source_response.brand_mentioned,
                    brand_position=source_response.brand_position,
                    competitors_mentioned=source_response.competitors_mentioned,
                    descriptors=source_response.descriptors,
                    sentiment=source_response.sentiment,
                    created_at=source_response.created_at
                )
                db.add(new_response)

            db.commit()
            print(f"  ✓ {len(source_responses)} responses copied")

            # Copy batch analytics
            source_analytics = db.query(models.BatchAnalytics).filter(
                models.BatchAnalytics.batch_id == source_batch.id
            ).first()

            if source_analytics:
                new_analytics = models.BatchAnalytics(
                    user_id=target_user.id,
                    brand_id=new_brand.id,
                    batch_id=new_batch.id,
                    tenant_id=target_user.tenant_id,
                    total_responses=source_analytics.total_responses,
                    mention_count=source_analytics.mention_count,
                    mention_rate=source_analytics.mention_rate,
                    leader_count=source_analytics.leader_count,
                    featured_count=source_analytics.featured_count,
                    listed_count=source_analytics.listed_count,
                    not_mentioned_count=source_analytics.not_mentioned_count,
                    very_positive_count=source_analytics.very_positive_count,
                    positive_count=source_analytics.positive_count,
                    neutral_count=source_analytics.neutral_count,
                    negative_count=source_analytics.negative_count,
                    very_negative_count=source_analytics.very_negative_count,
                    mixed_count=source_analytics.mixed_count,
                    sov_data=source_analytics.sov_data,
                    descriptor_data=source_analytics.descriptor_data,
                    computed_at=source_analytics.computed_at
                )
                db.add(new_analytics)
                db.commit()
                print(f"  ✓ Batch analytics copied")

            # Copy report
            source_report = db.query(models.Report).filter(
                models.Report.brand_id == source_brand.id,
                models.Report.start_date == source_batch.started_at
            ).first()

            if source_report:
                new_report = models.Report(
                    user_id=target_user.id,
                    brand_id=new_brand.id,
                    tenant_id=target_user.tenant_id,
                    title=source_report.title,
                    report_content=source_report.report_content,
                    start_date=source_report.start_date,
                    end_date=source_report.end_date,
                    total_responses=source_report.total_responses,
                    mention_rate=source_report.mention_rate,
                    created_at=source_report.created_at
                )
                db.add(new_report)
                db.commit()
                print(f"  ✓ Report copied")

        print("\n" + "=" * 60)
        print("✓ Copy complete!")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  • Brand: Virelyxa (ID: {new_brand.id})")
        print(f"  • User: {target_user.email}")
        print(f"  • Tenant: {target_user.tenant_id}")
        print(f"  • Batches copied: {len(source_batches)}")
        print(f"  • Brand set to active: Yes")
        print(f"\nThe Solstice user now has a complete copy of Virelyxa demo data!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
