"""
Database Query Helper Utilities

This module provides generic helper functions for common CRUD operations
to reduce code duplication while maintaining type safety and readability.

DESIGN PHILOSOPHY:
- Extract ONLY truly identical patterns (Update/Delete)
- Keep domain-specific operations (Get/Create) explicit in crud.py
- Preserve readability and debuggability
- Single source of truth for update/delete logic

USAGE:
Only use these helpers when the operation is truly generic with no
domain-specific logic. For operations with special business logic,
keep them explicit in the CRUD layer.
"""
from typing import Optional, Callable, TypeVar, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Generic type for SQLAlchemy models
ModelType = TypeVar('ModelType')


def generic_update(
    db: Session,
    get_function: Callable[..., Optional[ModelType]],
    schema_update: BaseModel,
    **get_kwargs
) -> Optional[ModelType]:
    """
    Generic update operation with ownership validation.

    This helper encapsulates the common update pattern:
    1. Retrieve item using provided get_function (which validates ownership)
    2. Return None if item not found
    3. Apply updates from schema using setattr
    4. Commit and refresh
    5. Return updated item

    Args:
        db: Database session
        get_function: Function to retrieve the item (e.g., get_competitor)
                     This function MUST handle ownership validation
        schema_update: Pydantic schema with update data
        **get_kwargs: Keyword arguments to pass to get_function
                     (e.g., competitor_id=123, user_id=456, brand_id=789)

    Returns:
        Updated model instance if found and updated, None if not found

    Example:
        >>> updated = generic_update(
        ...     db=db,
        ...     get_function=get_competitor,
        ...     schema_update=competitor_update,
        ...     competitor_id=123,
        ...     user_id=current_user.id,
        ...     brand_id=brand_id
        ... )
    """
    # Retrieve the item (ownership validation happens in get_function)
    db_obj = get_function(db, **get_kwargs)

    if not db_obj:
        return None

    # Apply updates from schema
    update_data = schema_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    # Commit and refresh
    db.commit()
    db.refresh(db_obj)

    return db_obj


def generic_delete(
    db: Session,
    get_function: Callable[..., Optional[ModelType]],
    **get_kwargs
) -> Optional[ModelType]:
    """
    Generic delete operation with ownership validation.

    This helper encapsulates the common delete pattern:
    1. Retrieve item using provided get_function (which validates ownership)
    2. Return None if item not found
    3. Delete the item
    4. Commit
    5. Return deleted item (for response/audit purposes)

    Args:
        db: Database session
        get_function: Function to retrieve the item (e.g., get_competitor)
                     This function MUST handle ownership validation
        **get_kwargs: Keyword arguments to pass to get_function
                     (e.g., competitor_id=123, user_id=456, brand_id=789)

    Returns:
        Deleted model instance if found and deleted, None if not found

    Example:
        >>> deleted = generic_delete(
        ...     db=db,
        ...     get_function=get_competitor,
        ...     competitor_id=123,
        ...     user_id=current_user.id,
        ...     brand_id=brand_id
        ... )
    """
    # Retrieve the item (ownership validation happens in get_function)
    db_obj = get_function(db, **get_kwargs)

    if not db_obj:
        return None

    # Delete and commit
    db.delete(db_obj)
    db.commit()

    return db_obj


# ==================== SPECIALIZED UPDATE HELPERS ====================

def update_with_timestamp(
    db: Session,
    get_function: Callable[..., Optional[ModelType]],
    schema_update: BaseModel,
    timestamp_field: str,
    timestamp_value: Any,
    **get_kwargs
) -> Optional[ModelType]:
    """
    Generic update with automatic timestamp field update.

    Use this for operations that need to track when an item was modified
    (e.g., analyzed_at, updated_at, last_modified).

    Args:
        db: Database session
        get_function: Function to retrieve the item
        schema_update: Pydantic schema with update data
        timestamp_field: Name of the timestamp field to update (e.g., 'analyzed_at')
        timestamp_value: Value to set for the timestamp (e.g., datetime.utcnow())
        **get_kwargs: Keyword arguments to pass to get_function

    Returns:
        Updated model instance if found and updated, None if not found

    Example:
        >>> from datetime import datetime
        >>> updated = update_with_timestamp(
        ...     db=db,
        ...     get_function=get_response,
        ...     schema_update=analysis_data,
        ...     timestamp_field='analyzed_at',
        ...     timestamp_value=datetime.utcnow(),
        ...     response_id=123,
        ...     user_id=current_user.id
        ... )
    """
    # Retrieve the item
    db_obj = get_function(db, **get_kwargs)

    if not db_obj:
        return None

    # Apply updates from schema
    update_data = schema_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    # Set timestamp field
    setattr(db_obj, timestamp_field, timestamp_value)

    # Commit and refresh
    db.commit()
    db.refresh(db_obj)

    return db_obj
