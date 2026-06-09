"""
Tests for the LLMProviderManager and ProviderConfig — focused on the Azure
OpenAI api_type plumbing added when the codebase went provider-agnostic.
"""
import os
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.services.llm_provider_manager import (
    API_TYPE_TO_ENV_VAR,
    LLMProviderManager,
    ProviderConfig,
)
from app.services.generic_llm_client import LLMConfigurationError


@pytest.fixture()
def test_db():
    test_db_uri = "sqlite:///file:llmpmtest?mode=memory&cache=shared"
    engine = create_engine(test_db_uri, connect_args={"check_same_thread": False, "uri": True})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield TestingSessionLocal
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_api_type_to_env_var_includes_azure():
    """Azure must have a default env var so admin-UI defaults work."""
    assert API_TYPE_TO_ENV_VAR["azure"] == "AZURE_OPENAI_API_KEY"


def test_provider_config_api_version_default_is_none():
    """api_version is optional on ProviderConfig — only Azure needs it."""
    cfg = ProviderConfig(
        provider_key="gpt",
        display_name="GPT-4o",
        api_type="openai",
        model_name="gpt-4o",
    )
    assert cfg.api_version is None


def test_provider_config_azure_get_api_key_uses_env_var(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "secret-from-env")
    cfg = ProviderConfig(
        provider_key="azure_openai",
        display_name="Azure OpenAI",
        api_type="azure",
        model_name="gpt-4o-deployment",
        api_endpoint="https://my-resource.openai.azure.com/",
        api_version="2024-10-21",
    )
    assert cfg.has_api_key() is True


def test_provider_config_azure_threads_api_version_into_call(monkeypatch):
    """ProviderConfig.call() must forward api_version into GenericLLMClient.call."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "secret-from-env")
    cfg = ProviderConfig(
        provider_key="azure_openai",
        display_name="Azure OpenAI",
        api_type="azure",
        model_name="gpt-4o-deployment",
        api_endpoint="https://my-resource.openai.azure.com/",
        api_version="2024-10-21",
    )

    with patch("app.services.llm_provider_manager.GenericLLMClient.call") as mock_call:
        mock_call.return_value = "ok"
        cfg.call("hello", max_tokens=10, temperature=0.5)

    mock_call.assert_called_once()
    kwargs = mock_call.call_args.kwargs
    assert kwargs["api_type"] == "azure"
    assert kwargs["api_version"] == "2024-10-21"
    assert kwargs["api_endpoint"] == "https://my-resource.openai.azure.com/"
    assert kwargs["model_name"] == "gpt-4o-deployment"


def test_azure_db_provider_loads_api_version(test_db, monkeypatch):
    """A DB-stored Azure provider's api_version threads into ProviderConfig."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "key")
    db = test_db()
    db.add(models.LLMProvider(
        tenant_id=None,
        provider_key="azure_openai",
        display_name="Azure OpenAI",
        api_type="azure",
        api_endpoint="https://my-resource.openai.azure.com/",
        api_version="2024-10-21",
        model_name="gpt-4o-prod",
        is_enabled=True,
        use_for_analysis=True,
        supports_web_search=False,
    ))
    db.commit()

    mgr = LLMProviderManager(db)
    analysis = mgr.get_analysis_provider()

    assert analysis is not None
    assert analysis.api_type == "azure"
    assert analysis.api_version == "2024-10-21"
    assert analysis.api_endpoint == "https://my-resource.openai.azure.com/"


def test_get_analysis_provider_returns_none_when_nothing_configured(test_db, monkeypatch):
    """With no providers and no env vars, the analysis provider is None."""
    for var in API_TYPE_TO_ENV_VAR.values():
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    db = test_db()
    mgr = LLMProviderManager(db)
    assert mgr.get_analysis_provider() is None
