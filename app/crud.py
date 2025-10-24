from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import datetime

# Import your models and schemas
from . import models, schemas

# === Query CRUD Functions ===

def get_query(db: Session, query_id_internal: int) -> Optional[models.Query]:
    """Gets a single query by its internal database ID."""
    return db.query(models.Query).filter(models.Query.id == query_id_internal).first()

def get_query_by_query_id(db: Session, query_id: str) -> Optional[models.Query]:
    """Gets a single query by its user-facing Query ID (e.g., 'Q001')."""
    return db.query(models.Query).filter(models.Query.query_id == query_id).first()

def get_queries(db: Session, skip: int = 0, limit: int = 100) -> List[models.Query]:
    """Gets a list of all queries, with pagination."""
    return db.query(models.Query).order_by(models.Query.query_id).offset(skip).limit(limit).all()

def get_active_queries(db: Session, skip: int = 0, limit: int = 100) -> List[models.Query]:
    """Gets a list of active queries, with pagination."""
    return db.query(models.Query).filter(models.Query.active == True).order_by(models.Query.query_id).offset(skip).limit(limit).all()

def generate_next_query_id(db: Session) -> str:
    """Generates the next sequential query ID (Q001, Q002, etc.)."""
    # Get the highest existing query_id
    last_query = db.query(models.Query).order_by(models.Query.query_id.desc()).first()

    if not last_query or not last_query.query_id:
        return "Q001"

    # Extract the number from the last query_id (e.g., "Q015" -> 15)
    try:
        last_num = int(last_query.query_id[1:])
        next_num = last_num + 1
        return f"Q{next_num:03d}"  # Format as Q001, Q002, etc.
    except (ValueError, IndexError):
        # If parsing fails, start from Q001
        return "Q001"

def create_query(db: Session, query: schemas.QueryCreate) -> models.Query:
    """Creates a new query in the database."""
    query_data = query.model_dump()

    # Auto-generate query_id if not provided
    if not query_data.get('query_id'):
        query_data['query_id'] = generate_next_query_id(db)

    db_query = models.Query(**query_data)
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return db_query

def update_query(db: Session, query_id: str, query_update: schemas.QueryUpdate) -> Optional[models.Query]:
    """Updates an existing query by its user-facing Query ID."""
    db_query = get_query_by_query_id(db, query_id=query_id)
    if not db_query:
        return None

    update_data = query_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_query, key, value)

    db.commit()
    db.refresh(db_query)
    return db_query

def delete_query(db: Session, query_id: str) -> Optional[models.Query]:
    """Deletes a query by its user-facing Query ID. Returns the deleted object."""
    db_query = get_query_by_query_id(db, query_id=query_id)
    if not db_query:
        return None
    db.delete(db_query)
    db.commit()
    return db_query


# === Response CRUD Functions ===

def get_response(db: Session, response_id: int) -> Optional[models.Response]:
    """Gets a single response by its internal database ID."""
    return db.query(models.Response).filter(models.Response.id == response_id).first()

def get_responses(db: Session, skip: int = 0, limit: int = 100) -> List[models.Response]:
    """Gets a list of all responses, with pagination."""
    return db.query(models.Response).order_by(models.Response.timestamp.desc()).offset(skip).limit(limit).all()

def create_response(db: Session, response: schemas.ResponseCreate) -> models.Response:
    """Creates a new response entry."""
    db_response = models.Response(**response.model_dump())
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

def get_unanalyzed_responses(db: Session, limit: int = 100) -> List[models.Response]:
    """Gets responses that haven't been analyzed yet."""
    return db.query(models.Response).filter(models.Response.analyzed_at == None).limit(limit).all()

def update_response_analysis(db: Session, response_id: int, analysis_data: dict) -> Optional[models.Response]:
    """Updates the analysis fields of a specific response."""
    db_response = db.query(models.Response).filter(models.Response.id == response_id).first()
    if not db_response:
        return None
    for key, value in analysis_data.items():
        setattr(db_response, key, value)
    db_response.analyzed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_response)
    return db_response


# === Competitor CRUD Functions ===

def get_competitor(db: Session, competitor_id: int) -> Optional[models.Competitor]:
    return db.query(models.Competitor).filter(models.Competitor.id == competitor_id).first()

def get_competitors(db: Session, skip: int = 0, limit: int = 100) -> List[models.Competitor]:
    return db.query(models.Competitor).order_by(models.Competitor.organization).offset(skip).limit(limit).all()

def create_competitor(db: Session, competitor: schemas.CompetitorCreate) -> models.Competitor:
    db_competitor = models.Competitor(**competitor.model_dump())
    db.add(db_competitor)
    db.commit()
    db.refresh(db_competitor)
    return db_competitor

def update_competitor(db: Session, competitor_id: int, competitor_update: schemas.CompetitorUpdate) -> Optional[models.Competitor]:
    db_competitor = get_competitor(db, competitor_id)
    if not db_competitor:
        return None
    update_data = competitor_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_competitor, key, value)
    db.commit()
    db.refresh(db_competitor)
    return db_competitor

def delete_competitor(db: Session, competitor_id: int) -> Optional[models.Competitor]:
    db_competitor = get_competitor(db, competitor_id)
    if not db_competitor:
        return None
    db.delete(db_competitor)
    db.commit()
    return db_competitor

def get_competitor_by_organization(db: Session, organization: str) -> Optional[models.Competitor]:
    """Gets a single competitor by its organization name."""
    return db.query(models.Competitor).filter(models.Competitor.organization == organization).first()


# === TargetDescriptor CRUD Functions ===

def get_descriptor(db: Session, descriptor_id: int) -> Optional[models.TargetDescriptor]:
    return db.query(models.TargetDescriptor).filter(models.TargetDescriptor.id == descriptor_id).first()

def get_descriptors(db: Session, skip: int = 0, limit: int = 100) -> List[models.TargetDescriptor]:
    return db.query(models.TargetDescriptor).order_by(models.TargetDescriptor.descriptor).offset(skip).limit(limit).all()

def get_descriptor_by_name(db: Session, name: str) -> Optional[models.TargetDescriptor]:
    """Gets a single descriptor by its name."""
    return db.query(models.TargetDescriptor).filter(models.TargetDescriptor.descriptor == name).first()

def create_descriptor(db: Session, descriptor: schemas.TargetDescriptorCreate) -> models.TargetDescriptor:
    db_descriptor = models.TargetDescriptor(**descriptor.model_dump())
    db.add(db_descriptor)
    db.commit()
    db.refresh(db_descriptor)
    return db_descriptor

def get_target_descriptors(db: Session, skip: int = 0, limit: int = 100) -> List[models.TargetDescriptor]:
    """Gets a list of descriptors that are marked as targets for PPPL."""
    return db.query(models.TargetDescriptor).filter(models.TargetDescriptor.target_for_pppl == True).order_by(models.TargetDescriptor.priority).offset(skip).limit(limit).all()

def update_descriptor(db: Session, descriptor_id: int, descriptor_update: schemas.TargetDescriptorUpdate) -> Optional[models.TargetDescriptor]:
    """Updates an existing descriptor."""
    db_descriptor = get_descriptor(db, descriptor_id)
    if not db_descriptor:
        return None
    update_data = descriptor_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_descriptor, key, value)
    db.commit()
    db.refresh(db_descriptor)
    return db_descriptor

def delete_descriptor(db: Session, descriptor_id: int) -> Optional[models.TargetDescriptor]:
    """Deletes a descriptor by its ID."""
    db_descriptor = get_descriptor(db, descriptor_id)
    if not db_descriptor:
        return None
    db.delete(db_descriptor)
    db.commit()
    return db_descriptor


# === Campaign CRUD Functions ===

def get_campaign(db: Session, campaign_id: int) -> Optional[models.Campaign]:
    return db.query(models.Campaign).filter(models.Campaign.id == campaign_id).first()

def get_campaigns(db: Session, skip: int = 0, limit: int = 100) -> List[models.Campaign]:
    return db.query(models.Campaign).order_by(models.Campaign.start_date.desc()).offset(skip).limit(limit).all()

def create_campaign(db: Session, campaign: schemas.CampaignCreate) -> models.Campaign:
    db_campaign = models.Campaign(**campaign.model_dump())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


# === AnalysisHistory CRUD Functions ===

def create_analysis_history(db: Session, analysis: schemas.AnalysisHistoryCreate) -> models.AnalysisHistory:
    db_analysis = models.AnalysisHistory(**analysis.model_dump())
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

def get_analysis_histories(db: Session, skip: int = 0, limit: int = 10) -> List[models.AnalysisHistory]:
    return db.query(models.AnalysisHistory).order_by(models.AnalysisHistory.timestamp.desc()).offset(skip).limit(limit).all()

def get_responses_by_ids(db: Session, response_ids: List[int]) -> List[models.Response]:
    """Gets a list of responses from a list of IDs."""
    if not response_ids:
        return []
    return db.query(models.Response).filter(models.Response.id.in_(response_ids)).all()
