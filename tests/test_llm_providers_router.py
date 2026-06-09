"""
Router-level regression tests for the LLM Providers admin endpoint.

Covers the post-merge review findings on PR #5 (Bing web search):
- Bing types (bing_v7, bing_grounded) are web-search-only and must be rejected
  if a user tries to mark one as `use_for_analysis=True` — either at create or
  update time.
- The update endpoint must enforce the same per-type field requirements that
  the create endpoint already enforces (api_endpoint for bing_v7;
  api_endpoint + api_version for bing_grounded).
"""
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.auth import get_current_user
from app import models


ADMIN_USER_ID = 1


@pytest.fixture()
def test_db():
    """Fresh in-memory SQLite DB with a single admin user seeded."""
    test_db_uri = "sqlite:///file:llmprovrouter?mode=memory&cache=shared"
    engine = create_engine(
        test_db_uri, connect_args={"check_same_thread": False, "uri": True}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        db.add(models.User(
            id=ADMIN_USER_ID,
            email="admin@example.com",
            full_name="Admin",
            is_active=True,
            is_admin=True,
            is_invited=True,
        ))
        db.commit()
    finally:
        db.close()

    yield TestingSessionLocal

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _make_admin_client(SessionLocal):
    """TestClient with get_db / get_current_user overridden as a logged-in admin."""
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def override_get_current_user(db: Session = Depends(get_db)):
        return db.query(models.User).filter(models.User.id == ADMIN_USER_ID).first()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)


@pytest.fixture(autouse=True)
def _cleanup_overrides():
    yield
    app.dependency_overrides.clear()


# ============================================================
# Finding #1: search-only providers cannot be analysis providers
# ============================================================

@pytest.mark.parametrize("bing_type,extra_fields", [
    ("bing_v7", {"api_endpoint": "https://api.bing.microsoft.com/"}),
    ("bing_grounded", {
        "api_endpoint": "https://my-foundry.example/",
        "api_version": "2025-05-15-preview",
    }),
])
def test_create_rejects_bing_with_use_for_analysis_true(test_db, bing_type, extra_fields):
    """A Bing provider with use_for_analysis=True would crash report generation
    because GenericLLMClient.call() has no branch for these api_types."""
    client = _make_admin_client(test_db)
    payload = {
        "provider_key": f"{bing_type}_test",
        "display_name": "Bing test",
        "api_type": bing_type,
        "model_name": "bing",
        "use_for_analysis": True,  # ← the disallowed combination
        "supports_web_search": True,
        **extra_fields,
    }
    resp = client.post("/admin/llm-providers", json=payload)
    assert resp.status_code == 400, resp.text
    assert "web-search-only" in resp.json()["detail"].lower() or "cannot be the analysis" in resp.json()["detail"].lower()


def test_create_allows_bing_when_use_for_analysis_false(test_db):
    """Same Bing config without use_for_analysis must succeed."""
    client = _make_admin_client(test_db)
    resp = client.post("/admin/llm-providers", json={
        "provider_key": "bing_v7_ok",
        "display_name": "Bing v7 OK",
        "api_type": "bing_v7",
        "model_name": "bing",
        "api_endpoint": "https://api.bing.microsoft.com/",
        "use_for_analysis": False,
        "supports_web_search": True,
    })
    assert resp.status_code in (200, 201), resp.text


# ============================================================
# Finding #2: update endpoint mirrors create-time validation
# ============================================================

def _seed_bing_provider(SessionLocal, api_type, **fields):
    """Insert a Bing provider directly into the DB so we can target it for updates."""
    db = SessionLocal()
    try:
        provider = models.LLMProvider(
            tenant_id=None,
            provider_key=f"{api_type}_seed",
            display_name=f"{api_type} seed",
            api_type=api_type,
            model_name="bing",
            is_enabled=True,
            supports_web_search=True,
            **fields,
        )
        db.add(provider)
        db.commit()
        db.refresh(provider)
        return provider.id
    finally:
        db.close()


def test_update_rejects_clearing_bing_v7_endpoint(test_db):
    """Trying to PUT api_endpoint=None on a bing_v7 provider must fail."""
    provider_id = _seed_bing_provider(
        test_db, "bing_v7", api_endpoint="https://api.bing.microsoft.com/"
    )
    client = _make_admin_client(test_db)
    resp = client.put(f"/admin/llm-providers/{provider_id}", json={"api_endpoint": None})
    assert resp.status_code == 400, resp.text
    assert "api_endpoint" in resp.json()["detail"]


def test_update_rejects_clearing_bing_grounded_version(test_db):
    """Trying to PUT api_version=None on a bing_grounded provider must fail."""
    provider_id = _seed_bing_provider(
        test_db, "bing_grounded",
        api_endpoint="https://my-foundry.example/",
        api_version="2025-05-15-preview",
    )
    client = _make_admin_client(test_db)
    resp = client.put(f"/admin/llm-providers/{provider_id}", json={"api_version": None})
    assert resp.status_code == 400, resp.text
    assert "api_version" in resp.json()["detail"]


def test_update_rejects_flipping_bing_to_analysis_provider(test_db):
    """Trying to PUT use_for_analysis=True on a Bing provider must fail."""
    provider_id = _seed_bing_provider(
        test_db, "bing_v7", api_endpoint="https://api.bing.microsoft.com/"
    )
    client = _make_admin_client(test_db)
    resp = client.put(
        f"/admin/llm-providers/{provider_id}", json={"use_for_analysis": True}
    )
    assert resp.status_code == 400, resp.text
    assert "web-search-only" in resp.json()["detail"].lower() or "cannot be the analysis" in resp.json()["detail"].lower()
