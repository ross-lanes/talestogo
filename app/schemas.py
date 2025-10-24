from pydantic import BaseModel, ConfigDict
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
    pppl_mentioned: Optional[str] = None
    pppl_position: Optional[str] = None
    sentiment: Optional[str] = None
    descriptors: Optional[str] = None
    competitors: Optional[str] = None
    sources: Optional[str] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class Response(ResponseBase):
    id: int
    timestamp: datetime.datetime
    pppl_mentioned: Optional[str] = None
    pppl_position: Optional[str] = None
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
    target_for_pppl: bool = True
    current_ownership: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None

class TargetDescriptorCreate(TargetDescriptorBase):
    pass

class TargetDescriptorUpdate(BaseModel):
    descriptor: Optional[str] = None
    category: Optional[str] = None
    target_for_pppl: Optional[bool] = None
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
    pppl_coverage: Optional[str] = None
    last_cited: Optional[datetime.date] = None
    notes: Optional[str] = None

class CitedSourceCreate(CitedSourceBase):
    pass

class CitedSourceUpdate(BaseModel):
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    authority_level: Optional[str] = None
    pppl_coverage: Optional[str] = None
    last_cited: Optional[datetime.date] = None
    notes: Optional[str] = None
    model_config = ConfigDict(extra='forbid')

class CitedSource(CitedSourceBase):
    id: int
    created_at: datetime.datetime
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

