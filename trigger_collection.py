"""
Manually trigger a scheduled collection for a specific user/brand
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Production database URL
PROD_DATABASE_URL = "postgresql://tales_3bh3_user:REDACTED_RAILWAY_PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models import ScheduledTask, User, BrandInfo

# Create production database connection
engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def trigger_collection(user_email: str, brand_name: str):
    """Manually trigger a collection by updating next_run_at to now"""
    db = SessionLocal()

    try:
        # Find the user
        user = db.query(User).filter_by(email=user_email).first()
        if not user:
            print(f"❌ User {user_email} not found")
            return False

        # Find the brand
        brand = db.query(BrandInfo).filter_by(user_id=user.id, brand_name=brand_name).first()
        if not brand:
            print(f"❌ Brand {brand_name} not found for user {user_email}")
            return False

        # Find the scheduled task
        schedule = db.query(ScheduledTask).filter_by(
            user_id=user.id,
            brand_id=brand.id,
            is_enabled=True
        ).first()

        if not schedule:
            print(f"❌ No enabled schedule found for {user_email} - {brand_name}")
            return False

        print(f"\n{'='*80}")
        print(f"TRIGGERING COLLECTION")
        print(f"{'='*80}")
        print(f"User: {user_email}")
        print(f"Brand: {brand_name}")
        print(f"Schedule Type: {schedule.schedule_type}")
        print(f"Current next_run_at: {schedule.next_run_at}")
        print(f"Setting next_run_at to: NOW")

        # Update next_run_at to now to trigger immediate execution
        schedule.next_run_at = datetime.utcnow()
        db.commit()

        print(f"\n✅ SUCCESS: Collection will start within the next minute")
        print(f"The scheduler checks every minute and will pick up this task immediately.")
        print(f"\nMonitor progress:")
        print(f"  - Check Admin Scheduler Dashboard")
        print(f"  - Or run: python check_production_users.py")

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    # Trigger collection for sl40@princeton.edu - Princeton Engineering
    trigger_collection("sl40@princeton.edu", "Princeton Engineering")
