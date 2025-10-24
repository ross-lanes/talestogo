"""
Tests for Celery tasks.

These tests use Celery's eager mode to run tasks synchronously for testing.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models, crud, schemas
from celery_app.tasks import (
    query_llm_platform_task,
    analyze_responses_batch_task,
    run_weekly_queries_task
)


@pytest.fixture()
def test_celery_db():
    """Create an in-memory test database for Celery tasks."""
    import app.models  # noqa - ensure models are registered
    test_db_uri = "sqlite:///file:celerytest?mode=memory&cache=shared"
    engine = create_engine(test_db_uri, connect_args={"check_same_thread": False, "uri": True})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def mock_session_local(test_celery_db):
    """Mock SessionLocal to use test database."""
    with patch('celery_app.tasks.SessionLocal', test_celery_db):
        yield test_celery_db


@pytest.fixture()
def sample_query(test_celery_db):
    """Create a sample query in the test database."""
    db = test_celery_db()
    try:
        query_data = schemas.QueryCreate(
            query_id="Q001",
            query_text="What is nuclear fusion research?",
            category="science",
            priority="High",
            target_outcome="mention",
            active=True,
            notes="Test query"
        )
        query = crud.create_query(db, query=query_data)
        db.commit()
        # Return the query ID instead of the object to avoid detached instance errors
        return query.id
    finally:
        db.close()


@pytest.fixture()
def sample_competitors_and_descriptors(test_celery_db):
    """Create sample competitors and descriptors."""
    db = test_celery_db()
    try:
        # Add competitors
        competitor1 = models.Competitor(
            organization="ITER",
            type="International Collaboration",
            track=True
        )
        competitor2 = models.Competitor(
            organization="National Ignition Facility",
            type="National Lab",
            track=True
        )
        db.add(competitor1)
        db.add(competitor2)

        # Add target descriptors
        descriptor1 = models.TargetDescriptor(
            descriptor="fusion energy leader",
            category="Leadership",
            target_for_pppl=True,
            priority="High"
        )
        descriptor2 = models.TargetDescriptor(
            descriptor="pioneering fusion research",
            category="Technical",
            target_for_pppl=True,
            priority="High"
        )
        db.add(descriptor1)
        db.add(descriptor2)

        db.commit()
        return {
            "competitors": ["ITER", "National Ignition Facility"],
            "descriptors": ["fusion energy leader", "pioneering fusion research"]
        }
    finally:
        db.close()


class TestQueryLLMPlatformTask:
    """Tests for query_llm_platform_task"""

    @patch('celery_app.tasks.query_platform_api')
    def test_successful_query(self, mock_query_api, mock_session_local, sample_query):
        """Test successful LLM query and response storage."""
        # Setup mock
        mock_query_api.return_value = "PPPL is a leading fusion research facility..."

        # Run task (sample_query is now an ID)
        result = query_llm_platform_task(sample_query, "Claude")

        # Verify API was called with correct query text
        mock_query_api.assert_called_once_with("What is nuclear fusion research?", "Claude")

        # Verify response was saved
        assert result is not None
        db = mock_session_local()
        try:
            response = crud.get_response(db, response_id=result)
            assert response is not None
            assert response.platform == "Claude"
            assert response.query_id == "Q001"
            assert "PPPL" in response.response_text
        finally:
            db.close()

    @patch('celery_app.tasks.query_platform_api')
    def test_query_with_nonexistent_query_id(self, mock_query_api, mock_session_local):
        """Test handling of nonexistent query."""
        # Run task with non-existent query ID
        result = query_llm_platform_task(99999, "Claude")

        # Should return None and not call API
        assert result is None
        mock_query_api.assert_not_called()

    @patch('celery_app.tasks.query_platform_api')
    def test_query_api_failure(self, mock_query_api, mock_session_local, sample_query):
        """Test handling of API failures."""
        # Setup mock to raise exception
        mock_query_api.side_effect = Exception("API connection failed")

        # Run task - it should raise and retry
        with pytest.raises(Exception):
            query_llm_platform_task(sample_query.id, "Claude")


class TestAnalyzeResponsesBatchTask:
    """Tests for analyze_responses_batch_task"""

    @patch('celery_app.tasks.analyze_raw_response')
    def test_successful_analysis(self, mock_analyze, mock_session_local,
                                sample_query, sample_competitors_and_descriptors):
        """Test successful batch analysis."""
        # Create a response to analyze (sample_query is now an ID)
        db = mock_session_local()
        try:
            response_data = schemas.ResponseCreate(
                query_id="Q001",  # Use the known query_id
                query_text="What is nuclear fusion research?",
                platform="Claude",
                response_text="PPPL is a fusion energy leader with pioneering research..."
            )
            response = crud.create_response(db, response=response_data)
            db.commit()
            response_id = response.id
        finally:
            db.close()

        # Setup mock analysis result
        mock_analyze.return_value = {
            "pppl_mentioned": "Yes",
            "pppl_position": "Leader",
            "sentiment": "Very Positive",
            "descriptors": "fusion energy leader, pioneering research",
            "competitors": "ITER",
            "sources": "Nature, Science Magazine",
            "notes": "Strong positioning"
        }

        # Run task
        result = analyze_responses_batch_task([response_id])

        # Verify analysis was called
        mock_analyze.assert_called_once()
        assert "Analyzed 1 responses" in result

        # Verify response was updated
        db = mock_session_local()
        try:
            updated_response = crud.get_response(db, response_id=response_id)
            assert updated_response.pppl_mentioned == "Yes"
            assert updated_response.pppl_position == "Leader"
            assert updated_response.sentiment == "Very Positive"
            assert updated_response.analyzed_at is not None
        finally:
            db.close()

    @patch('celery_app.tasks.analyze_raw_response')
    def test_analysis_with_no_responses(self, mock_analyze, mock_session_local):
        """Test analysis task with empty response list."""
        result = analyze_responses_batch_task([])

        # Should handle gracefully
        assert "No responses found" in result
        mock_analyze.assert_not_called()

    @patch('celery_app.tasks.analyze_raw_response')
    def test_analysis_with_error(self, mock_analyze, mock_session_local, sample_query):
        """Test handling of analysis errors."""
        # Create a response (sample_query is now an ID)
        db = mock_session_local()
        try:
            response_data = schemas.ResponseCreate(
                query_id="Q001",  # Use the known query_id
                query_text="What is nuclear fusion research?",
                platform="Claude",
                response_text="Some response text"
            )
            response = crud.create_response(db, response=response_data)
            db.commit()
            response_id = response.id
        finally:
            db.close()

        # Setup mock to return error
        mock_analyze.return_value = {"error": "Analysis failed due to API timeout"}

        # Run task - should handle error gracefully
        result = analyze_responses_batch_task([response_id])

        # Verify it completed but logged the error
        assert "Analyzed 1 responses" in result

        # Check that error was recorded
        db = mock_session_local()
        try:
            updated_response = crud.get_response(db, response_id=response_id)
            assert "Analysis failed" in (updated_response.notes or "")
        finally:
            db.close()


class TestRunWeeklyQueriesTask:
    """Tests for run_weekly_queries_task orchestration task"""

    @patch('celery_app.tasks.chord')
    @patch('celery_app.tasks.query_llm_platform_task')
    @patch('celery_app.tasks.analyze_responses_batch_task')
    def test_weekly_run_with_active_queries(self, mock_analyze_task, mock_query_task,
                                           mock_chord, mock_session_local, sample_query):
        """Test weekly task dispatches correct number of subtasks."""
        # sample_query is the query ID, the query is already active by default in the fixture

        # Mock the task signatures
        mock_query_sig = MagicMock()
        mock_query_task.s.return_value = mock_query_sig
        mock_analyze_sig = MagicMock()
        mock_analyze_task.s.return_value = mock_analyze_sig

        # Mock chord to avoid actual execution
        mock_chord_instance = MagicMock()
        mock_chord_instance.apply_async = MagicMock()
        mock_chord.return_value = mock_chord_instance

        # Run the weekly task
        result = run_weekly_queries_task()

        # Verify chord was called
        assert mock_chord.called
        # Should dispatch chord for 1 query * 3 platforms
        assert "Successfully dispatched chord for 1 queries" in result

    @patch('celery_app.tasks.query_llm_platform_task')
    def test_weekly_run_with_no_active_queries(self, mock_query_task, mock_session_local):
        """Test weekly task when no active queries exist."""
        # Run the weekly task
        result = run_weekly_queries_task()

        # Should return early
        assert "No active queries" in result
        mock_query_task.s.assert_not_called()
