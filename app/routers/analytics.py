"""
Analytics API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from .. import analytics, crud, models


# Dependency
def get_db():
    """Database session dependency."""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db)):
    """Get current user dependency - simplified for analytics."""
    from ..auth import get_current_user as auth_get_current_user
    from fastapi import Request
    # Import from auth module
    return auth_get_current_user

def get_active_brand_id(
    db: Session = Depends(get_db)
) -> Optional[int]:
    """
    Helper function to get the active brand_id for the current user.
    Returns None if no active brand exists (allows multi-brand view).
    """
    # For now, get the first active brand for the authenticated user
    # This should be replaced with actual user authentication
    active_brand = db.query(models.BrandInfo).filter(
        models.BrandInfo.is_active == True
    ).first()
    return active_brand.id if active_brand else None

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


@router.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get key metrics for the dashboard for the active brand.
    """
    return analytics.get_dashboard_metrics(db, brand_id=brand_id)


@router.get("/trends/mentions", response_model=List[Dict[str, Any]])
def get_mention_trends(
    days: int = 30,
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get mention rate trends over time for the active brand.
    Query parameter: days (default: 30)
    """
    return analytics.get_mention_trend(db, days, brand_id=brand_id)


@router.get("/sentiment/breakdown", response_model=Dict[str, Any])
def get_sentiment_analysis(
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get sentiment distribution for brand mentions.
    """
    return analytics.get_sentiment_breakdown(db, brand_id=brand_id)


@router.get("/positioning/breakdown", response_model=Dict[str, Any])
def get_positioning_analysis(
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get brand positioning distribution across responses.
    """
    return analytics.get_positioning_breakdown(db, brand_id=brand_id)


@router.get("/share-of-voice", response_model=List[Dict[str, Any]])
def get_share_of_voice_analysis(
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get share of voice comparison between brand and competitors.
    """
    return analytics.get_share_of_voice(db, brand_id=brand_id)
