"""
Utility functions for query processing.
"""
import re
from typing import Optional
from sqlalchemy.orm import Session
from .. import models


def detect_brand_in_query(query_text: str, brand_name: str) -> bool:
    """
    Automatically detect if a brand name is mentioned in a query text.

    Uses case-insensitive matching and handles common variations like:
    - Direct mentions: "Tell me about [Brand]"
    - Questions: "What is [Brand]?"
    - Comparisons: "How does [Brand] compare to..."

    Args:
        query_text: The query text to check
        brand_name: The brand name to search for

    Returns:
        True if the brand name is found in the query, False otherwise
    """
    if not query_text or not brand_name:
        return False

    # Normalize both strings for comparison
    query_lower = query_text.lower().strip()
    brand_lower = brand_name.lower().strip()

    # Check for exact brand name match (case-insensitive)
    # Use word boundaries to avoid partial matches
    # e.g., "Princeton" should match "Princeton Plasma Physics Laboratory"
    # but not match if it's part of another word

    # For multi-word brand names, check if the full name or significant parts appear
    brand_words = brand_lower.split()

    # If brand name has multiple words, check for the full phrase
    if len(brand_words) > 1:
        # Use word boundary regex for full brand name
        pattern = r'\b' + re.escape(brand_lower) + r'\b'
        if re.search(pattern, query_lower):
            return True

        # Also check for significant partial matches (e.g., acronyms or key words)
        # For "Princeton Plasma Physics Laboratory", match "PPPL" or "Princeton"
        # Get potential acronym
        acronym = ''.join([word[0] for word in brand_words if len(word) > 0])
        if len(acronym) >= 2:
            acronym_pattern = r'\b' + re.escape(acronym.lower()) + r'\b'
            if re.search(acronym_pattern, query_lower):
                return True

        # Check for first significant word (usually organization name)
        # Skip common words like "the", "a", "of"
        skip_words = {'the', 'a', 'an', 'of', 'and', 'for', 'to', 'in', 'on', 'at'}
        for word in brand_words:
            if word not in skip_words and len(word) > 2:
                word_pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(word_pattern, query_lower):
                    return True
                break  # Only check first significant word
    else:
        # Single word brand name - simple word boundary check
        pattern = r'\b' + re.escape(brand_lower) + r'\b'
        if re.search(pattern, query_lower):
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
