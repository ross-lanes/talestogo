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


@router.post("/reset-sequences")
def reset_sequences(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reset auto-increment sequences for all tables to match current max IDs.
    This fixes "duplicate key value" errors when sequences get out of sync.
    Admin only.
    """
    # Only admin can run this
    if current_user.email != "robotrachel@gmail.com":
        raise HTTPException(status_code=403, detail="Admin only")

    tables = [
        'users',
        'queries',
        'responses',
        'target_descriptors',
        'competitors',
        'brand_info',
        'brand_shares',
        'task_status',
        'reports',
        'collection_batches',
        'scheduled_tasks',
        'tenants'
    ]

    results = {}

    try:
        for table in tables:
            try:
                # Get the sequence name for this table's id column
                result = db.execute(text(f"SELECT pg_get_serial_sequence('{table}', 'id')"))
                sequence_name = result.scalar()

                if sequence_name:
                    # Reset the sequence to max(id) + 1
                    db.execute(text(f"""
                        SELECT setval(
                            '{sequence_name}',
                            COALESCE((SELECT MAX(id) FROM {table}), 1),
                            true
                        )
                    """))
                    results[table] = "reset"
                else:
                    results[table] = "no sequence"
            except Exception as e:
                results[table] = f"error: {str(e)}"

        db.commit()

        return {
            "success": True,
            "message": "Sequences reset successfully",
            "results": results
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to reset sequences: {str(e)}")


@router.get("/debug-brand-shares")
def debug_brand_shares(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Debug endpoint to check brand_shares table state.
    Admin only.
    """
    # Only admin can run this
    if current_user.email != "robotrachel@gmail.com":
        raise HTTPException(status_code=403, detail="Admin only")

    try:
        # Get all shares
        shares_result = db.execute(text("SELECT * FROM brand_shares ORDER BY id"))
        shares = [dict(row._mapping) for row in shares_result]

        # Get max ID and current sequence value
        max_id_result = db.execute(text("SELECT MAX(id) FROM brand_shares"))
        max_id = max_id_result.scalar()

        seq_result = db.execute(text("SELECT pg_get_serial_sequence('brand_shares', 'id')"))
        sequence_name = seq_result.scalar()

        seq_value = None
        if sequence_name:
            seq_val_result = db.execute(text(f"SELECT last_value FROM {sequence_name}"))
            seq_value = seq_val_result.scalar()

        return {
            "shares": shares,
            "max_id": max_id,
            "sequence_name": sequence_name,
            "sequence_current_value": seq_value,
            "total_shares": len(shares)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")
