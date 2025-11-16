"""
Check production database for user setup and recent collections
"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Production database URL
PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import User, BrandInfo, Query, ScheduledTask, ScheduledTaskHistory

# Create production database connection
engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_production_users():
    """Check production database for user configuration"""
    db = SessionLocal()

    try:
        # First, list all users
        users = db.query(User).all()

        print(f"\n{'='*80}")
        print(f"PRODUCTION DATABASE - ALL USERS ({len(users)} total)")
        print(f"{'='*80}\n")

        for user in users:
            brands_count = db.query(BrandInfo).filter_by(user_id=user.id).count()
            queries_count = db.query(Query).filter_by(user_id=user.id).count()
            schedules_count = db.query(ScheduledTask).filter_by(user_id=user.id, is_enabled=True).count()

            print(f"{'-'*80}")
            print(f"Email:     {user.email}")
            print(f"Name:      {user.full_name if user.full_name else 'Not set'}")
            print(f"Active:    {'✅' if user.is_active else '❌'}")
            print(f"Brands:    {brands_count}")
            print(f"Queries:   {queries_count}")
            print(f"Schedules: {schedules_count} active")
            print()

        # Check recent collections
        print(f"\n{'='*80}")
        print(f"RECENT COLLECTIONS (Last 24 Hours)")
        print(f"{'='*80}\n")

        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_history = db.query(ScheduledTaskHistory).filter(
            ScheduledTaskHistory.started_at >= cutoff_time
        ).order_by(ScheduledTaskHistory.started_at.desc()).all()

        if not recent_history:
            print("❌ NO collections in last 24 hours\n")
        else:
            print(f"✅ Found {len(recent_history)} collection(s)\n")
            for h in recent_history:
                user = db.query(User).filter_by(id=h.user_id).first()
                brand = db.query(BrandInfo).filter_by(id=h.brand_id).first()
                print(f"  - {h.status.upper()}: {user.email if user else 'Unknown'}")
                print(f"    Brand: {brand.brand_name if brand else 'Unknown'}")
                print(f"    Started: {h.started_at}")
                print(f"    Collected: {h.collection_responses}, Analyzed: {h.analysis_responses}")
                print()

        # Check specific users
        print(f"\n{'='*80}")
        print(f"CHECKING SPECIFIC USERS")
        print(f"{'='*80}\n")

        target_emails = ['sl40@princeton.edu', 'wslyon@princeton.edu']

        for email in target_emails:
            user = db.query(User).filter_by(email=email).first()

            if not user:
                print(f"❌ {email}: NOT FOUND in production database\n")
                continue

            brands = db.query(BrandInfo).filter_by(user_id=user.id).all()
            queries = db.query(Query).filter_by(user_id=user.id).all()
            schedules = db.query(ScheduledTask).filter_by(user_id=user.id).all()

            print(f"✅ {email}: FOUND")
            print(f"   User ID: {user.id}")
            print(f"   Active: {'✅ Yes' if user.is_active else '❌ No'}")
            print(f"   Brands: {len(brands)}")
            if brands:
                for b in brands:
                    print(f"     • {b.brand_name}")
            print(f"   Queries: {len(queries)}")
            print(f"   Scheduled Tasks: {len(schedules)}")
            if schedules:
                for s in schedules:
                    brand = db.query(BrandInfo).filter_by(id=s.brand_id).first()
                    print(f"     • {s.schedule_type} for {brand.brand_name if brand else 'Unknown'}")
                    print(f"       Enabled: {'✅' if s.is_enabled else '❌'}")
                    print(f"       Next run: {s.next_run_at}")
                    print(f"       Last run: {s.last_run_at if s.last_run_at else 'Never'}")

            # Check if ready
            has_data = len(brands) > 0 and len(queries) > 0
            has_schedule = len([s for s in schedules if s.is_enabled]) > 0

            if has_data and has_schedule:
                print(f"   STATUS: ✅ READY - Should collect automatically")
            elif has_data:
                print(f"   STATUS: ⚠️  HAS DATA - No active schedules")
            else:
                print(f"   STATUS: ❌ NOT READY - Missing data")
            print()

    except Exception as e:
        print(f"❌ Error connecting to production database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    check_production_users()
