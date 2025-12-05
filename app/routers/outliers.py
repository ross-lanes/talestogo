"""
Outlier Management Router - API endpoints for NSTXView parameter outlier detection and review.

This module provides endpoints for:
- Listing flagged outliers with filters
- Getting outlier details
- Reviewing/correcting/dismissing outliers
- Getting outlier statistics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.database import get_db
from app.auth import get_current_user
from app.dependencies import check_product_access
from app.models import (
    User, NSTXParameter, NSTXPaper, ParameterThreshold
)


# === Pydantic Schemas ===

class OutlierSummary(BaseModel):
    """Summary of a flagged outlier for list views"""
    id: int
    parameter_name: str
    parameter_category: Optional[str]
    value: Optional[float]
    unit: Optional[str]
    paper_id: int
    paper_title: Optional[str]
    paper_doi: Optional[str]
    page_number: Optional[int]
    outlier_reason: Optional[str]
    flagged_at: Optional[datetime]
    reviewed: bool
    review_action: Optional[str]

    class Config:
        from_attributes = True


class OutlierDetail(BaseModel):
    """Full outlier details including context"""
    id: int
    parameter_name: str
    parameter_category: Optional[str]
    value: Optional[float]
    value_min: Optional[float]
    value_max: Optional[float]
    unit: Optional[str]
    paper_id: int
    paper_title: Optional[str]
    paper_doi: Optional[str]
    paper_authors: Optional[List[str]]
    page_number: Optional[int]
    context: Optional[str]
    outlier_reason: Optional[str]
    flagged_at: Optional[datetime]
    flagged_by_threshold_id: Optional[int]
    threshold_min: Optional[float]
    threshold_max: Optional[float]
    threshold_unit: Optional[str]
    reviewed: bool
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    review_action: Optional[str]
    review_notes: Optional[str]
    corrected_value: Optional[float]
    corrected_unit: Optional[str]

    class Config:
        from_attributes = True


class OutlierReviewRequest(BaseModel):
    """Request to review an outlier"""
    action: str = Field(..., description="Action: 'correct', 'dismiss', or 'delete'")
    notes: Optional[str] = Field(None, description="Review notes explaining decision")
    corrected_value: Optional[float] = Field(None, description="Corrected value if action is 'correct'")
    corrected_unit: Optional[str] = Field(None, description="Corrected unit if action is 'correct'")


class OutlierStatistics(BaseModel):
    """Statistics about outliers"""
    total_outliers: int
    unreviewed_outliers: int
    reviewed_outliers: int
    by_parameter: List[dict]
    by_action: dict
    flagged_today: int
    flagged_this_week: int


# === Router Setup ===

router = APIRouter(
    prefix="/nstxview/outliers",
    tags=["nstxview-outliers"],
    dependencies=[Depends(check_product_access("nstxview"))]
)


# === Endpoints ===

@router.get("/", response_model=List[OutlierSummary])
async def list_outliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    parameter_name: Optional[str] = Query(None, description="Filter by parameter name"),
    reviewed: Optional[bool] = Query(None, description="Filter by review status"),
    review_action: Optional[str] = Query(None, description="Filter by review action"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    List flagged outliers with optional filters.

    Returns a paginated list of parameter measurements flagged as outliers.
    Requires admin or data_reviewer role.
    """
    # Check access permissions
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Data reviewer or admin privileges required")
    query = db.query(NSTXParameter).filter(NSTXParameter.is_outlier == True)

    # Apply filters
    if parameter_name:
        query = query.filter(NSTXParameter.parameter_name.ilike(f"%{parameter_name}%"))

    if reviewed is not None:
        query = query.filter(NSTXParameter.reviewed == reviewed)

    if review_action:
        query = query.filter(NSTXParameter.review_action == review_action)

    # Order by flagged date (newest first)
    query = query.order_by(desc(NSTXParameter.flagged_at))

    # Apply pagination
    outliers = query.offset(offset).limit(limit).all()

    # Build response with paper info
    results = []
    for outlier in outliers:
        paper = db.query(NSTXPaper).filter(NSTXPaper.id == outlier.paper_id).first()
        results.append(OutlierSummary(
            id=outlier.id,
            parameter_name=outlier.parameter_name,
            parameter_category=outlier.parameter_category,
            value=outlier.value,
            unit=outlier.unit,
            paper_id=outlier.paper_id,
            paper_title=paper.title if paper else None,
            paper_doi=paper.doi if paper else None,
            page_number=getattr(outlier, 'page_number', None),
            outlier_reason=outlier.outlier_reason,
            flagged_at=outlier.flagged_at,
            reviewed=outlier.reviewed if outlier.reviewed is not None else False,
            review_action=outlier.review_action
        ))

    return results


@router.get("/{measurement_id}", response_model=OutlierDetail)
async def get_outlier_detail(
    measurement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full details for a specific outlier including paper context and threshold information.
    Requires admin or data_reviewer role.
    """
    # Check access permissions
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Data reviewer or admin privileges required")
    outlier = db.query(NSTXParameter).filter(
        NSTXParameter.id == measurement_id,
        NSTXParameter.is_outlier == True
    ).first()

    if not outlier:
        raise HTTPException(status_code=404, detail="Outlier not found")

    # Get paper info
    paper = db.query(NSTXPaper).filter(NSTXPaper.id == outlier.paper_id).first()

    # Get threshold info
    threshold = None
    if outlier.flagged_by_threshold_id:
        threshold = db.query(ParameterThreshold).filter(
            ParameterThreshold.id == outlier.flagged_by_threshold_id
        ).first()

    # Parse authors from JSON string if needed
    import json
    authors = None
    if paper and paper.authors:
        try:
            if isinstance(paper.authors, str):
                authors = json.loads(paper.authors)
            else:
                authors = paper.authors
        except:
            authors = None

    return OutlierDetail(
        id=outlier.id,
        parameter_name=outlier.parameter_name,
        parameter_category=outlier.parameter_category,
        value=outlier.value,
        value_min=outlier.value_min,
        value_max=outlier.value_max,
        unit=outlier.unit,
        paper_id=outlier.paper_id,
        paper_title=paper.title if paper else None,
        paper_doi=paper.doi if paper else None,
        paper_authors=authors,
        page_number=getattr(outlier, 'page_number', None),
        context=outlier.context,
        outlier_reason=outlier.outlier_reason,
        flagged_at=outlier.flagged_at,
        flagged_by_threshold_id=outlier.flagged_by_threshold_id,
        threshold_min=threshold.min_value if threshold else None,
        threshold_max=threshold.max_value if threshold else None,
        threshold_unit=threshold.expected_unit if threshold else None,
        reviewed=outlier.reviewed if outlier.reviewed is not None else False,
        reviewed_by=outlier.reviewed_by,
        reviewed_at=outlier.reviewed_at,
        review_action=outlier.review_action,
        review_notes=outlier.review_notes,
        corrected_value=outlier.corrected_value,
        corrected_unit=outlier.corrected_unit
    )


@router.post("/{measurement_id}/review")
async def review_outlier(
    measurement_id: int,
    review: OutlierReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Review an outlier: correct the value, dismiss as false positive, or delete.

    Actions:
    - 'correct': Update with corrected value/unit
    - 'dismiss': Mark as reviewed but keep original value (false positive)
    - 'delete': Mark for deletion (requires admin approval)

    Requires admin or data_reviewer role.
    """
    # Check access permissions
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Data reviewer or admin privileges required")
    # Validate action
    if review.action not in ['correct', 'dismiss', 'delete']:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'correct', 'dismiss', or 'delete'")

    # Find outlier
    outlier = db.query(NSTXParameter).filter(
        NSTXParameter.id == measurement_id,
        NSTXParameter.is_outlier == True
    ).first()

    if not outlier:
        raise HTTPException(status_code=404, detail="Outlier not found")

    # Validate corrected values if action is 'correct'
    if review.action == 'correct':
        if review.corrected_value is None:
            raise HTTPException(status_code=400, detail="corrected_value required for 'correct' action")

    # Update outlier
    outlier.reviewed = True
    outlier.reviewed_by = current_user.id
    outlier.reviewed_at = datetime.utcnow()
    outlier.review_action = review.action
    outlier.review_notes = review.notes

    if review.action == 'correct':
        outlier.corrected_value = review.corrected_value
        outlier.corrected_unit = review.corrected_unit

    db.commit()
    db.refresh(outlier)

    return {
        "status": "success",
        "message": f"Outlier {review.action}ed successfully",
        "measurement_id": measurement_id,
        "action": review.action
    }


@router.get("/statistics/summary", response_model=OutlierStatistics)
async def get_outlier_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get summary statistics about outliers.
    Requires admin or data_reviewer role.
    """
    # Check access permissions
    if not (current_user.is_admin or current_user.is_data_reviewer):
        raise HTTPException(status_code=403, detail="Data reviewer or admin privileges required")
    from datetime import timedelta

    # Total outliers
    total = db.query(func.count(NSTXParameter.id)).filter(
        NSTXParameter.is_outlier == True
    ).scalar()

    # Reviewed vs unreviewed
    unreviewed = db.query(func.count(NSTXParameter.id)).filter(
        NSTXParameter.is_outlier == True,
        NSTXParameter.reviewed == False
    ).scalar()

    reviewed = total - unreviewed

    # By parameter
    by_param = db.query(
        NSTXParameter.parameter_name,
        func.count(NSTXParameter.id).label('count')
    ).filter(
        NSTXParameter.is_outlier == True
    ).group_by(
        NSTXParameter.parameter_name
    ).order_by(
        desc('count')
    ).all()

    by_parameter = [
        {"parameter_name": p[0], "count": p[1]}
        for p in by_param
    ]

    # By review action
    by_act = db.query(
        NSTXParameter.review_action,
        func.count(NSTXParameter.id).label('count')
    ).filter(
        NSTXParameter.is_outlier == True,
        NSTXParameter.reviewed == True
    ).group_by(
        NSTXParameter.review_action
    ).all()

    by_action = {
        action: count for action, count in by_act if action
    }

    # Flagged today
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    flagged_today = db.query(func.count(NSTXParameter.id)).filter(
        NSTXParameter.is_outlier == True,
        NSTXParameter.flagged_at >= today_start
    ).scalar()

    # Flagged this week
    week_start = now - timedelta(days=7)
    flagged_this_week = db.query(func.count(NSTXParameter.id)).filter(
        NSTXParameter.is_outlier == True,
        NSTXParameter.flagged_at >= week_start
    ).scalar()

    return OutlierStatistics(
        total_outliers=total,
        unreviewed_outliers=unreviewed,
        reviewed_outliers=reviewed,
        by_parameter=by_parameter,
        by_action=by_action,
        flagged_today=flagged_today,
        flagged_this_week=flagged_this_week
    )
