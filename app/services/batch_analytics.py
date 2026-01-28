"""
Batch Analytics Caching Service

Computes and caches analytics for collection batches to avoid
reprocessing responses when generating reports or viewing trends.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, Dict, Any
import json
import datetime
from .. import models
from .metrics import normalize_organization_name


def compute_batch_analytics(
    db: Session,
    batch_id: int,
    user_id: int,
    brand_id: int
) -> Optional[models.BatchAnalytics]:
    """
    Compute analytics for a specific batch and cache them in batch_analytics table.

    Args:
        db: Database session
        batch_id: ID of the collection batch
        user_id: User ID (for data isolation)
        brand_id: Brand ID

    Returns:
        BatchAnalytics model instance or None if no responses found
    """
    # Get the batch to get the collection date
    batch = db.query(models.CollectionBatch).filter(
        models.CollectionBatch.id == batch_id,
        models.CollectionBatch.user_id == user_id,
        models.CollectionBatch.brand_id == brand_id
    ).first()

    if not batch:
        return None

    # Get all responses for this batch
    responses = db.query(models.Response).filter(
        models.Response.batch_id == batch_id,
        models.Response.user_id == user_id,
        models.Response.brand_id == brand_id
    ).all()

    if not responses:
        return None

    # Build a set of query_ids where brand_in_query=False (organic queries)
    # This is used for Share of Voice calculation to match AnalyticsCache behavior
    organic_query_ids = set()
    queries = db.query(models.Query).filter(
        models.Query.user_id == user_id,
        models.Query.brand_id == brand_id,
        models.Query.brand_in_query == False
    ).all()
    for q in queries:
        organic_query_ids.add(q.query_id)

    # Filter to only organic responses (brand_in_query=False) for brand mention metrics
    # This ensures we measure true organic brand visibility, not mentions when explicitly asked about the brand
    organic_responses = [r for r in responses if r.query_id in organic_query_ids]
    total_responses = len(organic_responses)

    # Initialize counters (all based on organic queries only)
    mention_count = 0
    leader_count = 0
    featured_count = 0
    listed_count = 0
    not_mentioned_count = 0

    # Sentiment counters (organic responses where brand is mentioned)
    very_positive_count = 0
    positive_count = 0
    neutral_count = 0
    negative_count = 0
    very_negative_count = 0
    mixed_count = 0

    # Share of voice data (only from organic queries)
    sov_counts: Dict[str, int] = {}

    # Descriptor usage
    descriptor_counts: Dict[str, int] = {}

    # Process only organic responses
    for response in organic_responses:
        # Brand mentions and positioning
        if response.brand_mentioned in ['Yes', 'Indirect']:
            mention_count += 1

            # Count positioning
            if response.brand_position == 'Leader':
                leader_count += 1
            elif response.brand_position == 'Featured':
                featured_count += 1
            elif response.brand_position == 'Listed':
                listed_count += 1
        else:
            not_mentioned_count += 1

        # Sentiment (only where brand is mentioned)
        if response.brand_mentioned == 'Yes':
            if response.sentiment == 'Very Positive':
                very_positive_count += 1
            elif response.sentiment == 'Positive':
                positive_count += 1
            elif response.sentiment == 'Neutral':
                neutral_count += 1
            elif response.sentiment == 'Negative':
                negative_count += 1
            elif response.sentiment == 'Very Negative':
                very_negative_count += 1
            elif response.sentiment == 'Mixed':
                mixed_count += 1

        # Share of voice - count competitor mentions from organic queries
        # where brand is mentioned (Yes or Indirect)
        # This matches AnalyticsCache._calculate_share_of_voice() behavior
        is_brand_mentioned = response.brand_mentioned in ['Yes', 'Indirect']
        if is_brand_mentioned and response.competitors:
            competitor_names = [c.strip() for c in response.competitors.split(',') if c.strip()]
            for comp in competitor_names:
                normalized = normalize_organization_name(comp)
                sov_counts[normalized] = sov_counts.get(normalized, 0) + 1

        # Descriptor usage (only where brand is mentioned)
        if response.brand_mentioned == 'Yes' and response.descriptors:
            descriptors = [d.strip() for d in response.descriptors.split(',') if d.strip()]
            for desc in descriptors:
                descriptor_counts[desc] = descriptor_counts.get(desc, 0) + 1

    # Calculate mention rate based on organic responses only
    mention_rate = round((mention_count / total_responses * 100)) if total_responses > 0 else 0

    # Check if analytics already exist for this batch
    existing = db.query(models.BatchAnalytics).filter(
        models.BatchAnalytics.batch_id == batch_id
    ).first()

    if existing:
        # Update existing record
        existing.collection_date = batch.started_at
        existing.total_responses = total_responses
        existing.mention_count = mention_count
        existing.mention_rate = mention_rate
        existing.leader_count = leader_count
        existing.featured_count = featured_count
        existing.listed_count = listed_count
        existing.not_mentioned_count = not_mentioned_count
        existing.very_positive_count = very_positive_count
        existing.positive_count = positive_count
        existing.neutral_count = neutral_count
        existing.negative_count = negative_count
        existing.very_negative_count = very_negative_count
        existing.mixed_count = mixed_count
        existing.sov_data = json.dumps(sov_counts) if sov_counts else None
        existing.descriptor_data = json.dumps(descriptor_counts) if descriptor_counts else None
        existing.updated_at = datetime.datetime.utcnow()

        db.commit()
        db.refresh(existing)
        return existing
    else:
        # Create new record
        analytics = models.BatchAnalytics(
            user_id=user_id,
            brand_id=brand_id,
            batch_id=batch_id,
            collection_date=batch.started_at,
            total_responses=total_responses,
            mention_count=mention_count,
            mention_rate=mention_rate,
            leader_count=leader_count,
            featured_count=featured_count,
            listed_count=listed_count,
            not_mentioned_count=not_mentioned_count,
            very_positive_count=very_positive_count,
            positive_count=positive_count,
            neutral_count=neutral_count,
            negative_count=negative_count,
            very_negative_count=very_negative_count,
            mixed_count=mixed_count,
            sov_data=json.dumps(sov_counts) if sov_counts else None,
            descriptor_data=json.dumps(descriptor_counts) if descriptor_counts else None
        )

        db.add(analytics)
        db.commit()
        db.refresh(analytics)
        return analytics


def get_or_compute_batch_analytics(
    db: Session,
    batch_id: int,
    user_id: int,
    brand_id: int,
    force_recompute: bool = False
) -> Optional[models.BatchAnalytics]:
    """
    Get cached batch analytics or compute them if they don't exist.

    Args:
        db: Database session
        batch_id: ID of the collection batch
        user_id: User ID
        brand_id: Brand ID
        force_recompute: If True, recompute even if cache exists

    Returns:
        BatchAnalytics instance or None
    """
    if not force_recompute:
        # Try to get existing cached analytics
        existing = db.query(models.BatchAnalytics).filter(
            models.BatchAnalytics.batch_id == batch_id,
            models.BatchAnalytics.user_id == user_id,
            models.BatchAnalytics.brand_id == brand_id
        ).first()

        if existing:
            return existing

    # Compute and cache
    return compute_batch_analytics(db, batch_id, user_id, brand_id)


def backfill_all_batch_analytics(
    db: Session,
    user_id: int,
    brand_id: int
) -> int:
    """
    Backfill analytics for all batches that don't have cached analytics.

    Args:
        db: Database session
        user_id: User ID
        brand_id: Brand ID

    Returns:
        Number of batches processed
    """
    # Get all batches for this user/brand
    batches = db.query(models.CollectionBatch).filter(
        models.CollectionBatch.user_id == user_id,
        models.CollectionBatch.brand_id == brand_id,
        models.CollectionBatch.status == 'completed'
    ).all()

    processed = 0
    for batch in batches:
        # Check if analytics already exist
        existing = db.query(models.BatchAnalytics).filter(
            models.BatchAnalytics.batch_id == batch.id
        ).first()

        if not existing:
            result = compute_batch_analytics(db, batch.id, user_id, brand_id)
            if result:
                processed += 1
                print(f"Cached analytics for batch {batch.id}: {batch.batch_name}")

    return processed
