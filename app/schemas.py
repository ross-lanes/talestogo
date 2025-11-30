from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
import datetime
from app.models import PersonaType

# --- Tenant Schemas ---
class TenantBase(BaseModel):
    tenant_name: str
    subdomain: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = "#75C9C8"
    secondary_color: Optional[str] = "#665775"
    custom_domain: Optional[str] = None

class TenantCreate(TenantBase):
    pass

class TenantUpdate(BaseModel):
    tenant_name: Optional[str] = None
    subdomain: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    custom_domain: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class Tenant(TenantBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- Query Schemas ---
class QueryBase(BaseModel):
    query_text: str
    category: Optional[str] = None
    priority: Optional[str] = None
    target_outcome: Optional[str] = None
    brand_in_query: bool = False
    active: bool = True
    notes: Optional[str] = None

class QueryCreate(QueryBase):
    query_id: Optional[str] = None  # Optional - will be auto-generated if not provided

class QueryUpdate(BaseModel):
    query_text: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    target_outcome: Optional[str] = None
    brand_in_query: Optional[bool] = None
    active: Optional[bool] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class Query(QueryBase):
    query_id: str  # Required in the response
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- Response Schemas ---
class ResponseBase(BaseModel):
    query_id: str
    platform: str
    response_text: str
    query_text: Optional[str] = None

class ResponseCreate(ResponseBase):
    pass

class ResponseAnalysisInput(BaseModel):
    brand_mentioned: Optional[str] = None
    brand_position: Optional[str] = None
    sentiment: Optional[str] = None
    descriptors: Optional[str] = None
    competitors: Optional[str] = None
    sources: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class Response(ResponseBase):
    id: int
    timestamp: datetime.datetime
    brand_mentioned: Optional[str] = None
    brand_position: Optional[str] = None
    sentiment: Optional[str] = None
    descriptors: Optional[str] = None
    competitors: Optional[str] = None
    sources: Optional[str] = None
    campaign_period: Optional[str] = None
    notes: Optional[str] = None
    analyzed_at: Optional[datetime.datetime] = None
    model_config = ConfigDict(from_attributes=True)

# --- Competitor Schemas ---
class CompetitorBase(BaseModel):
    organization: str
    type: Optional[str] = None
    focus_area: Optional[str] = None
    track: bool = True
    key_descriptors: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None

class CompetitorCreate(CompetitorBase):
    pass

class CompetitorUpdate(BaseModel):
    organization: Optional[str] = None
    type: Optional[str] = None
    focus_area: Optional[str] = None
    track: Optional[bool] = None
    key_descriptors: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class Competitor(CompetitorBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- TargetDescriptor Schemas ---
class TargetDescriptorBase(BaseModel):
    descriptor: str
    is_target: bool = True
    current_ownership: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None

class TargetDescriptorCreate(TargetDescriptorBase):
    pass

class TargetDescriptorUpdate(BaseModel):
    descriptor: Optional[str] = None
    is_target: Optional[bool] = None
    current_ownership: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class TargetDescriptor(TargetDescriptorBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- Campaign Schemas ---
class CampaignBase(BaseModel):
    campaign_name: str
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    status: Optional[str] = None
    target_narrative: Optional[str] = None
    key_messages: Optional[str] = None
    success_metrics: Optional[str] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    campaign_name: Optional[str] = None
    start_date: Optional[datetime.date] = None
    end_date: Optional[datetime.date] = None
    status: Optional[str] = None
    target_narrative: Optional[str] = None
    key_messages: Optional[str] = None
    success_metrics: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class Campaign(CampaignBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)
    
# --- CitedSource Schemas ---
class CitedSourceBase(BaseModel):
    source_name: str
    source_type: Optional[str] = None
    authority_level: Optional[str] = None
    brand_coverage: Optional[str] = None
    last_cited: Optional[datetime.date] = None
    notes: Optional[str] = None

class CitedSourceCreate(CitedSourceBase):
    pass

class CitedSourceUpdate(BaseModel):
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    authority_level: Optional[str] = None
    brand_coverage: Optional[str] = None
    last_cited: Optional[datetime.date] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class CitedSource(CitedSourceBase):
    id: int
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- BatchAnalytics Schemas ---
class BatchAnalyticsBase(BaseModel):
    batch_id: int
    collection_date: datetime.datetime
    total_responses: int = 0
    mention_count: int = 0
    mention_rate: float = 0.0
    leader_count: int = 0
    featured_count: int = 0
    listed_count: int = 0
    not_mentioned_count: int = 0
    very_positive_count: int = 0
    positive_count: int = 0
    neutral_count: int = 0
    negative_count: int = 0
    very_negative_count: int = 0
    mixed_count: int = 0
    sov_data: Optional[str] = None
    descriptor_data: Optional[str] = None

class BatchAnalyticsCreate(BatchAnalyticsBase):
    pass

class BatchAnalytics(BatchAnalyticsBase):
    id: int
    user_id: int
    brand_id: int
    computed_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- Report Schemas ---
class ReportBase(BaseModel):
    title: str
    report_content: str
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    total_responses: int = 0
    mention_rate: Optional[float] = None
    google_doc_url: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    google_doc_url: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class Report(ReportBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- AnalysisHistory Schemas ---
class AnalysisHistoryBase(BaseModel):
    analysis_type: str
    executive_summary: Optional[str] = None
    recommendations: Optional[str] = None
    full_analysis_text: Optional[str] = None
    report_url: Optional[str] = None

class AnalysisHistoryCreate(AnalysisHistoryBase):
    pass

class AnalysisHistory(AnalysisHistoryBase):
    id: int
    timestamp: datetime.datetime
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- BrandInfo Schemas ---
class BrandInfoBase(BaseModel):
    brand_name: str
    website_url: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    strategic_messages: Optional[str] = None

class BrandInfoCreate(BrandInfoBase):
    pass

class BrandInfoUpdate(BaseModel):
    brand_name: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    strategic_messages: Optional[str] = None
    is_active: Optional[bool] = None
    model_config = ConfigDict(extra='forbid')

class BrandInfo(BrandInfoBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# Simple schema for listing brands
class BrandInfoList(BaseModel):
    id: int
    brand_name: str
    is_active: bool
    industry: Optional[str] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

# --- BrandShare Schemas ---
class BrandShareCreate(BaseModel):
    email: EmailStr  # Email of user to share with

class BrandShare(BaseModel):
    id: int
    brand_id: int
    user_id: int
    shared_by_user_id: int
    permission_level: str
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class BrandShareWithUser(BaseModel):
    """BrandShare with user details for display"""
    id: int
    brand_id: int
    user_id: int
    user_email: str
    user_full_name: Optional[str] = None
    shared_by_user_id: int
    shared_by_email: str
    permission_level: str
    created_at: datetime.datetime

class BrandTransferRequest(BaseModel):
    """Request to transfer brand to another user"""
    email: EmailStr  # Email of user to transfer to

class BrandTransferResponse(BaseModel):
    """Response after transferring brand"""
    message: str
    brand_id: int
    brand_name: str
    new_owner_email: str
    new_owner_full_name: Optional[str] = None

# --- User/Auth Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    organization: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleLogin(BaseModel):
    token: str  # Google OAuth ID token

class MicrosoftLogin(BaseModel):
    token: str  # Microsoft OAuth ID token

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    organization: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class User(UserBase):
    id: int
    is_admin: bool
    is_active: bool
    is_invited: bool
    google_id: Optional[str] = None
    oauth_provider: Optional[str] = None
    picture_url: Optional[str] = None
    invitation_expires_at: Optional[datetime.datetime] = None
    tenant_id: Optional[int] = None
    allowed_products: Optional[List[str]] = None  # Product IDs user can access
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None

class UserInvite(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    organization: Optional[str] = None

class UserAdminUpdate(BaseModel):
    """Schema for admin to update user status"""
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    allowed_products: Optional[List[str]] = None  # Product IDs user can access
    model_config = ConfigDict(extra='forbid')

# --- Invitation Schemas ---
class InvitationCreate(BaseModel):
    """Schema for creating an invitation"""
    email: EmailStr
    full_name: str
    organization: Optional[str] = None
    tenant_id: Optional[int] = None  # Optional: assign to specific tenant, defaults to admin's tenant

class InvitationResponse(BaseModel):
    """Schema for invitation response with token"""
    email: EmailStr
    full_name: str
    invitation_token: str
    expires_at: Optional[datetime.datetime] = None
    invitation_url: str

class InvitationValidate(BaseModel):
    """Schema for validating invitation token"""
    email: EmailStr
    full_name: str
    expires_at: datetime.datetime

class InvitationAccept(BaseModel):
    """Schema for accepting invitation and setting password"""
    token: str
    password: str

# --- Task Status Schemas ---
class TaskStatus(BaseModel):
    id: int
    user_id: int
    brand_id: Optional[int] = None
    task_type: str
    status: str
    progress: int
    total_items: int
    processed_items: int
    message: Optional[str] = None
    error_message: Optional[str] = None
    process_id: Optional[int] = None
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# HEADS - PERSONA GENERATION SCHEMAS
# ============================================================================

class PersonaInput(BaseModel):
    """Single persona input for manual generation"""
    # Patient fields
    patient_occupation: Optional[str] = None
    patient_clinical_scenario: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_symptoms: Optional[str] = None
    patient_age_range: Optional[str] = None

    # HCP fields
    hcp_doctor_type: Optional[str] = None
    hcp_disease: Optional[str] = None
    hcp_location: Optional[str] = None


class PersonaGenerationCreate(BaseModel):
    # New fields for AI/manual distinction
    persona_type: str  # 'patient' or 'hcp'
    ai_generation: bool = False  # True for AI, False for manual
    count: Optional[int] = None  # Number of personas for AI generation (1-10)
    personas: Optional[List[PersonaInput]] = None  # Manual persona inputs

    # Legacy fields for backward compatibility
    patient_occupation: Optional[str] = None
    patient_clinical_scenario: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_symptoms: Optional[str] = None
    patient_age_range: Optional[str] = None
    hcp_doctor_type: Optional[str] = None
    hcp_disease: Optional[str] = None
    hcp_location: Optional[str] = None


class PersonaGenerationUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    deck_url: Optional[str] = None


class PersonaGeneration(BaseModel):
    id: int
    user_id: int
    brand_id: int
    tenant_id: int
    patient_occupation: Optional[str] = None
    patient_clinical_scenario: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_symptoms: Optional[str] = None
    patient_age_range: Optional[str] = None
    hcp_doctor_type: Optional[str] = None
    hcp_disease: Optional[str] = None
    hcp_location: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    llm_provider: Optional[str] = None
    deck_url: Optional[str] = None
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# HEADS - PERSONA SCHEMAS
# ============================================================================

class PersonaBase(BaseModel):
    persona_type: PersonaType
    order_index: int = 0
    name: str
    age: Optional[int] = None
    location: Optional[str] = None
    quote: Optional[str] = None
    about: Optional[str] = None
    goals: Optional[str] = None
    fears: Optional[str] = None
    pain_points: Optional[str] = None

    # Patient-specific
    family_status: Optional[str] = None
    occupation: Optional[str] = None
    tech_savviness: Optional[str] = None
    clinical_scenario: Optional[str] = None
    recent_diagnosis: Optional[str] = None
    mindset: Optional[str] = None
    symptoms: Optional[str] = None
    information_channels: Optional[str] = None
    key_question_for_doctor: Optional[str] = None
    marketing_message: Optional[str] = None
    marketing_tone: Optional[str] = None
    call_to_action: Optional[str] = None
    how_they_view_brand: Optional[str] = None

    # HCP-specific
    job_title: Optional[str] = None
    practice_type: Optional[str] = None
    specialty: Optional[str] = None
    motivations: Optional[str] = None
    frustrations: Optional[str] = None
    marketing_channels: Optional[str] = None
    marketing_messaging: Optional[str] = None
    marketing_tactics: Optional[str] = None

    personality_traits: Optional[str] = None


class PersonaCreate(PersonaBase):
    generation_id: int


class Persona(PersonaBase):
    id: int
    generation_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class PersonaGenerationWithPersonas(PersonaGeneration):
    personas: List[Persona] = []


# ========================================
# Admin Audit Log Schemas
# ========================================
class AdminAuditLogBase(BaseModel):
    admin_user_id: int
    action_type: str
    target_user_id: Optional[int] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None


class AdminAuditLogCreate(AdminAuditLogBase):
    pass


class AdminAuditLog(AdminAuditLogBase):
    id: int
    timestamp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

