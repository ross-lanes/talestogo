"""
Analytics calculations for dashboard and reports.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from . import models
from typing import Dict, List, Any, Optional
import datetime


def get_dashboard_metrics(db: Session, user_id: int, brand_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate key metrics for the dashboard for a specific brand.
    Returns mention rate, sentiment, descriptor match, and share of voice.

    Args:
        db: Database session
        user_id: User ID to filter by (required for data isolation)
        brand_id: Optional brand ID to filter by. If None, returns metrics for all user's brands.
    """
    # Base query for responses - filter by user_id and optionally brand_id
    def apply_filters(query):
        query = query.filter(models.Response.user_id == user_id)
        if brand_id:
            query = query.filter(models.Response.brand_id == brand_id)
        return query

    # Get total responses
    total_responses = apply_filters(
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
    pppl_mentions = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
        )
    ).scalar() or 0
    mention_rate = (pppl_mentions / total_responses) * 100

    # Calculate positive sentiment rate (Very Positive, Positive)
    positive_responses = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            and_(
                models.Response.brand_mentioned.in_(['Yes', 'Indirect']),
                models.Response.sentiment.in_(['Very Positive', 'Positive'])
            )
        )
    ).scalar() or 0
    positive_sentiment = (positive_responses / pppl_mentions * 100) if pppl_mentions > 0 else 0.0

    # Calculate descriptor match rate (% of target descriptors found in AI responses about brand)
    # Get target descriptors for this brand
    target_descriptors_query = db.query(models.TargetDescriptor).filter(
        models.TargetDescriptor.user_id == user_id
    )
    if brand_id:
        target_descriptors_query = target_descriptors_query.filter(
            models.TargetDescriptor.brand_id == brand_id
        )
    target_descriptors_list = target_descriptors_query.all()
    total_target_descriptors = len(target_descriptors_list)

    if total_target_descriptors == 0:
        descriptor_match = 0.0
    else:
        # Get all responses with descriptors for this brand
        responses_with_descriptors = apply_filters(
            db.query(models.Response).filter(
                and_(
                    models.Response.brand_mentioned.in_(['Yes', 'Indirect']),
                    models.Response.descriptors.isnot(None),
                    models.Response.descriptors != ''
                )
            )
        ).all()

        # Find which target descriptors were actually used
        target_descriptors_set = {td.descriptor.lower().strip() for td in target_descriptors_list}
        found_target_descriptors = set()

        for response in responses_with_descriptors:
            if response.descriptors:
                # Split comma-separated descriptors
                descriptors_list = [d.lower().strip() for d in response.descriptors.split(',') if d.strip()]

                # Check which target descriptors appear in this response
                for desc in descriptors_list:
                    if desc in target_descriptors_set:
                        found_target_descriptors.add(desc)

        # Calculate percentage of target descriptors that were found
        descriptor_match = (len(found_target_descriptors) / total_target_descriptors * 100)

    # Calculate leadership visibility (Leader + Top 3 positions)
    pppl_leader_count = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position.in_(['Leader', 'Top 3'])
        )
    ).scalar() or 0
    leadership_visibility = (pppl_leader_count / total_responses * 100) if total_responses > 0 else 0.0

    # Calculate true share of voice - need to get from share_of_voice function
    # For dashboard, we'll use a simplified version based on all brand mentions
    sov_data = get_share_of_voice(db, user_id=user_id, brand_id=brand_id)
    brand_sov = next((item for item in sov_data if item.get('is_brand')), None)
    share_of_voice = brand_sov.get('share_of_voice', 0.0) if brand_sov else 0.0

    # Determine leading position
    leader_count = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Leader'
        )
    ).scalar() or 0
    leading_position = "Leading" if leader_count > (total_responses * 0.3) else "Competitive"

    # Get previous period metrics for comparison (last 7 days vs previous 7 days)
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    fourteen_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=14)

    # Current period (last 7 days)
    recent_total = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            models.Response.timestamp >= seven_days_ago
        )
    ).scalar() or 0

    recent_mentions = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            and_(
                models.Response.timestamp >= seven_days_ago,
                models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
            )
        )
    ).scalar() or 0

    # Previous period (7-14 days ago)
    prev_total = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            and_(
                models.Response.timestamp >= fourteen_days_ago,
                models.Response.timestamp < seven_days_ago
            )
        )
    ).scalar() or 0

    prev_mentions = apply_filters(
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
        "mention_rate": round(mention_rate),
        "mention_count": pppl_mentions,
        "total_responses": total_responses,
        "positive_sentiment": round(positive_sentiment),
        "descriptor_match": round(descriptor_match),
        "share_of_voice": round(share_of_voice),
        "leadership_visibility": round(leadership_visibility),
        "change_mention_rate": round(change_mention_rate),
        "change_sentiment": 0.0,  # TODO: Calculate sentiment change
        "change_descriptor": 0.0,  # TODO: Calculate descriptor change
        "leading_position": leading_position
    }


def get_mention_trend(db: Session, user_id: int, days: int = 30, brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
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
        models.Response.user_id == user_id,
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
            "mention_rate": round(mention_rate),
            "total_responses": row.total,
            "mentions": row.mentions
        })

    return trend_data


def get_sentiment_breakdown(db: Session, user_id: int, brand_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get sentiment distribution for brand mentions.

    Args:
        db: Database session
        brand_id: Optional brand ID to filter by
    """
    from app.services.llm_service import _call_gemini_api

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

    # Sentiment insights will be generated during report generation (Full Analysis → Run Analysis)
    # For now, return placeholder text
    sentiment_insights = {
        'very_positive': 'No insight available. Go to Full Analysis → Run Analysis to generate insights with most recent data.',
        'positive': 'No insight available. Go to Full Analysis → Run Analysis to generate insights with most recent data.',
        'neutral': 'No insight available. Go to Full Analysis → Run Analysis to generate insights with most recent data.',
        'negative': 'No insight available. Go to Full Analysis → Run Analysis to generate insights with most recent data.',
        'very_negative': 'No insight available. Go to Full Analysis → Run Analysis to generate insights with most recent data.'
    }

    return {
        "very_positive": sentiment_map.get('Very Positive', 0),
        "positive": sentiment_map.get('Positive', 0),
        "neutral": sentiment_map.get('Neutral', 0),
        "negative": sentiment_map.get('Negative', 0),
        "very_negative": sentiment_map.get('Very Negative', 0),
        "mixed": sentiment_map.get('Mixed', 0),
        "total": total,
        "very_positive_pct": round((sentiment_map.get('Very Positive', 0) / total * 100) if total > 0 else 0),
        "positive_pct": round((sentiment_map.get('Positive', 0) / total * 100) if total > 0 else 0),
        "neutral_pct": round((sentiment_map.get('Neutral', 0) / total * 100) if total > 0 else 0),
        "negative_pct": round((sentiment_map.get('Negative', 0) / total * 100) if total > 0 else 0),
        "very_negative_pct": round((sentiment_map.get('Very Negative', 0) / total * 100) if total > 0 else 0),
        "mixed_pct": round((sentiment_map.get('Mixed', 0) / total * 100) if total > 0 else 0),
        "negative_statements": negative_statements,
        "sentiment_insights": sentiment_insights
    }


def get_positioning_breakdown(db: Session, user_id: int, brand_id: Optional[int] = None) -> Dict[str, Any]:
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
        "leader_pct": round((position_map.get('Leader', 0) / total * 100) if total > 0 else 0),
        "top_3_pct": round((position_map.get('Top 3', 0) / total * 100) if total > 0 else 0),
        "featured_pct": round((position_map.get('Featured', 0) / total * 100) if total > 0 else 0),
        "listed_pct": round((position_map.get('Listed', 0) / total * 100) if total > 0 else 0),
        "not_mentioned_pct": round((position_map.get('Not Mentioned', 0) / total * 100) if total > 0 else 0),
    }


def get_share_of_voice(db: Session, user_id: int, brand_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Calculate share of voice for brand vs competitors.

    Args:
        db: Database session
        brand_id: Optional brand ID to filter by
    """
    # Helper function to apply user and brand filters
    def apply_filters(query):
        query = query.filter(models.Response.user_id == user_id)
        if brand_id:
            query = query.filter(models.Response.brand_id == brand_id)
        return query

    # Get total responses
    total_responses = apply_filters(
        db.query(func.count(models.Response.id))
    ).scalar() or 1

    # Get brand mentions by position
    pppl_leader = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Leader'
        )
    ).scalar() or 0

    pppl_top3 = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Top 3'
        )
    ).scalar() or 0

    pppl_featured = apply_filters(
        db.query(func.count(models.Response.id)).filter(
            models.Response.brand_position == 'Featured'
        )
    ).scalar() or 0

    pppl_listed = apply_filters(
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
        "leadership_visibility": round(((pppl_leader + pppl_top3) / total_responses * 100)),  # Quality-weighted
        "is_brand": True  # Mark this as the user's brand
    }]

    # Get ALL unique competitors mentioned in responses (not just tracked competitors)
    responses_query = apply_filters(
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
            item['share_of_voice'] = round((item['total_mentions'] / total_all_mentions * 100))
        else:
            item['share_of_voice'] = 0

    # Calculate trends by comparing with previous collection period
    # Get the two most recent unique collection dates
    dates_query = apply_filters(
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
        latest_total = apply_filters(
            db.query(func.count(models.Response.id)).filter(
                func.date(models.Response.timestamp) == latest_date
            )
        ).scalar() or 1

        previous_total = apply_filters(
            db.query(func.count(models.Response.id)).filter(
                func.date(models.Response.timestamp) == previous_date
            )
        ).scalar() or 1

        # Calculate previous period share of voice for brand
        brand_item = next((item for item in sov_data if item['is_brand']), None)
        if brand_item:
            prev_brand_mentions = apply_filters(
                db.query(func.count(models.Response.id)).filter(
                    func.date(models.Response.timestamp) == previous_date,
                    models.Response.brand_position.in_(['Leader', 'Top 3', 'Featured'])
                )
            ).scalar() or 0

            prev_brand_sov = (prev_brand_mentions / previous_total * 100) if previous_total > 0 else 0
            current_brand_sov = brand_item['share_of_voice']
            change = current_brand_sov - prev_brand_sov

            brand_item['trend_change'] = round(change)
            if change > 0.5:
                brand_item['trend'] = 'up'
            elif change < -0.5:
                brand_item['trend'] = 'down'

        # Calculate previous period share of voice for competitors
        prev_responses = apply_filters(
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

                item['trend_change'] = round(change)
                if change > 0.5:
                    item['trend'] = 'up'
                elif change < -0.5:
                    item['trend'] = 'down'

    # Sort by total mentions descending
    sov_data.sort(key=lambda x: x['total_mentions'], reverse=True)

    return sov_data


def get_descriptor_insights(db: Session, user_id: int, brand_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate comprehensive AI-powered insights about descriptor usage patterns.

    Args:
        db: Database session
        brand_id: Optional brand ID to filter by

    Returns:
        Dictionary containing LLM-generated analysis of descriptor patterns
    """
    from app.services.llm_service import _call_gemini_api

    # Get the brand name
    brand_query = db.query(models.BrandInfo)
    if brand_id:
        brand_query = brand_query.filter(models.BrandInfo.id == brand_id)
    brand = brand_query.first()
    brand_name = brand.brand_name if brand else "the brand"

    # Get all target descriptors
    target_descriptors_query = db.query(models.TargetDescriptor)
    if brand_id:
        target_descriptors_query = target_descriptors_query.filter(models.TargetDescriptor.brand_id == brand_id)
    target_descriptors = target_descriptors_query.all()
    target_descriptor_names = [td.descriptor for td in target_descriptors]

    # Get all responses where brand is mentioned
    responses_query = db.query(
        models.Response.response_text,
        models.Response.descriptors,
        models.Response.competitors,
        models.Response.pppl_position,
        models.Response.sentiment
    ).filter(
        models.Response.brand_mentioned.in_(['Yes', 'Indirect'])
    )

    if brand_id:
        responses_query = responses_query.filter(models.Response.brand_id == brand_id)

    responses = responses_query.all()

    # Count descriptor occurrences and analyze contexts
    descriptor_counts = {}
    descriptor_contexts = {}
    descriptor_with_competitors = {}
    descriptor_by_position = {}

    for resp in responses:
        if resp.descriptors:
            desc_list = [d.strip() for d in resp.descriptors.split(',') if d.strip()]

            for desc in desc_list:
                # Count occurrences
                descriptor_counts[desc] = descriptor_counts.get(desc, 0) + 1

                # Store context samples
                if desc not in descriptor_contexts:
                    descriptor_contexts[desc] = []
                if len(descriptor_contexts[desc]) < 3:  # Keep up to 3 samples
                    descriptor_contexts[desc].append(resp.response_text[:200])

                # Track competitor co-mentions
                if resp.competitors:
                    if desc not in descriptor_with_competitors:
                        descriptor_with_competitors[desc] = []
                    comp_list = [c.strip() for c in resp.competitors.split(',') if c.strip()]
                    descriptor_with_competitors[desc].extend(comp_list)

                # Track by positioning
                if resp.pppl_position:
                    if desc not in descriptor_by_position:
                        descriptor_by_position[desc] = []
                    descriptor_by_position[desc].append(resp.pppl_position)

    # Get all unique descriptors mentioned
    all_descriptors = list(descriptor_counts.keys())

    # Identify descriptors used vs not used from target list
    used_target_descriptors = [td for td in target_descriptor_names if td in descriptor_counts]
    unused_target_descriptors = [td for td in target_descriptor_names if td not in descriptor_counts]

    # Get descriptors not in target list
    non_target_descriptors = [d for d in all_descriptors if d not in target_descriptor_names]

    # Build comprehensive context for LLM
    context = f"""
Brand: {brand_name}
Total brand mentions analyzed: {len(responses)}
Total unique descriptors found: {len(all_descriptors)}

TARGET DESCRIPTORS ANALYSIS:
Target descriptors being tracked: {len(target_descriptor_names)}
Target descriptors actually used: {len(used_target_descriptors)}
Target descriptors NOT appearing: {len(unused_target_descriptors)}

STRONG ASSOCIATIONS (Most Frequently Used):
"""

    # Add top 10 most frequent descriptors with details
    sorted_descriptors = sorted(descriptor_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (desc, count) in enumerate(sorted_descriptors[:10], 1):
        percentage = round((count / len(responses)) * 100)
        context += f"\n{i}. '{desc}' - {count} mentions ({percentage}%)"

        # Add competitor context if available
        if desc in descriptor_with_competitors:
            unique_comps = list(set(descriptor_with_competitors[desc]))[:3]
            if unique_comps:
                context += f" | Often with competitors: {', '.join(unique_comps)}"

        # Add positioning context
        if desc in descriptor_by_position:
            positions = descriptor_by_position[desc]
            leader_count = positions.count('Leader')
            if leader_count > 0:
                context += f" | Appears in 'Leader' positioning {leader_count} times"

    context += "\n\nWEAK ASSOCIATIONS (Target Descriptors with Low/No Usage):\n"
    for desc in unused_target_descriptors[:10]:
        context += f"- '{desc}' - NOT mentioned at all\n"

    # Add some used but infrequent target descriptors
    weak_used = [(d, descriptor_counts[d]) for d in used_target_descriptors if descriptor_counts[d] < 3]
    if weak_used:
        context += "\nInfrequently used target descriptors:\n"
        for desc, count in weak_used[:5]:
            context += f"- '{desc}' - only {count} mention(s)\n"

    context += "\n\nNON-TARGET DESCRIPTORS (High frequency but not tracked):\n"
    non_target_freq = [(d, descriptor_counts[d]) for d in non_target_descriptors if descriptor_counts[d] >= 3]
    for desc, count in sorted(non_target_freq, key=lambda x: x[1], reverse=True)[:10]:
        context += f"- '{desc}' - {count} mentions\n"

    # Add competitor analysis
    all_competitors_mentioned = set()
    for comp_list in descriptor_with_competitors.values():
        all_competitors_mentioned.update(comp_list)

    if all_competitors_mentioned:
        context += f"\n\nCOMPETITORS FREQUENTLY MENTIONED ALONGSIDE DESCRIPTORS:\n"
        for comp in list(all_competitors_mentioned)[:10]:
            context += f"- {comp}\n"

    # Descriptor insights will be generated during report generation (Full Analysis → Run Analysis)
    # Return summary stats and placeholder text
    sorted_descriptors = sorted(descriptor_counts.items(), key=lambda x: x[1], reverse=True) if descriptor_counts else []

    # Build a simple summary text from the stats
    if not all_descriptors:
        analysis_text = "No descriptor data available yet. Run some queries to start tracking descriptor usage."
    else:
        analysis_text = "Descriptor usage summary based on analyzed responses. "
        if used_target_descriptors:
            analysis_text += f"Your target descriptors are appearing in responses, with {len(used_target_descriptors)} out of {len(target_descriptor_names)} tracked descriptors being used. "
        if sorted_descriptors:
            top_desc = sorted_descriptors[0]
            analysis_text += f"The most frequently mentioned descriptor is '{top_desc[0]}' with {top_desc[1]} mentions. "
        if unused_target_descriptors:
            analysis_text += f"Note: {len(unused_target_descriptors)} target descriptors have not yet appeared in any responses."

    return {
        "analysis": analysis_text,
        "summary_stats": {
            "total_unique_descriptors": len(all_descriptors),
            "target_descriptors_tracked": len(target_descriptor_names),
            "target_descriptors_used": len(used_target_descriptors),
            "target_descriptors_unused": len(unused_target_descriptors),
            "most_frequent_descriptor": sorted_descriptors[0][0] if sorted_descriptors else None,
            "most_frequent_count": sorted_descriptors[0][1] if sorted_descriptors else 0
        }
    }
