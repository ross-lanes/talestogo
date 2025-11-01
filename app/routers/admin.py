"""
Admin API endpoints for managing all users' data.

Only accessible to admin users (is_admin=True).
Allows admins to view and manage all brands, queries, descriptors, and competitors
across all users for support and troubleshooting purposes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import crud, models, schemas
from ..auth import get_current_admin_user
from ..database import get_db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin_user)]  # Require admin for all endpoints
)


# === User Management ===

@router.get("/users", response_model=List[schemas.User])
def get_all_users(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all users in the system."""
    users = db.query(models.User).all()
    return users


@router.get("/users/{user_id}", response_model=schemas.User)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get a specific user by ID."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# === Brand Management ===

@router.get("/brands", response_model=List[schemas.BrandInfo])
def get_all_brands(
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all brands across all users."""
    brands = db.query(models.BrandInfo).all()
    return brands


@router.get("/users/{user_id}/brands", response_model=List[schemas.BrandInfo])
def get_user_brands(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all brands for a specific user."""
    brands = db.query(models.BrandInfo).filter(
        models.BrandInfo.user_id == user_id
    ).all()
    return brands


@router.get("/brands/{brand_id}", response_model=schemas.BrandInfo)
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get a specific brand by ID."""
    brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.put("/brands/{brand_id}", response_model=schemas.BrandInfo)
def update_brand(
    brand_id: int,
    brand_update: schemas.BrandInfoUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Update a brand (admin can modify any user's brand)."""
    brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    update_data = brand_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)

    db.commit()
    db.refresh(brand)
    return brand


# === Query Management ===

@router.get("/users/{user_id}/brands/{brand_id}/queries", response_model=List[schemas.Query])
def get_user_brand_queries(
    user_id: int,
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all queries for a specific user and brand."""
    queries = crud.get_queries(db, user_id=user_id, brand_id=brand_id, limit=1000)
    return queries


@router.post("/users/{user_id}/brands/{brand_id}/queries", response_model=schemas.Query)
def create_query_for_user(
    user_id: int,
    brand_id: int,
    query: schemas.QueryCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Create a query for a specific user and brand."""
    return crud.create_query(db, query=query, user_id=user_id, brand_id=brand_id)


@router.put("/users/{user_id}/brands/{brand_id}/queries/{query_id}", response_model=schemas.Query)
def update_user_query(
    user_id: int,
    brand_id: int,
    query_id: str,
    query_update: schemas.QueryUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Update a query for a specific user and brand."""
    updated_query = crud.update_query(
        db, query_id=query_id, query_update=query_update,
        user_id=user_id, brand_id=brand_id
    )
    if not updated_query:
        raise HTTPException(status_code=404, detail="Query not found")
    return updated_query


@router.delete("/users/{user_id}/brands/{brand_id}/queries/{query_id}")
def delete_user_query(
    user_id: int,
    brand_id: int,
    query_id: str,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Delete a query for a specific user and brand."""
    deleted = crud.delete_query(db, query_id=query_id, user_id=user_id, brand_id=brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Query not found")
    return {"message": "Query deleted successfully"}


# === Descriptor Management ===

@router.get("/users/{user_id}/brands/{brand_id}/descriptors", response_model=List[schemas.TargetDescriptor])
def get_user_brand_descriptors(
    user_id: int,
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all descriptors for a specific user and brand."""
    descriptors = crud.get_target_descriptors(db, user_id=user_id, brand_id=brand_id, limit=1000)
    return descriptors


@router.post("/users/{user_id}/brands/{brand_id}/descriptors", response_model=schemas.TargetDescriptor)
def create_descriptor_for_user(
    user_id: int,
    brand_id: int,
    descriptor: schemas.TargetDescriptorCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Create a descriptor for a specific user and brand."""
    return crud.create_target_descriptor(db, descriptor=descriptor, user_id=user_id, brand_id=brand_id)


@router.put("/users/{user_id}/brands/{brand_id}/descriptors/{descriptor_id}", response_model=schemas.TargetDescriptor)
def update_user_descriptor(
    user_id: int,
    brand_id: int,
    descriptor_id: int,
    descriptor_update: schemas.TargetDescriptorUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Update a descriptor for a specific user and brand."""
    updated = crud.update_target_descriptor(
        db, descriptor_id=descriptor_id, descriptor_update=descriptor_update,
        user_id=user_id, brand_id=brand_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return updated


@router.delete("/users/{user_id}/brands/{brand_id}/descriptors/{descriptor_id}")
def delete_user_descriptor(
    user_id: int,
    brand_id: int,
    descriptor_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Delete a descriptor for a specific user and brand."""
    deleted = crud.delete_target_descriptor(db, descriptor_id=descriptor_id, user_id=user_id, brand_id=brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Descriptor not found")
    return {"message": "Descriptor deleted successfully"}


# === Competitor Management ===

@router.get("/users/{user_id}/brands/{brand_id}/competitors", response_model=List[schemas.Competitor])
def get_user_brand_competitors(
    user_id: int,
    brand_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Get all competitors for a specific user and brand."""
    competitors = crud.get_competitors(db, user_id=user_id, brand_id=brand_id, limit=1000)
    return competitors


@router.post("/users/{user_id}/brands/{brand_id}/competitors", response_model=schemas.Competitor)
def create_competitor_for_user(
    user_id: int,
    brand_id: int,
    competitor: schemas.CompetitorCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Create a competitor for a specific user and brand."""
    return crud.create_competitor(db, competitor=competitor, user_id=user_id, brand_id=brand_id)


@router.put("/users/{user_id}/brands/{brand_id}/competitors/{competitor_id}", response_model=schemas.Competitor)
def update_user_competitor(
    user_id: int,
    brand_id: int,
    competitor_id: int,
    competitor_update: schemas.CompetitorUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Update a competitor for a specific user and brand."""
    updated = crud.update_competitor(
        db, competitor_id=competitor_id, competitor_update=competitor_update,
        user_id=user_id, brand_id=brand_id
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return updated


@router.delete("/users/{user_id}/brands/{brand_id}/competitors/{competitor_id}")
def delete_user_competitor(
    user_id: int,
    brand_id: int,
    competitor_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin_user)
):
    """Delete a competitor for a specific user and brand."""
    deleted = crud.delete_competitor(db, competitor_id=competitor_id, user_id=user_id, brand_id=brand_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"message": "Competitor deleted successfully"}
