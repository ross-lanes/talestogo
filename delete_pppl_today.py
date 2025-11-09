"""
Script to delete Queries, Competitors, and Descriptors created TODAY for Princeton Plasma Physics Laboratory.
Run this in Render backend shell.
"""
import datetime
from app.database import SessionLocal
from app import models

def delete_pppl_today_items():
    db = SessionLocal()
    try:
        # Find PPPL brand
        pppl = db.query(models.BrandInfo).filter(
            models.BrandInfo.brand_name.like('%Princeton%')
        ).first()

        if not pppl:
            print("ERROR: PPPL brand not found!")
            return

        print(f"Found brand: {pppl.brand_name}")
        print(f"Brand ID: {pppl.id}")
        print(f"User ID: {pppl.user_id}")

        # Get today's date (start of day in UTC)
        today_start = datetime.datetime.now(datetime.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        print(f"\n=== Searching for items created after: {today_start} ===\n")

        # Find queries created today
        queries_today = db.query(models.Query).filter(
            models.Query.brand_id == pppl.id,
            models.Query.user_id == pppl.user_id,
            models.Query.created_at >= today_start
        ).all()

        # Find competitors created today
        competitors_today = db.query(models.Competitor).filter(
            models.Competitor.brand_id == pppl.id,
            models.Competitor.user_id == pppl.user_id,
            models.Competitor.created_at >= today_start
        ).all()

        # Find descriptors created today
        descriptors_today = db.query(models.TargetDescriptor).filter(
            models.TargetDescriptor.brand_id == pppl.id,
            models.TargetDescriptor.user_id == pppl.user_id,
            models.TargetDescriptor.created_at >= today_start
        ).all()

        print(f"Found {len(queries_today)} queries created today")
        print(f"Found {len(competitors_today)} competitors created today")
        print(f"Found {len(descriptors_today)} descriptors created today")

        if len(queries_today) == 0 and len(competitors_today) == 0 and len(descriptors_today) == 0:
            print("\nNo items created today. Nothing to delete.")
            return

        # Show sample of what will be deleted
        print("\n=== PREVIEW OF ITEMS TO DELETE ===\n")

        if queries_today:
            print(f"Queries (showing first 5 of {len(queries_today)}):")
            for q in queries_today[:5]:
                print(f"  - query_id: {q.query_id}, created: {q.created_at}, text: {q.query_text[:60]}...")

        if competitors_today:
            print(f"\nCompetitors (showing first 5 of {len(competitors_today)}):")
            for c in competitors_today[:5]:
                print(f"  - org: {c.organization}, created: {c.created_at}")

        if descriptors_today:
            print(f"\nDescriptors (showing first 5 of {len(descriptors_today)}):")
            for d in descriptors_today[:5]:
                print(f"  - descriptor: {d.descriptor}, created: {d.created_at}")

        # Ask for confirmation
        print("\n" + "="*60)
        confirm = input(f"\nType 'DELETE' to confirm deletion of these {len(queries_today) + len(competitors_today) + len(descriptors_today)} items: ")

        if confirm != 'DELETE':
            print("Deletion cancelled.")
            return

        # Delete queries
        for query in queries_today:
            db.delete(query)

        # Delete competitors
        for competitor in competitors_today:
            db.delete(competitor)

        # Delete descriptors
        for descriptor in descriptors_today:
            db.delete(descriptor)

        db.commit()

        print(f"\n✓ Successfully deleted:")
        print(f"  - {len(queries_today)} queries")
        print(f"  - {len(competitors_today)} competitors")
        print(f"  - {len(descriptors_today)} descriptors")

    except Exception as e:
        db.rollback()
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    delete_pppl_today_items()
