"""
Analytics calculations for dashboard and reports.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from . import models
from typing import Dict, List, Any
import datetime


def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    Calculate key metrics for the dashboard.
    Returns mention rate, sentiment, descriptor match, and share of voice.
    """
    # Get total responses
    total_responses = db.query(func.count(models.Response.id)).scalar() or 0

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
    pppl_mentions = db.query(func.count(models.Response.id)).filter(
        models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
    ).scalar() or 0
    mention_rate = (pppl_mentions / total_responses) * 100

    # Calculate positive sentiment rate (Very Positive, Positive)
    positive_responses = db.query(func.count(models.Response.id)).filter(
        and_(
            models.Response.brand_mentioned.in_(['Yes', 'Indirect']),
            models.Response.sentiment.in_(['Very Positive', 'Positive'])
        )
    ).scalar() or 0
    positive_sentiment = (positive_responses / pppl_mentions * 100) if pppl_mentions > 0 else 0.0

    # Calculate descriptor match rate (responses with descriptors)
    descriptor_responses = db.query(func.count(models.Response.id)).filter(
        and_(
            models.Response.brand_mentioned.in_(['Yes', 'Indirect']),
            models.Response.descriptors.isnot(None),
            models.Response.descriptors != ''
        )
    ).scalar() or 0
    descriptor_match = (descriptor_responses / pppl_mentions * 100) if pppl_mentions > 0 else 0.0

    # Calculate share of voice (PPPL vs competitors)
    pppl_leader_count = db.query(func.count(models.Response.id)).filter(
        models.Response.brand_position.in_(['Leader', 'Top 3'])
    ).scalar() or 0
    share_of_voice = (pppl_leader_count / total_responses * 100) if total_responses > 0 else 0.0

    # Determine leading position
    leader_count = db.query(func.count(models.Response.id)).filter(
        models.Response.brand_position == 'Leader'
    ).scalar() or 0
    leading_position = "Leading" if leader_count > (total_responses * 0.3) else "Competitive"

    # Get previous period metrics for comparison (last 7 days vs previous 7 days)
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    fourteen_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=14)

    # Current period (last 7 days)
    recent_total = db.query(func.count(models.Response.id)).filter(
        models.Response.timestamp >= seven_days_ago
    ).scalar() or 0

    recent_mentions = db.query(func.count(models.Response.id)).filter(
        and_(
            models.Response.timestamp >= seven_days_ago,
            models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
        )
    ).scalar() or 0

    # Previous period (7-14 days ago)
    prev_total = db.query(func.count(models.Response.id)).filter(
        and_(
            models.Response.timestamp >= fourteen_days_ago,
            models.Response.timestamp < seven_days_ago
        )
    ).scalar() or 0

    prev_mentions = db.query(func.count(models.Response.id)).filter(
        and_(
            models.Response.timestamp >= fourteen_days_ago,
            models.Response.timestamp < seven_days_ago,
            models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
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
        "change_mention_rate": round(change_mention_rate, 1),
        "change_sentiment": 0.0,  # TODO: Calculate sentiment change
        "change_descriptor": 0.0,  # TODO: Calculate descriptor change
        "leading_position": leading_position
    }


def get_mention_trend(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get mention rate trend over time.
    """
    start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    # Get responses grouped by date
    results = db.query(
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
    ).group_by(
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


def get_sentiment_breakdown(db: Session) -> Dict[str, Any]:
    """
    Get sentiment distribution for PPPL mentions.
    """
    # Get all PPPL mentions grouped by sentiment
    results = db.query(
        models.Response.sentiment,
        func.count(models.Response.id).label('count')
    ).filter(
        models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
    ).group_by(
        models.Response.sentiment
    ).all()

    sentiment_map = {row.sentiment: row.count for row in results}
    total = sum(sentiment_map.values())

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
    }


def get_positioning_breakdown(db: Session) -> Dict[str, Any]:
    """
    Get PPPL positioning distribution across responses.
    """
    results = db.query(
        models.Response.brand_position,
        func.count(models.Response.id).label('count')
    ).group_by(
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


def get_share_of_voice(db: Session) -> List[Dict[str, Any]]:
    """
    Calculate share of voice for PPPL vs competitors.
    """
    # Get all competitors
    competitors = db.query(models.Competitor).filter(models.Competitor.track == True).all()

    # Get PPPL mentions by position
    pppl_leader = db.query(func.count(models.Response.id)).filter(
        models.Response.brand_position == 'Leader'
    ).scalar() or 0

    pppl_top3 = db.query(func.count(models.Response.id)).filter(
        models.Response.brand_position == 'Top 3'
    ).scalar() or 0

    pppl_featured = db.query(func.count(models.Response.id)).filter(
        models.Response.brand_position == 'Featured'
    ).scalar() or 0

    total_responses = db.query(func.count(models.Response.id)).scalar() or 1

    sov_data = [{
        "organization": "PPPL",
        "leader_count": pppl_leader,
        "top3_count": pppl_top3,
        "featured_count": pppl_featured,
        "total_mentions": pppl_leader + pppl_top3 + pppl_featured,
        "share_of_voice": round(((pppl_leader + pppl_top3) / total_responses * 100), 1)
    }]

    # Add competitor data (simplified - assumes competitors in text field)
    for comp in competitors[:5]:  # Top 5 competitors
        # Count mentions in competitors field (comma-separated text)
        comp_mentions = db.query(func.count(models.Response.id)).filter(
            models.Response.competitors.like(f'%{comp.organization}%')
        ).scalar() or 0

        sov_data.append({
            "organization": comp.organization,
            "leader_count": 0,  # Would need more sophisticated parsing
            "top3_count": 0,
            "featured_count": 0,
            "total_mentions": comp_mentions,
            "share_of_voice": round((comp_mentions / total_responses * 100), 1)
        })

    return sov_data
