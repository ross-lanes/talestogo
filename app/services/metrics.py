"""
TALES Metrics Calculation Module
=================================
Single source of truth for ALL metric calculations.
Used by both analytics cache service and report generation.

FILTERING RULES:
---------------
1. Positioning/SOV/Mentions: EXCLUDE brand_in_query=True queries
   Rationale: When brand is in the query, it's not a fair test of organic visibility

2. Sentiment/Descriptors: INCLUDE all queries (applies to ALL mentions)
   Rationale: Sentiment and descriptors apply to all mentions regardless of query type

3. Direct mentions only: brand_mentioned == 'Yes'
   Use for: Sentiment analysis, Descriptor analysis (descriptors tied to direct mentions)

4. Direct + Indirect: brand_mentioned in ['Yes', 'Indirect']
   Use for: Positioning analysis (includes all forms of brand presence)

IMPORTANT: All functions accept Response and Query objects as parameters.
They do NOT make database calls - that's handled by the calling layer.
"""

from typing import List, Dict, Any
from collections import Counter


# ==================== CONSTANTS ====================

POSITION_SCORES = {
    "Leader": 5,
    "Top 3": 4,
    "Featured": 3,
    "Listed": 2,
    "Not Mentioned": 1,
}

THREAT_WEIGHTS = {
    "mention_weight": 0.7,
    "negative_weight": 2.0,
    "positive_weight": 1.5,
}

THREAT_THRESHOLDS = {
    "high": 50,
    "medium": 20,
}


# ==================== UTILITY FUNCTIONS ====================

def normalize_organization_name(name: str) -> str:
    """
    Normalize organization names for consistent grouping.
    Combines variations of the same organization.

    Examples:
    - "OpenAI" and "Open AI" -> "OpenAI"
    - "Google Cloud" and "Google" -> "Google"
    """
    if not name:
        return name

    name = name.strip()

    # Common normalizations
    normalizations = {
        # OpenAI variations
        'open ai': 'OpenAI',
        'openai': 'OpenAI',

        # Google variations
        'google cloud': 'Google',
        'google workspace': 'Google',

        # Microsoft variations
        'microsoft azure': 'Microsoft',
        'microsoft 365': 'Microsoft',

        # Amazon variations
        'amazon web services': 'AWS',
        'amazon aws': 'AWS',

        # Add more as needed
    }

    name_lower = name.lower()
    return normalizations.get(name_lower, name)


def filter_exclude_branded_queries(responses: List[Any], queries: List[Any]) -> List[Any]:
    """
    Filter out responses from queries where brand is in the query text.

    Use this for: Positioning, Share of Voice, Mention Rate calculations.
    Don't use for: Sentiment, Descriptors (which apply to all mentions).

    Args:
        responses: List of Response objects
        queries: List of Query objects

    Returns:
        Filtered list of responses excluding branded queries
    """
    branded_query_ids = {q.query_id for q in queries if q.brand_in_query}
    return [r for r in responses if r.query_id not in branded_query_ids]


# ==================== CORE METRIC CALCULATIONS ====================

def calculate_mention_metrics(responses: List[Any]) -> Dict[str, Any]:
    """
    Calculate mention breakdown (Yes/Indirect/No).

    NOTE: This function does NOT filter by brand_in_query internally.
    The caller should pre-filter responses if needed.

    Args:
        responses: List of Response objects

    Returns:
        Dict with counts and percentages for each mention type
    """
    total = len(responses)
    if total == 0:
        return {"total": 0, "yes": 0, "indirect": 0, "no": 0}

    mentions = Counter([r.brand_mentioned for r in responses])

    return {
        "total": total,
        "yes": mentions.get("Yes", 0),
        "indirect": mentions.get("Indirect", 0),
        "no": mentions.get("No", 0),
        "yes_pct": round((mentions.get("Yes", 0) / total) * 100, 1),
        "indirect_pct": round((mentions.get("Indirect", 0) / total) * 100, 1),
        "no_pct": round((mentions.get("No", 0) / total) * 100, 1),
    }


def calculate_positioning_metrics(responses: List[Any], queries: List[Any]) -> Dict[str, Any]:
    """
    Calculate brand positioning metrics.

    FILTERS APPLIED:
    - Excludes responses from queries where brand_in_query=True
    - Only counts responses where brand_mentioned in ['Yes', 'Indirect']

    This matches dashboard logic for fair positioning analysis.

    Args:
        responses: List of Response objects
        queries: List of Query objects

    Returns:
        Dict with counts and percentages for each position level
    """
    # Build set of query_ids where brand_in_query=True to exclude
    branded_query_ids = {q.query_id for q in queries if q.brand_in_query}

    # Filter responses: exclude branded queries and only count mentions
    filtered_responses = [
        r for r in responses
        if r.query_id not in branded_query_ids
        and r.brand_mentioned in ['Yes', 'Indirect']
    ]

    total = len(filtered_responses)
    if total == 0:
        return {
            "total": 0,
            "leader": 0,
            "top_3": 0,
            "featured": 0,
            "listed": 0,
            "not_mentioned": 0,
            "leader_pct": 0,
            "top_3_pct": 0,
            "featured_pct": 0,
            "listed_pct": 0,
            "not_mentioned_pct": 0,
        }

    positions = Counter([r.brand_position for r in filtered_responses])

    return {
        "total": total,
        "leader": positions.get("Leader", 0),
        "top_3": positions.get("Top 3", 0),
        "featured": positions.get("Featured", 0),
        "listed": positions.get("Listed", 0),
        "not_mentioned": positions.get("Not Mentioned", 0),
        "leader_pct": round((positions.get("Leader", 0) / total) * 100, 1),
        "top_3_pct": round((positions.get("Top 3", 0) / total) * 100, 1),
        "featured_pct": round((positions.get("Featured", 0) / total) * 100, 1),
        "listed_pct": round((positions.get("Listed", 0) / total) * 100, 1),
        "not_mentioned_pct": round((positions.get("Not Mentioned", 0) / total) * 100, 1),
    }


def calculate_positioning_average(responses: List[Any], queries: List[Any]) -> float:
    """
    Calculate average positioning score.

    Scoring: Leader=5, Top 3=4, Featured=3, Listed=2, Not Mentioned=1

    FILTERS APPLIED:
    - Excludes responses from queries where brand_in_query=True
    - Only counts responses where brand_mentioned in ['Yes', 'Indirect']

    Args:
        responses: List of Response objects
        queries: List of Query objects

    Returns:
        Average positioning score (0.0 to 5.0)
    """
    # Build set of query_ids where brand_in_query=True to exclude
    branded_query_ids = {q.query_id for q in queries if q.brand_in_query}

    # Filter responses: exclude branded queries and only count mentions
    filtered_responses = [
        r for r in responses
        if r.query_id not in branded_query_ids
        and r.brand_mentioned in ['Yes', 'Indirect']
    ]

    if not filtered_responses:
        return 0.0

    total_score = sum(POSITION_SCORES.get(r.brand_position, 1) for r in filtered_responses)
    return round(total_score / len(filtered_responses), 2)


def calculate_sentiment_metrics(responses: List[Any]) -> Dict[str, Any]:
    """
    Calculate sentiment distribution for DIRECT brand mentions only.

    FILTERS APPLIED:
    - Only counts responses where brand_mentioned == 'Yes' (direct mentions)
    - NO brand_in_query filtering (sentiment applies to ALL queries)

    Rationale: Sentiment analysis should focus on direct mentions where
    sentiment can be clearly attributed to the brand.

    Args:
        responses: List of Response objects

    Returns:
        Dict with counts and percentages for each sentiment category
    """
    # Filter to only direct brand mentions
    brand_responses = [r for r in responses if r.brand_mentioned == "Yes"]
    total = len(brand_responses)

    if total == 0:
        return {
            "total": 0,
            "very_positive": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "mixed": 0,
            "very_negative": 0,
            "very_positive_pct": 0,
            "positive_pct": 0,
            "neutral_pct": 0,
            "negative_pct": 0,
            "mixed_pct": 0,
            "very_negative_pct": 0,
        }

    sentiments = Counter([r.sentiment for r in brand_responses])

    return {
        "total": total,
        "very_positive": sentiments.get("Very Positive", 0),
        "positive": sentiments.get("Positive", 0),
        "neutral": sentiments.get("Neutral", 0),
        "negative": sentiments.get("Negative", 0),
        "mixed": sentiments.get("Mixed", 0),
        "very_negative": sentiments.get("Very Negative", 0),
        "very_positive_pct": round((sentiments.get("Very Positive", 0) / total) * 100, 1),
        "positive_pct": round((sentiments.get("Positive", 0) / total) * 100, 1),
        "neutral_pct": round((sentiments.get("Neutral", 0) / total) * 100, 1),
        "negative_pct": round((sentiments.get("Negative", 0) / total) * 100, 1),
        "mixed_pct": round((sentiments.get("Mixed", 0) / total) * 100, 1),
        "very_negative_pct": round((sentiments.get("Very Negative", 0) / total) * 100, 1),
    }


def calculate_positive_sentiment_rate(responses: List[Any]) -> float:
    """
    Calculate percentage of responses with positive or very positive sentiment.

    FILTERS APPLIED:
    - Only counts direct mentions (brand_mentioned == 'Yes')

    Args:
        responses: List of Response objects

    Returns:
        Percentage of positive responses (0.0 to 100.0)
    """
    brand_responses = [r for r in responses if r.brand_mentioned == "Yes"]
    if not brand_responses:
        return 0.0

    positive_count = sum(1 for r in brand_responses if r.sentiment in ["Positive", "Very Positive"])
    return round((positive_count / len(brand_responses)) * 100, 1)


def calculate_platform_metrics(responses: List[Any], queries: List[Any]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate metrics broken down by platform.

    Returns positioning, mention, and sentiment metrics for each platform.

    Args:
        responses: List of Response objects
        queries: List of Query objects

    Returns:
        Dict with platform names as keys, each containing full metrics
    """
    platforms = {}

    for platform in ["ChatGPT", "Claude", "Gemini", "Perplexity"]:
        platform_responses = [r for r in responses if r.platform == platform]

        platforms[platform] = {
            "total": len(platform_responses),
            "mention": calculate_mention_metrics(platform_responses),
            "positioning": calculate_positioning_metrics(platform_responses, queries),
            "sentiment": calculate_sentiment_metrics(platform_responses),
        }

    return platforms


def analyze_descriptors(responses: List[Any]) -> Dict[str, int]:
    """
    Count occurrences of descriptors in responses where brand is directly mentioned.

    FILTERS APPLIED:
    - Only counts direct mentions (brand_mentioned == 'Yes')
    - NO brand_in_query filtering (descriptors apply to all mentions)

    Rationale: Descriptors are typically associated with direct brand mentions
    where the descriptor can be clearly attributed to the brand.

    Args:
        responses: List of Response objects

    Returns:
        Dict mapping descriptor -> count
    """
    descriptor_counts = Counter()

    for response in responses:
        # Only count descriptors from responses where brand is directly mentioned
        if response.brand_mentioned == "Yes" and hasattr(response, 'descriptors') and response.descriptors:
            # Descriptors are stored as comma-separated strings
            descriptors = [d.strip() for d in response.descriptors.split(',') if d.strip()]
            for descriptor in descriptors:
                descriptor_counts[descriptor] += 1

    return dict(descriptor_counts)


def calculate_descriptor_match_rate(responses: List[Any], descriptors: List[Any]) -> float:
    """
    Calculate percentage of target descriptors that appear in AI responses.

    FILTERS APPLIED:
    - Only counts direct mentions (brand_mentioned == 'Yes')
    - NO brand_in_query filtering

    This matches the 'Target Descriptor Adoption' metric on the dashboard.

    Args:
        responses: List of Response objects
        descriptors: List of TargetDescriptor objects with 'descriptor' and 'is_target' attributes

    Returns:
        Percentage of target descriptors found (0.0 to 100.0)
    """
    # Get only direct brand mentions
    brand_responses = [r for r in responses if r.brand_mentioned == "Yes"]
    if not brand_responses:
        return 0.0

    # Build set of target descriptor names (case-insensitive)
    target_descriptors_set = {td.descriptor.lower().strip() for td in descriptors if td.is_target}
    if not target_descriptors_set:
        return 0.0

    # Find which target descriptors actually appear in responses
    found_target_descriptors = set()
    for response in brand_responses:
        if response.descriptors and response.descriptors.strip():
            desc_list = [d.lower().strip() for d in response.descriptors.split(',') if d.strip()]
            for desc in desc_list:
                if desc in target_descriptors_set:
                    found_target_descriptors.add(desc)

    # Calculate percentage of target descriptors found
    return round((len(found_target_descriptors) / len(target_descriptors_set)) * 100, 1)


def analyze_competitors(responses: List[Any]) -> Dict[str, int]:
    """
    Count occurrences of competitors in all responses.

    FILTERS APPLIED:
    - None (counts all competitor mentions across all responses)

    Args:
        responses: List of Response objects

    Returns:
        Dict mapping competitor name -> count
    """
    competitor_counts = Counter()

    for response in responses:
        if response.competitors:
            # Competitors are stored as comma-separated strings
            competitors = [c.strip() for c in response.competitors.split(',') if c.strip()]
            for competitor in competitors:
                # Apply normalization for consistent grouping
                normalized_name = normalize_organization_name(competitor)
                competitor_counts[normalized_name] += 1

    return dict(competitor_counts)


def calculate_share_of_voice(
    responses: List[Any],
    queries: List[Any],
    competitors: List[Any],
    brand_name: str
) -> Dict[str, Any]:
    """
    Calculate share of voice for brand vs competitors.

    FILTERS APPLIED:
    - Excludes responses from queries where brand_in_query=True
    - Counts brand by POSITIONING (Leader, Top 3, Featured, Listed), not just 'Yes' mentions

    This provides a more accurate measure of brand visibility vs competitors.

    Args:
        responses: List of Response objects
        queries: List of Query objects
        competitors: List of Competitor objects (not currently used, kept for compatibility)
        brand_name: Name of the brand being analyzed

    Returns:
        Dict with brand_mentions, total_mentions, brand_sov, competitor_sov
    """
    # Build set of query_ids where brand_in_query=True to exclude
    branded_query_ids = {q.query_id for q in queries if q.brand_in_query}

    # Count total mentions across all organizations (excluding branded queries)
    total_mentions = 0
    brand_mentions = 0
    competitor_mentions = Counter()

    for response in responses:
        # Skip responses from queries where brand name is in the query
        if response.query_id in branded_query_ids:
            continue

        # Count brand mentions by positioning (not just "Yes")
        # This counts any response where brand appears in a meaningful position
        if response.brand_position in ['Leader', 'Top 3', 'Featured', 'Listed']:
            brand_mentions += 1
            total_mentions += 1

        # Count competitor mentions
        if response.competitors:
            comp_list = [c.strip() for c in response.competitors.split(',') if c.strip()]
            for comp in comp_list:
                # Apply normalization for consistent grouping
                normalized_name = normalize_organization_name(comp)
                competitor_mentions[normalized_name] += 1
                total_mentions += 1

    # Calculate brand share of voice
    brand_sov = round((brand_mentions / total_mentions) * 100, 1) if total_mentions > 0 else 0.0

    # Build competitor SOV data (top 5 by default for compatibility)
    competitor_sov = {}
    for comp_name, count in competitor_mentions.most_common(5):
        sov = round((count / total_mentions) * 100, 1) if total_mentions > 0 else 0.0
        competitor_sov[comp_name] = {"count": count, "sov": sov}

    return {
        "brand_mentions": brand_mentions,
        "total_mentions": total_mentions,
        "brand_sov": brand_sov,
        "competitor_sov": competitor_sov,
    }


def calculate_competitor_threats(
    competitor_sov: Dict[str, Dict[str, Any]],
    responses: List[Any],
    brand_name: str
) -> List[Dict[str, Any]]:
    """
    Calculate competitor threat scores using standardized formula.

    THREAT SCORE FORMULA:
    threatScore = (total_mentions * 0.7) + (negative_when_competitor_present * 2) + (positive_competitor * 1.5)

    THREAT LEVELS:
    - High: score > 50 (requires immediate strategic attention)
    - Medium: score 20-50 (requires monitoring)
    - Low: score < 20 (minimal competitive pressure)

    This is the SINGLE SOURCE OF TRUTH for threat calculations.
    Used by: Dashboard, Competitor Threats page, and Report generation.

    Args:
        competitor_sov: Dict from calculate_share_of_voice() with competitor SOV data
        responses: List of Response objects
        brand_name: Name of the brand being analyzed (not currently used)

    Returns:
        List of dicts sorted by threat_score (highest first), each containing:
        - name, mention_count, share_of_voice, competitive_responses,
          negative_overlap, positive_competitor, threat_score, threat_level
    """
    competitor_threats = []

    for comp_name, comp_data in competitor_sov.items():
        # Get all responses where this competitor is mentioned
        competitive_responses = [
            r for r in responses
            if r.competitors and comp_name.lower() in r.competitors.lower()
        ]

        # Count negative sentiment when competitor is present
        # This indicates the competitor is being mentioned in negative contexts
        negative_when_competitor_present = sum(
            1 for r in competitive_responses
            if r.sentiment in ['Negative', 'Very Negative']
        )

        # Count positive sentiment for competitor
        # This indicates the competitor is being recommended positively
        positive_competitor = sum(
            1 for r in competitive_responses
            if r.sentiment in ['Positive', 'Very Positive']
        )

        # Calculate threat score using standardized formula
        mention_count = comp_data.get('count', 0)
        threat_score = (
            (mention_count * THREAT_WEIGHTS["mention_weight"]) +
            (negative_when_competitor_present * THREAT_WEIGHTS["negative_weight"]) +
            (positive_competitor * THREAT_WEIGHTS["positive_weight"])
        )
        threat_score = round(threat_score)

        # Determine threat level based on thresholds
        if threat_score > THREAT_THRESHOLDS["high"]:
            threat_level = 'High'
        elif threat_score > THREAT_THRESHOLDS["medium"]:
            threat_level = 'Medium'
        else:
            threat_level = 'Low'

        competitor_threats.append({
            'name': comp_name,
            'mention_count': mention_count,
            'share_of_voice': comp_data.get('sov', 0.0),
            'competitive_responses': len(competitive_responses),
            'negative_overlap': negative_when_competitor_present,
            'positive_competitor': positive_competitor,
            'threat_score': threat_score,
            'threat_level': threat_level
        })

    # Sort by threat score (highest first)
    competitor_threats.sort(key=lambda x: x['threat_score'], reverse=True)

    return competitor_threats


def get_negative_sentiment_statements(responses: List[Any]) -> List[Dict[str, str]]:
    """
    Extract responses with negative or mixed sentiment about the brand.

    Used for detailed analysis and reporting.

    Args:
        responses: List of Response objects

    Returns:
        List of dicts with query, platform, sentiment, and response text
    """
    negative_responses = [
        r for r in responses
        if r.brand_mentioned in ["Yes", "Indirect"]
        and r.sentiment in ["Negative", "Mixed"]
    ]

    return [
        {
            "query": r.query_text,
            "platform": r.platform,
            "sentiment": r.sentiment,
            "response": r.response_text[:500] + "..." if len(r.response_text) > 500 else r.response_text
        }
        for r in negative_responses[:10]  # Limit to top 10
    ]
