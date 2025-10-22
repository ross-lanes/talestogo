import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float, Text, Date,
    MetaData, Table, create_engine
)
# Import Base from your database setup file
from .database import Base

# Using a naming convention for constraints can be helpful for migrations later
# (though less critical with SQLite initially)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
Base.metadata = MetaData(naming_convention=convention)

class Query(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, index=True)
    # Using String(10) assuming format like Q001 up to Q9999999
    query_id = Column(String(10), unique=True, index=True, nullable=False)
    query_text = Column(Text, nullable=False)
    category = Column(String(100))
    priority = Column(String(20)) # High, Medium, Low
    target_outcome = Column(Text)
    active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    # No Foreign Key constraint, just index for faster lookups by query_id
    query_id = Column(String(10), index=True, nullable=False)
    query_text = Column(Text) # Denormalized
    platform = Column(String(20), index=True, nullable=False) # ChatGPT, Claude, Gemini
    response_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    # Analysis fields
    pppl_mentioned = Column(String(10)) # Yes, No, Indirect
    pppl_position = Column(String(20)) # Leader, Top 3, Featured, Listed, Not Mentioned
    sentiment = Column(String(20)) # Very Positive, Positive, Neutral, Negative, Mixed
    descriptors = Column(Text) # Comma-separated
    competitors = Column(Text) # Comma-separated
    sources = Column(Text) # Comma-separated
    campaign_period = Column(String(100))
    notes = Column(Text) # Analysis notes
    analyzed_at = Column(DateTime, nullable=True, index=True) # Index to quickly find unanalyzed

class Competitor(Base):
    __tablename__ = "competitors"
    id = Column(Integer, primary_key=True, index=True)
    organization = Column(String(200), nullable=False, index=True)
    type = Column(String(100)) # National Lab, University, Private Company
    focus_area = Column(Text)
    track = Column(Boolean, default=True) # Include in SoV calcs?
    key_descriptors = Column(Text)
    website = Column(String(500))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TargetDescriptor(Base):
    __tablename__ = "target_descriptors"
    id = Column(Integer, primary_key=True, index=True)
    descriptor = Column(String(200), nullable=False, index=True)
    category = Column(String(100)) # Technical, Leadership, Innovation
    target_for_pppl = Column(Boolean, default=True)
    current_ownership = Column(String(200)) # Who 'owns' this term now
    priority = Column(String(20)) # High, Medium, Low
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String(200), nullable=False, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(50)) # Active, Completed, Planned
    target_narrative = Column(Text)
    key_messages = Column(Text)
    success_metrics = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CitedSource(Base):
    __tablename__ = "cited_sources"
    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(200), nullable=False, index=True)
    source_type = Column(String(100)) # News, Academic, Official, Social, Reference
    authority_level = Column(String(20)) # High, Medium, Low
    pppl_coverage = Column(Text) # Notes on quality of coverage
    last_cited = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Note: DashboardMetrics table is omitted - we'll calculate these on-demand or cache them.
# Storing them directly can lead to stale data unless updated rigorously.

class AnalysisHistory(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(50), nullable=False) # Full, ShareOfVoice, Campaign
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    # Storing report content directly for simplicity, could store URLs instead
    executive_summary = Column(Text)
    recommendations = Column(Text) # Might store as JSON later
    full_analysis_text = Column(Text) # The raw markdown from the LLM
    report_url = Column(String(500)) # Link to generated Google Doc
    # presentation_url = Column(String(500)) # Removed as per requirement
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Trend(Base):
    __tablename__ = "trends"
    id = Column(Integer, primary_key=True, index=True)
    # E.g., '2025-10-14' for week, '2025-10' for month
    period = Column(String(20), nullable=False, index=True)
    grouping = Column(String(10), nullable=False, index=True) # 'week' or 'month'
    mention_rate = Column(Float)
    share_of_voice = Column(Float)
    avg_visibility_score = Column(Float) # Numeric score 0-5
    sentiment_rate = Column(Float) # Pct positive
    descriptor_match_rate = Column(Float)
    response_count = Column(Integer)
    pppl_mention_count = Column(Integer)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow)
    # Add unique constraint for period+grouping if needed by DB
    # __table_args__ = (UniqueConstraint('period', 'grouping', name='uq_period_grouping'),)

class Configuration(Base):
    __tablename__ = "configuration"
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    # encrypted = Column(Boolean, default=False) # Removed for simplicity with SQLite
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# --- End of Models ---

# You can create the database file and tables by running this:
if __name__ == "__main__":
    from .database import engine # Import engine from database.py
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")