"""
Utility functions for query processing.
"""
import re
from typing import Optional
from sqlalchemy.orm import Session
from .. import models


def detect_brand_in_query(query_text: str, brand_name: str) -> bool:
    """
    Automatically detect if the exact brand name or its acronym is mentioned in a query text.

    Uses case-insensitive matching for:
    1. Exact brand name
    2. Acronym (first letter of each significant word)

    Examples:
    - Brand: "Physics of Plasmas"
      - Matches: "Tell me about Physics of Plasmas" (exact match)
      - Matches: "What is PoP?" (acronym match)
      - Does NOT match: "Tell me about Physics" (partial word)

    Args:
        query_text: The query text to check
        brand_name: The exact brand name to search for

    Returns:
        True if the exact brand name or acronym is found in the query, False otherwise
    """
    if not query_text or not brand_name:
        return False

    # Normalize both strings for comparison
    query_lower = query_text.lower().strip()
    brand_lower = brand_name.lower().strip()

    # Check for exact brand name match (case-insensitive)
    pattern = r'\b' + re.escape(brand_lower) + r'\b'
    if re.search(pattern, query_lower):
        return True

    # Check for acronym match (for multi-word brand names)
    brand_words = brand_lower.split()
    if len(brand_words) > 1:
        # Skip common words when building acronym
        skip_words = {'the', 'a', 'an', 'of', 'and', 'for', 'to', 'in', 'on', 'at'}
        acronym = ''.join([word[0] for word in brand_words if word not in skip_words and len(word) > 0])

        if len(acronym) >= 2:
            acronym_pattern = r'\b' + re.escape(acronym.lower()) + r'\b'
            if re.search(acronym_pattern, query_lower):
                return True

    return False


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
