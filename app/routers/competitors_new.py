"""
Competitors API Endpoints
CRUD and upload endpoints for managing competitors - using CRUD factory
"""
from .. import crud, models, schemas
from ..crud_factory import create_crud_router, CrudConfig, UploadConfig

# Configure the competitors router
config = CrudConfig(
    resource_name="competitor",
    resource_name_plural="competitors",
    resource_display_name="Competitor",

    model=models.Competitor,
    schema=schemas.Competitor,
    schema_create=schemas.CompetitorCreate,
    schema_update=schemas.CompetitorUpdate,

    crud_create=crud.create_competitor,
    crud_get_list=crud.get_competitors,
    crud_get_by_id=None,  # No single GET endpoint needed
    crud_update=crud.update_competitor,
    crud_delete=crud.delete_competitor,

    id_field_name="competitor_id",
    id_field_type=int,

    upload_config=UploadConfig(
        required_columns=["competitor_name"],
        unique_field="competitor_name",
        field_mapping={
            "competitor_name": "competitor_name",
            "active": "active"
        },
        defaults={"active": True},
        admin_only=True
    )
)

# Generate the router
router = create_crud_router(config)
