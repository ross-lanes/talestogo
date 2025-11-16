"""
Quick script to check recent data collections for specific users
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ScheduledTaskHistory, User, BrandInfo, ScheduledTask

def check_recent_collections(hours=24):
    """Check collections run in the last N hours"""
    db = SessionLocal()

    try:
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        print(f"\n{'='*80}")
        print(f"SCHEDULED TASK HISTORY - Last {hours} Hours")
        print(f"Cutoff Time: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"{'='*80}\n")

        # Get all task history from the last N hours
        recent_history = db.query(ScheduledTaskHistory).filter(
            ScheduledTaskHistory.started_at >= cutoff_time
        ).order_by(ScheduledTaskHistory.started_at.desc()).all()

        if not recent_history:
            print(f"❌ NO collections found in the last {hours} hours")
            print("\nChecking all scheduled tasks status...")

            # Show all active scheduled tasks
            active_tasks = db.query(ScheduledTask).filter(
                ScheduledTask.is_enabled == True
            ).all()

            if active_tasks:
                print(f"\n📋 Active Scheduled Tasks ({len(active_tasks)}):")
                for task in active_tasks:
                    user = db.query(User).filter_by(id=task.user_id).first()
                    brand = db.query(BrandInfo).filter_by(id=task.brand_id).first()
                    print(f"\n  Task ID: {task.id}")
                    print(f"  User: {user.email if user else 'Unknown'}")
                    print(f"  Brand: {brand.brand_name if brand else 'Unknown'}")
                    print(f"  Schedule: {task.schedule_type}")
                    print(f"  Next Run: {task.next_run_at}")
                    print(f"  Last Run: {task.last_run_at if task.last_run_at else 'Never'}")
            else:
                print("\n⚠️  No active scheduled tasks found!")

            return

        print(f"✅ Found {len(recent_history)} collection(s) in the last {hours} hours\n")

        # Track totals
        success_count = 0
        failed_count = 0
        partial_count = 0

        # Display each collection
        for i, history in enumerate(recent_history, 1):
            user = db.query(User).filter_by(id=history.user_id).first()
            brand = db.query(BrandInfo).filter_by(id=history.brand_id).first()
            scheduled_task = db.query(ScheduledTask).filter_by(id=history.scheduled_task_id).first()

            # Count by status
            if history.status == 'success':
                success_count += 1
                status_icon = "✅"
            elif history.status == 'failed':
                failed_count += 1
                status_icon = "❌"
            elif history.status == 'partial':
                partial_count += 1
                status_icon = "⚠️ "
            else:
                status_icon = "❓"

            print(f"{'-'*80}")
            print(f"Collection #{i}")
            print(f"{'-'*80}")
            print(f"Status:     {status_icon} {history.status.upper()}")
            print(f"User:       {user.email if user else 'Unknown'} (ID: {history.user_id})")
            print(f"Brand:      {brand.brand_name if brand else 'Unknown'} (ID: {history.brand_id})")
            print(f"Started:    {history.started_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"Completed:  {history.completed_at.strftime('%Y-%m-%d %H:%M:%S') if history.completed_at else 'N/A'} UTC")

            if history.started_at and history.completed_at:
                duration = history.completed_at - history.started_at
                print(f"Duration:   {duration}")

            print(f"Collected:  {history.collection_responses if history.collection_responses else 0} responses")
            print(f"Analyzed:   {history.analysis_responses if history.analysis_responses else 0} responses")

            if history.error_message:
                print(f"Error:      {history.error_message}")

            if scheduled_task:
                print(f"Schedule:   {scheduled_task.schedule_type}")
                print(f"Next Run:   {scheduled_task.next_run_at if scheduled_task.next_run_at else 'Not scheduled'}")

            print()

        # Summary
        print(f"{'='*80}")
        print(f"SUMMARY")
        print(f"{'='*80}")
        print(f"Total Collections: {len(recent_history)}")
        print(f"  ✅ Success: {success_count}")
        print(f"  ⚠️  Partial: {partial_count}")
        print(f"  ❌ Failed:  {failed_count}")
        print(f"{'='*80}\n")

        # Check specific users
        print(f"\n{'='*80}")
        print(f"CHECKING SPECIFIC USERS")
        print(f"{'='*80}\n")

        target_emails = ['sl40@princeton.edu', 'wslyon@princeton.edu']

        for email in target_emails:
            user = db.query(User).filter_by(email=email).first()
            if not user:
                print(f"❌ {email}: User not found in database")
                continue

            # Check if this user had any collections
            user_collections = [h for h in recent_history if h.user_id == user.id]

            if user_collections:
                print(f"✅ {email}: {len(user_collections)} collection(s) in last {hours} hours")
                for h in user_collections:
                    brand = db.query(BrandInfo).filter_by(id=h.brand_id).first()
                    print(f"   - {h.status.upper()} at {h.started_at.strftime('%Y-%m-%d %H:%M')} for {brand.brand_name if brand else 'Unknown'}")
            else:
                print(f"⚠️  {email}: NO collections in last {hours} hours")

                # Check if they have scheduled tasks
                user_tasks = db.query(ScheduledTask).filter(
                    ScheduledTask.user_id == user.id,
                    ScheduledTask.is_enabled == True
                ).all()

                if user_tasks:
                    print(f"   📋 Has {len(user_tasks)} active scheduled task(s):")
                    for task in user_tasks:
                        brand = db.query(BrandInfo).filter_by(id=task.brand_id).first()
                        print(f"      - {brand.brand_name if brand else 'Unknown'}: Next run at {task.next_run_at}")
                        print(f"        Last run: {task.last_run_at if task.last_run_at else 'Never'}")
                else:
                    print(f"   ❌ Has NO active scheduled tasks")

        print(f"\n{'='*80}\n")

    finally:
        db.close()


if __name__ == "__main__":
    check_recent_collections(hours=24)
