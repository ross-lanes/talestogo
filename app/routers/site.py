"""
Site Configuration Router
Public endpoints for site branding and configuration.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services.site_config import get_branding_config

router = APIRouter(
    prefix="/site",
    tags=["Site Configuration"]
)


@router.get("/branding", response_model=schemas.BrandingConfig)
def get_site_branding(db: Session = Depends(get_db)):
    """
    Return site branding configuration for the frontend.
    This endpoint is public (no authentication required).
    Labs can configure branding via environment variables or admin UI.
    """
    config = get_branding_config(db)
    return schemas.BrandingConfig(**config)
