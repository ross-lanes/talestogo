from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
import logging

from app import crud, models, schemas

logger = logging.getLogger(__name__)
from app.database import SessionLocal
from app.auth import get_current_user
from app.utils.brand_access import (
    get_active_brand_id,
    get_user_brand_or_404,
    get_user_owned_brand_or_403
)


def get_db():
    """
    Dependency function that provides a database session per request.
    Ensures the session is always closed, even if errors occur.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create routers for modern and legacy endpoints
router_brands = APIRouter(prefix="/brands", tags=["Brands"])
router_brand_info = APIRouter(prefix="/brand-info", tags=["Brand Info"])


# ==================== MODERN BRAND MANAGEMENT ENDPOINTS ====================

@router_brands.get("/", response_model=List[schemas.BrandInfoList])
def get_all_brands_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all brands for the current user."""
    return crud.get_all_brands(db, user_id=current_user.id)


@router_brands.get("/active", response_model=schemas.BrandInfo)
def get_active_brand_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the currently active brand for the user."""
    brand = crud.get_active_brand(db, user_id=current_user.id)
    if not brand:
        raise HTTPException(status_code=404, detail="No active brand found. Please create a brand first.")
    return brand


@router_brands.get("/{brand_id}", response_model=schemas.BrandInfo)
def get_brand_endpoint(
    brand_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific brand by ID."""
    brand = crud.get_brand_by_id(db, brand_id=brand_id, user_id=current_user.id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router_brands.post("/", response_model=schemas.BrandInfo, status_code=201)
def create_brand_endpoint(
    brand_info: schemas.BrandInfoCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new brand (max 20 per user)."""
    try:
        return crud.create_brand_info(db, brand_info=brand_info, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_brands.put("/{brand_id}", response_model=schemas.BrandInfo)
def update_brand_endpoint(
    brand_id: int,
    brand_info: schemas.BrandInfoUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a specific brand."""
    updated_brand = crud.update_brand_info(db, brand_id=brand_id, brand_info_update=brand_info, user_id=current_user.id)
    if not updated_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return updated_brand


@router_brands.post("/{brand_id}/activate", response_model=schemas.BrandInfo)
def activate_brand_endpoint(
    brand_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set a brand as active (deactivates all other brands)."""
    brand = crud.activate_brand(db, brand_id=brand_id, user_id=current_user.id)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router_brands.delete("/{brand_id}", response_model=schemas.BrandInfo)
def delete_brand_endpoint(
    brand_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently delete a brand and all associated data.

    ADMIN ONLY: only users with is_admin=true can permanently delete brands.
    Regular users should use POST /brands/{brand_id}/remove to transfer to an
    admin instead.

    WARNING: This permanently deletes all data with no recovery option.
    """
    # Restrict hard delete to admin only
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only admins can permanently delete brands. Use POST /brands/{brand_id}/remove to remove from your account (data will be preserved)."
        )

    deleted_brand = crud.delete_brand_info(db, brand_id=brand_id, user_id=current_user.id, admin_override=True)
    if not deleted_brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return deleted_brand


# ==================== BRAND SHARING ENDPOINTS ====================

@router_brands.post("/{brand_id}/share", response_model=schemas.BrandShare, status_code=201)
def share_brand_endpoint(
    brand_id: int,
    share_data: schemas.BrandShareCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Share a brand with another user by email."""
    # Verify the current user has access to this brand (owns it or has it shared)
    brand = get_user_brand_or_404(db, brand_id, current_user.id)

    # Find the user to share with by email
    user_to_share_with = db.query(models.User).filter(models.User.email == share_data.email).first()

    if not user_to_share_with:
        raise HTTPException(status_code=404, detail=f"No user found with email {share_data.email}. User must have a TALES account.")

    if user_to_share_with.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot share a brand with yourself")

    # Ensure both users are in the same tenant
    if current_user.tenant_id and user_to_share_with.tenant_id:
        if current_user.tenant_id != user_to_share_with.tenant_id:
            raise HTTPException(status_code=403, detail="You can only share brands with users in your organization")

    # Check if already shared with this user
    existing_share = db.query(models.BrandShare).filter(
        models.BrandShare.brand_id == brand_id,
        models.BrandShare.user_id == user_to_share_with.id
    ).first()

    if existing_share:
        logger.info(f"Brand {brand_id} is already shared with user {user_to_share_with.id} (share id: {existing_share.id})")
        raise HTTPException(status_code=400, detail=f"Brand is already shared with {share_data.email}")

    # Create the share with error handling for race conditions
    try:
        new_share = models.BrandShare(
            brand_id=brand_id,
            user_id=user_to_share_with.id,
            shared_by_user_id=current_user.id,
            permission_level='edit'
        )
        db.add(new_share)
        db.commit()
        db.refresh(new_share)
        logger.info(f"Successfully shared brand {brand_id} with user {user_to_share_with.id} (share id: {new_share.id})")
        return new_share
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError sharing brand {brand_id} with user {user_to_share_with.id}: {str(e)}")
        # Check if the error is due to a unique constraint (brand already shared)
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Brand is already shared with {share_data.email}")
        # Re-raise for other integrity errors
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router_brands.get("/{brand_id}/shares", response_model=List[schemas.BrandShareWithUser])
def get_brand_shares_endpoint(
    brand_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users this brand is shared with."""
    # Verify user has access to this brand
    get_user_brand_or_404(db, brand_id, current_user.id)

    # Get all shares with user details
    shares = db.query(models.BrandShare).filter(
        models.BrandShare.brand_id == brand_id
    ).all()

    # Build response with user details
    result = []
    for share in shares:
        user = db.query(models.User).filter(models.User.id == share.user_id).first()
        shared_by = db.query(models.User).filter(models.User.id == share.shared_by_user_id).first()

        result.append(schemas.BrandShareWithUser(
            id=share.id,
            brand_id=share.brand_id,
            user_id=share.user_id,
            user_email=user.email if user else "Unknown",
            user_full_name=user.full_name if user else None,
            shared_by_user_id=share.shared_by_user_id,
            shared_by_email=shared_by.email if shared_by else "Unknown",
            permission_level=share.permission_level,
            created_at=share.created_at
        ))

    return result


@router_brands.delete("/{brand_id}/shares/{share_id}")
def remove_brand_share_endpoint(
    brand_id: int,
    share_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a brand share (unshare with a user). Only the brand owner can remove shares."""
    # Verify user OWNS this brand (not just has access)
    get_user_owned_brand_or_403(db, brand_id, current_user.id)

    # Find and delete the share
    share = db.query(models.BrandShare).filter(
        models.BrandShare.id == share_id,
        models.BrandShare.brand_id == brand_id
    ).first()

    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    db.delete(share)
    db.commit()

    return {"message": "Share removed successfully"}


# ==================== BRAND TRANSFER ENDPOINTS ====================

@router_brands.post("/{brand_id}/transfer", response_model=schemas.BrandTransferResponse)
def transfer_brand_endpoint(
    brand_id: int,
    transfer_request: schemas.BrandTransferRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Transfer brand ownership to another user.

    Only the brand owner can transfer. This operation:
    - Transfers brand ownership to the specified user
    - Transfers all associated data (queries, responses, etc.)
    - Removes the brand from current owner's view
    - Sets brand as inactive for new owner (they must activate it)
    """
    # Verify user OWNS this brand (not just has access)
    brand = get_user_owned_brand_or_403(db, brand_id, current_user.id)

    # Find the user to transfer to by email
    new_owner = db.query(models.User).filter(models.User.email == transfer_request.email).first()

    if not new_owner:
        raise HTTPException(
            status_code=404,
            detail=f"No user found with email {transfer_request.email}. User must have a TALES account."
        )

    if new_owner.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot transfer a brand to yourself")

    # Ensure both users are in the same tenant (if applicable)
    if current_user.tenant_id and new_owner.tenant_id:
        if current_user.tenant_id != new_owner.tenant_id:
            raise HTTPException(
                status_code=403,
                detail="You can only transfer brands to users in your organization"
            )

    # Perform the transfer
    transferred_brand = crud.transfer_brand_ownership(
        db,
        brand_id=brand_id,
        current_owner_id=current_user.id,
        new_owner_id=new_owner.id
    )

    if not transferred_brand:
        raise HTTPException(status_code=500, detail="Failed to transfer brand")

    return schemas.BrandTransferResponse(
        message=f"Brand '{brand.brand_name}' successfully transferred to {new_owner.email}",
        brand_id=brand_id,
        brand_name=brand.brand_name,
        new_owner_email=new_owner.email,
        new_owner_full_name=new_owner.full_name
    )


@router_brands.post("/{brand_id}/remove", response_model=schemas.BrandTransferResponse)
def remove_brand_endpoint(
    brand_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove brand from your account by transferring it to an admin.

    This preserves all data by transferring ownership to an admin user.
    Only the brand owner can remove. You will no longer see this brand.
    """
    # Verify user OWNS this brand (not just has access)
    brand = get_user_owned_brand_or_403(db, brand_id, current_user.id)

    # Prevent admins from removing brands (admins can only hard delete)
    if current_user.is_admin:
        raise HTTPException(
            status_code=400,
            detail="Admin cannot remove brands. Use delete endpoint instead."
        )

    # Find an admin user to transfer ownership to (prefer the oldest admin
    # account for stability)
    admin = (
        db.query(models.User)
        .filter(models.User.is_admin == True, models.User.is_active == True)
        .order_by(models.User.id.asc())
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=500,
            detail="No active admin user found. Cannot remove brand."
        )

    # Transfer to admin
    transferred_brand = crud.transfer_brand_ownership(
        db,
        brand_id=brand_id,
        current_owner_id=current_user.id,
        new_owner_id=admin.id
    )

    if not transferred_brand:
        raise HTTPException(status_code=500, detail="Failed to remove brand")

    return schemas.BrandTransferResponse(
        message=f"Brand '{brand.brand_name}' removed from your account. Data preserved for admin.",
        brand_id=brand_id,
        brand_name=brand.brand_name,
        new_owner_email=admin.email,
        new_owner_full_name=admin.full_name
    )


# ==================== LEGACY ENDPOINTS FOR BACKWARD COMPATIBILITY ====================

@router_brand_info.get("/", response_model=schemas.BrandInfo)
def get_brand_info_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active brand info (legacy endpoint - use /brands/active instead)."""
    brand_info = crud.get_active_brand(db, user_id=current_user.id)
    if not brand_info:
        raise HTTPException(status_code=404, detail="Brand info not found. Please create it first.")
    return brand_info


@router_brand_info.post("/", response_model=schemas.BrandInfo, status_code=201)
def create_brand_info_endpoint(
    brand_info: schemas.BrandInfoCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create brand info (legacy endpoint - use /brands/ instead)."""
    try:
        return crud.create_brand_info(db, brand_info=brand_info, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_brand_info.put("/", response_model=schemas.BrandInfo)
def update_brand_info_endpoint(
    brand_info: schemas.BrandInfoUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update active brand info (legacy endpoint)."""
    active_brand = crud.get_active_brand(db, user_id=current_user.id)
    if not active_brand:
        raise HTTPException(status_code=404, detail="No active brand found")
    updated_brand = crud.update_brand_info(db, brand_id=active_brand.id, brand_info_update=brand_info, user_id=current_user.id)
    if not updated_brand:
        raise HTTPException(status_code=404, detail="Brand info not found")
    return updated_brand


@router_brand_info.delete("/", response_model=schemas.BrandInfo)
def delete_brand_info_endpoint(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete active brand info (legacy endpoint - ADMIN ONLY).

    Only users with is_admin=true can permanently delete brands.
    Regular users should use POST /brands/{brand_id}/remove instead.
    """
    # Restrict hard delete to admin only
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Only admins can permanently delete brands. Use POST /brands/{brand_id}/remove to remove from your account (data will be preserved)."
        )

    active_brand = crud.get_active_brand(db, user_id=current_user.id)
    if not active_brand:
        raise HTTPException(status_code=404, detail="No active brand found")
    deleted_brand = crud.delete_brand_info(db, brand_id=active_brand.id, user_id=current_user.id, admin_override=True)
    if not deleted_brand:
        raise HTTPException(status_code=404, detail="Brand info not found")
    return deleted_brand


@router_brand_info.post("/generate")
def generate_content_from_brand_info(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    brand_id: Optional[int] = Depends(get_active_brand_id)
):
    """
    Generate queries, descriptors, and competitors based on active brand info using AI.
    This will replace any existing queries, descriptors, and competitors for the active brand.
    """
    from app.ai_generator import AIGenerator

    if not brand_id:
        raise HTTPException(status_code=400, detail="No active brand found. Please select a brand first.")

    try:
        generator = AIGenerator(db)
        result = generator.generate_all(user_id=current_user.id, brand_id=brand_id)
        return {
            "message": "Content generated successfully",
            "queries_created": result["queries_created"],
            "descriptors_created": result["descriptors_created"],
            "competitors_created": result["competitors_created"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")
