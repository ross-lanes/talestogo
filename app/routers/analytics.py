"""
Analytics API endpoints.

All analytics calculations are centralized through AnalyticsCache service
to avoid redundant calculations across different endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from .. import analytics, crud, models
from ..auth import get_current_user
from ..database import get_db
from ..services.analytics_cache import AnalyticsCache
from ..services.metrics import calculate_share_of_voice, calculate_competitor_threats


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
    Uses centralized AnalyticsCache to avoid redundant calculations.
    """
    cache = AnalyticsCache(db, user_id=current_user.id, brand_id=brand_id)
    return cache.get_dashboard_data()


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
    Uses centralized AnalyticsCache to avoid redundant calculations.
    """
    cache = AnalyticsCache(db, user_id=current_user.id, brand_id=brand_id)
    return cache.get_sentiment_data()


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
    Uses centralized AnalyticsCache to avoid redundant calculations.
    """
    cache = AnalyticsCache(db, user_id=current_user.id, brand_id=brand_id)
    return cache.get_positioning_data()


@router.get("/share-of-voice", response_model=List[Dict[str, Any]])
def get_share_of_voice_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get share of voice comparison between brand and competitors.
    Uses centralized AnalyticsCache to avoid redundant calculations.
    """
    cache = AnalyticsCache(db, user_id=current_user.id, brand_id=brand_id)
    return cache.get_share_of_voice_data()


@router.get("/recommendations", response_model=Dict[str, Any])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get the latest AI-generated recommendations from the most recent report.
    """
    # Query for the most recent report for the user/brand
    query = db.query(models.Report).filter(models.Report.user_id == current_user.id)
    if brand_id:
        query = query.filter(models.Report.brand_id == brand_id)

    latest_report = query.order_by(models.Report.created_at.desc()).first()

    if not latest_report:
        return {
            "has_recommendations": False,
            "message": "No analysis reports found. Run a Full Analysis to generate recommendations.",
            "recommendations": None,
            "report_date": None
        }

    # Extract recommendations section from the report content
    report_content = latest_report.report_content
    recommendations_text = ""

    # Try to find recommendations in different formats (newer reports use ### 6., older use ## 4.)
    if "## 4. Strategic Recommendations" in report_content:
        # Split by ## sections to find the right one
        sections = report_content.split("\n## ")
        for section in sections:
            if section.startswith("4. Strategic Recommendations"):
                # Get everything until the next ## section or end
                recommendations_text = section
                # If there's another section after, cut it off
                next_section_pos = recommendations_text.find("\n## ", 3)
                if next_section_pos > 0:
                    recommendations_text = recommendations_text[:next_section_pos]

                # Remove the numbered header entirely since the page already has "Strategic Recommendations" as its title
                recommendations_text = recommendations_text.replace("4. Strategic Recommendations\n\n", "", 1)
                recommendations_text = recommendations_text.replace("4. Strategic Recommendations\n", "", 1)
                recommendations_text = recommendations_text.replace("4. Strategic Recommendations", "", 1)

                # Remove the trailing horizontal rule (---) if present at the end
                recommendations_text = recommendations_text.rstrip()
                if recommendations_text.endswith("---"):
                    recommendations_text = recommendations_text[:-3].rstrip()

                break
    elif "### 6. Recommendations" in report_content:
        # Newer format: ### 6. Recommendations
        sections = report_content.split("\n### ")
        for section in sections:
            if section.startswith("6. Recommendations"):
                # Get everything until the next ## or ### section or end
                recommendations_text = section
                # Look for next section (could be ## or ###)
                next_section_pos = min(
                    [pos for pos in [
                        recommendations_text.find("\n## ", 3),
                        recommendations_text.find("\n### ", 3)
                    ] if pos > 0] or [len(recommendations_text)]
                )
                if next_section_pos < len(recommendations_text):
                    recommendations_text = recommendations_text[:next_section_pos]

                # Remove the numbered header
                recommendations_text = recommendations_text.replace("6. Recommendations\n\n", "", 1)
                recommendations_text = recommendations_text.replace("6. Recommendations\n", "", 1)
                recommendations_text = recommendations_text.replace("6. Recommendations", "", 1)

                # Remove the trailing horizontal rule (---) if present at the end
                recommendations_text = recommendations_text.rstrip()
                if recommendations_text.endswith("---"):
                    recommendations_text = recommendations_text[:-3].rstrip()

                break

    return {
        "has_recommendations": bool(recommendations_text),
        "recommendations": recommendations_text if recommendations_text else "No recommendations section found in the report.",
        "report_date": latest_report.created_at.isoformat() if latest_report.created_at else None,
        "report_id": latest_report.id,
        "total_responses": latest_report.total_responses
    }


@router.get("/competitor-threats", response_model=List[Dict[str, Any]])
def get_competitor_threats_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get competitor threat analysis with threat scores.

    Returns a list of competitors sorted by threat level (highest first).
    Each competitor includes:
    - mention_count: Number of times mentioned
    - share_of_voice: Percentage of total mentions
    - negative_overlap: Times competitor mentioned with negative brand sentiment
    - positive_competitor: Times competitor mentioned with positive sentiment
    - threat_score: Calculated threat score
    - threat_level: High/Medium/Low threat classification
    """
    # Fetch all responses for the user/brand
    query = db.query(models.Response).filter(models.Response.user_id == current_user.id)
    if brand_id:
        query = query.filter(models.Response.brand_id == brand_id)

    responses = query.all()

    # Fetch all queries for the user/brand (needed for filtering)
    queries_query = db.query(models.Query).filter(models.Query.user_id == current_user.id)
    if brand_id:
        queries_query = queries_query.filter(models.Query.brand_id == brand_id)

    queries = queries_query.all()

    # Fetch competitors list
    competitors_query = db.query(models.Competitor).filter(models.Competitor.user_id == current_user.id)
    if brand_id:
        competitors_query = competitors_query.filter(models.Competitor.brand_id == brand_id)

    competitors = competitors_query.all()

    # Get brand name
    brand_query = db.query(models.BrandInfo).filter(models.BrandInfo.user_id == current_user.id)
    if brand_id:
        brand_query = brand_query.filter(models.BrandInfo.id == brand_id)

    brand = brand_query.first()
    brand_name = brand.brand_name if brand else "Your Brand"

    # Use metrics module to calculate share of voice
    sov_data = calculate_share_of_voice(responses, queries, competitors, brand_name)

    # Use metrics module to calculate competitor threats
    competitor_threats = calculate_competitor_threats(
        sov_data['competitor_sov'],
        responses,
        brand_name
    )

    return competitor_threats
