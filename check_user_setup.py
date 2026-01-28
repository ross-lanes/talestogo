"""
Check which users have queries, brands, and other data set up
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User, BrandInfo, Query, Competitor, TargetDescriptor, ScheduledTask

def check_user_setup(email):
    """Check if a user has queries and other data configured"""
    db = SessionLocal()

    try:
        user = db.query(User).filter_by(email=email).first()

        if not user:
            print(f"❌ {email}: User not found in database\n")
            return

        print(f"\n{'='*80}")
        print(f"USER: {email} (ID: {user.id})")
        print(f"{'='*80}")
        print(f"Name: {user.full_name if user.full_name else 'Not set'}")
        print(f"Organization: {user.organization if user.organization else 'Not set'}")
        print(f"Active: {'✅ Yes' if user.is_active else '❌ No'}")
        print(f"Admin: {'✅ Yes' if user.is_admin else 'No'}")
        print(f"Tenant ID: {user.tenant_id}")

        # Check brands
        brands = db.query(BrandInfo).filter_by(user_id=user.id).all()
        print(f"\n📦 BRANDS: {len(brands)}")
        if brands:
            for brand in brands:
                print(f"  - {brand.brand_name} (ID: {brand.id})")
        else:
            print(f"  ❌ No brands configured")

        # Check queries
        queries = db.query(Query).filter_by(user_id=user.id).all()
        print(f"\n❓ QUERIES: {len(queries)}")
        if queries:
            # Group by brand
            brand_queries = {}
            for query in queries:
                if query.brand_id not in brand_queries:
                    brand_queries[query.brand_id] = []
                brand_queries[query.brand_id].append(query)

            for brand_id, brand_query_list in brand_queries.items():
                brand = db.query(BrandInfo).filter_by(id=brand_id).first()
                brand_name = brand.brand_name if brand else f"Brand ID {brand_id}"
                print(f"\n  {brand_name}: {len(brand_query_list)} queries")
                for q in brand_query_list[:5]:  # Show first 5
                    print(f"    • {q.query_text[:70]}...")
                if len(brand_query_list) > 5:
                    print(f"    ... and {len(brand_query_list) - 5} more")
        else:
            print(f"  ❌ No queries configured")

        # Check competitors
        competitors = db.query(Competitor).filter_by(user_id=user.id).all()
        print(f"\n🏢 COMPETITORS: {len(competitors)}")
        if competitors:
            for comp in competitors[:10]:  # Show first 10
                brand = db.query(BrandInfo).filter_by(id=comp.brand_id).first()
                brand_name = brand.brand_name if brand else "Unknown"
                print(f"  - {comp.competitor_name} (for {brand_name})")
            if len(competitors) > 10:
                print(f"  ... and {len(competitors) - 10} more")
        else:
            print(f"  ⚠️  No competitors configured")

        # Check target descriptors
        descriptors = db.query(TargetDescriptor).filter_by(user_id=user.id).all()
        print(f"\n📝 TARGET DESCRIPTORS: {len(descriptors)}")
        if descriptors:
            for desc in descriptors[:10]:  # Show first 10
                brand = db.query(BrandInfo).filter_by(id=desc.brand_id).first()
                brand_name = brand.brand_name if brand else "Unknown"
                print(f"  - {desc.descriptor} (for {brand_name})")
            if len(descriptors) > 10:
                print(f"  ... and {len(descriptors) - 10} more")
        else:
            print(f"  ⚠️  No target descriptors configured")

        # Check scheduled tasks
        scheduled_tasks = db.query(ScheduledTask).filter_by(user_id=user.id).all()
        print(f"\n⏰ SCHEDULED TASKS: {len(scheduled_tasks)}")
        if scheduled_tasks:
            for task in scheduled_tasks:
                brand = db.query(BrandInfo).filter_by(id=task.brand_id).first()
                brand_name = brand.brand_name if brand else "Unknown"
                status = "✅ Enabled" if task.is_enabled else "❌ Disabled"
                print(f"  - {brand_name}: {task.schedule_type} ({status})")
                print(f"    Next run: {task.next_run_at if task.next_run_at else 'Not scheduled'}")
                print(f"    Last run: {task.last_run_at if task.last_run_at else 'Never'}")
        else:
            print(f"  ❌ No scheduled tasks configured")

        # Summary
        print(f"\n{'='*80}")
        print(f"READY TO COLLECT DATA?")
        print(f"{'='*80}")

        has_brands = len(brands) > 0
        has_queries = len(queries) > 0
        has_schedule = len([t for t in scheduled_tasks if t.is_enabled]) > 0

        print(f"  Brands:     {'✅' if has_brands else '❌'}")
        print(f"  Queries:    {'✅' if has_queries else '❌'}")
        print(f"  Schedule:   {'✅' if has_schedule else '❌'}")

        if has_brands and has_queries and has_schedule:
            print(f"\n✅ USER IS FULLY CONFIGURED - Collections should run automatically")
        elif has_brands and has_queries:
            print(f"\n⚠️  USER HAS DATA but NO SCHEDULED TASKS - Can run manual collections only")
        else:
            print(f"\n❌ USER IS NOT READY - Missing required data")

        print(f"{'='*80}\n")

    finally:
        db.close()


if __name__ == "__main__":
    target_emails = ['sl40@princeton.edu', 'wslyon@princeton.edu']

    for email in target_emails:
        check_user_setup(email)
