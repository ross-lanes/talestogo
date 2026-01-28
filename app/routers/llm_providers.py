"""
LLM Providers Admin Router

Allows admins to configure LLM providers for their tenant.
Supports up to 6 LLM providers per tenant (4 default + 2 custom).
API keys are read from environment variables, not stored in the database.
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user, get_current_admin_user
from ..services.generic_llm_client import GenericLLMClient
from ..services.llm_provider_manager import LLMProviderManager, API_TYPE_TO_ENV_VAR

router = APIRouter(
    prefix="/admin/llm-providers",
    tags=["LLM Providers (Admin)"]
)

MAX_PROVIDERS_PER_TENANT = 6


def get_tenant_id_for_user(user: models.User) -> Optional[int]:
    """Get tenant ID for a user, handling None case."""
    return user.tenant_id


def _get_api_key_for_provider(provider: models.LLMProvider) -> str:
    """Get API key from environment for a provider."""
    if provider.env_var_name:
        return os.getenv(provider.env_var_name, "")
    env_var = API_TYPE_TO_ENV_VAR.get(provider.api_type, "")
    return os.getenv(env_var, "") if env_var else ""


def _get_env_var_for_provider(provider: models.LLMProvider) -> str:
    """Get the environment variable name for a provider."""
    if provider.env_var_name:
        return provider.env_var_name
    return API_TYPE_TO_ENV_VAR.get(provider.api_type, "")


@router.get("", response_model=List[schemas.LLMProvider])
def list_providers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    List all LLM providers for the current tenant.

    Returns providers configured for the user's tenant, including
    global providers (tenant_id=None).
    """
    tenant_id = get_tenant_id_for_user(current_user)

    query = db.query(models.LLMProvider)

    if tenant_id is not None:
        query = query.filter(
            (models.LLMProvider.tenant_id == tenant_id) |
            (models.LLMProvider.tenant_id == None)
        )
    else:
        query = query.filter(models.LLMProvider.tenant_id == None)

    providers = query.order_by(models.LLMProvider.sort_order).all()

    # Build response with api_key_source field
    result = []
    for p in providers:
        provider_dict = {
            "id": p.id,
            "tenant_id": p.tenant_id,
            "provider_key": p.provider_key,
            "display_name": p.display_name,
            "api_type": p.api_type,
            "api_endpoint": p.api_endpoint,
            "model_name": p.model_name,
            "env_var_name": p.env_var_name,
            "color": p.color,
            "sort_order": p.sort_order,
            "is_enabled": p.is_enabled,
            "use_for_analysis": p.use_for_analysis,
            "supports_web_search": p.supports_web_search,
            "api_key_source": "environment",
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        }
        result.append(provider_dict)

    return result


@router.post("", response_model=schemas.LLMProvider, status_code=201)
def create_provider(
    provider: schemas.LLMProviderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Create a new LLM provider for the current tenant.

    Maximum of 6 providers per tenant. API keys are read from environment
    variables. For custom providers (non-default), env_var_name is required.
    """
    tenant_id = provider.tenant_id or get_tenant_id_for_user(current_user)

    # Check provider limit
    existing_count = db.query(models.LLMProvider).filter(
        models.LLMProvider.tenant_id == tenant_id
    ).count()

    if existing_count >= MAX_PROVIDERS_PER_TENANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {MAX_PROVIDERS_PER_TENANT} providers allowed per tenant"
        )

    # Check for duplicate provider_key
    existing = db.query(models.LLMProvider).filter(
        models.LLMProvider.tenant_id == tenant_id,
        models.LLMProvider.provider_key == provider.provider_key
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider with key '{provider.provider_key}' already exists"
        )

    # Validate api_type
    valid_api_types = ["openai", "anthropic", "google", "openai_compatible"]
    if provider.api_type not in valid_api_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid api_type. Must be one of: {', '.join(valid_api_types)}"
        )

    # Require api_endpoint for openai_compatible
    if provider.api_type == "openai_compatible" and not provider.api_endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="api_endpoint is required for openai_compatible API type"
        )

    # For custom providers (not in default mapping), require env_var_name
    is_default_type = provider.api_type in API_TYPE_TO_ENV_VAR
    if not is_default_type and not provider.env_var_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="env_var_name is required for custom providers"
        )

    # If this is the first provider or use_for_analysis is True, handle analysis flag
    if provider.use_for_analysis:
        # Clear use_for_analysis from other providers
        db.query(models.LLMProvider).filter(
            models.LLMProvider.tenant_id == tenant_id,
            models.LLMProvider.use_for_analysis == True
        ).update({"use_for_analysis": False})

    # Create provider (no API key stored - read from env at runtime)
    db_provider = models.LLMProvider(
        tenant_id=tenant_id,
        provider_key=provider.provider_key,
        display_name=provider.display_name,
        api_type=provider.api_type,
        api_endpoint=provider.api_endpoint,
        model_name=provider.model_name,
        env_var_name=provider.env_var_name,
        color=provider.color,
        sort_order=provider.sort_order,
        is_enabled=provider.is_enabled,
        use_for_analysis=provider.use_for_analysis,
        supports_web_search=provider.supports_web_search,
    )

    db.add(db_provider)
    db.commit()
    db.refresh(db_provider)

    return {
        **db_provider.__dict__,
        "api_key_source": "environment"
    }


@router.get("/{provider_id}", response_model=schemas.LLMProvider)
def get_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Get a specific LLM provider by ID."""
    tenant_id = get_tenant_id_for_user(current_user)

    provider = db.query(models.LLMProvider).filter(
        models.LLMProvider.id == provider_id
    ).first()

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    # Verify tenant access
    if provider.tenant_id is not None and provider.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this provider"
        )

    return {
        **provider.__dict__,
        "api_key_source": "environment"
    }


@router.put("/{provider_id}", response_model=schemas.LLMProvider)
def update_provider(
    provider_id: int,
    provider_update: schemas.LLMProviderUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Update an LLM provider."""
    tenant_id = get_tenant_id_for_user(current_user)

    provider = db.query(models.LLMProvider).filter(
        models.LLMProvider.id == provider_id
    ).first()

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    # Verify tenant access
    if provider.tenant_id is not None and provider.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this provider"
        )

    # Update fields
    update_data = provider_update.model_dump(exclude_unset=True)

    # If setting use_for_analysis to True, clear it from others
    if update_data.get("use_for_analysis") is True:
        db.query(models.LLMProvider).filter(
            models.LLMProvider.tenant_id == tenant_id,
            models.LLMProvider.id != provider_id,
            models.LLMProvider.use_for_analysis == True
        ).update({"use_for_analysis": False})

    # Validate api_type if being updated
    if "api_type" in update_data:
        valid_api_types = ["openai", "anthropic", "google", "openai_compatible"]
        if update_data["api_type"] not in valid_api_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid api_type. Must be one of: {', '.join(valid_api_types)}"
            )

    # Apply updates
    for key, value in update_data.items():
        setattr(provider, key, value)

    db.commit()
    db.refresh(provider)

    return {
        **provider.__dict__,
        "api_key_source": "environment"
    }


@router.delete("/{provider_id}", status_code=204)
def delete_provider(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """Delete an LLM provider."""
    tenant_id = get_tenant_id_for_user(current_user)

    provider = db.query(models.LLMProvider).filter(
        models.LLMProvider.id == provider_id
    ).first()

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    # Verify tenant access
    if provider.tenant_id is not None and provider.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this provider"
        )

    db.delete(provider)
    db.commit()


@router.post("/{provider_id}/test", response_model=schemas.LLMProviderTestResponse)
def test_provider(
    provider_id: int,
    test_request: schemas.LLMProviderTestRequest = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Test connection to an LLM provider.

    Gets API key from environment variable and sends a test prompt.
    """
    tenant_id = get_tenant_id_for_user(current_user)

    provider = db.query(models.LLMProvider).filter(
        models.LLMProvider.id == provider_id
    ).first()

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    # Verify tenant access
    if provider.tenant_id is not None and provider.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this provider"
        )

    # Get API key from environment
    api_key = _get_api_key_for_provider(provider)
    env_var = _get_env_var_for_provider(provider)

    if not api_key:
        return schemas.LLMProviderTestResponse(
            success=False,
            message=f"API key not found in environment variable: {env_var}",
            response_preview=None
        )

    # Test the connection
    test_prompt = test_request.test_prompt if test_request else "Hello, please respond with a brief greeting."

    success, message, response_preview = GenericLLMClient.test_connection(
        api_type=provider.api_type,
        api_key=api_key,
        model_name=provider.model_name,
        api_endpoint=provider.api_endpoint,
        test_prompt=test_prompt
    )

    return schemas.LLMProviderTestResponse(
        success=success,
        message=message,
        response_preview=response_preview
    )
