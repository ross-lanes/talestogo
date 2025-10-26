from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional, List
import datetime

# --- Query Schemas ---
class QueryBase(BaseModel):
    query_text: str
    category: Optional[str] = None
    priority: Optional[str] = None
    target_outcome: Optional[str] = None
    active: bool = True
    notes: Optional[str] = None

class QueryCreate(QueryBase):
    query_id: Optional[str] = None  # Optional - will be auto-generated if not provided

class QueryUpdate(BaseModel):
    query_text: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    target_outcome: Optional[str] = None
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
    category: Optional[str] = None
    is_target: bool = True
    current_ownership: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None

class TargetDescriptorCreate(TargetDescriptorBase):
    pass

class TargetDescriptorUpdate(BaseModel):
    descriptor: Optional[str] = None
    category: Optional[str] = None
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
    model_config = ConfigDict(extra='forbid')

