"""
API endpoints for managing collection batches
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import datetime

from ..database import get_db
from ..models import User, CollectionBatch, Response
from ..auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/batches", tags=["batches"])


# === Pydantic Schemas ===

class BatchCreate(BaseModel):
    batch_name: str
    description: Optional[str] = None
    platforms: Optional[str] = None
    notes: Optional[str] = None

class BatchUpdate(BaseModel):
    batch_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class BatchResponse(BaseModel):
    id: int
    batch_name: str
    description: Optional[str]
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime]
    status: str
    total_queries: int
    total_responses: int
    platforms: Optional[str]
    notes: Optional[str]
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# === Endpoints ===

@router.get("/", response_model=List[BatchResponse])
async def list_batches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    brand_id: Optional[int] = None
):
    """
    List all collection batches for the current user.
    Optionally filter by brand_id.
    """
    query = db.query(CollectionBatch).filter_by(user_id=current_user.id)

    if brand_id:
        query = query.filter_by(brand_id=brand_id)

    batches = query.order_by(desc(CollectionBatch.started_at)).all()

    return batches


@router.get("/{batch_id}", response_model=BatchResponse)
async def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific batch.
    """
    batch = db.query(CollectionBatch).filter_by(
        id=batch_id,
        user_id=current_user.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    return batch


@router.post("/", response_model=BatchResponse)
async def create_batch(
    batch_data: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    brand_id: Optional[int] = None
):
    """
    Create a new collection batch.
    This is typically called when starting a new data collection.
    """
    # Get brand_id from user's active brand if not provided
    if not brand_id and hasattr(current_user, 'active_brand_id'):
        brand_id = current_user.active_brand_id

    batch = CollectionBatch(
        user_id=current_user.id,
        brand_id=brand_id,
        batch_name=batch_data.batch_name,
        description=batch_data.description,
        platforms=batch_data.platforms,
        notes=batch_data.notes,
        started_at=datetime.datetime.utcnow(),
        status='in_progress',
        total_queries=0,
        total_responses=0
    )

    db.add(batch)
    db.commit()
    db.refresh(batch)

    return batch


@router.patch("/{batch_id}", response_model=BatchResponse)
async def update_batch(
    batch_id: int,
    batch_data: BatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a batch's metadata (name, description, status, notes).
    """
    batch = db.query(CollectionBatch).filter_by(
        id=batch_id,
        user_id=current_user.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Update fields if provided
    if batch_data.batch_name is not None:
        batch.batch_name = batch_data.batch_name
    if batch_data.description is not None:
        batch.description = batch_data.description
    if batch_data.status is not None:
        batch.status = batch_data.status
        # If marking as completed, set completed_at
        if batch_data.status == 'completed' and not batch.completed_at:
            batch.completed_at = datetime.datetime.utcnow()
    if batch_data.notes is not None:
        batch.notes = batch_data.notes

    db.commit()
    db.refresh(batch)

    return batch


@router.post("/{batch_id}/complete")
async def complete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a batch as completed and update its statistics.
    This should be called when a data collection finishes.
    Automatically caches batch analytics for fast reporting.
    """
    from ..services.batch_analytics import compute_batch_analytics

    batch = db.query(CollectionBatch).filter_by(
        id=batch_id,
        user_id=current_user.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Update batch statistics
    response_count = db.query(func.count(Response.id)).filter_by(batch_id=batch_id).scalar()
    query_count = db.query(func.count(func.distinct(Response.query_id))).filter_by(batch_id=batch_id).scalar()

    batch.completed_at = datetime.datetime.utcnow()
    batch.status = 'completed'
    batch.total_responses = response_count
    batch.total_queries = query_count

    db.commit()
    db.refresh(batch)

    # Compute and cache batch analytics for fast future reporting
    try:
        compute_batch_analytics(db, batch_id, current_user.id, batch.brand_id)
    except Exception as e:
        # Log the error but don't fail the batch completion
        print(f"Warning: Failed to cache batch analytics: {e}")

    return {
        "message": "Batch completed successfully",
        "batch_id": batch.id,
        "total_responses": batch.total_responses,
        "total_queries": batch.total_queries
    }


@router.delete("/{batch_id}")
async def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a batch and all its associated responses.
    USE WITH CAUTION - This cannot be undone!
    """
    batch = db.query(CollectionBatch).filter_by(
        id=batch_id,
        user_id=current_user.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Count responses before deletion
    response_count = db.query(Response).filter_by(batch_id=batch_id).count()

    # Delete all responses in this batch
    db.query(Response).filter_by(batch_id=batch_id).delete()

    # Delete the batch record
    db.delete(batch)
    db.commit()

    return {
        "message": f"Batch '{batch.batch_name}' deleted successfully",
        "deleted_responses": response_count
    }


@router.get("/{batch_id}/stats")
async def get_batch_stats(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed statistics for a specific batch.
    """
    batch = db.query(CollectionBatch).filter_by(
        id=batch_id,
        user_id=current_user.id
    ).first()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Get response breakdown by platform
    platform_stats = db.query(
        Response.platform,
        func.count(Response.id).label('count')
    ).filter_by(batch_id=batch_id).group_by(Response.platform).all()

    # Get analysis status
    analyzed_count = db.query(Response).filter_by(
        batch_id=batch_id
    ).filter(Response.analyzed_at.isnot(None)).count()

    unanalyzed_count = db.query(Response).filter_by(
        batch_id=batch_id
    ).filter(Response.analyzed_at.is_(None)).count()

    # Calculate duration
    duration_minutes = None
    if batch.completed_at:
        duration = batch.completed_at - batch.started_at
        duration_minutes = int(duration.total_seconds() / 60)

    return {
        "batch_id": batch.id,
        "batch_name": batch.batch_name,
        "status": batch.status,
        "started_at": batch.started_at,
        "completed_at": batch.completed_at,
        "duration_minutes": duration_minutes,
        "total_responses": batch.total_responses,
        "total_queries": batch.total_queries,
        "analyzed_responses": analyzed_count,
        "unanalyzed_responses": unanalyzed_count,
        "platform_breakdown": [
            {"platform": p, "count": c} for p, c in platform_stats
        ]
    }
