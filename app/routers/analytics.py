"""
Analytics API endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from .. import analytics


# Dependency
def get_db():
    """Database session dependency."""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


@router.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_analytics(db: Session = Depends(get_db)):
    """
    Get key metrics for the dashboard.
    """
    return analytics.get_dashboard_metrics(db)


@router.get("/trends/mentions", response_model=List[Dict[str, Any]])
def get_mention_trends(days: int = 30, db: Session = Depends(get_db)):
    """
    Get mention rate trends over time.
    Query parameter: days (default: 30)
    """
    return analytics.get_mention_trend(db, days)


@router.get("/sentiment/breakdown", response_model=Dict[str, Any])
def get_sentiment_analysis(db: Session = Depends(get_db)):
    """
    Get sentiment distribution for PPPL mentions.
    """
    return analytics.get_sentiment_breakdown(db)


@router.get("/positioning/breakdown", response_model=Dict[str, Any])
def get_positioning_analysis(db: Session = Depends(get_db)):
    """
    Get PPPL positioning distribution across responses.
    """
    return analytics.get_positioning_breakdown(db)


@router.get("/share-of-voice", response_model=List[Dict[str, Any]])
def get_share_of_voice_analysis(db: Session = Depends(get_db)):
    """
    Get share of voice comparison between PPPL and competitors.
    """
    return analytics.get_share_of_voice(db)
