"""
Analytics calculations for dashboard and reports.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from . import models
from typing import Dict, List, Any, Optional
import datetime


def get_dashboard_metrics(db: Session, brand_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate key metrics for the dashboard for a specific brand.
    Returns mention rate, sentiment, descriptor match, and share of voice.

    Args:
        db: Database session
        brand_id: Optional brand ID to filter by. If None, returns metrics for all brands.
    """
    # Base query for responses - filter by brand_id if provided
    def apply_brand_filter(query):
        if brand_id:
            return query.filter(models.Response.brand_id == brand_id)
        return query

    # Get total responses
    total_responses = apply_brand_filter(
        db.query(func.count(models.Response.id))
    ).scalar() or 0

    if total_responses == 0:
        return {
            "mention_rate": 0.0,
            "mention_count": 0,
            "total_responses": 0,
            "positive_sentiment": 0.0,
            "descriptor_match": 0.0,
            "share_of_voice": 0.0,
            "change_mention_rate": 0.0,
            "change_sentiment": 0.0,
            "change_descriptor": 0.0,
            "leading_position": "N/A"
        }

    # Calculate mention rate (Yes or Indirect mentions)
    pppl_mentions = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
        )
    ).scalar() or 0
    mention_rate = (pppl_mentions / total_responses) * 100

    # Calculate positive sentiment rate (Very Positive, Positive)
    positive_responses = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            and_(
                models.Response.brand_mentioned.in_(['Yes', 'Indirect']),
                models.Response.sentiment.in_(['Very Positive', 'Positive'])
            )
        )
    ).scalar() or 0
    positive_sentiment = (positive_responses / pppl_mentions * 100) if pppl_mentions > 0 else 0.0

    # Calculate descriptor match rate (responses with descriptors)
    descriptor_responses = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            and_(
                models.Response.brand_mentioned.in_(['Yes', 'Indirect']),
                models.Response.descriptors.isnot(None),
                models.Response.descriptors != ''
            )
        )
    ).scalar() or 0
    descriptor_match = (descriptor_responses / pppl_mentions * 100) if pppl_mentions > 0 else 0.0

    # Calculate leadership visibility (Leader + Top 3 positions)
    pppl_leader_count = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position.in_(['Leader', 'Top 3'])
        )
    ).scalar() or 0
    leadership_visibility = (pppl_leader_count / total_responses * 100) if total_responses > 0 else 0.0

    # Calculate true share of voice - need to get from share_of_voice function
    # For dashboard, we'll use a simplified version based on all brand mentions
    sov_data = get_share_of_voice(db, brand_id=brand_id)
    brand_sov = next((item for item in sov_data if item.get('is_brand')), None)
    share_of_voice = brand_sov.get('share_of_voice', 0.0) if brand_sov else 0.0

    # Determine leading position
    leader_count = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Leader'
        )
    ).scalar() or 0
    leading_position = "Leading" if leader_count > (total_responses * 0.3) else "Competitive"

    # Get previous period metrics for comparison (last 7 days vs previous 7 days)
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    fourteen_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=14)

    # Current period (last 7 days)
    recent_total = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            models.Response.timestamp >= seven_days_ago
        )
    ).scalar() or 0

    recent_mentions = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            and_(
                models.Response.timestamp >= seven_days_ago,
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            )
        )
    ).scalar() or 0

    # Previous period (7-14 days ago)
    prev_total = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            and_(
                models.Response.timestamp >= fourteen_days_ago,
                models.Response.timestamp < seven_days_ago
            )
        )
    ).scalar() or 0

    prev_mentions = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            and_(
                models.Response.timestamp >= fourteen_days_ago,
                models.Response.timestamp < seven_days_ago,
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            )
        )
    ).scalar() or 0

    # Calculate changes
    current_mention_rate = (recent_mentions / recent_total * 100) if recent_total > 0 else 0
    prev_mention_rate = (prev_mentions / prev_total * 100) if prev_total > 0 else 0
    change_mention_rate = current_mention_rate - prev_mention_rate

    return {
        "mention_rate": round(mention_rate, 1),
        "mention_count": pppl_mentions,
        "total_responses": total_responses,
        "positive_sentiment": round(positive_sentiment, 1),
        "descriptor_match": round(descriptor_match, 1),
        "share_of_voice": round(share_of_voice, 1),
        "leadership_visibility": round(leadership_visibility, 1),
        "change_mention_rate": round(change_mention_rate, 1),
        "change_sentiment": 0.0,  # TODO: Calculate sentiment change
        "change_descriptor": 0.0,  # TODO: Calculate descriptor change
        "leading_position": leading_position
    }


def get_mention_trend(db: Session, days: int = 30, brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get mention rate trend over time for a specific brand.

    Args:
        db: Database session
        days: Number of days to include in the trend
        brand_id: Optional brand ID to filter by
    """
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    # Get responses grouped by date
    query = db.query(
        func.date(models.Response.timestamp).label('date'),
        func.count(models.Response.id).label('total'),
        func.sum(
            func.case(
                (models.Response.brand_mentioned.in_(['Yes', 'Indirect']), 1),
                else_=0
            )
        ).label('mentions')
    ).filter(
        models.Response.timestamp >= start_date
    )

    if brand_id:
        query = query.filter(models.Response.brand_id == brand_id)

    results = query.group_by(
        func.date(models.Response.timestamp)
    ).order_by(
        func.date(models.Response.timestamp)
    ).all()

    trend_data = []
    for row in results:
        mention_rate = (row.mentions / row.total * 100) if row.total > 0 else 0
        trend_data.append({
            "date": row.date.isoformat() if row.date else None,
            "mention_rate": round(mention_rate, 1),
            "total_responses": row.total,
            "mentions": row.mentions
        })

    return trend_data


def get_sentiment_breakdown(db: Session, brand_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get sentiment distribution for brand mentions.

    Args:
        db: Database session
        brand_id: Optional brand ID to filter by
    """
    # Get all brand mentions grouped by sentiment
    query = db.query(
        models.Response.sentiment,
        func.count(models.Response.id).label('count')
    ).filter(
        models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
    )

    if brand_id:
        query = query.filter(models.Response.brand_id == brand_id)

    results = query.group_by(
        models.Response.sentiment
    ).all()

    sentiment_map = {row.sentiment: row.count for row in results}
    total = sum(sentiment_map.values())

    # Get actual negative statements
    negative_query = db.query(
        models.Response.response_text,
        models.Response.query_text,
        models.Response.platform
    ).filter(
        and_(
            models.Response.brand_mentioned.in_(['Yes', 'Indirect']),
            models.Response.sentiment == 'Negative'
        )
    )
    if brand_id:
        negative_query = negative_query.filter(models.Response.brand_id == brand_id)

    negative_responses = negative_query.all()
    negative_statements = [
        {
            "text": resp.response_text,
            "query": resp.query_text,
            "platform": resp.platform
        }
        for resp in negative_responses
    ]

    # Get actual mixed statements
    mixed_query = db.query(
        models.Response.response_text,
        models.Response.query_text,
        models.Response.platform
    ).filter(
        and_(
            models.Response.brand_mentioned.in_(['Yes', 'Indirect']),
            models.Response.sentiment == 'Mixed'
        )
    )
    if brand_id:
        mixed_query = mixed_query.filter(models.Response.brand_id == brand_id)

    mixed_responses = mixed_query.all()
    mixed_statements = [
        {
            "text": resp.response_text,
            "query": resp.query_text,
            "platform": resp.platform
        }
        for resp in mixed_responses
    ]

    return {
        "very_positive": sentiment_map.get('Very Positive', 0),
        "positive": sentiment_map.get('Positive', 0),
        "neutral": sentiment_map.get('Neutral', 0),
        "negative": sentiment_map.get('Negative', 0),
        "mixed": sentiment_map.get('Mixed', 0),
        "total": total,
        "very_positive_pct": round((sentiment_map.get('Very Positive', 0) / total * 100) if total > 0 else 0, 1),
        "positive_pct": round((sentiment_map.get('Positive', 0) / total * 100) if total > 0 else 0, 1),
        "neutral_pct": round((sentiment_map.get('Neutral', 0) / total * 100) if total > 0 else 0, 1),
        "negative_pct": round((sentiment_map.get('Negative', 0) / total * 100) if total > 0 else 0, 1),
        "mixed_pct": round((sentiment_map.get('Mixed', 0) / total * 100) if total > 0 else 0, 1),
        "negative_statements": negative_statements,
        "mixed_statements": mixed_statements
    }


def get_positioning_breakdown(db: Session, brand_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get brand positioning distribution across responses.

    Args:
        db: Database session
        brand_id: Optional brand ID to filter by
    """
    query = db.query(
        models.Response.brand_position,
        func.count(models.Response.id).label('count')
    )

    if brand_id:
        query = query.filter(models.Response.brand_id == brand_id)

    results = query.group_by(
        models.Response.brand_position
    ).all()

    position_map = {row.brand_position: row.count for row in results}
    total = sum(position_map.values())

    return {
        "leader": position_map.get('Leader', 0),
        "top_3": position_map.get('Top 3', 0),
        "featured": position_map.get('Featured', 0),
        "listed": position_map.get('Listed', 0),
        "not_mentioned": position_map.get('Not Mentioned', 0),
        "total": total,
        "leader_pct": round((position_map.get('Leader', 0) / total * 100) if total > 0 else 0, 1),
        "top_3_pct": round((position_map.get('Top 3', 0) / total * 100) if total > 0 else 0, 1),
        "featured_pct": round((position_map.get('Featured', 0) / total * 100) if total > 0 else 0, 1),
        "listed_pct": round((position_map.get('Listed', 0) / total * 100) if total > 0 else 0, 1),
        "not_mentioned_pct": round((position_map.get('Not Mentioned', 0) / total * 100) if total > 0 else 0, 1),
    }


def get_share_of_voice(db: Session, brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Calculate share of voice for brand vs competitors.

    Args:
        db: Database session
        brand_id: Optional brand ID to filter by
    """
    # Helper function to apply brand filter
    def apply_brand_filter(query):
        if brand_id:
            return query.filter(models.Response.brand_id == brand_id)
        return query

    # Get total responses
    total_responses = apply_brand_filter(
        db.query(func.count(models.Response.id))
    ).scalar() or 1

    # Get brand mentions by position
    pppl_leader = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Leader'
        )
    ).scalar() or 0

    pppl_top3 = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Top 3'
        )
    ).scalar() or 0

    pppl_featured = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Featured'
        )
    ).scalar() or 0

    pppl_listed = apply_brand_filter(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Listed'
        )
    ).scalar() or 0

    # Total mentions includes all positions (Leader, Top 3, Featured, Listed)
    pppl_total_mentions = pppl_leader + pppl_top3 + pppl_featured + pppl_listed

    # Get brand name for this brand_id
    brand_name = "Your Brand"
    if brand_id:
        brand_info = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
        if brand_info:
            brand_name = brand_info.brand_name

    sov_data = [{
        "organization": brand_name,
        "leader_count": pppl_leader,
        "top3_count": pppl_top3,
        "featured_count": pppl_featured,
        "listed_count": pppl_listed,
        "total_mentions": pppl_total_mentions,
        "share_of_voice": 0,  # Will calculate after getting all mentions
        "leadership_visibility": round(((pppl_leader + pppl_top3) / total_responses * 100), 1),  # Quality-weighted
        "is_brand": True  # Mark this as the user's brand
    }]

    # Get ALL unique competitors mentioned in responses (not just tracked competitors)
    responses_query = apply_brand_filter(
        db.query(models.Response.competitors).filter(
            models.Response.competitors.isnot(None),
            models.Response.competitors != ''
        )
    )
    responses = responses_query.all()

    # Parse all competitors from comma-separated strings
    competitor_mention_counts = {}
    for response in responses:
        if response.competitors:
            # Split by comma and clean up names
            competitors_list = [comp.strip() for comp in response.competitors.split(',')]
            for comp in competitors_list:
                if comp:  # Skip empty strings
                    competitor_mention_counts[comp] = competitor_mention_counts.get(comp, 0) + 1

    # Add all competitors to sov_data
    for comp_name, mention_count in competitor_mention_counts.items():
        sov_data.append({
            "organization": comp_name,
            "leader_count": 0,  # Would need more sophisticated parsing
            "top3_count": 0,
            "featured_count": 0,
            "listed_count": 0,
            "total_mentions": mention_count,
            "share_of_voice": 0,  # Will calculate after getting total
            "leadership_visibility": 0,  # Not tracked for competitors
            "is_brand": False  # Mark as competitor
        })

    # Calculate share_of_voice as percentage of total mentions (not total responses)
    total_all_mentions = sum(item['total_mentions'] for item in sov_data)
    for item in sov_data:
        if total_all_mentions > 0:
            item['share_of_voice'] = round((item['total_mentions'] / total_all_mentions * 100), 1)
        else:
            item['share_of_voice'] = 0

    # Calculate trends by comparing with previous collection period
    # Get the two most recent unique collection dates
    dates_query = apply_brand_filter(
        db.query(func.date(models.Response.timestamp)).distinct()
    ).order_by(func.date(models.Response.timestamp).desc()).limit(2)

    dates = [row[0] for row in dates_query.all()]

    # Initialize trend data
    for item in sov_data:
        item['trend'] = 'neutral'  # Default to neutral
        item['trend_change'] = 0.0

    # Only calculate trends if we have at least 2 collection dates
    if len(dates) >= 2:
        latest_date = dates[0]
        previous_date = dates[1]

        # Get total responses for each period
        latest_total = apply_brand_filter(
            db.query(func.count(models.Response.id)).filter(
                func.date(models.Response.timestamp) == latest_date
            )
        ).scalar() or 1

        previous_total = apply_brand_filter(
            db.query(func.count(models.Response.id)).filter(
                func.date(models.Response.timestamp) == previous_date
            )
        ).scalar() or 1

        # Calculate previous period share of voice for brand
        brand_item = next((item for item in sov_data if item['is_brand']), None)
        if brand_item:
            prev_brand_mentions = apply_brand_filter(
                db.query(func.count(models.Response.id)).filter(
                    func.date(models.Response.timestamp) == previous_date,
                    models.Response.brand_position.in_(['Leader', 'Top 3', 'Featured'])
                )
            ).scalar() or 0

            prev_brand_sov = (prev_brand_mentions / previous_total * 100) if previous_total > 0 else 0
            current_brand_sov = brand_item['share_of_voice']
            change = current_brand_sov - prev_brand_sov

            brand_item['trend_change'] = round(change, 1)
            if change > 0.5:
                brand_item['trend'] = 'up'
            elif change < -0.5:
                brand_item['trend'] = 'down'

        # Calculate previous period share of voice for competitors
        prev_responses = apply_brand_filter(
            db.query(models.Response.competitors).filter(
                func.date(models.Response.timestamp) == previous_date,
                models.Response.competitors.isnot(None),
                models.Response.competitors != ''
            )
        ).all()

        prev_competitor_counts = {}
        for response in prev_responses:
            if response.competitors:
                competitors_list = [comp.strip() for comp in response.competitors.split(',')]
                for comp in competitors_list:
                    if comp:
                        prev_competitor_counts[comp] = prev_competitor_counts.get(comp, 0) + 1

        # Update trends for competitors
        for item in sov_data:
            if not item['is_brand']:
                comp_name = item['organization']
                prev_mentions = prev_competitor_counts.get(comp_name, 0)
                prev_sov = (prev_mentions / previous_total * 100) if previous_total > 0 else 0
                current_sov = item['share_of_voice']
                change = current_sov - prev_sov

                item['trend_change'] = round(change, 1)
                if change > 0.5:
                    item['trend'] = 'up'
                elif change < -0.5:
                    item['trend'] = 'down'

    # Sort by total mentions descending
    sov_data.sort(key=lambda x: x['total_mentions'], reverse=True)

    return sov_data
