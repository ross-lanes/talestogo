"""
Analytics API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from .. import analytics, crud, models
from ..auth import get_current_user
from ..database import get_db


def get_active_brand_id(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Optional[int]:
    """
    Helper function to get the active brand_id for the current user.
    Returns None if no active brand exists (allows multi-brand view).
    """
    # Get the active brand for the CURRENT USER ONLY
    active_brand = crud.get_active_brand(db, user_id=current_user.id)
    return active_brand.id if active_brand else None

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


@router.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get key metrics for the dashboard for the active brand.
    """
    return analytics.get_dashboard_metrics(db, user_id=current_user.id, brand_id=brand_id)


@router.get("/trends/mentions", response_model=List[Dict[str, Any]])
def get_mention_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get mention rate trends over time for the active brand.
    Query parameter: days (default: 30)
    """
    return analytics.get_mention_trend(db, user_id=current_user.id, days=days, brand_id=brand_id)


@router.get("/sentiment/breakdown", response_model=Dict[str, Any])
def get_sentiment_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get sentiment distribution for brand mentions.
    """
    return analytics.get_sentiment_breakdown(db, user_id=current_user.id, brand_id=brand_id)


@router.get("/descriptors/insights", response_model=Dict[str, Any])
def get_descriptor_insights_endpoint(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get AI-generated insights about descriptor usage patterns.
    """
    return analytics.get_descriptor_insights(db, user_id=current_user.id, brand_id=brand_id)


@router.get("/positioning/breakdown", response_model=Dict[str, Any])
def get_positioning_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get brand positioning distribution across responses.
    """
    return analytics.get_positioning_breakdown(db, user_id=current_user.id, brand_id=brand_id)


@router.get("/share-of-voice", response_model=List[Dict[str, Any]])
def get_share_of_voice_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get share of voice comparison between brand and competitors.
    """
    return analytics.get_share_of_voice(db, user_id=current_user.id, brand_id=brand_id)
