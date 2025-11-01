"""
Utility functions for query processing.
"""
import re
from typing import Optional
from sqlalchemy.orm import Session
from .. import models


def detect_brand_in_query(query_text: str, brand_name: str) -> bool:
    """
    Automatically detect if the exact brand name is mentioned in a query text.

    Uses case-insensitive matching for EXACT brand name only.
    Examples:
    - Brand: "Physics of Plasmas"
      - Matches: "Tell me about Physics of Plasmas"
      - Does NOT match: "Tell me about Physics" or "What is PoP?"

    Args:
        query_text: The query text to check
        brand_name: The exact brand name to search for

    Returns:
        True if the exact brand name is found in the query, False otherwise
    """
    if not query_text or not brand_name:
        return False

    # Normalize both strings for comparison
    query_lower = query_text.lower().strip()
    brand_lower = brand_name.lower().strip()

    # Check for exact brand name match only (case-insensitive)
    # Use word boundaries to ensure complete match
    pattern = r'\b' + re.escape(brand_lower) + r'\b'
    return bool(re.search(pattern, query_lower))


def auto_set_brand_in_query_flag(
    query_text: str,
    db: Session,
    user_id: int,
    brand_id: Optional[int] = None
) -> bool:
    """
    Automatically determine if brand_in_query flag should be set based on query text.

    Args:
        query_text: The query text to analyze
        db: Database session
        user_id: User ID to get brand info for
        brand_id: Optional specific brand ID; if None, uses active brand

    Returns:
        True if brand name is detected in query, False otherwise
    """
    # Get brand info
    brand_query = db.query(models.BrandInfo).filter(
        models.BrandInfo.user_id == user_id
    )

    if brand_id:
        brand_query = brand_query.filter(models.BrandInfo.id == brand_id)
    else:
        # Get active brand
        brand_query = brand_query.filter(models.BrandInfo.is_active == True)

    brand = brand_query.first()

    if not brand or not brand.brand_name:
        return False

    return detect_brand_in_query(query_text, brand.brand_name)
