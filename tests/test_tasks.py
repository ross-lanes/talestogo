import pytest
from unittest.mock import patch, MagicMock, call

from celery_app import tasks
from app import schemas

# It's good practice to have a shared fixture for mocking the DB session
@pytest.fixture
def mock_db_session():
    """Fixture to mock the database session."""
    with patch('celery_app.tasks.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        yield mock_db


class TestQueryLlmPlatformTask:
    """Tests for the query_llm_platform_task."""

    @patch('celery_app.tasks.crud')
    @patch('celery_app.tasks.query_platform_api')
    def test_success(self, mock_query_api, mock_crud, mock_db_session):
        """Test the successful execution of the task."""
        # Arrange
        mock_query = MagicMock(id=1, query_id="Q001", query_text="What is PPPL?")
        mock_crud.get_query.return_value = mock_query
        mock_query_api.return_value = "This is a raw response."
        
        mock_created_response = MagicMock(id=101)
        mock_crud.create_response.return_value = mock_created_response

        # Act
        result = tasks.query_llm_platform_task(query_pk=1, platform="TestPlatform")

        # Assert
        mock_crud.get_query.assert_called_once_with(mock_db_session, query_id_internal=1)
        mock_query_api.assert_called_once_with("What is PPPL?", "TestPlatform")
        
        # Check that create_response was called with a schema object
        call_args = mock_crud.create_response.call_args
        assert call_args is not None
        assert call_args.args[0] == mock_db_session
        
        response_schema = call_args.kwargs['response']
        assert isinstance(response_schema, schemas.ResponseCreate)
        assert response_schema.query_id == "Q001"
        assert response_schema.response_text == "This is a raw response."

        assert result == 101 # The ID of the created response
        mock_db_session.close.assert_called_once()

    @patch('celery_app.tasks.crud')
    def test_query_not_found(self, mock_crud, mock_db_session):
        """Test when the query does not exist in the database."""
        # Arrange
        mock_crud.get_query.return_value = None

        # Act
        result = tasks.query_llm_platform_task(query_pk=999, platform="TestPlatform")

        # Assert
        assert result is None
        mock_crud.get_query.assert_called_once_with(mock_db_session, query_id_internal=999)
        mock_db_session.close.assert_called_once()

    @patch('celery_app.tasks.query_llm_platform_task.retry')
    @patch('celery_app.tasks.crud')
    @patch('celery_app.tasks.query_platform_api')
    def test_api_failure_and_retry(self, mock_query_api, mock_crud, mock_retry, mock_db_session):
        """Test that the task retries on API failure."""
        # Arrange
        mock_query = MagicMock(id=1, query_id="Q001", query_text="What is PPPL?")
        mock_crud.get_query.return_value = mock_query
        api_error = ValueError("API is down")
        mock_query_api.side_effect = api_error

        # Act & Assert
        # The task catches the exception and calls retry. The mock for retry doesn't re-raise.
        # We just need to verify that retry was called.
        tasks.query_llm_platform_task(query_pk=1, platform="TestPlatform")
        mock_retry.assert_called_once_with(exc=api_error)
        mock_db_session.close.assert_called_once()


class TestAnalyzeResponsesBatchTask:
    """Tests for the analyze_responses_batch_task."""

    @patch('celery_app.tasks.crud')
    @patch('celery_app.tasks.analyze_raw_response')
    def test_batch_analysis_success(self, mock_analyze_api, mock_crud, mock_db_session):
        """Test successful analysis of a batch of responses."""
        # Arrange
        mock_crud.get_competitors.return_value = [MagicMock(organization="Competitor A")]
        mock_crud.get_target_descriptors.return_value = [MagicMock(descriptor="Descriptor 1")]

        mock_responses = [
            MagicMock(id=1, query_id="Q001", query_text="Q1", response_text="R1", query=MagicMock(query_text="Q1")),
            MagicMock(id=2, query_id="Q002", query_text="Q2", response_text="R2", query=MagicMock(query_text="Q2")),
        ]
        mock_crud.get_responses_by_ids.return_value = mock_responses

        analysis_results = [
            {"sentiment": "POSITIVE"},
            {"sentiment": "NEUTRAL"},
        ]
        mock_analyze_api.side_effect = analysis_results

        # Act
        result = tasks.analyze_responses_batch_task(response_ids=[1, 2])

        # Assert
        assert result == "Analyzed 2 responses."
        mock_crud.get_responses_by_ids.assert_called_once_with(mock_db_session, response_ids=[1, 2])
        
        # Check that the analysis API was called for each response
        assert mock_analyze_api.call_count == 2
        mock_analyze_api.assert_has_calls([
            call(query_text="Q1", response_text="R1", competitors=["Competitor A"], descriptors=["Descriptor 1"]),
            call(query_text="Q2", response_text="R2", competitors=["Competitor A"], descriptors=["Descriptor 1"]),
        ])

        # Check that the DB was updated for each response
        mock_crud.update_response_analysis.assert_has_calls([
            call(mock_db_session, response_id=1, analysis_data=analysis_results[0]),
            call(mock_db_session, response_id=2, analysis_data=analysis_results[1]),
        ])
        mock_db_session.close.assert_called_once()

    @patch('celery_app.tasks.crud')
    def test_no_responses_found(self, mock_crud, mock_db_session):
        """Test the case where no responses are found for the given IDs."""
        # Arrange
        mock_crud.get_responses_by_ids.return_value = []

        # Act
        result = tasks.analyze_responses_batch_task(response_ids=[99, 100])

        # Assert
        assert "No responses found" in result
        mock_db_session.close.assert_called_once()


class TestRunWeeklyQueriesTask:
    """Tests for the main orchestrator task."""

    @patch('celery_app.tasks.chord')
    @patch('celery_app.tasks.crud')
    def test_dispatches_chord_for_active_queries(self, mock_crud, mock_chord, mock_db_session):
        """Test that a chord is created and applied for active queries."""
        # Arrange
        mock_queries = [
            MagicMock(id=1),
            MagicMock(id=2),
        ]
        mock_crud.get_active_queries.return_value = mock_queries
        
        # Mock the chord object chain
        mock_chord_instance = MagicMock()
        mock_chord.return_value.return_value = mock_chord_instance

        # Act
        result = tasks.run_weekly_queries_task()

        # Assert
        assert "Successfully dispatched" in result
        mock_crud.get_active_queries.assert_called_once()
        
        # Verify the chord was constructed correctly
        assert mock_chord.call_count == 1
        # The number of tasks in the header should be num_queries * num_platforms
        assert len(list(mock_chord.call_args[0][0])) == 2 * 3

        # Verify the chord was scheduled
        mock_chord_instance.apply_async.assert_called_once()
        mock_db_session.close.assert_called_once()