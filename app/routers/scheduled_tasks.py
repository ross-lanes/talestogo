"""
API endpoints for scheduled task management
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import calendar
import pytz

from ..database import get_db
from ..models import User, ScheduledTask, ScheduledTaskHistory
from ..auth import get_current_user

router = APIRouter(prefix="/scheduled-tasks", tags=["scheduling"])


# === Pydantic Schemas ===

class ScheduleCreate(BaseModel):
    brand_id: int
    schedule_type: str  # 'first_day', 'middle', 'last_day'
    timezone: Optional[str] = 'UTC'
    send_email_notification: Optional[bool] = True
    notification_email: Optional[str] = None


class ScheduleUpdate(BaseModel):
    schedule_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    timezone: Optional[str] = None
    send_email_notification: Optional[bool] = None
    notification_email: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: int
    user_id: int
    brand_id: int
    schedule_type: str
    is_enabled: bool
    timezone: str
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    last_batch_id: Optional[int]
    send_email_notification: bool
    notification_email: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    id: int
    scheduled_task_id: int
    started_at: datetime
    completed_at: Optional[datetime]
    status: str
    batch_id: Optional[int]
    collection_responses: int
    analysis_responses: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


# === Helper Functions ===

def calculate_next_run(schedule_type: str, timezone_str: str) -> datetime:
    """Calculate the next run time based on schedule type"""
    try:
        tz = pytz.timezone(timezone_str)
    except:
        tz = pytz.UTC

    now = datetime.now(tz)

    if schedule_type == 'first_day':
        # Next first day of month at 2 AM
        if now.day == 1 and now.hour < 2:
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
        else:
            # Go to next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=1, hour=2, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=1, hour=2, minute=0, second=0, microsecond=0)

    elif schedule_type == 'middle':
        # 15th of month at 2 AM
        if now.day < 15 or (now.day == 15 and now.hour < 2):
            next_run = now.replace(day=15, hour=2, minute=0, second=0, microsecond=0)
        else:
            # Go to 15th of next month
            if now.month == 12:
                next_run = now.replace(year=now.year + 1, month=1, day=15, hour=2, minute=0, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month + 1, day=15, hour=2, minute=0, second=0, microsecond=0)

    elif schedule_type == 'last_day':
        # Last day of month at 2 AM
        last_day = calendar.monthrange(now.year, now.month)[1]

        if now.day < last_day or (now.day == last_day and now.hour < 2):
            next_run = now.replace(day=last_day, hour=2, minute=0, second=0, microsecond=0)
        else:
            # Go to last day of next month
            if now.month == 12:
                next_year = now.year + 1
                next_month = 1
            else:
                next_year = now.year
                next_month = now.month + 1

            last_day = calendar.monthrange(next_year, next_month)[1]
            next_run = now.replace(year=next_year, month=next_month, day=last_day, hour=2, minute=0, second=0, microsecond=0)

    else:
        raise ValueError(f"Invalid schedule_type: {schedule_type}")

    # Convert to UTC for storage
    return next_run.astimezone(pytz.UTC)


# === Endpoints ===

@router.get("/", response_model=Optional[ScheduleResponse])
async def get_schedule(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current schedule for a brand"""
    schedule = db.query(ScheduledTask).filter_by(
        user_id=current_user.id,
        brand_id=brand_id
    ).first()

    return schedule


@router.post("/", response_model=ScheduleResponse)
async def create_or_update_schedule(
    schedule_data: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update a schedule"""
    # Validate schedule_type
    if schedule_data.schedule_type not in ['first_day', 'middle', 'last_day']:
        raise HTTPException(status_code=400, detail="Invalid schedule_type. Must be 'first_day', 'middle', or 'last_day'")

    # Check if schedule already exists
    existing = db.query(ScheduledTask).filter_by(
        user_id=current_user.id,
        brand_id=schedule_data.brand_id
    ).first()

    if existing:
        # Update existing
        existing.schedule_type = schedule_data.schedule_type
        existing.timezone = schedule_data.timezone or 'UTC'
        existing.is_enabled = True
        existing.send_email_notification = schedule_data.send_email_notification
        existing.notification_email = schedule_data.notification_email
        existing.next_run_at = calculate_next_run(
            schedule_data.schedule_type,
            existing.timezone
        )
        existing.updated_at = datetime.utcnow()
        schedule = existing
    else:
        # Create new
        schedule = ScheduledTask(
            user_id=current_user.id,
            brand_id=schedule_data.brand_id,
            schedule_type=schedule_data.schedule_type,
            timezone=schedule_data.timezone or 'UTC',
            is_enabled=True,
            send_email_notification=schedule_data.send_email_notification,
            notification_email=schedule_data.notification_email,
            next_run_at=calculate_next_run(
                schedule_data.schedule_type,
                schedule_data.timezone or 'UTC'
            )
        )
        db.add(schedule)

    db.commit()
    db.refresh(schedule)
    return schedule


@router.patch("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing schedule"""
    schedule = db.query(ScheduledTask).filter_by(
        id=schedule_id,
        user_id=current_user.id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    # Update fields
    if schedule_data.schedule_type is not None:
        if schedule_data.schedule_type not in ['first_day', 'middle', 'last_day']:
            raise HTTPException(status_code=400, detail="Invalid schedule_type")
        schedule.schedule_type = schedule_data.schedule_type
        schedule.next_run_at = calculate_next_run(
            schedule_data.schedule_type,
            schedule.timezone
        )

    if schedule_data.is_enabled is not None:
        schedule.is_enabled = schedule_data.is_enabled

    if schedule_data.timezone is not None:
        schedule.timezone = schedule_data.timezone
        # Recalculate next run with new timezone
        schedule.next_run_at = calculate_next_run(
            schedule.schedule_type,
            schedule.timezone
        )

    if schedule_data.send_email_notification is not None:
        schedule.send_email_notification = schedule_data.send_email_notification

    if schedule_data.notification_email is not None:
        schedule.notification_email = schedule_data.notification_email

    schedule.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a schedule"""
    schedule = db.query(ScheduledTask).filter_by(
        id=schedule_id,
        user_id=current_user.id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    db.delete(schedule)
    db.commit()
    return {"message": "Schedule deleted successfully"}


@router.get("/{schedule_id}/history", response_model=List[HistoryResponse])
async def get_schedule_history(
    schedule_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution history for a schedule"""
    schedule = db.query(ScheduledTask).filter_by(
        id=schedule_id,
        user_id=current_user.id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    history = db.query(ScheduledTaskHistory).filter_by(
        scheduled_task_id=schedule_id
    ).order_by(desc(ScheduledTaskHistory.started_at)).limit(limit).all()

    return history
