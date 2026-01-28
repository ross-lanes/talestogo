#!/usr/bin/env python3
"""
Script to clean up stale tasks in the database.
Marks tasks that have been "running" for more than 2 hours as "failed".

Usage:
    python cleanup_stale_tasks.py
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import TaskStatus


def cleanup_stale_tasks(hours_threshold: int = 2):
    """
    Mark tasks that have been running for more than the threshold as failed.

    Args:
        hours_threshold: Number of hours after which a running task is considered stale
    """
    db: Session = SessionLocal()
    try:
        # Calculate the cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        # Find all running tasks started before the cutoff time
        stale_tasks = db.query(TaskStatus).filter(
            TaskStatus.status == 'running',
            TaskStatus.started_at < cutoff_time
        ).all()

        if not stale_tasks:
            print("✓ No stale tasks found.")
            return 0

        print(f"Found {len(stale_tasks)} stale task(s) that have been running for more than {hours_threshold} hours:")
        print()

        for task in stale_tasks:
            elapsed_hours = (datetime.utcnow() - task.started_at).total_seconds() / 3600
            print(f"  • Task ID: {task.id}")
            print(f"    Type: {task.task_type}")
            print(f"    Started: {task.started_at}")
            print(f"    Elapsed: {elapsed_hours:.1f} hours")
            print(f"    Message: {task.message or 'N/A'}")
            print()

            # Mark as failed
            task.status = 'failed'
            task.completed_at = datetime.utcnow()
            task.error_message = f"Task auto-failed after running for {elapsed_hours:.1f} hours without completion"
            task.updated_at = datetime.utcnow()

        # Commit the changes
        db.commit()
        print(f"✓ Successfully marked {len(stale_tasks)} stale task(s) as failed.")
        return len(stale_tasks)

    except Exception as e:
        print(f"✗ Error cleaning up stale tasks: {e}")
        db.rollback()
        return -1
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Stale Task Cleanup Utility")
    print("=" * 60)
    print()

    count = cleanup_stale_tasks(hours_threshold=2)

    if count > 0:
        print()
        print("Note: These tasks will no longer appear in the frontend.")
    elif count == 0:
        print("Database is clean!")

    sys.exit(0 if count >= 0 else 1)
