"""
Background scheduler service for automated tasks
"""
import asyncio
import subprocess
import os
import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging

from .database import SessionLocal
from .models import ScheduledTask, ScheduledTaskHistory, User, BrandInfo, TaskStatus
from .email import send_email

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def execute_scheduled_task(schedule_id: int):
    """Execute a scheduled collection + analysis"""
    db = SessionLocal()

    try:
        schedule = db.query(ScheduledTask).filter_by(id=schedule_id).first()
        if not schedule or not schedule.is_enabled:
            logger.info(f"Schedule {schedule_id} not found or not enabled, skipping")
            return

        logger.info(f"Starting scheduled task {schedule_id} for user {schedule.user_id}, brand {schedule.brand_id}")

        # Create history entry
        history = ScheduledTaskHistory(
            scheduled_task_id=schedule.id,
            user_id=schedule.user_id,
            brand_id=schedule.brand_id,
            started_at=datetime.utcnow(),
            status='running'
        )
        db.add(history)
        db.commit()
        db.refresh(history)

        # === Run Collection ===
        logger.info(f"Starting data collection for schedule {schedule_id}")

        # Create task status for collection
        collection_task = TaskStatus(
            user_id=schedule.user_id,
            brand_id=schedule.brand_id,
            task_type="collection",
            status="running",
            message="Starting automated collection..."
        )
        db.add(collection_task)
        db.commit()
        db.refresh(collection_task)

        # Run collection script
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "collect_responses.py")
        cmd = [
            "python3", script_path,
            str(schedule.user_id),
            "--brand-id", str(schedule.brand_id),
            "--task-id", str(collection_task.id)
        ]

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send "1" to auto-select run all queries
        process.stdin.write("1\n")
        process.stdin.flush()
        process.stdin.close()

        # Wait for collection to complete (with timeout)
        collection_success = await wait_for_task_completion(
            schedule.user_id,
            'collection',
            db,
            timeout=3600  # 1 hour timeout
        )

        if not collection_success:
            history.status = 'failed'
            history.error_message = 'Collection failed or timed out'
            history.completed_at = datetime.utcnow()
            db.commit()

            # Send failure notification
            if schedule.send_email_notification:
                await send_completion_email(schedule, history, db)

            return

        # Get collection results
        final_collection_task = db.query(TaskStatus).filter_by(id=collection_task.id).first()
        if final_collection_task:
            history.collection_responses = final_collection_task.processed_items or 0
            history.batch_id = final_collection_task.brand_id  # Assuming batch_id tracking

        logger.info(f"Collection completed for schedule {schedule_id}, collected {history.collection_responses} responses")

        # === Run Analysis ===
        logger.info(f"Starting data analysis for schedule {schedule_id}")

        # Create task status for analysis
        analysis_task = TaskStatus(
            user_id=schedule.user_id,
            brand_id=schedule.brand_id,
            task_type="analysis_and_report",
            status="running",
            message="Starting automated analysis..."
        )
        db.add(analysis_task)
        db.commit()
        db.refresh(analysis_task)

        # Run analysis script
        analysis_script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analyze_responses.py")
        analysis_cmd = [
            "python3", analysis_script_path,
            str(schedule.user_id),
            "--brand-id", str(schedule.brand_id),
            "--task-id", str(analysis_task.id),
            "--auto-generate-report"
        ]

        analysis_process = subprocess.Popen(
            analysis_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Auto-select options for analysis (1 = analyze latest, 1 = generate report)
        analysis_process.stdin.write("1\n1\n")
        analysis_process.stdin.flush()
        analysis_process.stdin.close()

        # Wait for analysis to complete (with timeout)
        analysis_success = await wait_for_task_completion(
            schedule.user_id,
            'analysis_and_report',
            db,
            timeout=3600  # 1 hour timeout
        )

        if not analysis_success:
            history.status = 'partial'
            history.error_message = 'Analysis failed or timed out after successful collection'
        else:
            # Get analysis results
            final_analysis_task = db.query(TaskStatus).filter_by(id=analysis_task.id).first()
            if final_analysis_task:
                history.analysis_responses = final_analysis_task.processed_items or 0

            history.status = 'success'
            logger.info(f"Analysis completed for schedule {schedule_id}, analyzed {history.analysis_responses} responses")

        history.completed_at = datetime.utcnow()

        # Update schedule
        schedule.last_run_at = datetime.utcnow()
        if history.batch_id:
            schedule.last_batch_id = history.batch_id

        # Calculate next run time
        from .routers.scheduled_tasks import calculate_next_run
        schedule.next_run_at = calculate_next_run(
            schedule.schedule_type,
            schedule.timezone
        )

        db.commit()

        # Send notification if enabled
        if schedule.send_email_notification:
            await send_completion_email(schedule, history, db)

        logger.info(f"Completed scheduled task {schedule_id} with status {history.status}")
        logger.info(f"Next run scheduled for: {schedule.next_run_at}")

    except Exception as e:
        logger.error(f"Error executing scheduled task {schedule_id}: {str(e)}")
        if 'history' in locals():
            history.status = 'failed'
            history.error_message = str(e)
            history.completed_at = datetime.utcnow()
            db.commit()

            # Send failure notification
            if schedule and schedule.send_email_notification:
                await send_completion_email(schedule, history, db)

    finally:
        db.close()


async def wait_for_task_completion(user_id: int, task_type: str, db: Session, timeout: int = 3600):
    """Wait for a task to complete (with timeout)"""
    start_time = time.time()

    while True:
        # Refresh session to get latest data
        db.expire_all()

        task = db.query(TaskStatus).filter_by(
            user_id=user_id,
            task_type=task_type
        ).order_by(TaskStatus.started_at.desc()).first()

        if not task:
            logger.warning(f"No task found for user {user_id}, type {task_type}")
            return False

        if task.status == 'completed':
            logger.info(f"Task {task_type} completed successfully")
            return True

        if task.status in ['failed', 'cancelled']:
            logger.warning(f"Task {task_type} finished with status: {task.status}")
            return False

        if time.time() - start_time > timeout:
            logger.warning(f"Task {task_type} timed out after {timeout}s")
            return False

        # Wait before polling again
        await asyncio.sleep(10)  # Poll every 10 seconds


async def send_completion_email(schedule: ScheduledTask, history: ScheduledTaskHistory, db: Session):
    """Send email notification about completed task"""
    try:
        user = db.query(User).filter_by(id=schedule.user_id).first()
        brand = db.query(BrandInfo).filter_by(id=schedule.brand_id).first()

        if not user or not brand:
            logger.warning(f"Could not find user or brand for notification")
            return

        email_to = schedule.notification_email or user.email

        if history.status == 'success':
            subject = f"TALES Monthly Report - {brand.brand_name}"
            body = f"""Your scheduled monthly data collection and analysis has completed successfully!

Brand: {brand.brand_name}
Collection Date: {history.started_at.strftime('%B %d, %Y')}
Responses Collected: {history.collection_responses}
Responses Analyzed: {history.analysis_responses}

View your results: https://tales.robotrachel.com/analytics

Next scheduled run: {schedule.next_run_at.strftime('%B %d, %Y at %I:%M %p') if schedule.next_run_at else 'Not scheduled'}

--
TALES - AI Reputation Intelligence & Optimization
"""
        else:
            subject = f"TALES Alert: Scheduled Task Issue - {brand.brand_name}"
            body = f"""Your scheduled monthly data collection encountered an issue.

Brand: {brand.brand_name}
Status: {history.status.upper()}
Started: {history.started_at.strftime('%B %d, %Y at %I:%M %p')}
Error: {history.error_message or 'Unknown error'}

Responses Collected: {history.collection_responses}
Responses Analyzed: {history.analysis_responses}

Please log in to review and manually re-run if needed: https://tales.robotrachel.com/data

Next scheduled run: {schedule.next_run_at.strftime('%B %d, %Y at %I:%M %p') if schedule.next_run_at else 'Not scheduled'}

--
TALES - AI Reputation Intelligence & Optimization
"""

        await send_email(email_to, subject, body)
        logger.info(f"Notification email sent to {email_to}")

    except Exception as e:
        logger.error(f"Failed to send notification email: {str(e)}")


def check_and_schedule_tasks():
    """Check for tasks that need to be scheduled - runs every minute"""
    db = SessionLocal()

    try:
        now = datetime.utcnow()

        # Find tasks ready to run (next_run_at is in the past and enabled)
        tasks = db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.is_enabled == True,
                ScheduledTask.next_run_at <= now
            )
        ).all()

        for task in tasks:
            logger.info(f"Found task {task.id} ready for execution (next_run: {task.next_run_at})")
            # Schedule the task execution
            asyncio.create_task(execute_scheduled_task(task.id))

    except Exception as e:
        logger.error(f"Error checking scheduled tasks: {str(e)}")

    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    try:
        # Check for tasks to run every minute
        scheduler.add_job(
            check_and_schedule_tasks,
            CronTrigger(minute='*'),  # Run every minute
            id='check_scheduled_tasks',
            replace_existing=True,
            max_instances=1
        )

        scheduler.start()
        logger.info("Scheduler started successfully - checking for tasks every minute")

    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")


def stop_scheduler():
    """Stop the background scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
