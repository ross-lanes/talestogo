"""
Task Status API Endpoints
Provides real-time task status for data collection and analysis operations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .. import models, crud
from ..auth import get_current_user
from ..database import get_db
from ..routers.analytics import get_active_brand_id

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)


@router.get("/status", response_model=List[Dict[str, Any]])
def get_active_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get active and recently completed tasks for the current user's active brand.
    Returns tasks from the last 24 hours that are running or just completed.
    """
    # Calculate cutoff time (24 hours ago)
    cutoff_time = datetime.utcnow() - timedelta(hours=24)

    # Build query for tasks
    query = db.query(models.TaskStatus).filter(
        models.TaskStatus.user_id == current_user.id,
        models.TaskStatus.started_at >= cutoff_time
    )

    # Filter by brand if specified
    if brand_id:
        query = query.filter(models.TaskStatus.brand_id == brand_id)

    # Get running tasks and recently completed/failed tasks
    tasks = query.filter(
        models.TaskStatus.status.in_(['running', 'completed', 'failed', 'cancelled'])
    ).order_by(models.TaskStatus.started_at.desc()).all()

    # Format response
    result = []
    for task in tasks:
        result.append({
            'id': task.id,
            'task_type': task.task_type,
            'status': task.status,
            'progress': task.progress,
            'total_items': task.total_items,
            'processed_items': task.processed_items,
            'message': task.message,
            'error_message': task.error_message,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'updated_at': task.updated_at.isoformat() if task.updated_at else None,
        })

    return result


@router.post("/{task_id}/dismiss")
def dismiss_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Mark a completed or failed task as dismissed (removes from active display).
    This doesn't delete the task, just marks it so the UI can hide it.
    """
    task = db.query(models.TaskStatus).filter(
        models.TaskStatus.id == task_id,
        models.TaskStatus.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # For now, we'll just return success. In future, could add a 'dismissed' flag to the model
    # or delete completed tasks older than a certain threshold

    return {"success": True, "message": "Task dismissed"}
