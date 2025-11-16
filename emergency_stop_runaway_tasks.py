"""
EMERGENCY: Stop runaway scheduler from spawning infinite tasks
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

from app.models import ScheduledTask, ScheduledTaskHistory

# Create production database connection
engine = create_engine(PROD_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def emergency_fix():
    """Stop runaway scheduler and clean up stuck tasks"""
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("EMERGENCY FIX - STOPPING RUNAWAY SCHEDULER")
        print("="*80 + "\n")

        # Step 1: Find all running tasks
        running_tasks = db.query(ScheduledTaskHistory).filter(
            ScheduledTaskHistory.status == 'running'
        ).all()

        print(f"Step 1: Found {len(running_tasks)} RUNNING tasks")
        for task in running_tasks:
            started = task.started_at
            running_for = (datetime.utcnow() - started).total_seconds() / 60
            print(f"  - Task {task.id}: Started {started}, running for {running_for:.1f} minutes")

        # Step 2: Mark all running tasks as failed
        print(f"\nStep 2: Marking {len(running_tasks)} tasks as FAILED...")
        for task in running_tasks:
            task.status = 'failed'
            task.error_message = 'Emergency stop - runaway scheduler spawning infinite tasks (collection script still hanging)'
            task.completed_at = datetime.utcnow()

        db.commit()
        print(f"✅ Marked {len(running_tasks)} tasks as failed")

        # Step 3: Update next_run_at to TOMORROW to stop scheduler from spawning more tasks
        schedules = db.query(ScheduledTask).filter(
            ScheduledTask.is_enabled == True,
            ScheduledTask.next_run_at < datetime.utcnow()
        ).all()

        print(f"\nStep 3: Found {len(schedules)} schedules with next_run_at in the past")
        for schedule in schedules:
            print(f"  - Schedule {schedule.id}: next_run_at was {schedule.next_run_at}")
            # Set to tomorrow at 2 AM UTC to stop spawning
            tomorrow = datetime.utcnow() + timedelta(days=1)
            schedule.next_run_at = tomorrow.replace(hour=2, minute=0, second=0, microsecond=0)
            print(f"    → Updated to {schedule.next_run_at}")

        db.commit()
        print(f"✅ Updated {len(schedules)} schedules to stop spawning")

        print("\n" + "="*80)
        print("EMERGENCY FIX COMPLETE")
        print("="*80)
        print("\n✅ Scheduler should stop spawning new tasks within 1 minute")
        print("✅ All stuck tasks marked as failed")
        print("\n⚠️  ROOT CAUSE: Collection script is STILL hanging despite automated mode fix")
        print("    Need to investigate why --task-id parameter isn't working")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    emergency_fix()
