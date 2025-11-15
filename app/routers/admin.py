"""
Admin API endpoints for managing all users' data.

Only accessible to admin users (is_admin=True).
Allows admins to view and manage all brands, queries, descriptors, and competitors
across all users for support and troubleshooting purposes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .. import crud, models, schemas
from ..auth import get_current_admin_user
from ..database import get_db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin_user)]  # Require admin for all endpoints
)


# === User Management ===

@router.get("/users", response_model=List[schemas.User])
def get_all_users(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all users in the system."""
    users = db.query(models.User).all()
    return users


@router.get("/users/{user_id}", response_model=schemas.User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get a specific user by ID."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# === Brand Management ===

@router.get("/brands", response_model=List[schemas.BrandInfo])
def get_all_brands(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all brands across all users."""
    brands = db.query(models.BrandInfo).all()
    return brands


@router.get("/users/{user_id}/brands", response_model=List[schemas.BrandInfo])
def get_user_brands(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all brands for a specific user."""
    brands = db.query(models.BrandInfo).filter(
        models.BrandInfo.user_id == user_id
    ).all()
    return brands


@router.get("/brands/{brand_id}", response_model=schemas.BrandInfo)
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get a specific brand by ID."""
    brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.put("/brands/{brand_id}", response_model=schemas.BrandInfo)
def update_brand(
    brand_id: int,
    brand_update: schemas.BrandInfoUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Update a brand (admin can modify any user's brand)."""
    brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    update_data = brand_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)

    db.commit()
    db.refresh(brand)
    return brand


# === Query Management ===

@router.get("/users/{user_id}/brands/{brand_id}/queries", response_model=List[schemas.Query])
def get_user_brand_queries(
    user_id: int,
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all queries for a specific user and brand."""
    queries = crud.get_queries(db, user_id=user_id, brand_id=brand_id, limit=1000)
    return queries


@router.post("/users/{user_id}/brands/{brand_id}/queries", response_model=schemas.Query)
def create_query_for_user(
    user_id: int,
    brand_id: int,
    query: schemas.QueryCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Create a query for a specific user and brand."""
    return crud.create_query(db, query=query, user_id=user_id, brand_id=brand_id)


@router.put("/users/{user_id}/brands/{brand_id}/queries/{query_id}", response_model=schemas.Query)
def update_user_query(
    user_id: int,
    brand_id: int,
    query_id: str,
    query_update: schemas.QueryUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Update a query for a specific user and brand."""
    updated_query = crud.update_query(
        db, query_id=query_id, query_update=query_update,
        user_id=user_id, brand_id=brand_id
    )
    if not updated_query:
        raise HTTPException(status_code=404, detail="Query not found")
    return updated_query


@router.delete("/users/{user_id}/brands/{brand_id}/queries/{query_id}")
def delete_user_query(
    user_id: int,
    brand_id: int,
    query_id: str,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Delete a query for a specific user and brand."""
    deleted = crud.delete_query(db, query_id=query_id, user_id=user_id, brand_id=brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Query not found")
    return {"message": "Query deleted successfully"}


# === Descriptor Management ===

@router.get("/users/{user_id}/brands/{brand_id}/descriptors", response_model=List[schemas.TargetDescriptor])
def get_user_brand_descriptors(
    user_id: int,
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all descriptors for a specific user and brand."""
    descriptors = crud.get_target_descriptors(db, user_id=user_id, brand_id=brand_id, limit=1000)
    return descriptors


@router.post("/users/{user_id}/brands/{brand_id}/descriptors", response_model=schemas.TargetDescriptor)
def create_descriptor_for_user(
    user_id: int,
    brand_id: int,
    descriptor: schemas.TargetDescriptorCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Create a descriptor for a specific user and brand."""
    return crud.create_target_descriptor(db, descriptor=descriptor, user_id=user_id, brand_id=brand_id)


@router.put("/users/{user_id}/brands/{brand_id}/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor)
def update_user_descriptor(
    user_id: int,
    brand_id: int,
    descriptor_id: int,
    descriptor_update: schemas.TargetDescriptorUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Update a descriptor for a specific user and brand."""
    updated = crud.update_target_descriptor(
        db, descriptor_id=descriptor_id, descriptor_update=descriptor_update,
        user_id=user_id, brand_id=brand_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return updated


@router.delete("/users/{user_id}/brands/{brand_id}/descriptors/{descriptor_id}")
def delete_user_descriptor(
    user_id: int,
    brand_id: int,
    descriptor_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Delete a descriptor for a specific user and brand."""
    deleted = crud.delete_target_descriptor(db, descriptor_id=descriptor_id, user_id=user_id, brand_id=brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return {"message": "Descriptor deleted successfully"}


# === Competitor Management ===

@router.get("/users/{user_id}/brands/{brand_id}/competitors", response_model=List[schemas.Competitor])
def get_user_brand_competitors(
    user_id: int,
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all competitors for a specific user and brand."""
    competitors = crud.get_competitors(db, user_id=user_id, brand_id=brand_id, limit=1000)
    return competitors


@router.post("/users/{user_id}/brands/{brand_id}/competitors", response_model=schemas.Competitor)
def create_competitor_for_user(
    user_id: int,
    brand_id: int,
    competitor: schemas.CompetitorCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Create a competitor for a specific user and brand."""
    return crud.create_competitor(db, competitor=competitor, user_id=user_id, brand_id=brand_id)


@router.put("/users/{user_id}/brands/{brand_id}/competitors/{competitor_id}", response_model=schemas.Competitor)
def update_user_competitor(
    user_id: int,
    brand_id: int,
    competitor_id: int,
    competitor_update: schemas.CompetitorUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Update a competitor for a specific user and brand."""
    updated = crud.update_competitor(
        db, competitor_id=competitor_id, competitor_update=competitor_update,
        user_id=user_id, brand_id=brand_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return updated


@router.delete("/users/{user_id}/brands/{brand_id}/competitors/{competitor_id}")
def delete_user_competitor(
    user_id: int,
    brand_id: int,
    competitor_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Delete a competitor for a specific user and brand."""
    deleted = crud.delete_competitor(db, competitor_id=competitor_id, user_id=user_id, brand_id=brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"message": "Competitor deleted successfully"}


# === Scheduler Monitoring ===

@router.get("/scheduler/dashboard")
def get_scheduler_dashboard(
    days: int = 30,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """
    Get comprehensive scheduler dashboard data.
    Shows recent activity, active schedules, and health status.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get recent task history
    recent_history = db.query(models.ScheduledTaskHistory).filter(
        models.ScheduledTaskHistory.started_at >= cutoff_date
    ).order_by(models.ScheduledTaskHistory.started_at.desc()).all()

    # Get all active scheduled tasks
    active_schedules = db.query(models.ScheduledTask).filter(
        models.ScheduledTask.is_enabled == True
    ).all()

    # Get all scheduled tasks (including disabled)
    all_schedules = db.query(models.ScheduledTask).all()

    # Build history data with user/brand info
    history_data = []
    for history in recent_history:
        user = db.query(models.User).filter_by(id=history.user_id).first()
        brand = db.query(models.BrandInfo).filter_by(id=history.brand_id).first()
        schedule = db.query(models.ScheduledTask).filter_by(id=history.scheduled_task_id).first()

        duration = None
        if history.completed_at and history.started_at:
            duration = (history.completed_at - history.started_at).total_seconds()

        history_data.append({
            "id": history.id,
            "scheduled_task_id": history.scheduled_task_id,
            "status": history.status,
            "user_email": user.email if user else None,
            "user_name": user.full_name if user else None,
            "brand_name": brand.brand_name if brand else None,
            "brand_id": history.brand_id,
            "started_at": history.started_at.isoformat() if history.started_at else None,
            "completed_at": history.completed_at.isoformat() if history.completed_at else None,
            "duration_seconds": duration,
            "collection_responses": history.collection_responses,
            "analysis_responses": history.analysis_responses,
            "error_message": history.error_message,
            "schedule_type": schedule.schedule_type if schedule else None
        })

    # Build active schedules data
    schedules_data = []
    for schedule in all_schedules:
        user = db.query(models.User).filter_by(id=schedule.user_id).first()
        brand = db.query(models.BrandInfo).filter_by(id=schedule.brand_id).first()

        # Get latest history for this schedule
        latest_run = db.query(models.ScheduledTaskHistory).filter(
            models.ScheduledTaskHistory.scheduled_task_id == schedule.id
        ).order_by(models.ScheduledTaskHistory.started_at.desc()).first()

        # Check if overdue
        is_overdue = False
        if schedule.is_enabled and schedule.next_run_at:
            is_overdue = schedule.next_run_at < datetime.utcnow()

        schedules_data.append({
            "id": schedule.id,
            "user_email": user.email if user else None,
            "user_name": user.full_name if user else None,
            "user_id": schedule.user_id,
            "brand_name": brand.brand_name if brand else None,
            "brand_id": schedule.brand_id,
            "schedule_type": schedule.schedule_type,
            "is_enabled": schedule.is_enabled,
            "next_run_at": schedule.next_run_at.isoformat() if schedule.next_run_at else None,
            "last_run_at": schedule.last_run_at.isoformat() if schedule.last_run_at else None,
            "last_status": latest_run.status if latest_run else None,
            "send_email_notification": schedule.send_email_notification,
            "notification_email": schedule.notification_email,
            "timezone": schedule.timezone,
            "is_overdue": is_overdue
        })

    # Calculate summary statistics
    total_runs = len(recent_history)
    success_count = len([h for h in recent_history if h.status == 'success'])
    failed_count = len([h for h in recent_history if h.status == 'failed'])
    partial_count = len([h for h in recent_history if h.status == 'partial'])
    running_count = len([h for h in recent_history if h.status == 'running'])

    # Identify issues
    failed_tasks = [h for h in history_data if h['status'] in ['failed', 'partial']]
    overdue_tasks = [s for s in schedules_data if s['is_overdue']]
    stalled_tasks = [h for h in history_data if h['status'] == 'running' and h['started_at']]

    # Check for stalled (running for > 2 hours)
    stalled_threshold = datetime.utcnow() - timedelta(hours=2)
    actual_stalled = []
    for task in stalled_tasks:
        if task['started_at']:
            started = datetime.fromisoformat(task['started_at'])
            if started < stalled_threshold:
                actual_stalled.append(task)

    return {
        "summary": {
            "total_runs_last_{}_days".format(days): total_runs,
            "success": success_count,
            "failed": failed_count,
            "partial": partial_count,
            "running": running_count,
            "success_rate": round((success_count / total_runs * 100) if total_runs > 0 else 0, 1),
            "total_active_schedules": len([s for s in schedules_data if s['is_enabled']]),
            "total_schedules": len(schedules_data)
        },
        "recent_activity": history_data,
        "active_schedules": [s for s in schedules_data if s['is_enabled']],
        "all_schedules": schedules_data,
        "health": {
            "failed_tasks": failed_tasks,
            "overdue_tasks": overdue_tasks,
            "stalled_tasks": actual_stalled,
            "has_issues": len(failed_tasks) > 0 or len(overdue_tasks) > 0 or len(actual_stalled) > 0
        }
    }


@router.get("/scheduler/history")
def get_scheduler_history(
    days: int = 7,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
) -> List[Dict[str, Any]]:
    """Get detailed scheduler history with filtering options."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(models.ScheduledTaskHistory).filter(
        models.ScheduledTaskHistory.started_at >= cutoff_date
    )

    if status:
        query = query.filter(models.ScheduledTaskHistory.status == status)

    if user_id:
        query = query.filter(models.ScheduledTaskHistory.user_id == user_id)

    history = query.order_by(models.ScheduledTaskHistory.started_at.desc()).all()

    result = []
    for h in history:
        user = db.query(models.User).filter_by(id=h.user_id).first()
        brand = db.query(models.BrandInfo).filter_by(id=h.brand_id).first()

        result.append({
            "id": h.id,
            "scheduled_task_id": h.scheduled_task_id,
            "status": h.status,
            "user_email": user.email if user else None,
            "brand_name": brand.brand_name if brand else None,
            "started_at": h.started_at.isoformat() if h.started_at else None,
            "completed_at": h.completed_at.isoformat() if h.completed_at else None,
            "collection_responses": h.collection_responses,
            "analysis_responses": h.analysis_responses,
            "error_message": h.error_message
        })

    return result
