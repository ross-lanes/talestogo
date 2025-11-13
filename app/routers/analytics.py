"""
Analytics API endpoints.

All analytics calculations are centralized through AnalyticsCache service
to avoid redundant calculations across different endpoints.

Redis caching is used to significantly reduce database load and improve
response times for frequently accessed analytics data.

Date range filtering is available to limit data lookback window for improved
performance with large datasets. Default lookback is 180 days (configurable).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import case
from typing import Dict, List, Any, Optional
from datetime import datetime
from .. import analytics, models, config
from ..auth import get_current_user
from ..database import get_db
from ..services.analytics_cache import AnalyticsCache
from ..services.metrics import calculate_share_of_voice, calculate_competitor_threats
from ..services.redis_cache import get_redis_cache
from ..utils.brand_access import get_active_brand_id, get_data_owner_user_id

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


@router.get("/dashboard", response_model=Dict[str, Any])
def get_dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id),
    batch_id: Optional[int] = None,
    date_from: Optional[datetime] = Query(None, description="Start date for filtering (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="End date for filtering (ISO format)"),
    days: Optional[int] = Query(None, description="Lookback period in days (overrides date_from)")
):
    """
    Get key metrics for the dashboard for the active brand.

    Performance optimizations:
    - Uses centralized AnalyticsCache to avoid redundant calculations
    - Redis caching with 15-minute TTL for improved performance
    - Default 180-day lookback window (configurable via ANALYTICS_DEFAULT_LOOKBACK_DAYS)

    Filtering options:
    - batch_id: Filter by specific collection batch (takes precedence over date filtering)
    - days: Number of days to look back (e.g., days=30 for last 30 days)
    - date_from/date_to: Custom date range (ISO format: 2024-01-01T00:00:00)

    Note: When batch_id is specified, date filtering is ignored as batches represent
    a specific point-in-time collection.
    """
    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Determine date range
    if days is not None:
        # Use days parameter as lookback window
        default_days = days
    else:
        # Use configured default
        default_days = config.ANALYTICS_DEFAULT_LOOKBACK_DAYS

    # Try Redis cache first (cache key includes date range)
    redis_cache = get_redis_cache()
    cached_data = redis_cache.get_dashboard_data(owner_user_id, brand_id, batch_id)
    if cached_data is not None:
        return cached_data

    # Cache miss - calculate from database
    cache = AnalyticsCache(
        db,
        user_id=owner_user_id,
        brand_id=brand_id,
        batch_id=batch_id,
        date_from=date_from,
        date_to=date_to,
        default_days=default_days
    )
    data = cache.get_dashboard_data()

    # Store in Redis for next time
    redis_cache.set_dashboard_data(
        owner_user_id,
        brand_id,
        data,
        batch_id,
        ttl_seconds=config.REDIS_CACHE_TTL_DASHBOARD
    )

    return data


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
    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)
    return analytics.get_mention_trend(db, user_id=owner_user_id, days=days, brand_id=brand_id)


@router.get("/sentiment/breakdown", response_model=Dict[str, Any])
def get_sentiment_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id),
    batch_id: Optional[int] = None
):
    """
    Get sentiment distribution for brand mentions.
    Uses centralized AnalyticsCache to avoid redundant calculations.
    Redis caching with 15-minute TTL for improved performance.
    Optionally filter by batch_id for specific collection batches.
    """
    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Try Redis cache first
    redis_cache = get_redis_cache()
    cached_data = redis_cache.get_sentiment_breakdown(owner_user_id, brand_id, batch_id)
    if cached_data is not None:
        return cached_data

    # Cache miss - calculate from database
    cache = AnalyticsCache(db, user_id=owner_user_id, brand_id=brand_id, batch_id=batch_id)
    data = cache.get_sentiment_data()

    # Store in Redis for next time
    redis_cache.set_sentiment_breakdown(owner_user_id, brand_id, data, batch_id, ttl_seconds=900)

    return data


@router.get("/descriptors/insights", response_model=Dict[str, Any])
def get_descriptor_insights_endpoint(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get AI-generated insights about descriptor usage patterns.
    """
    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)
    return analytics.get_descriptor_insights(db, user_id=owner_user_id, brand_id=brand_id)


@router.get("/positioning/breakdown", response_model=Dict[str, Any])
def get_positioning_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id),
    batch_id: Optional[int] = None
):
    """
    Get brand positioning distribution across responses.
    Uses centralized AnalyticsCache to avoid redundant calculations.
    Redis caching with 15-minute TTL for improved performance.
    Optionally filter by batch_id for specific collection batches.
    """
    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Try Redis cache first
    redis_cache = get_redis_cache()
    cached_data = redis_cache.get_positioning_breakdown(owner_user_id, brand_id, batch_id)
    if cached_data is not None:
        return cached_data

    # Cache miss - calculate from database
    cache = AnalyticsCache(db, user_id=owner_user_id, brand_id=brand_id, batch_id=batch_id)
    data = cache.get_positioning_data()

    # Store in Redis for next time
    redis_cache.set_positioning_breakdown(owner_user_id, brand_id, data, batch_id, ttl_seconds=900)

    return data


@router.get("/share-of-voice", response_model=List[Dict[str, Any]])
def get_share_of_voice_analysis(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id),
    batch_id: Optional[int] = None
):
    """
    Get share of voice comparison between brand and competitors.
    Uses centralized AnalyticsCache to avoid redundant calculations.
    Redis caching with 15-minute TTL for improved performance.
    Optionally filter by batch_id for specific collection batches.
    """
    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Try Redis cache first
    redis_cache = get_redis_cache()
    cached_data = redis_cache.get_share_of_voice(owner_user_id, brand_id, batch_id)
    if cached_data is not None:
        return cached_data

    # Cache miss - calculate from database
    cache = AnalyticsCache(db, user_id=owner_user_id, brand_id=brand_id, batch_id=batch_id)
    data = cache.get_share_of_voice_data()

    # Store in Redis for next time
    redis_cache.set_share_of_voice(owner_user_id, brand_id, data, batch_id, ttl_seconds=900)

    return data


@router.get("/recommendations", response_model=Dict[str, Any])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get the latest AI-generated recommendations from the most recent report.
    """
    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)
    # Query for the most recent report for the user/brand
    query = db.query(models.Report).filter(models.Report.user_id == owner_user_id)
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

    # Try to find recommendations in different formats (newer reports use ### 7., older use ### 6., even older use ## 4.)
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
    elif "### 7. Recommendations" in report_content:
        # Newest format: ### 7. Recommendations (with LLM breakdown section)
        sections = report_content.split("\n### ")
        for section in sections:
            if section.startswith("7. Recommendations"):
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
                recommendations_text = recommendations_text.replace("7. Recommendations\n\n", "", 1)
                recommendations_text = recommendations_text.replace("7. Recommendations\n", "", 1)
                recommendations_text = recommendations_text.replace("7. Recommendations", "", 1)

                # Remove the trailing horizontal rule (---) if present at the end
                recommendations_text = recommendations_text.rstrip()
                if recommendations_text.endswith("---"):
                    recommendations_text = recommendations_text[:-3].rstrip()

                break
    elif "### 6. Recommendations" in report_content:
        # Old format: ### 6. Recommendations (without LLM breakdown section)
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
    brand_id: Optional[int] = Depends(get_active_brand_id),
    batch_id: Optional[int] = None
):
    """
    Get competitor threat analysis with threat scores.
    Optionally filter by batch_id for specific collection batches.

    Returns a list of competitors sorted by threat level (highest first).
    Each competitor includes:
    - mention_count: Number of times mentioned
    - share_of_voice: Percentage of total mentions
    - negative_overlap: Times competitor mentioned with negative brand sentiment
    - positive_competitor: Times competitor mentioned with positive sentiment
    - threat_score: Calculated threat score
    - threat_level: High/Medium/Low threat classification
    """
    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)
    # Fetch all responses for the user/brand/batch
    query = db.query(models.Response).filter(models.Response.user_id == owner_user_id)
    if brand_id:
        query = query.filter(models.Response.brand_id == brand_id)
    if batch_id:
        query = query.filter(models.Response.batch_id == batch_id)

    responses = query.all()

    # Fetch all queries for the user/brand (needed for filtering)
    queries_query = db.query(models.Query).filter(models.Query.user_id == owner_user_id)
    if brand_id:
        queries_query = queries_query.filter(models.Query.brand_id == brand_id)

    queries = queries_query.all()

    # Fetch competitors list
    competitors_query = db.query(models.Competitor).filter(models.Competitor.user_id == owner_user_id)
    if brand_id:
        competitors_query = competitors_query.filter(models.Competitor.brand_id == brand_id)

    competitors = competitors_query.all()

    # Get brand name
    brand_query = db.query(models.BrandInfo).filter(models.BrandInfo.user_id == owner_user_id)
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


@router.get("/trends/brand-mentions", response_model=List[Dict[str, Any]])
def get_brand_mentions_over_time(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get brand mention percentage over time, grouped by collection batches.
    Uses cached batch analytics for fast performance.
    """
    from ..services.cached_metrics import get_brand_mentions_trend_cached

    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)
    return get_brand_mentions_trend_cached(db, owner_user_id, brand_id)


@router.get("/trends/positioning", response_model=List[Dict[str, Any]])
def get_positioning_over_time(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get positioning distribution over time, grouped by collection batches.
    Uses cached batch analytics for fast performance.
    """
    from ..services.cached_metrics import get_positioning_trend_cached

    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)
    return get_positioning_trend_cached(db, owner_user_id, brand_id)


@router.get("/trends/share-of-voice", response_model=List[Dict[str, Any]])
def get_share_of_voice_over_time(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get share of voice over time for brand and top competitors, grouped by collection batches.
    Uses cached batch analytics for fast performance.
    """
    from ..services.cached_metrics import get_share_of_voice_trend_cached

    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)
    # Get brand name
    brand_query = db.query(models.BrandInfo).filter(models.BrandInfo.user_id == owner_user_id)
    if brand_id:
        brand_query = brand_query.filter(models.BrandInfo.id == brand_id)
    brand = brand_query.first()
    brand_name = brand.brand_name if brand else "Your Brand"

    return get_share_of_voice_trend_cached(db, owner_user_id, brand_id, brand_name)


@router.get("/trends/sentiment", response_model=List[Dict[str, Any]])
def get_sentiment_over_time(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get sentiment distribution over time, grouped by collection batches.
    Uses cached batch analytics for fast performance.
    """
    from ..services.cached_metrics import get_sentiment_trend_cached

    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)
    return get_sentiment_trend_cached(db, owner_user_id, brand_id)


@router.get("/brand-mentions-by-llm")
def get_brand_mentions_by_llm(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get brand mention rates broken down by LLM platform.
    Returns mention rate for each platform (ChatGPT, Claude, Gemini, Perplexity).
    """
    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Query responses grouped by platform
    from sqlalchemy import func, case

    platform_stats = db.query(
        models.Response.platform,
        func.count(models.Response.id).label('total'),
        func.sum(
            case(
                (models.Response.brand_mentioned == 'Yes', 1),
                else_=0
            )
        ).label('mentioned')
    ).filter(
        models.Response.user_id == owner_user_id,
        models.Response.brand_id == brand_id,
        models.Response.platform.isnot(None)
    ).group_by(
        models.Response.platform
    ).all()

    # Calculate mention rate for each platform
    results = []
    for platform, total, mentioned in platform_stats:
        mention_rate = (mentioned / total * 100) if total > 0 else 0
        results.append({
            'platform': platform,
            'total_responses': total,
            'mentions': mentioned,
            'mention_rate': round(mention_rate, 1)
        })

    return results


@router.get("/positioning-by-llm")
def get_positioning_by_llm(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get brand positioning breakdown by LLM platform.
    Returns positioning counts (Leader, Featured, Listed, Not Mentioned) for each platform.
    """
    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Query responses grouped by platform and position
    from sqlalchemy import func

    platform_positioning = db.query(
        models.Response.platform,
        models.Response.brand_position,
        func.count(models.Response.id).label('count')
    ).filter(
        models.Response.user_id == owner_user_id,
        models.Response.brand_id == brand_id,
        models.Response.platform.isnot(None),
        models.Response.brand_position.isnot(None)
    ).group_by(
        models.Response.platform,
        models.Response.brand_position
    ).all()

    # Organize data by platform
    platforms = {}
    for platform, position, count in platform_positioning:
        if platform not in platforms:
            platforms[platform] = {
                'platform': platform,
                'Leader': 0,
                'Featured': 0,
                'Listed': 0,
                'Not Mentioned': 0,
                'total': 0
            }

        # Map the position to our standard categories
        if position in ['Leader', 'Featured', 'Listed', 'Not Mentioned']:
            platforms[platform][position] = count
            platforms[platform]['total'] += count

    return list(platforms.values())


@router.get("/sentiment-by-llm")
def get_sentiment_by_llm(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get sentiment analysis breakdown by LLM platform.
    Returns sentiment distribution (Very Positive, Positive, Neutral, Negative, Very Negative, Mixed) for each platform.
    """
    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Query responses grouped by platform and sentiment
    from sqlalchemy import func

    platform_sentiment = db.query(
        models.Response.platform,
        models.Response.sentiment,
        func.count(models.Response.id).label('count')
    ).filter(
        models.Response.user_id == owner_user_id,
        models.Response.brand_id == brand_id,
        models.Response.platform.isnot(None),
        models.Response.sentiment.isnot(None),
        models.Response.brand_mentioned == 'Yes'  # Only analyze sentiment where brand is mentioned
    ).group_by(
        models.Response.platform,
        models.Response.sentiment
    ).all()

    # Organize data by platform
    platforms = {}
    for platform, sentiment, count in platform_sentiment:
        if platform not in platforms:
            platforms[platform] = {
                'platform': platform,
                'Very Positive': 0,
                'Positive': 0,
                'Neutral': 0,
                'Negative': 0,
                'Very Negative': 0,
                'Mixed': 0,
                'total': 0
            }

        # Map the sentiment to our standard categories
        if sentiment in ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative', 'Mixed']:
            platforms[platform][sentiment] = count
            platforms[platform]['total'] += count

    return list(platforms.values())


@router.get("/share-of-voice-by-llm")
def get_share_of_voice_by_llm(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get share of voice breakdown by LLM platform.
    Returns mention counts for brand and competitors by platform.
    """
    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Get brand name
    brand = db.query(models.BrandInfo).filter(
        models.BrandInfo.user_id == owner_user_id,
        models.BrandInfo.id == brand_id
    ).first()

    if not brand:
        return []

    brand_name = brand.brand_name

    # Get all responses grouped by platform
    from sqlalchemy import func, case

    # Count brand mentions by platform
    brand_mentions = db.query(
        models.Response.platform,
        func.count(models.Response.id).label('brand_mentions')
    ).filter(
        models.Response.user_id == owner_user_id,
        models.Response.brand_id == brand_id,
        models.Response.platform.isnot(None),
        models.Response.brand_mentioned == 'Yes'
    ).group_by(
        models.Response.platform
    ).all()

    # Count competitor mentions by platform
    competitor_mentions = db.query(
        models.Response.platform,
        func.count(models.Response.id).label('competitor_mentions')
    ).filter(
        models.Response.user_id == owner_user_id,
        models.Response.brand_id == brand_id,
        models.Response.platform.isnot(None),
        models.Response.competitors_mentioned.isnot(None),
        models.Response.competitors_mentioned != ''
    ).group_by(
        models.Response.platform
    ).all()

    # Combine the data
    platforms = {}

    # Add brand mentions
    for platform, count in brand_mentions:
        if platform not in platforms:
            platforms[platform] = {
                'platform': platform,
                'brand': 0,
                'competitors': 0
            }
        platforms[platform]['brand'] = count

    # Add competitor mentions
    for platform, count in competitor_mentions:
        if platform not in platforms:
            platforms[platform] = {
                'platform': platform,
                'brand': 0,
                'competitors': 0
            }
        platforms[platform]['competitors'] = count

    return list(platforms.values())


@router.get("/descriptors-by-llm")
def get_descriptors_by_llm(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get top descriptors breakdown by LLM platform.
    Returns the most common descriptors used by each platform.
    """
    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Get all descriptors by platform
    responses = db.query(
        models.Response.platform,
        models.Response.descriptors
    ).filter(
        models.Response.user_id == owner_user_id,
        models.Response.brand_id == brand_id,
        models.Response.platform.isnot(None),
        models.Response.descriptors.isnot(None),
        models.Response.descriptors != ''
    ).all()

    # Process descriptors by platform
    platform_descriptors = {}

    for platform, descriptors_str in responses:
        if platform not in platform_descriptors:
            platform_descriptors[platform] = {}

        # Split descriptors by comma and count
        if descriptors_str:
            descriptors = [d.strip() for d in descriptors_str.split(',') if d.strip()]
            for descriptor in descriptors:
                if descriptor not in platform_descriptors[platform]:
                    platform_descriptors[platform][descriptor] = 0
                platform_descriptors[platform][descriptor] += 1

    # Format results - get top 5 descriptors per platform
    results = []
    for platform, descriptors in platform_descriptors.items():
        # Sort by count and get top 5
        top_descriptors = sorted(descriptors.items(), key=lambda x: x[1], reverse=True)[:5]

        results.append({
            'platform': platform,
            'descriptors': [{'descriptor': d, 'count': c} for d, c in top_descriptors],
            'total_mentions': sum(descriptors.values())
        })

    return results


@router.get("/threats-by-llm")
def get_threats_by_llm(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Get competitor threat analysis breakdown by LLM platform.
    Returns top competitors mentioned by each platform.
    """
    if not brand_id:
        return []

    owner_user_id = get_data_owner_user_id(db, brand_id, current_user.id)

    # Get all responses with competitors by platform
    responses = db.query(
        models.Response.platform,
        models.Response.competitors_mentioned,
        models.Response.sentiment
    ).filter(
        models.Response.user_id == owner_user_id,
        models.Response.brand_id == brand_id,
        models.Response.platform.isnot(None),
        models.Response.competitors_mentioned.isnot(None),
        models.Response.competitors_mentioned != ''
    ).all()

    # Process competitors by platform
    platform_competitors = {}

    for platform, competitors_str, sentiment in responses:
        if platform not in platform_competitors:
            platform_competitors[platform] = {}

        # Split competitors by comma and count
        if competitors_str:
            competitors = [c.strip() for c in competitors_str.split(',') if c.strip()]
            for competitor in competitors:
                if competitor not in platform_competitors[platform]:
                    platform_competitors[platform][competitor] = {
                        'count': 0,
                        'negative_overlap': 0
                    }
                platform_competitors[platform][competitor]['count'] += 1

                # Track negative overlap
                if sentiment in ['Negative', 'Very Negative']:
                    platform_competitors[platform][competitor]['negative_overlap'] += 1

    # Format results - get top 5 competitors per platform
    results = []
    for platform, competitors in platform_competitors.items():
        # Sort by count and get top 5
        top_competitors = sorted(
            competitors.items(),
            key=lambda x: (x[1]['count'], x[1]['negative_overlap']),
            reverse=True
        )[:5]

        results.append({
            'platform': platform,
            'competitors': [
                {
                    'name': name,
                    'mentions': data['count'],
                    'negative_overlap': data['negative_overlap']
                }
                for name, data in top_competitors
            ],
            'total_competitor_mentions': sum(c['count'] for c in competitors.values())
        })

    return results
