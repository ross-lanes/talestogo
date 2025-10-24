"""
Tests for CRUD operations (database layer).

These tests verify that data is being correctly saved to and retrieved from the database.
"""
import pytest
from datetime import datetime, date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import crud, models, schemas


@pytest.fixture()
def test_db():
    """Create an in-memory test database for CRUD tests."""
    import app.models  # noqa - ensure models are registered
    test_db_uri = "sqlite:///file:crudtest?mode=memory&cache=shared"
    engine = create_engine(test_db_uri, connect_args={"check_same_thread": False, "uri": True})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


class TestQueryCRUD:
    """Tests for Query CRUD operations"""

    def test_create_query(self, test_db):
        """Test creating a new query"""
        db = test_db()
        try:
            query_data = schemas.QueryCreate(
                query_id="Q001",
                query_text="What is plasma physics?",
                category="science",
                priority="High",
                target_outcome="mention",
                active=True,
                notes="Test query"
            )

            created_query = crud.create_query(db, query=query_data)

            assert created_query.id is not None
            assert created_query.query_id == "Q001"
            assert created_query.query_text == "What is plasma physics?"
            assert created_query.active is True
            assert created_query.created_at is not None
        finally:
            db.close()

    def test_get_query_by_id(self, test_db):
        """Test retrieving a query by internal ID"""
        db = test_db()
        try:
            # Create a query
            query_data = schemas.QueryCreate(
                query_id="Q002",
                query_text="Test query",
                category="test",
                priority="Low",
                target_outcome="test",
                active=True
            )
            created = crud.create_query(db, query=query_data)

            # Retrieve by internal ID
            retrieved = crud.get_query(db, query_id_internal=created.id)

            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.query_id == "Q002"
        finally:
            db.close()

    def test_get_query_by_query_id(self, test_db):
        """Test retrieving a query by user-facing query_id"""
        db = test_db()
        try:
            # Create a query
            query_data = schemas.QueryCreate(
                query_id="Q003",
                query_text="Another test",
                category="test",
                priority="Medium",
                target_outcome="test",
                active=False
            )
            crud.create_query(db, query=query_data)

            # Retrieve by query_id
            retrieved = crud.get_query_by_query_id(db, query_id="Q003")

            assert retrieved is not None
            assert retrieved.query_id == "Q003"
            assert retrieved.active is False
        finally:
            db.close()

    def test_get_queries_pagination(self, test_db):
        """Test retrieving queries with pagination"""
        db = test_db()
        try:
            # Create multiple queries
            for i in range(5):
                query_data = schemas.QueryCreate(
                    query_id=f"Q{i:03d}",
                    query_text=f"Query {i}",
                    category="test",
                    priority="Low",
                    target_outcome="test",
                    active=True
                )
                crud.create_query(db, query=query_data)

            # Get first 3
            queries = crud.get_queries(db, skip=0, limit=3)
            assert len(queries) == 3

            # Get next 2
            queries = crud.get_queries(db, skip=3, limit=3)
            assert len(queries) == 2
        finally:
            db.close()

    def test_get_active_queries_only(self, test_db):
        """Test retrieving only active queries"""
        db = test_db()
        try:
            # Create active and inactive queries
            for i in range(3):
                query_data = schemas.QueryCreate(
                    query_id=f"QA{i:03d}",
                    query_text=f"Active query {i}",
                    category="test",
                    priority="Low",
                    target_outcome="test",
                    active=True
                )
                crud.create_query(db, query=query_data)

            for i in range(2):
                query_data = schemas.QueryCreate(
                    query_id=f"QI{i:03d}",
                    query_text=f"Inactive query {i}",
                    category="test",
                    priority="Low",
                    target_outcome="test",
                    active=False
                )
                crud.create_query(db, query=query_data)

            # Get only active queries
            active_queries = crud.get_active_queries(db)

            assert len(active_queries) == 3
            assert all(q.active for q in active_queries)
        finally:
            db.close()

    def test_update_query(self, test_db):
        """Test updating an existing query"""
        db = test_db()
        try:
            # Create a query
            query_data = schemas.QueryCreate(
                query_id="Q100",
                query_text="Original text",
                category="original",
                priority="Low",
                target_outcome="test",
                active=True
            )
            crud.create_query(db, query=query_data)

            # Update it
            update_data = schemas.QueryUpdate(
                query_text="Updated text",
                priority="High",
                active=False
            )
            updated = crud.update_query(db, query_id="Q100", query_update=update_data)

            assert updated is not None
            assert updated.query_text == "Updated text"
            assert updated.priority == "High"
            assert updated.active is False
            # Category should remain unchanged
            assert updated.category == "original"
        finally:
            db.close()

    def test_update_nonexistent_query(self, test_db):
        """Test updating a query that doesn't exist"""
        db = test_db()
        try:
            update_data = schemas.QueryUpdate(query_text="Updated")
            result = crud.update_query(db, query_id="NONEXISTENT", query_update=update_data)

            assert result is None
        finally:
            db.close()

    def test_delete_query(self, test_db):
        """Test deleting a query"""
        db = test_db()
        try:
            # Create a query
            query_data = schemas.QueryCreate(
                query_id="Q200",
                query_text="To be deleted",
                category="test",
                priority="Low",
                target_outcome="test",
                active=True
            )
            crud.create_query(db, query=query_data)

            # Delete it
            deleted = crud.delete_query(db, query_id="Q200")

            assert deleted is not None
            assert deleted.query_id == "Q200"

            # Verify it's gone
            retrieved = crud.get_query_by_query_id(db, query_id="Q200")
            assert retrieved is None
        finally:
            db.close()


class TestResponseCRUD:
    """Tests for Response CRUD operations"""

    def test_create_response(self, test_db):
        """Test creating a new response"""
        db = test_db()
        try:
            response_data = schemas.ResponseCreate(
                query_id="Q001",
                query_text="What is fusion?",
                platform="Claude",
                response_text="Fusion is the process of combining atomic nuclei..."
            )

            created = crud.create_response(db, response=response_data)

            assert created.id is not None
            assert created.query_id == "Q001"
            assert created.platform == "Claude"
            assert created.timestamp is not None
            assert created.analyzed_at is None  # Not analyzed yet
        finally:
            db.close()

    def test_get_response(self, test_db):
        """Test retrieving a response by ID"""
        db = test_db()
        try:
            response_data = schemas.ResponseCreate(
                query_id="Q002",
                query_text="Test",
                platform="Gemini",
                response_text="Response text"
            )
            created = crud.create_response(db, response=response_data)

            retrieved = crud.get_response(db, response_id=created.id)

            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.platform == "Gemini"
        finally:
            db.close()

    def test_get_responses_ordered_by_timestamp(self, test_db):
        """Test that responses are returned in descending timestamp order"""
        db = test_db()
        try:
            # Create multiple responses
            for i in range(3):
                response_data = schemas.ResponseCreate(
                    query_id=f"Q{i}",
                    query_text=f"Query {i}",
                    platform="Claude",
                    response_text=f"Response {i}"
                )
                crud.create_response(db, response=response_data)

            responses = crud.get_responses(db, limit=10)

            assert len(responses) == 3
            # Should be in descending order (newest first)
            for i in range(len(responses) - 1):
                assert responses[i].timestamp >= responses[i + 1].timestamp
        finally:
            db.close()

    def test_get_unanalyzed_responses(self, test_db):
        """Test retrieving only unanalyzed responses"""
        db = test_db()
        try:
            # Create unanalyzed responses
            for i in range(2):
                response_data = schemas.ResponseCreate(
                    query_id=f"QU{i}",
                    query_text="Test",
                    platform="Claude",
                    response_text="Response"
                )
                crud.create_response(db, response=response_data)

            # Create an analyzed response
            response_data = schemas.ResponseCreate(
                query_id="QA1",
                query_text="Test",
                platform="Gemini",
                response_text="Analyzed response"
            )
            analyzed = crud.create_response(db, response=response_data)

            # Mark it as analyzed
            crud.update_response_analysis(
                db,
                response_id=analyzed.id,
                analysis_data={"pppl_mentioned": "Yes"}
            )

            # Get unanalyzed
            unanalyzed = crud.get_unanalyzed_responses(db)

            assert len(unanalyzed) == 2
            assert all(r.analyzed_at is None for r in unanalyzed)
        finally:
            db.close()

    def test_update_response_analysis(self, test_db):
        """Test updating response with analysis data"""
        db = test_db()
        try:
            # Create a response
            response_data = schemas.ResponseCreate(
                query_id="Q999",
                query_text="Test query",
                platform="Claude",
                response_text="PPPL is a leading fusion research facility..."
            )
            response = crud.create_response(db, response=response_data)

            # Update with analysis
            analysis_data = {
                "pppl_mentioned": "Yes",
                "pppl_position": "Leader",
                "sentiment": "Very Positive",
                "descriptors": "leading, pioneering",
                "competitors": "ITER, NIF",
                "sources": "Nature, Science",
                "notes": "Strong positioning"
            }
            updated = crud.update_response_analysis(
                db,
                response_id=response.id,
                analysis_data=analysis_data
            )

            assert updated is not None
            assert updated.pppl_mentioned == "Yes"
            assert updated.pppl_position == "Leader"
            assert updated.sentiment == "Very Positive"
            assert updated.analyzed_at is not None
            assert isinstance(updated.analyzed_at, datetime)
        finally:
            db.close()

    def test_get_responses_by_ids(self, test_db):
        """Test retrieving multiple responses by ID list"""
        db = test_db()
        try:
            # Create several responses
            created_ids = []
            for i in range(5):
                response_data = schemas.ResponseCreate(
                    query_id=f"Q{i}",
                    query_text="Test",
                    platform="Claude",
                    response_text=f"Response {i}"
                )
                response = crud.create_response(db, response=response_data)
                created_ids.append(response.id)

            # Get subset by IDs
            target_ids = [created_ids[1], created_ids[3], created_ids[4]]
            responses = crud.get_responses_by_ids(db, response_ids=target_ids)

            assert len(responses) == 3
            response_ids = [r.id for r in responses]
            assert all(rid in response_ids for rid in target_ids)
        finally:
            db.close()

    def test_get_responses_by_ids_empty_list(self, test_db):
        """Test getting responses with empty ID list"""
        db = test_db()
        try:
            responses = crud.get_responses_by_ids(db, response_ids=[])
            assert responses == []
        finally:
            db.close()


class TestCompetitorCRUD:
    """Tests for Competitor CRUD operations"""

    def test_create_competitor(self, test_db):
        """Test creating a new competitor"""
        db = test_db()
        try:
            competitor_data = schemas.CompetitorCreate(
                organization="ITER",
                type="International Collaboration",
                focus_area="Fusion energy",
                track=True,
                website="https://www.iter.org"
            )

            created = crud.create_competitor(db, competitor=competitor_data)

            assert created.id is not None
            assert created.organization == "ITER"
            assert created.track is True
            assert created.created_at is not None
        finally:
            db.close()

    def test_get_competitor(self, test_db):
        """Test retrieving a competitor by ID"""
        db = test_db()
        try:
            competitor_data = schemas.CompetitorCreate(
                organization="National Ignition Facility",
                type="National Lab",
                track=True
            )
            created = crud.create_competitor(db, competitor=competitor_data)

            retrieved = crud.get_competitor(db, competitor_id=created.id)

            assert retrieved is not None
            assert retrieved.organization == "National Ignition Facility"
        finally:
            db.close()

    def test_get_competitor_by_organization(self, test_db):
        """Test retrieving a competitor by organization name"""
        db = test_db()
        try:
            competitor_data = schemas.CompetitorCreate(
                organization="MIT Plasma Science",
                type="University",
                track=True
            )
            crud.create_competitor(db, competitor=competitor_data)

            retrieved = crud.get_competitor_by_organization(db, organization="MIT Plasma Science")

            assert retrieved is not None
            assert retrieved.organization == "MIT Plasma Science"
            assert retrieved.type == "University"
        finally:
            db.close()

    def test_get_competitors_list(self, test_db):
        """Test retrieving list of competitors"""
        db = test_db()
        try:
            # Create multiple competitors
            for i, org in enumerate(["ITER", "NIF", "MIT", "UKAEA"]):
                competitor_data = schemas.CompetitorCreate(
                    organization=org,
                    type="Test",
                    track=True
                )
                crud.create_competitor(db, competitor=competitor_data)

            competitors = crud.get_competitors(db, limit=10)

            assert len(competitors) == 4
            # Should be ordered alphabetically by organization
            orgs = [c.organization for c in competitors]
            assert orgs == sorted(orgs)
        finally:
            db.close()

    def test_update_competitor(self, test_db):
        """Test updating a competitor"""
        db = test_db()
        try:
            competitor_data = schemas.CompetitorCreate(
                organization="Test Org",
                type="University",
                track=True
            )
            created = crud.create_competitor(db, competitor=competitor_data)

            update_data = schemas.CompetitorUpdate(
                type="National Lab",
                track=False,
                notes="No longer tracking"
            )
            updated = crud.update_competitor(db, competitor_id=created.id, competitor_update=update_data)

            assert updated is not None
            assert updated.type == "National Lab"
            assert updated.track is False
            assert updated.notes == "No longer tracking"
            # Organization should remain unchanged
            assert updated.organization == "Test Org"
        finally:
            db.close()

    def test_delete_competitor(self, test_db):
        """Test deleting a competitor"""
        db = test_db()
        try:
            competitor_data = schemas.CompetitorCreate(
                organization="To Delete",
                type="Test",
                track=False
            )
            created = crud.create_competitor(db, competitor=competitor_data)

            deleted = crud.delete_competitor(db, competitor_id=created.id)

            assert deleted is not None
            assert deleted.organization == "To Delete"

            # Verify it's gone
            retrieved = crud.get_competitor(db, competitor_id=created.id)
            assert retrieved is None
        finally:
            db.close()


class TestDescriptorCRUD:
    """Tests for TargetDescriptor CRUD operations"""

    def test_create_descriptor(self, test_db):
        """Test creating a new descriptor"""
        db = test_db()
        try:
            descriptor_data = schemas.TargetDescriptorCreate(
                descriptor="fusion energy leader",
                category="Leadership",
                target_for_pppl=True,
                priority="High"
            )

            created = crud.create_descriptor(db, descriptor=descriptor_data)

            assert created.id is not None
            assert created.descriptor == "fusion energy leader"
            assert created.target_for_pppl is True
            assert created.created_at is not None
        finally:
            db.close()

    def test_get_descriptor(self, test_db):
        """Test retrieving a descriptor by ID"""
        db = test_db()
        try:
            descriptor_data = schemas.TargetDescriptorCreate(
                descriptor="pioneering research",
                category="Technical",
                target_for_pppl=True,
                priority="Medium"
            )
            created = crud.create_descriptor(db, descriptor=descriptor_data)

            retrieved = crud.get_descriptor(db, descriptor_id=created.id)

            assert retrieved is not None
            assert retrieved.descriptor == "pioneering research"
        finally:
            db.close()

    def test_get_descriptor_by_name(self, test_db):
        """Test retrieving a descriptor by name"""
        db = test_db()
        try:
            descriptor_data = schemas.TargetDescriptorCreate(
                descriptor="innovative technology",
                category="Innovation",
                target_for_pppl=False,
                priority="Low"
            )
            crud.create_descriptor(db, descriptor=descriptor_data)

            retrieved = crud.get_descriptor_by_name(db, name="innovative technology")

            assert retrieved is not None
            assert retrieved.category == "Innovation"
            assert retrieved.target_for_pppl is False
        finally:
            db.close()

    def test_get_target_descriptors_only(self, test_db):
        """Test retrieving only descriptors marked as targets for PPPL"""
        db = test_db()
        try:
            # Create target descriptors
            for i in range(3):
                descriptor_data = schemas.TargetDescriptorCreate(
                    descriptor=f"target descriptor {i}",
                    category="Test",
                    target_for_pppl=True,
                    priority="High"
                )
                crud.create_descriptor(db, descriptor=descriptor_data)

            # Create non-target descriptors
            for i in range(2):
                descriptor_data = schemas.TargetDescriptorCreate(
                    descriptor=f"non-target descriptor {i}",
                    category="Test",
                    target_for_pppl=False,
                    priority="Low"
                )
                crud.create_descriptor(db, descriptor=descriptor_data)

            # Get only target descriptors
            targets = crud.get_target_descriptors(db)

            assert len(targets) == 3
            assert all(d.target_for_pppl for d in targets)
        finally:
            db.close()

    def test_update_descriptor(self, test_db):
        """Test updating a descriptor"""
        db = test_db()
        try:
            descriptor_data = schemas.TargetDescriptorCreate(
                descriptor="original descriptor",
                category="Original",
                target_for_pppl=False,
                priority="Low"
            )
            created = crud.create_descriptor(db, descriptor=descriptor_data)

            update_data = schemas.TargetDescriptorUpdate(
                category="Updated",
                target_for_pppl=True,
                priority="High",
                current_ownership="ITER"
            )
            updated = crud.update_descriptor(db, descriptor_id=created.id, descriptor_update=update_data)

            assert updated is not None
            assert updated.category == "Updated"
            assert updated.target_for_pppl is True
            assert updated.priority == "High"
            assert updated.current_ownership == "ITER"
            # Descriptor text should remain unchanged
            assert updated.descriptor == "original descriptor"
        finally:
            db.close()

    def test_delete_descriptor(self, test_db):
        """Test deleting a descriptor"""
        db = test_db()
        try:
            descriptor_data = schemas.TargetDescriptorCreate(
                descriptor="to be deleted",
                category="Test",
                target_for_pppl=False,
                priority="Low"
            )
            created = crud.create_descriptor(db, descriptor=descriptor_data)

            deleted = crud.delete_descriptor(db, descriptor_id=created.id)

            assert deleted is not None
            assert deleted.descriptor == "to be deleted"

            # Verify it's gone
            retrieved = crud.get_descriptor(db, descriptor_id=created.id)
            assert retrieved is None
        finally:
            db.close()


class TestCampaignCRUD:
    """Tests for Campaign CRUD operations"""

    def test_create_campaign(self, test_db):
        """Test creating a new campaign"""
        db = test_db()
        try:
            campaign_data = schemas.CampaignCreate(
                campaign_name="Q1 2025 Leadership Campaign",
                start_date=date(2025, 1, 1),
                end_date=date(2025, 3, 31),
                status="Active",
                target_narrative="Position PPPL as fusion energy leader"
            )

            created = crud.create_campaign(db, campaign=campaign_data)

            assert created.id is not None
            assert created.campaign_name == "Q1 2025 Leadership Campaign"
            assert created.status == "Active"
            assert created.created_at is not None
        finally:
            db.close()

    def test_get_campaign(self, test_db):
        """Test retrieving a campaign by ID"""
        db = test_db()
        try:
            campaign_data = schemas.CampaignCreate(
                campaign_name="Test Campaign",
                start_date=date(2025, 1, 1),
                status="Planned"
            )
            created = crud.create_campaign(db, campaign=campaign_data)

            retrieved = crud.get_campaign(db, campaign_id=created.id)

            assert retrieved is not None
            assert retrieved.campaign_name == "Test Campaign"
        finally:
            db.close()

    def test_get_campaigns_ordered_by_start_date(self, test_db):
        """Test that campaigns are returned in descending start_date order"""
        db = test_db()
        try:
            # Create campaigns with different start dates
            for i in range(3):
                campaign_data = schemas.CampaignCreate(
                    campaign_name=f"Campaign {i}",
                    start_date=date(2025, i + 1, 1),
                    status="Active"
                )
                crud.create_campaign(db, campaign=campaign_data)

            campaigns = crud.get_campaigns(db, limit=10)

            assert len(campaigns) == 3
            # Should be in descending order (newest first)
            for i in range(len(campaigns) - 1):
                assert campaigns[i].start_date >= campaigns[i + 1].start_date
        finally:
            db.close()


class TestAnalysisHistoryCRUD:
    """Tests for AnalysisHistory CRUD operations"""

    def test_create_analysis_history(self, test_db):
        """Test creating an analysis history entry"""
        db = test_db()
        try:
            analysis_data = schemas.AnalysisHistoryCreate(
                analysis_type="Full",
                executive_summary="PPPL shows strong positioning in Q1 2025",
                recommendations="Continue leadership messaging",
                full_analysis_text="Detailed analysis...",
                report_url="https://docs.google.com/document/d/xxx"
            )

            created = crud.create_analysis_history(db, analysis=analysis_data)

            assert created.id is not None
            assert created.analysis_type == "Full"
            assert created.executive_summary == "PPPL shows strong positioning in Q1 2025"
            assert created.timestamp is not None
        finally:
            db.close()

    def test_get_analysis_histories_ordered(self, test_db):
        """Test that analysis histories are returned in descending timestamp order"""
        db = test_db()
        try:
            # Create multiple analysis entries
            for i in range(3):
                analysis_data = schemas.AnalysisHistoryCreate(
                    analysis_type="ShareOfVoice",
                    executive_summary=f"Summary {i}",
                    recommendations=f"Recommendation {i}",
                    full_analysis_text=f"Analysis {i}"
                )
                crud.create_analysis_history(db, analysis=analysis_data)

            histories = crud.get_analysis_histories(db, limit=10)

            assert len(histories) == 3
            # Should be in descending order (newest first)
            for i in range(len(histories) - 1):
                assert histories[i].timestamp >= histories[i + 1].timestamp
        finally:
            db.close()
