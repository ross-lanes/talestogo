"""
NSTXView Router - API endpoints for NSTX/NSTX-U plasma physics research analysis.

This module provides endpoints for:
- Paper management and browsing
- Shot exploration and querying
- Parameter analysis
- Processing pipeline control
- Semantic search
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import datetime
import json
import re

from app.database import get_db
from app.auth import get_current_user
from app.dependencies import check_product_access
from app.models import (
    User, NSTXPaper, NSTXShot, NSTXParameter, NSTXPhenomenon,
    NSTXPaperChunk, NSTXProcessingTask, NSTXProcessingStatus,
    NSTXConversation, NSTXConversationMessage,
    MAX_SAVED_CONVERSATIONS_PER_USER, MAX_MESSAGES_PER_CONVERSATION
)
from app.services.nstxview.processing_service import perform_drive_sync, perform_extraction
from pydantic import BaseModel, Field


# === Pydantic Schemas ===

class PaperSummary(BaseModel):
    """Summary of a paper for list views"""
    id: int
    title: Optional[str]
    authors: Optional[List[str]]
    journal: Optional[str]
    publication_date: Optional[str]
    doi: Optional[str]
    status: str
    shot_count: int
    parameter_count: int
    phenomenon_count: int

    class Config:
        from_attributes = True


class PaperDetail(BaseModel):
    """Full paper details including extracted data"""
    id: int
    drive_file_id: str
    original_filename: str
    subfolder: Optional[str]
    title: Optional[str]
    authors: Optional[List[str]]
    journal: Optional[str]
    publication_date: Optional[str]
    doi: Optional[str]
    abstract: Optional[str]
    key_findings: Optional[List[str]]
    experiment_type: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShotSummary(BaseModel):
    """Summary of a shot"""
    id: int
    shot_number: int
    role: str
    paper_id: int
    paper_title: Optional[str]
    context: Optional[str]
    parameter_count: int
    phenomenon_count: int

    class Config:
        from_attributes = True


class ShotDetail(BaseModel):
    """Full shot details with parameters and phenomena"""
    id: int
    shot_number: int
    role: str
    context: Optional[str]
    characteristics: Optional[dict]
    paper_id: int
    paper_title: Optional[str]
    parameters: List[dict]
    phenomena: List[dict]

    class Config:
        from_attributes = True


class ParameterSummary(BaseModel):
    """Summary of a parameter value"""
    id: int
    parameter_name: str
    parameter_category: Optional[str]
    value: Optional[float]
    value_min: Optional[float]
    value_max: Optional[float]
    unit: Optional[str]
    uncertainty: Optional[float]
    shot_number: Optional[int]
    paper_id: int
    paper_title: Optional[str]

    class Config:
        from_attributes = True


class ParameterStatistics(BaseModel):
    """Aggregate statistics for a parameter"""
    parameter_name: str
    count: int
    min_value: Optional[float]
    max_value: Optional[float]
    avg_value: Optional[float]
    unit: Optional[str]
    paper_count: int
    shot_count: int


class PhenomenonSummary(BaseModel):
    """Summary of a phenomenon"""
    id: int
    phenomenon_type: str
    phenomenon_category: Optional[str]
    description: Optional[str]
    is_primary_focus: bool
    paper_id: int
    paper_title: Optional[str]
    shot_number: Optional[int]

    class Config:
        from_attributes = True


class ProcessingStatus(BaseModel):
    """Status of the processing pipeline"""
    total_papers: int
    pending: int
    processing: int
    completed: int
    error: int
    active_task: Optional[dict]


class SearchQuery(BaseModel):
    """Search query parameters"""
    query: str
    limit: int = Field(default=10, le=100)
    include_content: bool = False


class SearchResult(BaseModel):
    """Search result"""
    paper_id: int
    paper_title: Optional[str]
    chunk_content: str
    section: Optional[str]
    relevance_score: float


# === Router Setup ===

router = APIRouter(
    prefix="/nstxview",
    tags=["nstxview"],
    dependencies=[Depends(check_product_access("nstxview"))]
)


# === Helper Functions ===

def parse_json_field(value: Optional[str]) -> Optional[list]:
    """Parse JSON string field to list"""
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def validate_shot_number(shot_number: int) -> bool:
    """Validate that shot number is 6 digits starting with 1"""
    return 100000 <= shot_number <= 199999


# === Paper Endpoints ===

@router.get("/papers", response_model=List[PaperSummary])
async def list_papers(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, le=2500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all papers with optional filtering.

    - **status**: Filter by processing status
    - **search**: Search in title, authors, abstract
    - **limit**: Maximum number of results (default 50, max 2500)
    - **offset**: Offset for pagination
    """
    query = db.query(NSTXPaper)

    if status:
        query = query.filter(NSTXPaper.status == status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                NSTXPaper.title.ilike(search_term),
                NSTXPaper.authors.ilike(search_term),
                NSTXPaper.abstract.ilike(search_term)
            )
        )

    papers = query.order_by(NSTXPaper.created_at.desc()).offset(offset).limit(limit).all()

    results = []
    for paper in papers:
        shot_count = db.query(func.count(NSTXShot.id)).filter(NSTXShot.paper_id == paper.id).scalar()
        param_count = db.query(func.count(NSTXParameter.id)).filter(NSTXParameter.paper_id == paper.id).scalar()
        phenom_count = db.query(func.count(NSTXPhenomenon.id)).filter(NSTXPhenomenon.paper_id == paper.id).scalar()

        results.append(PaperSummary(
            id=paper.id,
            title=paper.title,
            authors=parse_json_field(paper.authors),
            journal=paper.journal,
            publication_date=paper.publication_date.isoformat() if paper.publication_date else None,
            doi=paper.doi,
            status=paper.status,
            shot_count=shot_count,
            parameter_count=param_count,
            phenomenon_count=phenom_count
        ))

    return results


@router.get("/papers/{paper_id}", response_model=PaperDetail)
async def get_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific paper"""
    paper = db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    return PaperDetail(
        id=paper.id,
        drive_file_id=paper.drive_file_id,
        original_filename=paper.original_filename,
        subfolder=paper.subfolder,
        title=paper.title,
        authors=parse_json_field(paper.authors),
        journal=paper.journal,
        publication_date=paper.publication_date.isoformat() if paper.publication_date else None,
        doi=paper.doi,
        abstract=paper.abstract,
        key_findings=parse_json_field(paper.key_findings),
        experiment_type=paper.experiment_type,
        status=paper.status,
        error_message=paper.error_message,
        created_at=paper.created_at,
        updated_at=paper.updated_at
    )


@router.get("/papers/{paper_id}/shots", response_model=List[ShotSummary])
async def get_paper_shots(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all shots mentioned in a paper"""
    paper = db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    shots = db.query(NSTXShot).filter(NSTXShot.paper_id == paper_id).all()

    results = []
    for shot in shots:
        param_count = db.query(func.count(NSTXParameter.id)).filter(NSTXParameter.shot_id == shot.id).scalar()
        phenom_count = db.query(func.count(NSTXPhenomenon.id)).filter(NSTXPhenomenon.shot_id == shot.id).scalar()

        results.append(ShotSummary(
            id=shot.id,
            shot_number=shot.shot_number,
            role=shot.role,
            paper_id=paper_id,
            paper_title=paper.title,
            context=shot.context,
            parameter_count=param_count,
            phenomenon_count=phenom_count
        ))

    return results


# === Shot Endpoints ===

@router.get("/shots", response_model=List[ShotSummary])
async def list_shots(
    shot_number: Optional[int] = None,
    role: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List shots with optional filtering.

    - **shot_number**: Filter by specific shot number (6 digits starting with 1)
    - **role**: Filter by role (primary, comparison, reference)
    """
    query = db.query(NSTXShot).join(NSTXPaper)

    if shot_number:
        if not validate_shot_number(shot_number):
            raise HTTPException(status_code=400, detail="Shot number must be 6 digits starting with 1")
        query = query.filter(NSTXShot.shot_number == shot_number)

    if role:
        query = query.filter(NSTXShot.role == role)

    shots = query.order_by(NSTXShot.shot_number).offset(offset).limit(limit).all()

    results = []
    for shot in shots:
        param_count = db.query(func.count(NSTXParameter.id)).filter(NSTXParameter.shot_id == shot.id).scalar()
        phenom_count = db.query(func.count(NSTXPhenomenon.id)).filter(NSTXPhenomenon.shot_id == shot.id).scalar()

        results.append(ShotSummary(
            id=shot.id,
            shot_number=shot.shot_number,
            role=shot.role,
            paper_id=shot.paper_id,
            paper_title=shot.paper.title,
            context=shot.context,
            parameter_count=param_count,
            phenomenon_count=phenom_count
        ))

    return results


@router.get("/shots/{shot_number}", response_model=List[ShotDetail])
async def get_shot(
    shot_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all occurrences of a shot number across all papers.
    Returns data from multiple papers if the shot is discussed in multiple publications.
    """
    if not validate_shot_number(shot_number):
        raise HTTPException(status_code=400, detail="Shot number must be 6 digits starting with 1")

    shots = db.query(NSTXShot).filter(NSTXShot.shot_number == shot_number).all()

    if not shots:
        raise HTTPException(status_code=404, detail=f"No data found for shot {shot_number}")

    results = []
    for shot in shots:
        # Get parameters for this shot
        params = db.query(NSTXParameter).filter(NSTXParameter.shot_id == shot.id).all()
        param_list = [
            {
                "name": p.parameter_name,
                "category": p.parameter_category,
                "value": p.value,
                "value_min": p.value_min,
                "value_max": p.value_max,
                "unit": p.unit,
                "uncertainty": p.uncertainty,
                "context": p.context
            }
            for p in params
        ]

        # Get phenomena for this shot
        phenoms = db.query(NSTXPhenomenon).filter(NSTXPhenomenon.shot_id == shot.id).all()
        phenom_list = [
            {
                "type": ph.phenomenon_type,
                "category": ph.phenomenon_category,
                "description": ph.description,
                "is_primary_focus": ph.is_primary_focus
            }
            for ph in phenoms
        ]

        results.append(ShotDetail(
            id=shot.id,
            shot_number=shot.shot_number,
            role=shot.role,
            context=shot.context,
            characteristics=parse_json_field(shot.characteristics) if shot.characteristics else None,
            paper_id=shot.paper_id,
            paper_title=shot.paper.title,
            parameters=param_list,
            phenomena=phenom_list
        ))

    return results


# === Parameter Endpoints ===

@router.get("/parameters", response_model=List[ParameterSummary])
async def list_parameters(
    name: Optional[str] = None,
    category: Optional[str] = None,
    shot_number: Optional[int] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List parameters with optional filtering.

    - **name**: Filter by parameter name (partial match)
    - **category**: Filter by category (plasma, operational, performance)
    - **shot_number**: Filter by specific shot
    """
    query = db.query(NSTXParameter).join(NSTXPaper)

    if name:
        query = query.filter(NSTXParameter.parameter_name.ilike(f"%{name}%"))

    if category:
        query = query.filter(NSTXParameter.parameter_category == category)

    if shot_number:
        if not validate_shot_number(shot_number):
            raise HTTPException(status_code=400, detail="Shot number must be 6 digits starting with 1")
        query = query.join(NSTXShot).filter(NSTXShot.shot_number == shot_number)

    params = query.offset(offset).limit(limit).all()

    results = []
    for p in params:
        shot_num = None
        if p.shot_id:
            shot = db.query(NSTXShot).filter(NSTXShot.id == p.shot_id).first()
            shot_num = shot.shot_number if shot else None

        results.append(ParameterSummary(
            id=p.id,
            parameter_name=p.parameter_name,
            parameter_category=p.parameter_category,
            value=p.value,
            value_min=p.value_min,
            value_max=p.value_max,
            unit=p.unit,
            uncertainty=p.uncertainty,
            shot_number=shot_num,
            paper_id=p.paper_id,
            paper_title=p.paper.title
        ))

    return results


@router.get("/parameters/statistics/{parameter_name}", response_model=ParameterStatistics)
async def get_parameter_statistics(
    parameter_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregate statistics for a specific parameter across all papers (excluding outliers)"""
    params = db.query(NSTXParameter).filter(
        NSTXParameter.parameter_name == parameter_name,
        or_(NSTXParameter.is_outlier == False, NSTXParameter.is_outlier.is_(None))
    ).all()

    if not params:
        raise HTTPException(status_code=404, detail=f"No data found for parameter: {parameter_name}")

    values = [p.value for p in params if p.value is not None]
    paper_ids = set(p.paper_id for p in params)
    shot_ids = set(p.shot_id for p in params if p.shot_id)

    # Get most common unit
    units = [p.unit for p in params if p.unit]
    unit = max(set(units), key=units.count) if units else None

    return ParameterStatistics(
        parameter_name=parameter_name,
        count=len(params),
        min_value=min(values) if values else None,
        max_value=max(values) if values else None,
        avg_value=sum(values) / len(values) if values else None,
        unit=unit,
        paper_count=len(paper_ids),
        shot_count=len(shot_ids)
    )


@router.get("/parameters/histogram/{parameter_name}")
async def get_parameter_histogram(
    parameter_name: str,
    bins: int = Query(default=10, ge=5, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get histogram data for a specific parameter (excluding outliers).

    Returns binned value distribution for visualization.
    """
    params = db.query(NSTXParameter).filter(
        NSTXParameter.parameter_name == parameter_name,
        NSTXParameter.value.isnot(None),
        or_(NSTXParameter.is_outlier == False, NSTXParameter.is_outlier.is_(None))
    ).all()

    if not params:
        raise HTTPException(status_code=404, detail=f"No numeric data found for parameter: {parameter_name}")

    values = [p.value for p in params]
    min_val = min(values)
    max_val = max(values)

    # Handle edge case where all values are the same
    if min_val == max_val:
        return {
            "parameter_name": parameter_name,
            "bins": [{"min": min_val, "max": max_val, "count": len(values), "label": f"{min_val:.3g}"}],
            "total_count": len(values),
            "unit": params[0].unit if params else None
        }

    # Calculate bin width
    bin_width = (max_val - min_val) / bins
    histogram_bins = []

    for i in range(bins):
        bin_min = min_val + i * bin_width
        bin_max = min_val + (i + 1) * bin_width

        # Count values in this bin (include max value in last bin)
        if i == bins - 1:
            count = sum(1 for v in values if bin_min <= v <= bin_max)
        else:
            count = sum(1 for v in values if bin_min <= v < bin_max)

        histogram_bins.append({
            "min": bin_min,
            "max": bin_max,
            "count": count,
            "label": f"{bin_min:.3g}-{bin_max:.3g}"
        })

    # Get most common unit
    units = [p.unit for p in params if p.unit]
    unit = max(set(units), key=units.count) if units else None

    return {
        "parameter_name": parameter_name,
        "bins": histogram_bins,
        "total_count": len(values),
        "unit": unit,
        "min_value": min_val,
        "max_value": max_val
    }


@router.get("/parameters/names")
async def list_parameter_names(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all unique parameter names with counts"""
    results = db.query(
        NSTXParameter.parameter_name,
        NSTXParameter.parameter_category,
        func.count(NSTXParameter.id).label('count')
    ).group_by(
        NSTXParameter.parameter_name,
        NSTXParameter.parameter_category
    ).order_by(func.count(NSTXParameter.id).desc()).all()

    return [
        {
            "name": r.parameter_name,
            "category": r.parameter_category,
            "count": r.count
        }
        for r in results
    ]


# === Phenomenon Endpoints ===

@router.get("/phenomena", response_model=List[PhenomenonSummary])
async def list_phenomena(
    type: Optional[str] = None,
    category: Optional[str] = None,
    primary_only: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List phenomena with optional filtering.

    - **type**: Filter by phenomenon type (partial match)
    - **category**: Filter by category
    - **primary_only**: Only show primary focus phenomena
    """
    query = db.query(NSTXPhenomenon).join(NSTXPaper)

    if type:
        query = query.filter(NSTXPhenomenon.phenomenon_type.ilike(f"%{type}%"))

    if category:
        query = query.filter(NSTXPhenomenon.phenomenon_category == category)

    if primary_only:
        query = query.filter(NSTXPhenomenon.is_primary_focus == True)

    phenoms = query.offset(offset).limit(limit).all()

    results = []
    for ph in phenoms:
        shot_num = None
        if ph.shot_id:
            shot = db.query(NSTXShot).filter(NSTXShot.id == ph.shot_id).first()
            shot_num = shot.shot_number if shot else None

        results.append(PhenomenonSummary(
            id=ph.id,
            phenomenon_type=ph.phenomenon_type,
            phenomenon_category=ph.phenomenon_category,
            description=ph.description,
            is_primary_focus=ph.is_primary_focus,
            paper_id=ph.paper_id,
            paper_title=ph.paper.title,
            shot_number=shot_num
        ))

    return results


@router.get("/phenomena/types")
async def list_phenomenon_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all unique phenomenon types with counts"""
    results = db.query(
        NSTXPhenomenon.phenomenon_type,
        NSTXPhenomenon.phenomenon_category,
        func.count(NSTXPhenomenon.id).label('count')
    ).group_by(
        NSTXPhenomenon.phenomenon_type,
        NSTXPhenomenon.phenomenon_category
    ).order_by(func.count(NSTXPhenomenon.id).desc()).all()

    return [
        {
            "type": r.phenomenon_type,
            "category": r.phenomenon_category,
            "count": r.count
        }
        for r in results
    ]


@router.get("/phenomena/details/{phenomenon_type}")
async def get_phenomenon_details(
    phenomenon_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed insights about a specific phenomenon type.

    Returns:
    - Shot characteristics when this phenomenon occurs
    - Co-occurring phenomena (other phenomena discussed alongside)
    - Related plasma parameters typically measured
    """
    # URL decode the phenomenon type (handle spaces as %20 or +)
    from urllib.parse import unquote
    phenomenon_type = unquote(phenomenon_type)

    # Get all occurrences of this phenomenon
    phenomena = db.query(NSTXPhenomenon).filter(
        NSTXPhenomenon.phenomenon_type == phenomenon_type
    ).all()

    if not phenomena:
        raise HTTPException(status_code=404, detail=f"Phenomenon not found: {phenomenon_type}")

    # Get basic info
    first = phenomena[0]
    occurrence_count = len(phenomena)
    paper_ids = set(p.paper_id for p in phenomena)
    shot_ids = set(p.shot_id for p in phenomena if p.shot_id)

    # 1. Shot characteristics when this phenomenon occurs
    shot_characteristics = []
    shot_roles = {}
    if shot_ids:
        shots = db.query(NSTXShot).filter(NSTXShot.id.in_(shot_ids)).all()
        for shot in shots:
            role = shot.role or 'unspecified'
            shot_roles[role] = shot_roles.get(role, 0) + 1
            if shot.context:
                shot_characteristics.append({
                    "shot_number": shot.shot_number,
                    "role": shot.role,
                    "context": shot.context[:200] + "..." if len(shot.context) > 200 else shot.context
                })

    # 2. Co-occurring phenomena (other phenomena in the same papers)
    co_occurring = {}
    for paper_id in paper_ids:
        other_phenomena = db.query(NSTXPhenomenon).filter(
            NSTXPhenomenon.paper_id == paper_id,
            NSTXPhenomenon.phenomenon_type != phenomenon_type
        ).all()
        for other in other_phenomena:
            key = other.phenomenon_type
            if key not in co_occurring:
                co_occurring[key] = {"count": 0, "category": other.phenomenon_category}
            co_occurring[key]["count"] += 1

    # Sort co-occurring by count and take top 10
    co_occurring_list = [
        {"type": k, "count": v["count"], "category": v["category"]}
        for k, v in sorted(co_occurring.items(), key=lambda x: x[1]["count"], reverse=True)[:10]
    ]

    # 3. Related plasma parameters typically measured (excluding outliers)
    related_parameters = {}
    for paper_id in paper_ids:
        params = db.query(NSTXParameter).filter(
            NSTXParameter.paper_id == paper_id,
            or_(NSTXParameter.is_outlier == False, NSTXParameter.is_outlier.is_(None))
        ).all()
        for param in params:
            key = param.parameter_name
            if key not in related_parameters:
                related_parameters[key] = {
                    "count": 0,
                    "category": param.parameter_category,
                    "values": [],
                    "unit": param.unit
                }
            related_parameters[key]["count"] += 1
            if param.value is not None:
                related_parameters[key]["values"].append(param.value)

    # Calculate statistics for each parameter and take top 10
    related_parameters_list = []
    for name, data in sorted(related_parameters.items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
        values = data["values"]
        entry = {
            "name": name,
            "count": data["count"],
            "category": data["category"],
            "unit": data["unit"]
        }
        if values:
            entry["min_value"] = min(values)
            entry["max_value"] = max(values)
            entry["avg_value"] = sum(values) / len(values)
        related_parameters_list.append(entry)

    return {
        "phenomenon_type": phenomenon_type,
        "category": first.phenomenon_category,
        "occurrence_count": occurrence_count,
        "paper_count": len(paper_ids),
        "shot_count": len(shot_ids),
        "shot_roles": shot_roles,
        "shot_characteristics": shot_characteristics[:5],  # Limit to 5 examples
        "co_occurring_phenomena": co_occurring_list,
        "related_parameters": related_parameters_list
    }


# === Processing Endpoints ===

@router.get("/processing/status", response_model=ProcessingStatus)
async def get_processing_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current processing pipeline status"""
    total = db.query(func.count(NSTXPaper.id)).scalar()
    pending = db.query(func.count(NSTXPaper.id)).filter(
        NSTXPaper.status == NSTXProcessingStatus.PENDING.value
    ).scalar()
    processing = db.query(func.count(NSTXPaper.id)).filter(
        NSTXPaper.status.in_([
            NSTXProcessingStatus.DOWNLOADING.value,
            NSTXProcessingStatus.EXTRACTING_TEXT.value,
            NSTXProcessingStatus.EXTRACTING_DATA.value,
            NSTXProcessingStatus.GENERATING_EMBEDDINGS.value
        ])
    ).scalar()
    completed = db.query(func.count(NSTXPaper.id)).filter(
        NSTXPaper.status == NSTXProcessingStatus.COMPLETED.value
    ).scalar()
    error = db.query(func.count(NSTXPaper.id)).filter(
        NSTXPaper.status == NSTXProcessingStatus.ERROR.value
    ).scalar()

    # Get active task if any
    active_task = db.query(NSTXProcessingTask).filter(
        NSTXProcessingTask.status == 'running'
    ).first()

    task_info = None
    if active_task:
        task_info = {
            "id": active_task.id,
            "type": active_task.task_type,
            "total_items": active_task.total_items,
            "processed_items": active_task.processed_items,
            "message": active_task.message,
            "started_at": active_task.started_at.isoformat() if active_task.started_at else None
        }

    return ProcessingStatus(
        total_papers=total,
        pending=pending,
        processing=processing,
        completed=completed,
        error=error,
        active_task=task_info
    )


@router.post("/processing/sync")
async def sync_with_drive(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Sync papers from Google Drive.
    Identifies new papers and queues them for processing.
    """
    # Check if there's already a sync task running
    active = db.query(NSTXProcessingTask).filter(
        NSTXProcessingTask.task_type == 'sync',
        NSTXProcessingTask.status == 'running'
    ).first()

    if active:
        raise HTTPException(status_code=409, detail="Sync already in progress")

    # Create a new task
    task = NSTXProcessingTask(
        task_type='sync',
        status='pending',
        message='Queued for sync with Google Drive'
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Add background task to perform sync
    background_tasks.add_task(perform_drive_sync, task.id)

    return {
        "message": "Sync task queued",
        "task_id": task.id
    }


@router.post("/processing/extract")
async def start_extraction(
    paper_ids: Optional[List[int]] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start extraction for papers.
    If paper_ids is not provided, processes all pending papers.
    """
    # Check if there's already an extraction running
    active = db.query(NSTXProcessingTask).filter(
        NSTXProcessingTask.task_type.in_(['extract_text', 'extract_data']),
        NSTXProcessingTask.status == 'running'
    ).first()

    if active:
        raise HTTPException(status_code=409, detail="Extraction already in progress")

    # Get papers to process
    query = db.query(NSTXPaper)
    if paper_ids:
        query = query.filter(NSTXPaper.id.in_(paper_ids))
    else:
        query = query.filter(NSTXPaper.status == NSTXProcessingStatus.PENDING.value)

    papers = query.all()

    if not papers:
        return {"message": "No papers to process", "count": 0}

    # Create a new task
    task = NSTXProcessingTask(
        task_type='extract_data',
        status='pending',
        total_items=len(papers),
        message=f'Queued {len(papers)} papers for extraction'
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Add background task to perform extraction
    background_tasks.add_task(perform_extraction, task.id, [p.id for p in papers])

    return {
        "message": f"Extraction task queued for {len(papers)} papers",
        "task_id": task.id,
        "paper_count": len(papers)
    }


# === Search Endpoints ===

@router.post("/search", response_model=List[SearchResult])
async def search_papers(
    query: SearchQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Semantic search across paper content using ChromaDB.

    - **query**: Search query text
    - **limit**: Maximum results (default 10, max 100)
    - **include_content**: Include full chunk content in results
    """
    from app.services.nstxview.vector_store import get_vector_store, is_available

    # Try ChromaDB first
    if is_available():
        try:
            vector_store = get_vector_store()

            # Perform semantic search
            search_results = vector_store.search(
                query=query.query,
                n_results=query.limit
            )

            results = []
            for doc_id, content, metadata, distance in zip(
                search_results["ids"],
                search_results["documents"],
                search_results["metadatas"],
                search_results["distances"]
            ):
                paper_id = metadata.get("paper_id")
                paper = db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()

                chunk_content = content
                if not query.include_content and len(content) > 500:
                    chunk_content = content[:500] + "..."

                results.append(SearchResult(
                    paper_id=paper_id,
                    paper_title=paper.title if paper else "Unknown",
                    chunk_content=chunk_content,
                    section=metadata.get("section"),
                    relevance_score=1.0 - distance  # Convert distance to similarity score
                ))

            return results

        except Exception as e:
            logger.error(f"ChromaDB search failed, falling back to SQL: {e}")

    # Fallback to simple text search if ChromaDB unavailable
    search_term = f"%{query.query}%"
    chunks = db.query(NSTXPaperChunk).join(NSTXPaper).filter(
        NSTXPaperChunk.content.ilike(search_term)
    ).limit(query.limit).all()

    results = []
    for chunk in chunks:
        chunk_content = chunk.content
        if not query.include_content and len(chunk.content) > 500:
            chunk_content = chunk.content[:500] + "..."

        results.append(SearchResult(
            paper_id=chunk.paper_id,
            paper_title=chunk.paper.title,
            chunk_content=chunk_content,
            section=chunk.section,
            relevance_score=0.5  # Lower score for SQL fallback
        ))

    return results


# === Chat Endpoint ===

class ChatRequest(BaseModel):
    """Chat request with user message"""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    """Chat response"""
    response: str
    tool_calls: List[dict] = []
    error: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat with the NSTXView AI assistant.

    Send a natural language question about NSTX/NSTX-U plasma physics research
    and get an AI-powered response based on the database.

    Example questions:
    - "What papers discuss H-mode transitions?"
    - "What are the typical ion temperatures in NSTX experiments?"
    - "Find papers about lithium wall conditioning"
    - "Give a detailed account for what happened in shot 107352, using citations."
    """
    import logging
    import traceback

    logger = logging.getLogger(__name__)
    logger.info(f"Chat request received: {request.message[:100]}...")

    try:
        from app.services.nstxview.chat_service import NSTXViewChatService
        from app.config import ANTHROPIC_API_KEY

        # Check if API key is configured
        if not ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY not configured")
            return ChatResponse(
                response="The AI chat service is not configured. Please contact the administrator.",
                tool_calls=[],
                error="ANTHROPIC_API_KEY not configured"
            )

        logger.info("Initializing chat service...")
        chat_service = NSTXViewChatService(db=db)

        logger.info("Calling chat service...")
        result = chat_service.chat(
            user_message=request.message,
            conversation_history=request.conversation_history
        )

        logger.info(f"Chat response received, tool_calls: {len(result.get('tool_calls', []))}")
        return ChatResponse(
            response=result.get("response", ""),
            tool_calls=result.get("tool_calls", []),
            error=result.get("error")
        )

    except ValueError as e:
        logger.error(f"Configuration error in chat: {e}")
        logger.error(traceback.format_exc())
        return ChatResponse(
            response="The AI chat service is not properly configured. Please contact the administrator.",
            tool_calls=[],
            error=str(e)
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        logger.error(traceback.format_exc())
        return ChatResponse(
            response=f"I encountered an error processing your request: {str(e)}",
            tool_calls=[],
            error=str(e)
        )


# === System Status Endpoint ===

class ComponentStatus(BaseModel):
    """Status of a single system component"""
    name: str
    enabled: bool
    message: str


class SystemStatusResponse(BaseModel):
    """System status for all NSTXView components"""
    components: List[ComponentStatus]
    all_operational: bool


@router.get("/system-status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get the operational status of NSTXView system components.

    Returns status of:
    - RAG Embeddings (sentence-transformers)
    - Vector Store (ChromaDB)
    - Chat Service (Anthropic API)
    """
    components = []

    # Check RAG/Embedding service
    try:
        from app.services.nstxview.embedding_service import is_available as embeddings_available
        if embeddings_available():
            components.append(ComponentStatus(
                name="RAG Embeddings",
                enabled=True,
                message="Semantic search available"
            ))
        else:
            components.append(ComponentStatus(
                name="RAG Embeddings",
                enabled=False,
                message="sentence-transformers not installed"
            ))
    except Exception as e:
        components.append(ComponentStatus(
            name="RAG Embeddings",
            enabled=False,
            message=f"Error: {str(e)}"
        ))

    # Check Vector Store
    try:
        from app.services.nstxview.vector_store import is_available as vector_store_available
        if vector_store_available():
            components.append(ComponentStatus(
                name="Vector Store",
                enabled=True,
                message="ChromaDB operational"
            ))
        else:
            components.append(ComponentStatus(
                name="Vector Store",
                enabled=False,
                message="ChromaDB not installed"
            ))
    except Exception as e:
        components.append(ComponentStatus(
            name="Vector Store",
            enabled=False,
            message=f"Error: {str(e)}"
        ))

    # Check Anthropic API key for chat
    from app.config import ANTHROPIC_API_KEY
    if ANTHROPIC_API_KEY:
        components.append(ComponentStatus(
            name="Chat Service",
            enabled=True,
            message="AI chat operational"
        ))
    else:
        components.append(ComponentStatus(
            name="Chat Service",
            enabled=False,
            message="Anthropic API key not configured"
        ))

    all_operational = all(c.enabled for c in components)

    return SystemStatusResponse(
        components=components,
        all_operational=all_operational
    )


# === Dashboard/Stats Endpoints ===

@router.get("/stats")
async def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall statistics for the NSTXView dashboard"""
    total_papers = db.query(func.count(NSTXPaper.id)).scalar()
    completed_papers = db.query(func.count(NSTXPaper.id)).filter(
        NSTXPaper.status == NSTXProcessingStatus.COMPLETED.value
    ).scalar()
    total_shots = db.query(func.count(NSTXShot.id)).scalar()
    unique_shots = db.query(func.count(func.distinct(NSTXShot.shot_number))).scalar()
    total_parameters = db.query(func.count(NSTXParameter.id)).scalar()
    total_phenomena = db.query(func.count(NSTXPhenomenon.id)).scalar()

    # Get top phenomena types
    top_phenomena = db.query(
        NSTXPhenomenon.phenomenon_type,
        func.count(NSTXPhenomenon.id).label('count')
    ).group_by(NSTXPhenomenon.phenomenon_type).order_by(
        func.count(NSTXPhenomenon.id).desc()
    ).limit(5).all()

    # Get top parameters
    top_parameters = db.query(
        NSTXParameter.parameter_name,
        func.count(NSTXParameter.id).label('count')
    ).group_by(NSTXParameter.parameter_name).order_by(
        func.count(NSTXParameter.id).desc()
    ).limit(5).all()

    # Get embedding statistics
    papers_with_embeddings = db.query(func.count(NSTXPaper.id)).filter(
        NSTXPaper.embedding_date.isnot(None)
    ).scalar()
    total_chunks = db.query(func.count(NSTXPaperChunk.id)).scalar()

    # Calculate average chunks per paper (for papers with chunks)
    avg_chunks = 0
    if papers_with_embeddings > 0:
        avg_chunks = total_chunks / papers_with_embeddings

    return {
        "papers": {
            "total": total_papers,
            "completed": completed_papers,
            "processing": total_papers - completed_papers,
            "with_embeddings": papers_with_embeddings
        },
        "shots": {
            "total": total_shots,
            "unique": unique_shots
        },
        "parameters": {
            "total": total_parameters,
            "top": [{"name": p.parameter_name, "count": p.count} for p in top_parameters]
        },
        "phenomena": {
            "total": total_phenomena,
            "top": [{"type": p.phenomenon_type, "count": p.count} for p in top_phenomena]
        },
        "embeddings": {
            "papers_with_embeddings": papers_with_embeddings,
            "total_chunks": total_chunks,
            "avg_chunks_per_paper": round(avg_chunks, 1)
        }
    }


# === Conversation Memory Endpoints ===

class ConversationMessageInput(BaseModel):
    """Input schema for a single message when saving a conversation"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class SaveConversationRequest(BaseModel):
    """Request to save current frontend conversation to database"""
    messages: List[ConversationMessageInput] = Field(..., min_items=2)
    title: Optional[str] = Field(None, max_length=255)


class ConversationSummaryResponse(BaseModel):
    """Summary of a conversation for list views"""
    id: int
    title: str
    summary: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationMessageResponse(BaseModel):
    """Single message in a conversation response"""
    role: str
    content: str
    sequence: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    """Full conversation with all messages"""
    id: int
    title: str
    summary: Optional[str]
    messages: List[ConversationMessageResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationUsageResponse(BaseModel):
    """Usage statistics for conversations"""
    saved_count: int
    max_allowed: int


class UpdateConversationRequest(BaseModel):
    """Request to update conversation title"""
    title: str = Field(..., min_length=1, max_length=255)


@router.get("/conversations", response_model=List[ConversationSummaryResponse])
async def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all saved conversations for the current user.
    Returns conversations ordered by most recently updated.
    """
    conversations = db.query(NSTXConversation).filter(
        NSTXConversation.user_id == current_user.id
    ).order_by(NSTXConversation.updated_at.desc()).all()

    results = []
    for conv in conversations:
        message_count = db.query(func.count(NSTXConversationMessage.id)).filter(
            NSTXConversationMessage.conversation_id == conv.id
        ).scalar()

        results.append(ConversationSummaryResponse(
            id=conv.id,
            title=conv.title,
            summary=conv.summary,
            message_count=message_count,
            created_at=conv.created_at,
            updated_at=conv.updated_at
        ))

    return results


@router.get("/conversations/usage", response_model=ConversationUsageResponse)
async def get_conversation_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get conversation usage statistics for the current user.
    Shows how many conversations they've saved vs the maximum allowed.
    """
    saved_count = db.query(func.count(NSTXConversation.id)).filter(
        NSTXConversation.user_id == current_user.id
    ).scalar()

    return ConversationUsageResponse(
        saved_count=saved_count,
        max_allowed=MAX_SAVED_CONVERSATIONS_PER_USER
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific conversation with all its messages.
    """
    conversation = db.query(NSTXConversation).filter(
        NSTXConversation.id == conversation_id,
        NSTXConversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(NSTXConversationMessage).filter(
        NSTXConversationMessage.conversation_id == conversation_id
    ).order_by(NSTXConversationMessage.sequence).all()

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        messages=[
            ConversationMessageResponse(
                role=msg.role,
                content=msg.content,
                sequence=msg.sequence,
                created_at=msg.created_at
            )
            for msg in messages
        ],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.post("/conversations", response_model=ConversationSummaryResponse)
async def save_conversation(
    request: SaveConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Save a new conversation from frontend state.

    - Generates title automatically if not provided
    - Generates summary using Claude
    - Enforces limits (20 conversations per user, 100 messages per conversation)
    """
    import logging
    logger = logging.getLogger(__name__)

    # Check conversation limit
    current_count = db.query(func.count(NSTXConversation.id)).filter(
        NSTXConversation.user_id == current_user.id
    ).scalar()

    if current_count >= MAX_SAVED_CONVERSATIONS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"You have reached the maximum of {MAX_SAVED_CONVERSATIONS_PER_USER} saved conversations. Please delete some to save new ones."
        )

    # Check message limit
    if len(request.messages) > MAX_MESSAGES_PER_CONVERSATION:
        raise HTTPException(
            status_code=400,
            detail=f"Conversation exceeds the maximum of {MAX_MESSAGES_PER_CONVERSATION} messages."
        )

    # Generate title if not provided
    title = request.title
    summary = None

    try:
        from app.services.nstxview.chat_service import NSTXViewChatService
        from app.config import ANTHROPIC_API_KEY

        if ANTHROPIC_API_KEY:
            chat_service = NSTXViewChatService(db=db)

            # Generate title from first exchange if not provided
            if not title and len(request.messages) >= 2:
                first_user_msg = next((m.content for m in request.messages if m.role == "user"), "")
                title = chat_service.generate_conversation_title(first_user_msg)

            # Generate summary
            messages_for_summary = [{"role": m.role, "content": m.content} for m in request.messages]
            summary = chat_service.generate_conversation_summary(messages_for_summary)

    except Exception as e:
        logger.warning(f"Failed to generate title/summary: {e}")

    # Fallback title if generation failed
    if not title:
        title = f"Conversation from {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # Create conversation
    conversation = NSTXConversation(
        user_id=current_user.id,
        title=title,
        summary=summary
    )
    db.add(conversation)
    db.flush()  # Get the ID

    # Create messages
    for i, msg in enumerate(request.messages):
        db_message = NSTXConversationMessage(
            conversation_id=conversation.id,
            role=msg.role,
            content=msg.content,
            sequence=i
        )
        db.add(db_message)

    db.commit()
    db.refresh(conversation)

    return ConversationSummaryResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        message_count=len(request.messages),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.put("/conversations/{conversation_id}", response_model=ConversationSummaryResponse)
async def update_conversation(
    conversation_id: int,
    request: UpdateConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a conversation's title.
    """
    conversation = db.query(NSTXConversation).filter(
        NSTXConversation.id == conversation_id,
        NSTXConversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.title = request.title
    db.commit()
    db.refresh(conversation)

    message_count = db.query(func.count(NSTXConversationMessage.id)).filter(
        NSTXConversationMessage.conversation_id == conversation.id
    ).scalar()

    return ConversationSummaryResponse(
        id=conversation.id,
        title=conversation.title,
        summary=conversation.summary,
        message_count=message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a saved conversation.
    """
    conversation = db.query(NSTXConversation).filter(
        NSTXConversation.id == conversation_id,
        NSTXConversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted successfully"}
