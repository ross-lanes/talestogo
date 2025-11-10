"""
Operations API Endpoints
Provides endpoints for triggering background tasks and operations including:
- Data collection
- Analysis tasks
- Report generation
- Task management (status, cancellation)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import datetime
import os
import subprocess
import threading
import signal

from .. import models, schemas, crud
from ..auth import get_current_user
from ..database import SessionLocal, get_db
from ..utils.brand_access import get_active_brand_id

router = APIRouter(
    prefix="/tasks",
    tags=["Operations"]
)


# --- Celery Task Trigger for the main weekly run ---
from celery_app.tasks import run_weekly_queries_task
@router.post("/trigger-weekly-run/", status_code=202)
async def trigger_weekly_run_endpoint():
    """Manually trigger the weekly query and analysis process."""
    task = run_weekly_queries_task.delay()
    return {"message": "Weekly run triggered.", "task_id": task.id}

@router.post("/trigger-analysis/", status_code=202)
async def trigger_analysis_on_unanalyzed(db: Session = Depends(get_db)):
    """Manually trigger analysis on all unanalyzed responses."""
    from celery_app.tasks import analyze_responses_batch_task
    unanalyzed_responses = crud.get_unanalyzed_responses(db, limit=1000)
    if not unanalyzed_responses:
        raise HTTPException(status_code=404, detail="No unanalyzed responses found.")

    response_ids = [resp.id for resp in unanalyzed_responses]
    task = analyze_responses_batch_task.delay(response_ids)
    return {"message": f"Analysis triggered for {len(response_ids)} responses.", "task_id": task.id}

# --- Direct Collection and Analysis Triggers (without Celery) ---
@router.post("/run-collection/", status_code=202)
async def run_collection(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Trigger response collection followed by automatic analysis for active brand.
    Collection and analysis run sequentially in the background.
    """
    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found. Please select a brand first.")

    # Get count of active queries
    query_count = db.query(models.Query).filter(
        models.Query.user_id == current_user.id,
        models.Query.brand_id == brand_id,
        models.Query.active == True
    ).count()

    if query_count == 0:
        raise HTTPException(status_code=400, detail="No active queries found for this brand.")

    # Create task status for collection
    collection_task = models.TaskStatus(
        user_id=current_user.id,
        brand_id=brand_id,
        task_type="collection",
        status="running",
        total_items=query_count * 4,  # queries × 4 platforms
        processed_items=0,
        message="Starting collection..."
    )
    db.add(collection_task)
    db.commit()
    db.refresh(collection_task)

    # Start background thread to run collection then analysis
    def run_collection_then_analysis():
        """Run collection, wait for completion, then run analysis."""
        db_thread = SessionLocal()
        try:
            # === RUN COLLECTION ===
            # In Docker: /app/scripts/admin/collect_responses.py
            # Locally: /path/to/tales_project/scripts/admin/collect_responses.py
            # Get project root (parent of app directory)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            script_path = os.path.join(project_root, "scripts", "admin", "collect_responses.py")
            cmd = [
                "python3", script_path,
                str(current_user.id),
                "--brand-id", str(brand_id),
                "--task-id", str(collection_task.id)
            ]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # Store the process ID
            task = db_thread.query(models.TaskStatus).filter(
                models.TaskStatus.id == collection_task.id
            ).first()
            if task:
                task.process_id = process.pid
                db_thread.commit()

            # Wait for collection to complete
            # Send "1" to run all queries (auto-select option 1)
            stdout, stderr = process.communicate(input="1\n", timeout=3600)  # 1 hour timeout

            if process.returncode != 0:
                # Collection failed
                task = db_thread.query(models.TaskStatus).filter(
                    models.TaskStatus.id == collection_task.id
                ).first()
                if task:
                    task.status = "failed"
                    task.error_message = f"Collection script failed: {stderr[-500:] if stderr else 'Unknown error'}"
                    task.completed_at = datetime.datetime.utcnow()
                    db_thread.commit()

                # Send email notification about collection failure
                from app.services.email_notifications import send_task_completion_email
                send_task_completion_email(
                    db=db_thread,
                    user_id=current_user.id,
                    task_type='collection',
                    task_id=collection_task.id,
                    status='failed',
                    brand_id=brand_id,
                    error_message=task.error_message if task else "Collection failed"
                )
                return

            # Collection succeeded - mark as completed
            task = db_thread.query(models.TaskStatus).filter(
                models.TaskStatus.id == collection_task.id
            ).first()
            if task:
                task.status = "completed"
                task.completed_at = datetime.datetime.utcnow()
                db_thread.commit()

            # Send email notification about collection success
            from app.services.email_notifications import send_task_completion_email
            send_task_completion_email(
                db=db_thread,
                user_id=current_user.id,
                task_type='collection',
                task_id=collection_task.id,
                status='completed',
                brand_id=brand_id
            )

            # === RUN ANALYSIS AUTOMATICALLY ===
            # Get newly collected responses
            responses_to_analyze = db_thread.query(models.Response).filter(
                models.Response.user_id == current_user.id,
                models.Response.brand_id == brand_id,
                models.Response.analyzed_at.is_(None)
            ).all()

            if not responses_to_analyze:
                # No new responses to analyze
                return

            # Create analysis task
            analysis_task = models.TaskStatus(
                user_id=current_user.id,
                brand_id=brand_id,
                task_type="analysis",
                status="running",
                total_items=len(responses_to_analyze),
                processed_items=0,
                message=f"Analyzing {len(responses_to_analyze)} newly collected responses..."
            )
            db_thread.add(analysis_task)
            db_thread.commit()
            db_thread.refresh(analysis_task)

            # Run analysis script
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            analysis_script = os.path.join(project_root, "analyze_responses.py")
            analysis_cmd = [
                "python3", analysis_script,
                "--all",
                "--user-id", str(current_user.id),
                "--brand-id", str(brand_id),
                "--task-id", str(analysis_task.id)
            ]

            analysis_process = subprocess.Popen(
                analysis_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Store the process ID
            task = db_thread.query(models.TaskStatus).filter(
                models.TaskStatus.id == analysis_task.id
            ).first()
            if task:
                task.process_id = analysis_process.pid
                db_thread.commit()

            # Wait for analysis to complete
            stdout, stderr = analysis_process.communicate(timeout=3600)  # 1 hour timeout

            if analysis_process.returncode != 0:
                # Analysis failed
                task = db_thread.query(models.TaskStatus).filter(
                    models.TaskStatus.id == analysis_task.id
                ).first()
                if task:
                    task.status = "failed"
                    task.error_message = f"Analysis script failed: {stderr[-500:] if stderr else 'Unknown error'}"
                    task.completed_at = datetime.datetime.utcnow()
                    db_thread.commit()

                # Send email notification about analysis failure
                send_task_completion_email(
                    db=db_thread,
                    user_id=current_user.id,
                    task_type='analysis',
                    task_id=analysis_task.id,
                    status='failed',
                    brand_id=brand_id,
                    error_message=task.error_message if task else "Analysis failed"
                )
                return

            # Analysis succeeded
            task = db_thread.query(models.TaskStatus).filter(
                models.TaskStatus.id == analysis_task.id
            ).first()
            if task:
                task.status = "completed"
                task.completed_at = datetime.datetime.utcnow()
                db_thread.commit()

            # Send email notification about analysis success
            send_task_completion_email(
                db=db_thread,
                user_id=current_user.id,
                task_type='analysis',
                task_id=analysis_task.id,
                status='completed',
                brand_id=brand_id
            )

        except subprocess.TimeoutExpired:
            # Timeout - mark task as failed
            task = db_thread.query(models.TaskStatus).filter(
                models.TaskStatus.id == collection_task.id
            ).first()
            if task and task.status == "running":
                task.status = "failed"
                task.error_message = "Collection timed out after 1 hour"
                task.completed_at = datetime.datetime.utcnow()
                db_thread.commit()
        except Exception as e:
            # General error
            task = db_thread.query(models.TaskStatus).filter(
                models.TaskStatus.id == collection_task.id
            ).first()
            if task and task.status == "running":
                task.status = "failed"
                task.error_message = str(e)
                task.completed_at = datetime.datetime.utcnow()
                db_thread.commit()
        finally:
            db_thread.close()

    # Start the background thread
    thread = threading.Thread(target=run_collection_then_analysis, daemon=True)
    thread.start()

    return {
        "message": "Data collection and analysis started for active brand.",
        "status": "running",
        "task_id": collection_task.id,
        "note": "Collection will run first, then analysis will automatically start. Check the task status banner for progress."
    }

@router.post("/run-analysis/", status_code=202)
async def run_analysis(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Analyze responses from most recent collection date and auto-generate report for active brand."""
    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found. Please select a brand first.")

    # Find the most recent collection date for this brand
    most_recent_response = db.query(models.Response).filter(
        models.Response.user_id == current_user.id,
        models.Response.brand_id == brand_id
    ).order_by(models.Response.timestamp.desc()).first()

    if not most_recent_response:
        raise HTTPException(status_code=404, detail="No responses found for active brand.")

    # Get the date of the most recent collection (just the date part)
    latest_date = most_recent_response.timestamp.date()

    # Find all responses from that date
    latest_date_start = datetime.datetime.combine(latest_date, datetime.time.min)
    latest_date_end = latest_date_start + datetime.timedelta(days=1)

    responses_to_analyze = db.query(models.Response).filter(
        models.Response.user_id == current_user.id,
        models.Response.brand_id == brand_id,
        models.Response.timestamp >= latest_date_start,
        models.Response.timestamp < latest_date_end
    ).all()

    if not responses_to_analyze:
        raise HTTPException(status_code=404, detail="No responses found for the most recent collection date.")

    # Reset analysis fields for these responses
    for response in responses_to_analyze:
        response.analyzed_at = None
        response.brand_mentioned = None
        response.brand_position = None
        response.sentiment = None
        response.descriptors = None
        response.competitors = None
        response.sources = None

    db.commit()

    # Create task status for analysis
    task_status = models.TaskStatus(
        user_id=current_user.id,
        brand_id=brand_id,
        task_type="analysis_and_report",
        status="running",
        total_items=len(responses_to_analyze),
        processed_items=0,
        message=f"Analyzing {len(responses_to_analyze)} responses from {latest_date.strftime('%Y-%m-%d')}..."
    )
    db.add(task_status)
    db.commit()
    db.refresh(task_status)

    # Get the project root directory (parent of app directory)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    analysis_script = os.path.join(project_root, "analyze_responses.py")
    report_script = os.path.join(project_root, "scripts", "admin", "generate_report.py")

    try:

        # Run analysis and report generation in sequence in the background with task-id
        # Use separate commands to capture which step fails
        analysis_cmd = f"python3 {analysis_script} --all --user-id {current_user.id} --brand-id {brand_id} --task-id {task_status.id}"
        report_cmd = f"python3 {report_script} --user-id {current_user.id} --brand-id {brand_id}"

        # Create a background task to monitor the subprocess
        def run_analysis_task():
            """Run analysis and report generation, updating task status on completion."""
            db_task = SessionLocal()
            try:
                # Run analysis script using Popen so we can track the PID
                analysis_process = subprocess.Popen(
                    analysis_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=project_root
                )

                # Store the process ID
                task = db_task.query(models.TaskStatus).filter(
                    models.TaskStatus.id == task_status.id
                ).first()
                if task:
                    task.process_id = analysis_process.pid
                    db_task.commit()

                # Wait for process to complete with timeout
                try:
                    stdout, stderr = analysis_process.communicate(timeout=3600)  # 1 hour timeout
                except subprocess.TimeoutExpired:
                    analysis_process.kill()
                    stdout, stderr = analysis_process.communicate()
                    raise

                if analysis_process.returncode != 0:
                    # Analysis failed
                    task = db_task.query(models.TaskStatus).filter(
                        models.TaskStatus.id == task_status.id
                    ).first()
                    if task:
                        task.status = "failed"
                        task.error_message = f"Analysis script failed: {stderr[-500:] if stderr else 'Unknown error'}"
                        db_task.commit()
                    return

                # Run report generation script
                report_process = subprocess.run(
                    report_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=project_root,
                    timeout=600  # 10 minute timeout
                )

                if report_process.returncode != 0:
                    # Report generation failed
                    task = db_task.query(models.TaskStatus).filter(
                        models.TaskStatus.id == task_status.id
                    ).first()
                    if task:
                        task.status = "failed"
                        task.error_message = f"Report generation failed: {report_process.stderr[-500:] if report_process.stderr else 'Unknown error'}"
                        db_task.commit()
                    return

                # Both succeeded
                task = db_task.query(models.TaskStatus).filter(
                    models.TaskStatus.id == task_status.id
                ).first()
                if task:
                    task.status = "completed"
                    task.message = "Analysis and report generation completed successfully"
                    db_task.commit()

            except subprocess.TimeoutExpired as e:
                task = db_task.query(models.TaskStatus).filter(
                    models.TaskStatus.id == task_status.id
                ).first()
                if task:
                    task.status = "failed"
                    task.error_message = f"Task timed out: {str(e)}"
                    db_task.commit()
            except Exception as e:
                task = db_task.query(models.TaskStatus).filter(
                    models.TaskStatus.id == task_status.id
                ).first()
                if task:
                    task.status = "failed"
                    task.error_message = f"Unexpected error: {str(e)}"
                    db_task.commit()
            finally:
                db_task.close()

        # Start the background thread
        thread = threading.Thread(target=run_analysis_task, daemon=True)
        thread.start()

        return {
            "message": f"Analysis and report generation started for {len(responses_to_analyze)} responses from {latest_date.strftime('%Y-%m-%d')}.",
            "status": "running",
            "task_id": task_status.id,
            "count": len(responses_to_analyze),
            "note": "Analyzing latest data and generating report. This will update all analytics pages."
        }
    except Exception as e:
        task_status.status = "failed"
        task_status.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@router.post("/rerun-analysis/", status_code=202)
async def rerun_analysis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Reset analysis on responses for active brand (optionally filtered by date range) and regenerate report."""
    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found. Please select a brand first.")

    # Build query for responses
    query = db.query(models.Response).filter(
        models.Response.user_id == current_user.id,
        models.Response.brand_id == brand_id
    )

    # Apply date filters if provided
    date_description = "all"
    if start_date:
        try:
            start_dt = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(models.Response.timestamp >= start_dt)
            date_description = f"from {start_date[:10]}"
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format (YYYY-MM-DD).")

    if end_date:
        try:
            end_dt = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            # Add one day to include the entire end date
            end_dt = end_dt + datetime.timedelta(days=1)
            query = query.filter(models.Response.timestamp < end_dt)
            if start_date:
                date_description = f"from {start_date[:10]} to {end_date[:10]}"
            else:
                date_description = f"through {end_date[:10]}"
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format (YYYY-MM-DD).")

    all_responses = query.all()

    if not all_responses:
        raise HTTPException(status_code=404, detail=f"No responses found for active brand {date_description}.")

    # Collect response IDs before resetting (so we only analyze these specific responses)
    response_ids = [response.id for response in all_responses]

    # Reset analyzed_at to NULL for filtered responses (marks them as unanalyzed)
    for response in all_responses:
        response.analyzed_at = None
        # Clear existing analysis fields so they get fresh analysis
        response.brand_mentioned = None
        response.brand_position = None
        response.sentiment = None
        response.descriptors = None
        response.competitors = None
        response.sources = None

    db.commit()

    # Create task status for re-analysis
    message = f"Re-analyzing {len(all_responses)} responses {date_description}..."
    task_status = models.TaskStatus(
        user_id=current_user.id,
        brand_id=brand_id,
        task_type="analysis_and_report",
        status="running",
        total_items=len(all_responses),
        processed_items=0,
        message=message,
        started_at=datetime.datetime.utcnow()
    )
    db.add(task_status)
    db.commit()
    db.refresh(task_status)

    # Get the project root directory (parent of app directory)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    analysis_script = os.path.join(project_root, "analyze_responses.py")
    report_script = os.path.join(project_root, "scripts", "admin", "generate_report.py")

    try:
        # Run analysis and report generation in sequence in the background
        # Use separate commands to capture which step fails
        # Pass specific response IDs instead of --all to only analyze date-filtered responses
        response_ids_str = ','.join(map(str, response_ids))
        analysis_cmd = f"python3 {analysis_script} --response-ids {response_ids_str} --user-id {current_user.id} --brand-id {brand_id} --task-id {task_status.id}"
        report_cmd = f"python3 {report_script} --user-id {current_user.id} --brand-id {brand_id}"

        # Create a background task to monitor the subprocess
        def run_reanalysis_task():
            """Run re-analysis and report generation, updating task status on completion."""
            db_task = SessionLocal()
            try:
                # Run analysis script
                analysis_process = subprocess.run(
                    analysis_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=project_root,
                    timeout=3600  # 1 hour timeout
                )

                if analysis_process.returncode != 0:
                    # Analysis failed
                    task = db_task.query(models.TaskStatus).filter(
                        models.TaskStatus.id == task_status.id
                    ).first()
                    if task:
                        task.status = "failed"
                        task.error_message = f"Analysis script failed: {analysis_process.stderr[-500:]}"
                        db_task.commit()
                    return

                # Run report generation script
                report_process = subprocess.run(
                    report_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=project_root,
                    timeout=600  # 10 minute timeout
                )

                if report_process.returncode != 0:
                    # Report generation failed
                    task = db_task.query(models.TaskStatus).filter(
                        models.TaskStatus.id == task_status.id
                    ).first()
                    if task:
                        task.status = "failed"
                        task.error_message = f"Report generation failed: {report_process.stderr[-500:]}"
                        db_task.commit()
                    return

                # Both succeeded
                task = db_task.query(models.TaskStatus).filter(
                    models.TaskStatus.id == task_status.id
                ).first()
                if task:
                    task.status = "completed"
                    task.message = "Re-analysis and report generation completed successfully"
                    db_task.commit()

            except subprocess.TimeoutExpired as e:
                task = db_task.query(models.TaskStatus).filter(
                    models.TaskStatus.id == task_status.id
                ).first()
                if task:
                    task.status = "failed"
                    task.error_message = f"Task timed out: {str(e)}"
                    db_task.commit()
            except Exception as e:
                task = db_task.query(models.TaskStatus).filter(
                    models.TaskStatus.id == task_status.id
                ).first()
                if task:
                    task.status = "failed"
                    task.error_message = f"Unexpected error: {str(e)}"
                    db_task.commit()
            finally:
                db_task.close()

        # Start the background thread
        thread = threading.Thread(target=run_reanalysis_task, daemon=True)
        thread.start()

        return {
            "message": f"Re-analysis started for {len(all_responses)} responses {date_description}.",
            "status": "running",
            "task_id": task_status.id,
            "count": len(all_responses),
            "date_range": date_description,
            "note": "Re-analyzing responses with updated analysis process. A new report will be generated when complete."
        }
    except Exception as e:
        task_status.status = "failed"
        task_status.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to start re-analysis: {str(e)}")

@router.get("/status/", response_model=Optional[schemas.TaskStatus])
def get_task_status(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """Get the status of the most recent task for the active brand."""
    if not brand_id:
        return None

    # Get the most recent task for this user and brand
    task = db.query(models.TaskStatus).filter(
        models.TaskStatus.user_id == current_user.id,
        models.TaskStatus.brand_id == brand_id
    ).order_by(models.TaskStatus.started_at.desc()).first()

    if not task:
        return None

    # Check if the task is still running by checking unanalyzed responses
    if task.status == "running":
        unanalyzed = crud.get_unanalyzed_responses(db, user_id=current_user.id, brand_id=brand_id, limit=1)
        if not unanalyzed and task.task_type == "analysis_and_report":
            # Analysis is complete, check if we're generating report
            # For simplicity, mark as completed if no unanalyzed responses
            task.status = "completed"
            task.completed_at = datetime.datetime.utcnow()
            task.message = "Analysis and report generation completed"
            db.commit()
            db.refresh(task)

    return task


@router.post("/cancel/{task_id}")
def cancel_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running task by task ID."""
    # Get the task
    task = db.query(models.TaskStatus).filter(
        models.TaskStatus.id == task_id,
        models.TaskStatus.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "running":
        raise HTTPException(status_code=400, detail="Task is not running")

    if not task.process_id:
        raise HTTPException(status_code=400, detail="Task has no process ID to cancel")

    try:
        # Try to terminate the process gracefully first
        os.kill(task.process_id, signal.SIGTERM)

        # Update task status
        task.status = "cancelled"
        task.message = "Task cancelled by user"
        task.completed_at = datetime.datetime.utcnow()
        db.commit()

        return {
            "message": "Task cancelled successfully",
            "task_id": task_id
        }
    except ProcessLookupError:
        # Process doesn't exist anymore, just mark as cancelled
        task.status = "cancelled"
        task.message = "Task process not found (may have already completed)"
        task.completed_at = datetime.datetime.utcnow()
        db.commit()

        return {
            "message": "Task process not found, marked as cancelled",
            "task_id": task_id
        }
    except PermissionError:
        raise HTTPException(status_code=403, detail="No permission to kill this process")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")
