import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app as fastapi_app, get_db
from app.database import Base
from app import models


@pytest.fixture()
def test_db():
    """Create an in-memory test database."""
    # Import models to ensure they're registered with Base.metadata
    import app.models  # noqa
    # Use shared cache so all connections see the same in-memory database
    test_db_uri = "sqlite:///file:testdb?mode=memory&cache=shared"
    engine = create_engine(test_db_uri, connect_args={"check_same_thread": False, "uri": True})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal

    # Cleanup: drop all tables and clear overrides
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    fastapi_app.dependency_overrides.clear()


def test_read_root():
    client = TestClient(fastapi_app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "Welcome to the TALES API!"}


def test_create_and_read_query(test_db):
    client = TestClient(fastapi_app)

    payload = {
        "query_id": "Q999",
        "query_text": "What is fusion?",
        "category": "science",
        "priority": "Low",
        "target_outcome": "inform",
        "active": True,
        "notes": "test entry"
    }

    # Create
    resp = client.post("/queries/", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["query_id"] == payload["query_id"]
    assert data["query_text"] == payload["query_text"]
    assert "id" in data

    # Read
    resp2 = client.get(f"/queries/{payload['query_id']}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["query_id"] == payload["query_id"]
    assert data2["query_text"] == payload["query_text"]
