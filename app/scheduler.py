"""
Background scheduler service for automated tasks

FIXED ISSUES:
- Prevents running every minute (updates next_run_at immediately)
- Uses direct data_pipeline calls instead of broken subprocess scripts
- Adds safety guards: duplicate run prevention, minimum 1-hour gap
- Better error handling and logging
- No "catch-up" runs for missed schedules
- Thread pool limits concurrent scheduled runs (max 50)
- Fixed lambda closure bug
"""
import asyncio
import time
import os
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import logging

from .database import SessionLocal
from .models import ScheduledTask, ScheduledTaskHistory, User, BrandInfo
from .email import send_email

logger = logging.getLogger(__name__)

# Check if scheduler should be enabled (controlled by environment variable)
def is_scheduler_enabled() -> bool:
    """
    Check if the scheduler should be enabled based on ENABLE_SCHEDULER environment variable.

    Returns:
        bool: True if scheduler should run, False otherwise (e.g., on localhost)
    """
    enable_scheduler = os.getenv('ENABLE_SCHEDULER', 'false').lower()
    return enable_scheduler in ('true', '1', 'yes')

# Global scheduler instance
scheduler = AsyncIOScheduler()

# Thread pool for scheduled tasks (limits concurrent runs to prevent overload)
_executor = ThreadPoolExecutor(max_workers=50, thread_name_prefix="scheduled_task_")

# Track currently running schedules to prevent duplicates
_running_schedules = set()


async def execute_scheduled_task(schedule_id: int):
    """Execute a scheduled collection + analysis using shared data pipeline"""

    # Prevent duplicate runs
    if schedule_id in _running_schedules:
        logger.warning(f"Schedule {schedule_id} is already running, skipping duplicate execution")
        return

    _running_schedules.add(schedule_id)
    db = SessionLocal()

    try:
        schedule = db.query(ScheduledTask).filter_by(id=schedule_id).first()
        if not schedule or not schedule.is_enabled:
            logger.info(f"Schedule {schedule_id} not found or not enabled, skipping")
            return

        # Safety check: Don't run if last run was less than 1 hour ago
        if schedule.last_run_at:
            time_since_last_run = datetime.utcnow() - schedule.last_run_at
            if time_since_last_run < timedelta(hours=1):
                logger.warning(f"Schedule {schedule_id} ran {time_since_last_run.total_seconds()/60:.1f} minutes ago, skipping (minimum 1 hour gap)")
                return

        logger.info(f"Starting scheduled task {schedule_id} for user {schedule.user_id}, brand {schedule.brand_id}")

        # CRITICAL: Update next_run_at and last_run_at IMMEDIATELY to prevent re-triggering
        from .routers.scheduled_tasks import calculate_next_run
        schedule.last_run_at = datetime.utcnow()
        schedule.next_run_at = calculate_next_run(
            schedule.schedule_type,
            schedule.timezone
        )
        db.commit()
        logger.info(f"Updated schedule {schedule_id}: next run at {schedule.next_run_at}")

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

        # Use the shared data pipeline service (FIXED: direct call, not subprocess)
        from app.services.data_pipeline import run_collection_analysis_report

        result = run_collection_analysis_report(
            user_id=schedule.user_id,
            brand_id=schedule.brand_id,
            triggered_by="scheduled"
        )

        if not result["success"]:
            # Pipeline failed to start
            error_msg = result.get("error", "Failed to start pipeline")

            # Don't retry on certain errors
            if "No active queries found" in error_msg:
                logger.warning(f"Schedule {schedule_id}: {error_msg} - not retrying")
                history.status = 'failed'
                history.error_message = error_msg
                history.completed_at = datetime.utcnow()
                db.commit()

                # Send notification
                if schedule.send_email_notification:
                    await send_completion_email(schedule, history, db)

                return

            # Other failures - log and notify
            history.status = 'failed'
            history.error_message = error_msg
            history.completed_at = datetime.utcnow()
            db.commit()

            # Send failure notification
            if schedule.send_email_notification:
                await send_completion_email(schedule, history, db)

            logger.error(f"Schedule {schedule_id} failed to start: {error_msg}")
            return

        task_id = result["task_id"]
        logger.info(f"Started data pipeline with task_id {task_id}")

        # Wait for the pipeline to complete (with timeout)
        # The data_pipeline service handles collection → analysis → report internally
        pipeline_success = await wait_for_pipeline_completion(
            task_id,
            db,
            timeout=7200  # 2 hour timeout
        )

        if pipeline_success:
            history.status = 'success'
            # Response counts are tracked in the history by the pipeline service
            logger.info(f"Pipeline completed successfully for schedule {schedule_id}")
        else:
            history.status = 'failed'
            history.error_message = 'Pipeline failed or timed out'
            logger.warning(f"Pipeline failed for schedule {schedule_id}")

        history.completed_at = datetime.utcnow()
        db.commit()

        # Send completion email (success or failure)
        if schedule.send_email_notification:
            await send_completion_email(schedule, history, db)

        logger.info(f"Completed scheduled task {schedule_id} with status {history.status}")
        logger.info(f"Next run scheduled for: {schedule.next_run_at}")

    except Exception as e:
        logger.error(f"Error executing scheduled task {schedule_id}: {str(e)}", exc_info=True)
        if 'history' in locals():
            try:
                history.status = 'failed'
                history.error_message = f"Unexpected error: {str(e)}"
                history.completed_at = datetime.utcnow()
                db.commit()

                # Send error notification
                if 'schedule' in locals() and schedule.send_email_notification:
                    await send_completion_email(schedule, history, db)
            except Exception as commit_error:
                logger.error(f"Failed to save error status: {str(commit_error)}")

    finally:
        db.close()
        _running_schedules.discard(schedule_id)


async def wait_for_pipeline_completion(task_id: int, db: Session, timeout: int = 7200):
    """
    Wait for the data pipeline task to complete (collection + analysis + report).

    Args:
        task_id: The TaskStatus ID to monitor
        db: Database session
        timeout: Maximum seconds to wait

    Returns:
        bool: True if completed successfully, False otherwise
    """
    from .models import TaskStatus

    start_time = time.time()
    last_status = None

    while True:
        # Refresh session to get latest data
        db.expire_all()

        task = db.query(TaskStatus).filter_by(id=task_id).first()

        if not task:
            logger.warning(f"Task {task_id} not found")
            return False

        # Log status changes
        if task.status != last_status:
            logger.info(f"Task {task_id} status: {task.status} - {task.message}")
            last_status = task.status

        if task.status == 'completed':
            logger.info(f"Task {task_id} completed successfully")
            return True

        if task.status in ['failed', 'cancelled']:
            logger.warning(f"Task {task_id} finished with status: {task.status}")
            if task.error_message:
                logger.warning(f"Task {task_id} error: {task.error_message}")
            return False

        if time.time() - start_time > timeout:
            logger.warning(f"Task {task_id} timed out after {timeout}s")
            return False

        # Wait before polling again
        await asyncio.sleep(15)  # Poll every 15 seconds


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
Responses Collected: {history.collection_responses or 'Processing'}
Responses Analyzed: {history.analysis_responses or 'Processing'}

View your results: https://apps.robotrachel.com/analytics

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

Responses Collected: {history.collection_responses or 0}
Responses Analyzed: {history.analysis_responses or 0}

Please log in to review and manually re-run if needed: https://apps.robotrachel.com/data

Next scheduled run: {schedule.next_run_at.strftime('%B %d, %Y at %I:%M %p') if schedule.next_run_at else 'Not scheduled'}

--
TALES - AI Reputation Intelligence & Optimization
"""

        await send_email(email_to, subject, body)
        logger.info(f"Notification email sent to {email_to}")

    except Exception as e:
        logger.error(f"Failed to send notification email: {str(e)}")


def check_and_schedule_tasks():
    """
    Check for tasks that need to be scheduled - runs every minute.

    FIXED:
    - Only runs tasks where next_run_at is in the past
    - Updates next_run_at immediately to prevent re-triggering
    - Prevents duplicate runs
    """
    db = SessionLocal()

    try:
        now = datetime.utcnow()

        # Find tasks ready to run (next_run_at is in the past and enabled)
        # Also exclude tasks currently running
        tasks = db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.is_enabled == True,
                ScheduledTask.next_run_at <= now
            )
        ).all()

        for task in tasks:
            # Skip if already running
            if task.id in _running_schedules:
                logger.debug(f"Task {task.id} already running, skipping")
                continue

            # Safety: Skip if run very recently (shouldn't happen with the update logic, but extra safety)
            if task.last_run_at and (now - task.last_run_at) < timedelta(minutes=55):
                logger.debug(f"Task {task.id} ran recently, skipping")
                continue

            logger.info(f"Found task {task.id} ready for execution (next_run: {task.next_run_at})")

            # Execute the task in thread pool (FIXED: pass task_id explicitly to avoid closure issues)
            def run_scheduled_task(schedule_id):
                """Wrapper to run scheduled task in thread pool"""
                asyncio.run(execute_scheduled_task(schedule_id))

            # Submit to thread pool (max 50 concurrent tasks)
            _executor.submit(run_scheduled_task, task.id)
            logger.info(f"Submitted task {task.id} to thread pool")

    except Exception as e:
        logger.error(f"Error checking scheduled tasks: {str(e)}", exc_info=True)

    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler (only if ENABLE_SCHEDULER=true)"""
    # Check if scheduler should be enabled
    if not is_scheduler_enabled():
        logger.info("Scheduler DISABLED (ENABLE_SCHEDULER=false) - scheduled tasks will not run")
        logger.info("This is expected on localhost. Set ENABLE_SCHEDULER=true in production to enable scheduled tasks.")
        return

    try:
        # Check for tasks to run every minute
        scheduler.add_job(
            check_and_schedule_tasks,
            CronTrigger(minute='*'),  # Run every minute
            id='check_scheduled_tasks',
            replace_existing=True,
            max_instances=1  # Only one instance at a time
        )

        scheduler.start()
        logger.info("Scheduler ENABLED and started successfully - checking for tasks every minute")
        logger.info("FIXED: Prevents duplicate runs, updates next_run_at immediately, uses direct data_pipeline calls")

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
