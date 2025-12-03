import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float, Text, Date,
    MetaData, Table, create_engine, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
# Import Base from your database setup file
from .database import Base


# === Enums ===
class PersonaType(str, enum.Enum):
    """Types of personas for Heads product"""
    PATIENT = "patient"
    HCP = "hcp"

# === Tenant Model (for multi-tenancy) ===
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    tenant_name = Column(String(200), nullable=False)
    subdomain = Column(String(100), unique=True, nullable=True)
    logo_url = Column(Text, nullable=True)
    primary_color = Column(String(7), default='#75C9C8')
    secondary_color = Column(String(7), default='#665775')
    custom_domain = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# === User Model (for authentication and multi-tenancy) ===
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
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
    # App access control - comma-separated list of allowed products (e.g., "tales,heads,canon")
    allowed_products = Column(Text, nullable=True, default="tales")
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

    # Composite indexes for performance optimization
    __table_args__ = (
        Index('idx_query_brand_branded', 'brand_id', 'brand_in_query'),
        Index('idx_query_compound_lookup', 'query_id', 'user_id', 'brand_id'),
    )

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

    # Composite indexes for performance optimization
    __table_args__ = (
        # Critical index for multi-tenant + multi-brand + batch filtering (used in every analytics query)
        Index('idx_response_user_brand_batch', 'user_id', 'brand_id', 'batch_id'),
        # For sentiment analysis queries that filter by both sentiment and brand_mentioned
        Index('idx_response_sentiment_mentioned', 'sentiment', 'brand_mentioned'),
        # For positioning breakdown queries
        Index('idx_response_position_mentioned', 'brand_position', 'brand_mentioned'),
        # For time-based queries with user filtering (trends, date ranges)
        Index('idx_response_timestamp_user', 'timestamp', 'user_id', 'brand_id'),
        # For JOIN operations with Query table on query_id lookups
        Index('idx_response_query_lookup', 'query_id', 'user_id', 'brand_id'),
    )

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

class BatchAnalytics(Base):
    """
    Cached analytics for each collection batch.
    Stores pre-computed metrics to avoid reprocessing responses.
    """
    __tablename__ = "batch_analytics"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("collection_batches.id"), nullable=False, unique=True, index=True)

    # Collection date (from batch)
    collection_date = Column(DateTime, nullable=False, index=True)

    # Overall metrics
    total_responses = Column(Integer, default=0)

    # Brand mentions (excluding brand_in_query responses)
    mention_count = Column(Integer, default=0)
    mention_rate = Column(Float, default=0.0)

    # Positioning breakdown
    leader_count = Column(Integer, default=0)
    featured_count = Column(Integer, default=0)
    listed_count = Column(Integer, default=0)
    not_mentioned_count = Column(Integer, default=0)

    # Sentiment breakdown (all responses where brand is mentioned)
    very_positive_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    very_negative_count = Column(Integer, default=0)
    mixed_count = Column(Integer, default=0)

    # Share of voice (JSON storing {org_name: count})
    sov_data = Column(Text, nullable=True)  # JSON string

    # Descriptor usage (JSON storing {descriptor: count})
    descriptor_data = Column(Text, nullable=True)  # JSON string

    # Metadata
    computed_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

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
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
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
    __table_args__ = (
        UniqueConstraint('brand_id', 'user_id', name='uq_brand_shares_brand_user'),
    )
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

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brand_info.id", ondelete="CASCADE"), nullable=False, index=True)

    # Schedule configuration
    schedule_type = Column(String(20), nullable=False)  # 'first_day', 'middle', 'last_day'
    is_enabled = Column(Boolean, default=True)
    timezone = Column(String(50), default='UTC')  # User's timezone

    # Execution tracking
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    last_batch_id = Column(Integer, ForeignKey("collection_batches.id"), nullable=True)

    # Notification preferences
    send_email_notification = Column(Boolean, default=True)
    notification_email = Column(String(255), nullable=True)  # Optional override email

    # Metadata
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ScheduledTaskHistory(Base):
    __tablename__ = "scheduled_task_history"
    id = Column(Integer, primary_key=True, index=True)
    scheduled_task_id = Column(Integer, ForeignKey("scheduled_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=False, index=True)

    # Execution details
    started_at = Column(DateTime, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False)  # 'success', 'failed', 'partial'

    # Results
    batch_id = Column(Integer, ForeignKey("collection_batches.id"), nullable=True)
    collection_responses = Column(Integer, default=0)
    analysis_responses = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ============================================================================
# HEADS - Persona Generation Models (Part of Solstice AI Suite)
# ============================================================================

class PersonaGeneration(Base):
    """Tracks a persona generation request and its output"""
    __tablename__ = "persona_generations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=False, index=True)

    # Generation parameters
    patient_occupation = Column(String(200), nullable=True)
    patient_diagnosis = Column(String(200), nullable=True)
    patient_gender = Column(String(50), nullable=True)
    patient_symptoms = Column(Text, nullable=True)
    patient_age_range = Column(String(50), nullable=True)

    hcp_type = Column(String(200), nullable=True)  # Type of doctor
    hcp_disease_focus = Column(String(200), nullable=True)
    hcp_location = Column(String(200), nullable=True)

    # Output
    pptx_file_path = Column(String(500), nullable=True)  # Path to generated PPTX
    pptx_file_url = Column(String(500), nullable=True)  # Public URL if uploaded to cloud

    # Status tracking
    status = Column(String(20), default='pending')  # pending, generating, completed, failed
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Composite indexes
    __table_args__ = (
        Index('idx_persona_gen_user_brand', 'user_id', 'brand_id'),
        Index('idx_persona_gen_status', 'status', 'created_at'),
    )


class Persona(Base):
    """Individual persona (4 patient + 4 HCP personas per generation)"""
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    generation_id = Column(Integer, ForeignKey("persona_generations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brand_info.id"), nullable=False, index=True)

    # Persona type
    persona_type = Column(String(20), nullable=False)  # 'patient' or 'hcp'
    persona_number = Column(Integer, nullable=False)  # 1-4

    # Patient Persona Fields
    # Demographics
    name = Column(String(200), nullable=True)
    age = Column(String(50), nullable=True)
    location = Column(String(200), nullable=True)
    family_status = Column(String(200), nullable=True)
    occupation = Column(String(200), nullable=True)
    tech_savviness = Column(String(100), nullable=True)

    # Clinical Profile
    clinical_scenario = Column(Text, nullable=True)
    recent_diagnosis = Column(String(300), nullable=True)
    mindset = Column(Text, nullable=True)

    # Goals & Fears
    goals = Column(Text, nullable=True)
    fears = Column(Text, nullable=True)

    # Information Journey
    information_channels = Column(Text, nullable=True)  # Comma-separated or JSON
    key_doctor_question = Column(Text, nullable=True)

    # Marketing/Messaging Cues
    marketing_message = Column(Text, nullable=True)
    marketing_tone = Column(String(200), nullable=True)
    call_to_action = Column(Text, nullable=True)

    # HCP Persona Fields
    specialty = Column(String(200), nullable=True)
    years_experience = Column(String(50), nullable=True)
    practice_setting = Column(String(200), nullable=True)
    patient_volume = Column(String(100), nullable=True)
    disease_focus = Column(String(200), nullable=True)

    # HCP-specific fields
    prescribing_preferences = Column(Text, nullable=True)
    information_sources = Column(Text, nullable=True)
    clinical_challenges = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Composite indexes
    __table_args__ = (
        Index('idx_persona_generation', 'generation_id', 'persona_type'),
        Index('idx_persona_user_brand', 'user_id', 'brand_id'),
    )

# ============================================================================
# NSTXVIEW - Plasma Physics Research Paper Analysis Models
# ============================================================================

class NSTXProcessingStatus(str, enum.Enum):
    """Processing status for NSTXView papers"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING_TEXT = "extracting_text"
    EXTRACTING_DATA = "extracting_data"
    GENERATING_EMBEDDINGS = "generating_embeddings"
    COMPLETED = "completed"
    ERROR = "error"


class NSTXShotRole(str, enum.Enum):
    """Role of a shot in a paper"""
    PRIMARY = "primary"  # Main focus of analysis
    COMPARISON = "comparison"  # Used for comparison
    REFERENCE = "reference"  # Referenced but not analyzed


class NSTXParameterCategory(str, enum.Enum):
    """Categories of plasma parameters"""
    PLASMA = "plasma"  # Ion/electron temp, density, pressure
    OPERATIONAL = "operational"  # Current, field, heating power
    PERFORMANCE = "performance"  # Confinement, H-factors, beta


class NSTXPhenomenonCategory(str, enum.Enum):
    """Categories of plasma phenomena"""
    INSTABILITY = "instability"  # ELMs, kink modes, tearing modes
    CONFINEMENT = "confinement"  # H-mode, L-mode, improved confinement
    TRANSPORT = "transport"  # Energy/particle transport
    HEATING = "heating"  # NBI, RF heating effects
    DISRUPTION = "disruption"  # Disruptions, runaway electrons
    DIVERTOR = "divertor"  # Divertor physics, heat flux


class NSTXPaper(Base):
    """
    Represents a journal article about NSTX/NSTX-U experiments.
    Papers are synced from Google Drive and processed to extract structured data.
    """
    __tablename__ = "nstx_papers"

    id = Column(Integer, primary_key=True, index=True)

    # Source tracking
    drive_file_id = Column(String(255), unique=True, nullable=False, index=True)
    original_filename = Column(String(500), nullable=False)
    subfolder = Column(String(255), nullable=True)  # Folder path in Drive
    storage_path = Column(String(500), nullable=True)  # Path in cloud storage

    # Extracted metadata
    title = Column(Text, nullable=True)
    authors = Column(Text, nullable=True)  # JSON array of author names
    journal = Column(String(255), nullable=True)
    publication_date = Column(Date, nullable=True)
    doi = Column(String(255), nullable=True, index=True)
    abstract = Column(Text, nullable=True)

    # Extracted content
    extracted_text = Column(Text, nullable=True)  # Raw extracted text from PDF
    key_findings = Column(Text, nullable=True)  # JSON array of key findings
    experiment_type = Column(String(100), nullable=True)  # confinement, stability, heating, etc.

    # Processing status
    status = Column(String(50), default=NSTXProcessingStatus.PENDING.value, index=True)
    error_message = Column(Text, nullable=True)
    text_extraction_date = Column(DateTime, nullable=True)
    data_extraction_date = Column(DateTime, nullable=True)
    embedding_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    shots = relationship("NSTXShot", back_populates="paper", cascade="all, delete-orphan")
    parameters = relationship("NSTXParameter", back_populates="paper", cascade="all, delete-orphan")
    phenomena = relationship("NSTXPhenomenon", back_populates="paper", cascade="all, delete-orphan")
    chunks = relationship("NSTXPaperChunk", back_populates="paper", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_nstx_paper_status_date', 'status', 'created_at'),
    )


class NSTXShot(Base):
    """
    Represents a plasma shot mentioned in a paper.
    Shot numbers are 6-digit integers starting with 1 (range: 100000-199999).
    """
    __tablename__ = "nstx_shots"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("nstx_papers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Shot identification - 6-digit numbers starting with 1
    shot_number = Column(Integer, nullable=False, index=True)
    role = Column(String(50), default=NSTXShotRole.PRIMARY.value)  # primary, comparison, reference

    # Context
    context = Column(Text, nullable=True)  # Why this shot was mentioned
    characteristics = Column(Text, nullable=True)  # JSON object of extracted characteristics

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    paper = relationship("NSTXPaper", back_populates="shots")
    parameters = relationship("NSTXParameter", back_populates="shot", cascade="all, delete-orphan")
    phenomena = relationship("NSTXPhenomenon", back_populates="shot", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_nstx_shot_number_paper', 'shot_number', 'paper_id'),
        Index('idx_nstx_shot_role', 'role', 'shot_number'),
    )


class NSTXParameter(Base):
    """
    Represents a plasma parameter value extracted from a paper.
    Stores both original values and normalized values for comparison.
    Multiple papers may report different values for the same parameter on the same shot.
    """
    __tablename__ = "nstx_parameters"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("nstx_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    shot_id = Column(Integer, ForeignKey("nstx_shots.id", ondelete="CASCADE"), nullable=True, index=True)

    # Parameter identification
    parameter_name = Column(String(100), nullable=False, index=True)  # e.g., 'ion_temperature'
    parameter_category = Column(String(50), nullable=True)  # plasma, operational, performance

    # Values (original as reported)
    value = Column(Float, nullable=True)
    value_min = Column(Float, nullable=True)  # For ranges
    value_max = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)  # e.g., 'keV', 'MA'
    uncertainty = Column(Float, nullable=True)

    # Normalized values (for comparison across papers)
    normalized_value = Column(Float, nullable=True)
    normalized_unit = Column(String(50), nullable=True)

    # Context
    context = Column(Text, nullable=True)  # Where in the paper this appeared

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    paper = relationship("NSTXPaper", back_populates="parameters")
    shot = relationship("NSTXShot", back_populates="parameters")

    __table_args__ = (
        Index('idx_nstx_param_name_paper', 'parameter_name', 'paper_id'),
        Index('idx_nstx_param_category', 'parameter_category', 'parameter_name'),
    )


class NSTXPhenomenon(Base):
    """
    Represents a plasma phenomenon observed and discussed in a paper.
    """
    __tablename__ = "nstx_phenomena"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("nstx_papers.id", ondelete="CASCADE"), nullable=False, index=True)
    shot_id = Column(Integer, ForeignKey("nstx_shots.id", ondelete="CASCADE"), nullable=True, index=True)

    # Phenomenon identification
    phenomenon_type = Column(String(100), nullable=False, index=True)  # e.g., 'H-mode_transition'
    phenomenon_category = Column(String(50), nullable=True)  # instability, confinement, transport
    description = Column(Text, nullable=True)
    is_primary_focus = Column(Boolean, default=False)  # Main topic of paper

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    paper = relationship("NSTXPaper", back_populates="phenomena")
    shot = relationship("NSTXShot", back_populates="phenomena")

    __table_args__ = (
        Index('idx_nstx_phenom_type_paper', 'phenomenon_type', 'paper_id'),
        Index('idx_nstx_phenom_category', 'phenomenon_category', 'phenomenon_type'),
    )


class NSTXPaperChunk(Base):
    """
    Represents a chunk of paper text for vector search / RAG.
    Metadata stored in PostgreSQL, embeddings stored in ChromaDB.
    """
    __tablename__ = "nstx_paper_chunks"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("nstx_papers.id", ondelete="CASCADE"), nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    section = Column(String(100), nullable=True)  # abstract, introduction, methods, results, etc.
    chromadb_id = Column(String(255), unique=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    paper = relationship("NSTXPaper", back_populates="chunks")

    __table_args__ = (
        Index('idx_nstx_chunk_paper_index', 'paper_id', 'chunk_index'),
    )


class NSTXProcessingTask(Base):
    """
    Tracks background processing tasks for NSTXView (similar to TaskStatus).
    """
    __tablename__ = "nstx_processing_tasks"

    id = Column(Integer, primary_key=True, index=True)

    # Task identification
    task_type = Column(String(50), nullable=False)  # sync, extract_text, extract_data, generate_embeddings
    status = Column(String(20), nullable=False, default='pending', index=True)  # pending, running, completed, failed

    # Progress tracking
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        Index('idx_nstx_task_status_type', 'status', 'task_type'),
    )


# ============================================================================
# NSTXVIEW - Conversation Memory Models
# ============================================================================

# Constants for conversation limits
MAX_SAVED_CONVERSATIONS_PER_USER = 30
MAX_MESSAGES_PER_CONVERSATION = 100


class NSTXConversation(Base):
    """Saved conversation for NSTXView chat - only explicitly saved conversations are stored"""
    __tablename__ = "nstx_conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Conversation metadata
    title = Column(String(255), nullable=False)  # Auto-generated from first exchange
    summary = Column(Text, nullable=True)  # LLM-generated summary when saved

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    messages = relationship("NSTXConversationMessage", back_populates="conversation", cascade="all, delete-orphan", order_by="NSTXConversationMessage.sequence")

    __table_args__ = (
        Index('idx_nstx_conv_user_created', 'user_id', 'created_at'),
    )


class NSTXConversationMessage(Base):
    """Individual message in a saved conversation"""
    __tablename__ = "nstx_conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("nstx_conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # Ordering
    sequence = Column(Integer, nullable=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    conversation = relationship("NSTXConversation", back_populates="messages")

    __table_args__ = (
        Index('idx_nstx_msg_conv_seq', 'conversation_id', 'sequence'),
    )


# --- End of Models ---

# You can create the database file and tables by running this:
if __name__ == "__main__":
    from .database import engine # Import engine from database.py
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")