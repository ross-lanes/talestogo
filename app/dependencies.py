"""
Product Access Control Middleware

This module provides FastAPI dependencies for controlling product-level access
based on tenant configuration.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from .auth import get_current_user
from .models import User, Tenant
from .config import TenantConfig
from .database import get_db


def check_product_access(product: str):
    """
    Dependency factory to verify user's tenant has access to a product.

    Usage:
        @router.get("/some-endpoint", dependencies=[Depends(check_product_access("heads"))])

    Args:
        product: The product ID to check (e.g., "tales", "heads", "vision")

    Returns:
        A dependency function that validates product access

    Raises:
        HTTPException: 403 if tenant doesn't have access to the product
    """
    def _check(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Get user's tenant name
        tenant_name = None
        if current_user.tenant_id:
            tenant = db.query(Tenant).filter(
                Tenant.id == current_user.tenant_id
            ).first()
            tenant_name = tenant.tenant_name if tenant else None

        # Check if product is allowed for this tenant
        if not TenantConfig.is_product_enabled_for_tenant(
            tenant_name or "default",
            product
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Product '{product}' is not available for your organization"
            )

        return current_user

    return _check


def get_tenant_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> list[str]:
    """
    Dependency to get the list of products available to the current user's tenant.

    Usage:
        @router.get("/available-products")
        def get_products(products: list[str] = Depends(get_tenant_products)):
            return {"products": products}

    Returns:
        List of product IDs the user's tenant has access to
    """
    # Get user's tenant name
    tenant_name = None
    if current_user.tenant_id:
        tenant = db.query(Tenant).filter(
            Tenant.id == current_user.tenant_id
        ).first()
        tenant_name = tenant.tenant_name if tenant else None

    return TenantConfig.get_tenant_products(tenant_name or "default")
