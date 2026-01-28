"""
Centralized Brand Access Control Utilities

This module provides standardized helper functions for brand access validation
across all routers. It ensures consistent security checks for:
- Brand ownership validation (only owner can perform certain actions)
- Brand access validation (owner OR shared users can access)
- Data owner resolution (for shared brands, fetch owner's data)

IMPORTANT: All routers should use these helpers instead of implementing
their own brand access logic to ensure consistent security.
"""
from typing import Optional
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session

from .. import models, crud
from ..auth import get_current_user
from ..database import get_db


# ==================== DEPENDENCY FUNCTIONS ====================

def get_active_brand_id(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Optional[int]:
    """
    FastAPI dependency to get the active brand_id for the current user.

    This is the SINGLE SOURCE OF TRUTH for getting the active brand.
    Returns None if no active brand exists (allows multi-brand view).

    Usage in router endpoints:
        @router.get("/endpoint")
        async def my_endpoint(
            brand_id: Optional[int] = Depends(get_active_brand_id),
            ...
        ):

    Returns:
        Optional[int]: Active brand ID, or None if no active brand
    """
    # Get the active brand for the CURRENT USER ONLY
    active_brand = crud.get_active_brand(db, user_id=current_user.id)
    return active_brand.id if active_brand else None


# ==================== VALIDATION FUNCTIONS ====================

def get_user_brand_or_404(
    db: Session,
    brand_id: int,
    user_id: int
) -> models.BrandInfo:
    """
    Get a brand that the user has access to (owns OR has shared).

    Raises HTTPException(404) if:
    - Brand doesn't exist
    - User doesn't own the brand
    - Brand is not shared with the user

    Use this for: Endpoints where both owners and shared users can access
    (e.g., viewing analytics, reading data)

    Args:
        db: Database session
        brand_id: Brand ID to validate
        user_id: User ID to check access for

    Returns:
        models.BrandInfo: The brand object if user has access

    Raises:
        HTTPException: 404 if brand not found or user has no access
    """
    # First check if user has access (owns OR shared)
    if not crud.user_has_brand_access(db, brand_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found or you don't have access"
        )

    # Get the brand object
    brand = db.query(models.BrandInfo).filter(
        models.BrandInfo.id == brand_id
    ).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )

    return brand


def get_user_owned_brand_or_403(
    db: Session,
    brand_id: int,
    user_id: int
) -> models.BrandInfo:
    """
    Get a brand that the user OWNS (not shared).

    Raises HTTPException(403) if user doesn't own the brand.
    Use this for: Owner-only operations (e.g., deleting brand, sharing, updating settings)

    Args:
        db: Database session
        brand_id: Brand ID to validate
        user_id: User ID to check ownership for

    Returns:
        models.BrandInfo: The brand object if user owns it

    Raises:
        HTTPException: 403 if user doesn't own the brand
    """
    brand = db.query(models.BrandInfo).filter(
        models.BrandInfo.id == brand_id,
        models.BrandInfo.user_id == user_id
    ).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the brand owner can perform this action"
        )

    return brand


def validate_brand_access_optional(
    db: Session,
    brand_id: Optional[int],
    user_id: int
) -> Optional[int]:
    """
    Validate brand access if brand_id is provided, allow None.

    Use this for: Endpoints that accept optional brand_id parameter
    (e.g., list endpoints that can show all brands or filter by one)

    Args:
        db: Database session
        brand_id: Optional brand ID to validate
        user_id: User ID to check access for

    Returns:
        Optional[int]: The brand_id if valid, None if brand_id was None

    Raises:
        HTTPException: 404 if brand_id provided but user has no access
    """
    if brand_id is None:
        return None

    # Validate user has access to this brand
    if not crud.user_has_brand_access(db, brand_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found or you don't have access"
        )

    return brand_id


# ==================== DATA OWNER RESOLUTION ====================

def get_data_owner_user_id(
    db: Session,
    brand_id: Optional[int],
    current_user_id: int
) -> int:
    """
    Get the user_id whose data should be queried.

    This is critical for shared brand support:
    - For shared brands: Returns the brand OWNER's user_id (so shared users see owner's data)
    - For owned brands: Returns the current user's user_id
    - For no brand (None): Returns the current user's user_id

    Also validates that the current user has access to the brand.

    Use this for: Any endpoint that queries Response, Query, Competitor, etc.
    data that should show the brand owner's data when brand is shared.

    Args:
        db: Database session
        brand_id: Optional brand ID
        current_user_id: Current authenticated user's ID

    Returns:
        int: The user_id to use for data queries

    Raises:
        HTTPException: 404 if brand_id provided but user has no access
    """
    if brand_id is None:
        return current_user_id

    # Validate user has access to this brand (security check)
    if not crud.user_has_brand_access(db, brand_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found or you don't have access"
        )

    # Get the brand owner's user_id
    brand = db.query(models.BrandInfo).filter(
        models.BrandInfo.id == brand_id
    ).first()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found"
        )

    return brand.user_id


# ==================== CONVENIENCE FUNCTIONS ====================

def require_brand_access(
    db: Session,
    brand_id: Optional[int],
    user_id: int,
    require_ownership: bool = False
) -> Optional[models.BrandInfo]:
    """
    Flexible brand access validation with multiple modes.

    Args:
        db: Database session
        brand_id: Optional brand ID to validate
        user_id: User ID to check access for
        require_ownership: If True, user must OWN the brand (not just have access)

    Returns:
        Optional[models.BrandInfo]: Brand object if brand_id provided and valid, None if brand_id is None

    Raises:
        HTTPException: 404 (no access) or 403 (not owner) depending on require_ownership
    """
    if brand_id is None:
        return None

    if require_ownership:
        return get_user_owned_brand_or_403(db, brand_id, user_id)
    else:
        return get_user_brand_or_404(db, brand_id, user_id)
