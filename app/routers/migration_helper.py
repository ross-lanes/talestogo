"""
Temporary migration helper endpoint
This will be removed after running the rollback migration
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..auth import get_current_user
from .. import models

router = APIRouter(
    prefix="/migration",
    tags=["Migration Helper"]
)


@router.post("/rollback-pending-shares")
def rollback_pending_shares(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run the rollback migration to remove pending shares columns.
    Only accessible to logged-in users.

    This endpoint will be removed after the migration is complete.
    """

    try:
        # Step 1: Delete pending shares
        result = db.execute(text("DELETE FROM brand_shares WHERE user_id IS NULL"))
        deleted_count = result.rowcount

        # Step 2: Make user_id NOT NULL
        db.execute(text("ALTER TABLE brand_shares ALTER COLUMN user_id SET NOT NULL"))

        # Step 3: Drop indexes
        db.execute(text("DROP INDEX IF EXISTS ix_brand_shares_pending_email"))
        db.execute(text("DROP INDEX IF EXISTS ix_brand_shares_is_pending"))

        # Step 4: Drop columns
        db.execute(text("ALTER TABLE brand_shares DROP COLUMN IF EXISTS pending_email"))
        db.execute(text("ALTER TABLE brand_shares DROP COLUMN IF EXISTS is_pending"))

        db.commit()

        return {
            "success": True,
            "message": "Rollback completed successfully",
            "details": {
                "deleted_pending_shares": deleted_count,
                "user_id_now_required": True,
                "columns_removed": ["pending_email", "is_pending"],
                "indexes_removed": ["ix_brand_shares_pending_email", "ix_brand_shares_is_pending"]
            }
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")
