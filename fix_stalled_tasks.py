"""
Safe script to mark stalled scheduled tasks as failed
This allows the scheduler to resume normal operations
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

from app.models import ScheduledTaskHistory

# Create production database connection
engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def fix_stalled_tasks():
    """Mark stalled tasks as failed so scheduler can resume"""
    db = SessionLocal()

    try:
        # Find all tasks with status 'running'
        running_tasks = db.query(ScheduledTaskHistory).filter(
            ScheduledTaskHistory.status == 'running'
        ).all()

        if not running_tasks:
            print("✅ No running tasks found - scheduler should be clear")
            return

        print(f"\n{'='*80}")
        print(f"FOUND {len(running_tasks)} RUNNING TASK(S)")
        print(f"{'='*80}\n")

        for task in running_tasks:
            # Calculate how long it's been running
            if task.started_at:
                running_time = datetime.utcnow() - task.started_at
                hours = running_time.total_seconds() / 3600

                print(f"Task ID: {task.id}")
                print(f"  User ID: {task.user_id}")
                print(f"  Brand ID: {task.brand_id}")
                print(f"  Started: {task.started_at}")
                print(f"  Running for: {hours:.1f} hours")
                print(f"  Collected: {task.collection_responses or 0} responses")
                print(f"  Analyzed: {task.analysis_responses or 0} responses")
                print()

        # Ask for confirmation
        print("\nThese tasks appear to be stalled (no progress, blocking scheduler).")
        response = input("\nMark these tasks as FAILED? (yes/no): ").strip().lower()

        if response != 'yes':
            print("\n❌ Cancelled - no changes made")
            return

        # Mark all as failed
        for task in running_tasks:
            task.status = 'failed'
            task.error_message = 'Task stalled - marked as failed to unblock scheduler (collection script was waiting for input in automated mode)'
            task.completed_at = datetime.utcnow()

        # Commit the changes
        db.commit()

        print(f"\n✅ SUCCESS: Marked {len(running_tasks)} task(s) as failed")
        print("\nThe scheduler should now be able to run new tasks.")
        print("Next scheduled run will execute normally with the fixed collection script.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🔧 TALES Stalled Task Repair Tool")
    print("="*80)
    print("\nThis script will:")
    print("  1. Find all tasks with status='running'")
    print("  2. Mark them as 'failed' with explanation")
    print("  3. Set completed_at timestamp")
    print("  4. Unblock the scheduler to resume normal operations")
    print("\n⚠️  This operates on the PRODUCTION database")
    print("="*80)

    fix_stalled_tasks()
