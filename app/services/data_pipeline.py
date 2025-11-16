"""
Shared data pipeline service for collection, analysis, and report generation.
Used by manual runs, scheduled tasks, and admin operations.
"""
import os
import subprocess
import asyncio
import threading
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models
from app.email import send_email


def utcnow():
    """Get current UTC time."""
    return datetime.utcnow()


def run_collection_analysis_report(
    user_id: int,
    brand_id: int,
    triggered_by: str = "manual"
) -> dict:
    """
    Run the complete data pipeline: collection → analysis → report → email.

    This is the single source of truth for the data collection workflow.
    Used by:
    - Manual "Run Collection & Analysis" button
    - Scheduled automated runs
    - Admin "Run Now" button

    Args:
        user_id: ID of the user
        brand_id: ID of the brand
        triggered_by: How this was triggered ("manual", "scheduled", "admin")

    Returns:
        dict with status information
    """
    db = SessionLocal()

    try:
        # Verify user and brand exist
        user = db.query(models.User).filter_by(id=user_id).first()
        if not user:
            return {"success": False, "error": f"User {user_id} not found"}

        # Import crud here to access user_has_brand_access
        from app import crud

        # Check if user has access to brand (owns it or has it shared)
        if not crud.user_has_brand_access(db, brand_id, user_id):
            return {"success": False, "error": f"Brand {brand_id} not found"}

        # Get the brand (we know it exists from the access check)
        brand = db.query(models.BrandInfo).filter_by(id=brand_id).first()
        if not brand:
            return {"success": False, "error": f"Brand {brand_id} not found"}

        # Get the brand owner's user_id (for shared brands, we need the owner's data)
        data_owner_user_id = brand.user_id

        # Check for active queries (use data owner's user_id for shared brands)
        query_count = db.query(models.Query).filter(
            models.Query.user_id == data_owner_user_id,
            models.Query.brand_id == brand_id,
            models.Query.active == True
        ).count()

        if query_count == 0:
            return {"success": False, "error": "No active queries found"}

        # Create task status for collection
        collection_task = models.TaskStatus(
            user_id=user_id,
            brand_id=brand_id,
            task_type="collection",
            status="running",
            total_items=query_count * 4,
            processed_items=0,
            message=f"Starting {triggered_by} collection...",
            started_at=utcnow()
        )
        db.add(collection_task)
        db.commit()
        db.refresh(collection_task)

        task_id = collection_task.id

        # Extract values we'll need for the return message before closing session
        user_email = user.email
        brand_name = brand.brand_name

    finally:
        db.close()

    # Run the pipeline in a background thread
    def run_pipeline():
        """Execute collection → analysis → report → email pipeline."""
        db_thread = SessionLocal()

        try:
            # Get project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

            # Set up environment
            env = os.environ.copy()
            env['PYTHONPATH'] = project_root

            # === STEP 1: COLLECTION ===
            script_path = os.path.join(project_root, "scripts", "admin", "collect_responses.py")
            # Use data_owner_user_id for shared brands (data belongs to the brand owner)
            cmd = [
                "python3", script_path,
                str(data_owner_user_id),
                "--brand-id", str(brand_id),
                "--task-id", str(task_id)
            ]

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # Store process ID
            task = db_thread.query(models.TaskStatus).filter_by(id=task_id).first()
            if task:
                task.process_id = process.pid
                db_thread.commit()

            # Wait for collection (send "1" to auto-select all queries)
            stdout, stderr = process.communicate(input="1\n", timeout=3600)

            if process.returncode != 0:
                # Collection failed
                task = db_thread.query(models.TaskStatus).filter_by(id=task_id).first()
                if task:
                    task.status = "failed"
                    task.error_message = f"Collection script failed: {stderr[-500:] if stderr else 'Unknown error'}"
                    task.completed_at = utcnow()
                    db_thread.commit()

                # Send failure email
                from app.services.email_notifications import send_task_completion_email
                send_task_completion_email(
                    db=db_thread,
                    user_id=user_id,
                    task_type='collection',
                    task_id=task_id,
                    status='failed',
                    brand_id=brand_id,
                    error_message=task.error_message if task else "Collection failed"
                )
                return

            # Collection succeeded
            task = db_thread.query(models.TaskStatus).filter_by(id=task_id).first()
            if task:
                task.status = "completed"
                task.completed_at = utcnow()
                db_thread.commit()

            # === STEP 2: ANALYSIS ===
            # Get the latest collection batch (use data owner for shared brands)
            latest_batch = db_thread.query(models.CollectionBatch).filter(
                models.CollectionBatch.user_id == data_owner_user_id,
                models.CollectionBatch.brand_id == brand_id
            ).order_by(models.CollectionBatch.started_at.desc()).first()

            if not latest_batch:
                # No batch found (shouldn't happen after collection)
                return

            # Only analyze responses from the latest batch that haven't been analyzed yet
            responses_to_analyze = db_thread.query(models.Response).filter(
                models.Response.user_id == data_owner_user_id,
                models.Response.brand_id == brand_id,
                models.Response.batch_id == latest_batch.id,
                models.Response.analyzed_at.is_(None)
            ).all()

            if not responses_to_analyze:
                # No new responses to analyze
                return

            # Create analysis task
            analysis_task = models.TaskStatus(
                user_id=user_id,
                brand_id=brand_id,
                task_type="analysis",
                status="running",
                total_items=len(responses_to_analyze),
                processed_items=0,
                message=f"Analyzing {len(responses_to_analyze)} newly collected responses...",
                started_at=utcnow()
            )
            db_thread.add(analysis_task)
            db_thread.commit()
            db_thread.refresh(analysis_task)

            # Run analysis script (use data owner for shared brands)
            analysis_script = os.path.join(project_root, "scripts", "admin", "analyze_responses.py")
            analysis_cmd = [
                "python3", analysis_script,
                "--all",
                "--user-id", str(data_owner_user_id),
                "--brand-id", str(brand_id),
                "--task-id", str(analysis_task.id)
            ]

            analysis_process = subprocess.Popen(
                analysis_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # Store process ID
            task = db_thread.query(models.TaskStatus).filter_by(id=analysis_task.id).first()
            if task:
                task.process_id = analysis_process.pid
                db_thread.commit()

            # Wait for analysis
            stdout, stderr = analysis_process.communicate(timeout=3600)

            if analysis_process.returncode != 0:
                # Analysis failed
                task = db_thread.query(models.TaskStatus).filter_by(id=analysis_task.id).first()
                if task:
                    task.status = "failed"
                    task.error_message = f"Analysis script failed: {stderr[-500:] if stderr else 'Unknown error'}"
                    task.completed_at = utcnow()
                    db_thread.commit()

                # Send failure email
                send_task_completion_email(
                    db=db_thread,
                    user_id=user_id,
                    task_type='analysis',
                    task_id=analysis_task.id,
                    status='failed',
                    brand_id=brand_id,
                    error_message=task.error_message if task else "Analysis failed"
                )
                return

            # Analysis succeeded
            task = db_thread.query(models.TaskStatus).filter_by(id=analysis_task.id).first()
            if task:
                task.status = "completed"
                task.completed_at = utcnow()
                db_thread.commit()

            # === STEP 3: REPORT GENERATION ===
            report_script = os.path.join(project_root, "scripts", "admin", "generate_report.py")
            report_cmd = [
                "python3", report_script,
                "--user-id", str(data_owner_user_id),
                "--brand-id", str(brand_id)
            ]

            report_process = subprocess.Popen(
                report_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # Wait for report generation
            report_stdout, report_stderr = report_process.communicate(timeout=3600)

            if report_process.returncode != 0:
                # Report generation failed, but we'll still send email about collection/analysis success
                print(f"Report generation failed: {report_stderr}")

            # === STEP 4: SEND COMPLETION EMAIL ===
            user_obj = db_thread.query(models.User).filter_by(id=user_id).first()
            brand_obj = db_thread.query(models.BrandInfo).filter_by(id=brand_id).first()

            # Get collection stats
            latest_batch = db_thread.query(models.CollectionBatch).filter(
                models.CollectionBatch.user_id == user_id,
                models.CollectionBatch.brand_id == brand_id
            ).order_by(models.CollectionBatch.started_at.desc()).first()

            responses_collected = latest_batch.total_responses if latest_batch else len(responses_to_analyze)

            subject = f'Your {brand_obj.brand_name} Report is Ready'
            body = f"""Hi {user_obj.full_name or user_obj.email},

Great news! Your AI reputation analysis for {brand_obj.brand_name} is complete.

We've collected and analyzed {responses_collected} responses from ChatGPT, Claude, Gemini, and Perplexity. Your fresh insights are waiting for you at https://tales.robotrachel.com/analytics.

Want to see the full story? Check out your detailed report at https://tales.robotrachel.com/reports.

Questions? Ideas? Plot twists? Reach out to admin@robotrachel.com.

May your metrics be ever in your favor,
RobotRachel"""

            # Send the email
            asyncio.run(send_email(user_obj.email, subject, body))

        except subprocess.TimeoutExpired:
            # Timeout - mark task as failed
            task = db_thread.query(models.TaskStatus).filter_by(id=task_id).first()
            if task and task.status == "running":
                task.status = "failed"
                task.error_message = "Process timed out after 1 hour"
                task.completed_at = utcnow()
                db_thread.commit()
        except Exception as e:
            # General error
            task = db_thread.query(models.TaskStatus).filter_by(id=task_id).first()
            if task and task.status == "running":
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = utcnow()
                db_thread.commit()
        finally:
            db_thread.close()

    # Start background thread
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    return {
        "success": True,
        "message": f"Collection started for {user_email} - {brand_name}",
        "task_id": task_id,
        "triggered_by": triggered_by
    }
