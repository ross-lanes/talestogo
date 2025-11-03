import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float, Text, Date,
    MetaData, Table, create_engine, ForeignKey
)
from sqlalchemy.orm import relationship
# Import Base from your database setup file
from .database import Base

# === User Model (for authentication and multi-tenancy) ===
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(200))
    organization = Column(String(200))  # The brand/org they're tracking (e.g., "PPPL", "MIT", etc.)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)  # Must be approved by admin to use system
    is_invited = Column(Boolean, default=False)  # Has received invite email
    # Invitation fields
    invitation_token = Column(String(500), nullable=True, unique=True, index=True)  # JWT token for invite link
    invitation_expires_at = Column(DateTime, nullable=True)  # When the invitation expires
    # OAuth fields
    google_id = Column(String(255), unique=True, index=True, nullable=True)  # Google OAuth ID
    microsoft_id = Column(String(255), unique=True, index=True, nullable=True)  # Microsoft OAuth ID
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'microsoft', etc.
    picture_url = Column(String(500), nullable=True)  # Profile picture URL from OAuth
    # Encrypted API keys (user-provided, encrypted at rest)
    openai_api_key_encrypted = Column(Text, nullable=True)
    anthropic_api_key_encrypted = Column(Text, nullable=True)
    gemini_api_key_encrypted = Column(Text, nullable=True)
    perplexity_api_key_encrypted = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Query(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)  # Multi-brand support
    # Using String(10) assuming format like Q001 up to Q9999999
    query_id = Column(String(10), index=True, nullable=False)  # No longer globally unique - unique per user+brand
    query_text = Column(Text, nullable=False)
    category = Column(String(100))
    priority = Column(String(20)) # High, Medium, Low
    target_outcome = Column(Text)
    brand_in_query = Column(Boolean, default=False)  # True if brand name is IN the query text
    active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)  # Multi-brand support
    batch_id = Column(Integer, ForeignKey("collection_batches.id"), nullable=True, index=True)  # Collection batch tracking
    # No Foreign Key constraint, just index for faster lookups by query_id
    query_id = Column(String(10), index=True, nullable=False)
    query_text = Column(Text) # Denormalized
    platform = Column(String(20), index=True, nullable=False) # ChatGPT, Claude, Gemini
    response_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    # Analysis fields
    brand_mentioned = Column(String(10)) # Yes, No, Indirect
    brand_position = Column(String(20)) # Leader, Top 3, Featured, Listed, Not Mentioned
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)  # Multi-brand support
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)  # Multi-brand support
    descriptor = Column(String(200), nullable=False, index=True)
    is_target = Column(Boolean, default=True)
    current_ownership = Column(String(200)) # Who 'owns' this term now
    priority = Column(String(20)) # High, Medium, Low
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CollectionBatch(Base):
    __tablename__ = "collection_batches"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)
    batch_name = Column(String(200), nullable=False)
    description = Column(Text)
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default='in_progress')  # in_progress, completed, failed
    total_queries = Column(Integer, default=0)
    total_responses = Column(Integer, default=0)
    platforms = Column(Text)  # Comma-separated list of platforms used
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)  # Multi-brand support
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)  # Multi-brand support
    source_name = Column(String(200), nullable=False, index=True)
    source_type = Column(String(100)) # News, Academic, Official, Social, Reference
    authority_level = Column(String(20)) # High, Medium, Low
    brand_coverage = Column(Text) # Notes on quality of coverage
    last_cited = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# Note: DashboardMetrics table is omitted - we'll calculate these on-demand or cache them.
# Storing them directly can lead to stale data unless updated rigorously.

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)  # Multi-brand support
    title = Column(String(200), nullable=False)
    report_content = Column(Text, nullable=False) # Full markdown content
    start_date = Column(DateTime, nullable=True) # Analysis period start
    end_date = Column(DateTime, nullable=True) # Analysis period end
    total_responses = Column(Integer, default=0)
    mention_rate = Column(Float, nullable=True)
    google_doc_url = Column(String(500), nullable=True) # Export URL
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class AnalysisHistory(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-tenancy
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
    # Add unique constraint for period+grouping+user_id if needed by DB
    # __table_args__ = (UniqueConstraint('period', 'grouping', 'user_id', name='uq_period_grouping_user'),)

class Configuration(Base):
    __tablename__ = "configuration"
    key = Column(String(100), primary_key=True)
    value = Column(Text)
    # encrypted = Column(Boolean, default=False) # Removed for simplicity with SQLite
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class BrandInfo(Base):
    __tablename__ = "brand_info"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # Multi-brand support: user can have up to 20 brands
    brand_name = Column(String(200), nullable=False)
    website_url = Column(String(500), nullable=True)
    industry = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)  # Brand blurb for analysis
    strategic_messages = Column(Text, nullable=True)  # Key messages/narratives you want people to say
    is_active = Column(Boolean, default=True)  # Which brand is currently active for the user
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class BrandShare(Base):
    __tablename__ = "brand_shares"
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brand_info.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)  # User being granted access
    shared_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)  # User who shared
    permission_level = Column(String(20), default='edit')  # 'edit' or 'view' (currently only 'edit' supported)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class TaskStatus(Base):
    __tablename__ = "task_status"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=True, index=True)
    task_type = Column(String(50), nullable=False)  # 'analysis', 'report_generation', 'collection'
    status = Column(String(20), nullable=False, index=True)  # 'running', 'completed', 'failed', 'cancelled'
    progress = Column(Integer, default=0)  # 0-100 percentage
    total_items = Column(Integer, default=0)  # Total items to process
    processed_items = Column(Integer, default=0)  # Items processed so far
    message = Column(Text, nullable=True)  # Current status message
    error_message = Column(Text, nullable=True)  # Error details if failed
    process_id = Column(Integer, nullable=True)  # Process ID for subprocess management
    started_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# --- End of Models ---

# You can create the database file and tables by running this:
if __name__ == "__main__":
    from .database import engine # Import engine from database.py
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")