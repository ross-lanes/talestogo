"""
Tenant Management Endpoints

Provides CRUD operations for managing tenants.
Only admins can create/update/delete tenants.
All users can view their own tenant info.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Tenant, User
from ..schemas import Tenant as TenantSchema, TenantCreate, TenantUpdate
from ..auth import get_current_user

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("/me", response_model=TenantSchema)
def get_my_tenant(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the current user's tenant information"""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not assigned to a tenant"
        )

    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant


@router.get("/", response_model=List[TenantSchema])
def list_tenants(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all tenants (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list all tenants"
        )

    tenants = db.query(Tenant).all()
    return tenants


@router.get("/{tenant_id}", response_model=TenantSchema)
def get_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific tenant by ID"""
    # Users can only view their own tenant, admins can view any
    if not current_user.is_admin and current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own tenant"
        )

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return tenant


@router.post("/", response_model=TenantSchema, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant: TenantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new tenant (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create tenants"
        )

    # Check if subdomain is already taken
    if tenant.subdomain:
        existing = db.query(Tenant).filter(Tenant.subdomain == tenant.subdomain).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subdomain '{tenant.subdomain}' is already taken"
            )

    db_tenant = Tenant(**tenant.model_dump())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)

    return db_tenant


@router.put("/{tenant_id}", response_model=TenantSchema)
def update_tenant(
    tenant_id: int,
    tenant_update: TenantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a tenant's information"""
    # Users can update their own tenant's branding, admins can update any
    if not current_user.is_admin and current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tenant"
        )

    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check if subdomain is being changed and if it's already taken
    if tenant_update.subdomain and tenant_update.subdomain != db_tenant.subdomain:
        existing = db.query(Tenant).filter(Tenant.subdomain == tenant_update.subdomain).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subdomain '{tenant_update.subdomain}' is already taken"
            )

    # Update fields
    update_data = tenant_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tenant, field, value)

    db.commit()
    db.refresh(db_tenant)

    return db_tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a tenant (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete tenants"
        )

    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # Check if tenant has users
    user_count = db.query(User).filter(User.tenant_id == tenant_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete tenant with {user_count} users. Reassign users first."
        )

    db.delete(db_tenant)
    db.commit()

    return None
