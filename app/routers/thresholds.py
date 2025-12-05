"""
Threshold Management Router - API endpoints for NSTXView parameter threshold configuration.

This module provides endpoints for:
- Listing parameter thresholds
- Updating threshold values
- Viewing threshold change history
- Triggering reprocessing with new thresholds
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import subprocess
import os

from app.database import get_db
from app.auth import get_current_user
from app.dependencies import check_product_access
from app.models import (
    User, ParameterThreshold, ThresholdHistory
)


# === Pydantic Schemas ===

class ThresholdSummary(BaseModel):
    """Summary of a parameter threshold"""
    id: int
    parameter_name: str
    parameter_pattern: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    expected_unit: Optional[str]
    category: Optional[str]
    active: bool
    source: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ThresholdDetail(BaseModel):
    """Full threshold details"""
    id: int
    parameter_name: str
    parameter_pattern: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    expected_unit: Optional[str]
    category: Optional[str]
    reason_below: Optional[str]
    reason_above: Optional[str]
    flag_all: bool
    special_case: Optional[str]
    source: Optional[str]
    active: bool
    created_at: datetime
    created_by: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


class ThresholdUpdateRequest(BaseModel):
    """Request to update a threshold"""
    min_value: Optional[float] = Field(None, description="Minimum acceptable value")
    max_value: Optional[float] = Field(None, description="Maximum acceptable value")
    reason: str = Field(..., description="Reason for changing threshold")
    trigger_reprocessing: bool = Field(False, description="Trigger reprocessing of all measurements")


class ThresholdHistoryRecord(BaseModel):
    """Historical threshold change record"""
    id: int
    parameter_name: str
    old_min: Optional[float]
    old_max: Optional[float]
    new_min: Optional[float]
    new_max: Optional[float]
    changed_by: int
    changed_by_email: Optional[str]
    changed_at: datetime
    reason: Optional[str]
    reprocessing_triggered: bool

    class Config:
        from_attributes = True


class ReprocessingStatus(BaseModel):
    """Status of reprocessing operation"""
    status: str
    message: str
    batch_id: Optional[int] = None


# === Router Setup ===

router = APIRouter(
    prefix="/nstxview/thresholds",
    tags=["nstxview-thresholds"],
    dependencies=[Depends(check_product_access("nstxview"))]
)


# === Endpoints ===

@router.get("/", response_model=List[ThresholdSummary])
async def list_thresholds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    active_only: bool = Query(True, description="Show only active thresholds"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """
    List all parameter thresholds.

    Returns thresholds ordered by parameter name.
    Requires admin or data_reviewer role.
    """
    # Check access permissions
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Data reviewer or admin privileges required")
    query = db.query(ParameterThreshold)

    if active_only:
        query = query.filter(ParameterThreshold.active == True)

    if category:
        query = query.filter(ParameterThreshold.category == category)

    query = query.order_by(ParameterThreshold.parameter_name)

    thresholds = query.all()

    return [
        ThresholdSummary(
            id=t.id,
            parameter_name=t.parameter_name,
            parameter_pattern=t.parameter_pattern,
            min_value=t.min_value,
            max_value=t.max_value,
            expected_unit=t.expected_unit,
            category=t.category,
            active=t.active,
            source=t.source,
            notes=t.notes
        )
        for t in thresholds
    ]


@router.get("/{threshold_id}", response_model=ThresholdDetail)
async def get_threshold_detail(
    threshold_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full details for a specific threshold.
    Requires admin or data_reviewer role.
    """
    # Check access permissions
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Data reviewer or admin privileges required")
    threshold = db.query(ParameterThreshold).filter(
        ParameterThreshold.id == threshold_id
    ).first()

    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")

    return ThresholdDetail(
        id=threshold.id,
        parameter_name=threshold.parameter_name,
        parameter_pattern=threshold.parameter_pattern,
        min_value=threshold.min_value,
        max_value=threshold.max_value,
        expected_unit=threshold.expected_unit,
        category=threshold.category,
        reason_below=threshold.reason_below,
        reason_above=threshold.reason_above,
        flag_all=threshold.flag_all,
        special_case=threshold.special_case,
        source=threshold.source,
        active=threshold.active,
        created_at=threshold.created_at,
        created_by=threshold.created_by,
        notes=threshold.notes
    )


@router.put("/{threshold_id}")
async def update_threshold(
    threshold_id: int,
    update: ThresholdUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a threshold's min/max values.

    Creates a history record and optionally triggers reprocessing.
    Requires admin or data_reviewer privileges.
    """
    # Check permission - admin or data_reviewer can update thresholds
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Admin or data reviewer privileges required")

    # Find threshold
    threshold = db.query(ParameterThreshold).filter(
        ParameterThreshold.id == threshold_id
    ).first()

    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")

    # Create history record
    history = ThresholdHistory(
        parameter_name=threshold.parameter_name,
        old_min=threshold.min_value,
        old_max=threshold.max_value,
        new_min=update.min_value if update.min_value is not None else threshold.min_value,
        new_max=update.max_value if update.max_value is not None else threshold.max_value,
        changed_by=current_user.id,
        changed_at=datetime.utcnow(),
        reason=update.reason,
        reprocessing_triggered=update.trigger_reprocessing
    )
    db.add(history)

    # Update threshold
    if update.min_value is not None:
        threshold.min_value = update.min_value
    if update.max_value is not None:
        threshold.max_value = update.max_value

    db.commit()

    # Trigger reprocessing if requested
    if update.trigger_reprocessing:
        # Run outlier detection script in background
        background_tasks.add_task(
            run_outlier_detection,
            reprocess_all=True
        )

    return {
        "status": "success",
        "message": "Threshold updated successfully",
        "threshold_id": threshold_id,
        "reprocessing_triggered": update.trigger_reprocessing
    }


@router.get("/{threshold_id}/history", response_model=List[ThresholdHistoryRecord])
async def get_threshold_history(
    threshold_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get change history for a specific threshold.
    Requires admin or data_reviewer role.
    """
    # Check access permissions
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Data reviewer or admin privileges required")
    # Get threshold
    threshold = db.query(ParameterThreshold).filter(
        ParameterThreshold.id == threshold_id
    ).first()

    if not threshold:
        raise HTTPException(status_code=404, detail="Threshold not found")

    # Get history
    history = db.query(ThresholdHistory).filter(
        ThresholdHistory.parameter_name == threshold.parameter_name
    ).order_by(desc(ThresholdHistory.changed_at)).all()

    # Build response with user emails
    results = []
    for record in history:
        user = db.query(User).filter(User.id == record.changed_by).first()
        results.append(ThresholdHistoryRecord(
            id=record.id,
            parameter_name=record.parameter_name,
            old_min=record.old_min,
            old_max=record.old_max,
            new_min=record.new_min,
            new_max=record.new_max,
            changed_by=record.changed_by,
            changed_by_email=user.email if user else None,
            changed_at=record.changed_at,
            reason=record.reason,
            reprocessing_triggered=record.reprocessing_triggered
        ))

    return results


@router.post("/reprocess")
async def trigger_reprocessing(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    batch_id: Optional[int] = Query(None, description="Reprocess specific batch only")
):
    """
    Trigger reprocessing of all measurements with current thresholds.

    Requires admin or data_reviewer privileges.
    """
    # Check permission - admin or data_reviewer can trigger reprocessing
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Admin or data reviewer privileges required")

    # Run outlier detection script in background
    background_tasks.add_task(
        run_outlier_detection,
        reprocess_all=True,
        batch_id=batch_id
    )

    return {
        "status": "success",
        "message": "Reprocessing initiated",
        "batch_id": batch_id
    }


# === Helper Functions ===

def run_outlier_detection(reprocess_all: bool = False, batch_id: Optional[int] = None):
    """
    Run the outlier detection script in a subprocess.

    This runs the script/outlier_detection.py script which:
    1. Loads thresholds from database
    2. Scans parameters for outliers
    3. Flags outliers with detailed reasoning
    """
    script_path = os.path.join(os.path.dirname(__file__), "../../scripts/outlier_detection.py")

    cmd = ["python3", script_path]

    if reprocess_all:
        cmd.append("--reprocess-all")

    if batch_id:
        cmd.extend(["--batch-id", str(batch_id)])

    # Run script
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            print(f"Outlier detection failed: {result.stderr}")
        else:
            print(f"Outlier detection completed: {result.stdout}")

    except subprocess.TimeoutExpired:
        print("Outlier detection timed out after 5 minutes")
    except Exception as e:
        print(f"Error running outlier detection: {e}")
