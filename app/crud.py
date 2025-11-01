from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import datetime

# Import your models and schemas
from . import models, schemas

# === Query CRUD Functions ===

def get_query(db: Session, query_id_internal: int, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Query]:
    """Gets a single query by its internal database ID for a specific user and brand."""
    query = db.query(models.Query).filter(
        models.Query.id == query_id_internal,
        models.Query.user_id == user_id
    )
    if brand_id is not None:
        query = query.filter(models.Query.brand_id == brand_id)
    return query.first()

def get_query_by_query_id(db: Session, query_id: str, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Query]:
    """Gets a single query by its user-facing Query ID (e.g., 'Q001') for a specific user and brand."""
    query = db.query(models.Query).filter(
        models.Query.query_id == query_id,
        models.Query.user_id == user_id
    )
    if brand_id is not None:
        query = query.filter(models.Query.brand_id == brand_id)
    return query.first()

def get_queries(db: Session, user_id: int, brand_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.Query]:
    """Gets a list of all queries for a specific user and optionally a specific brand, with pagination."""
    query = db.query(models.Query).filter(models.Query.user_id == user_id)
    if brand_id is not None:
        query = query.filter(models.Query.brand_id == brand_id)
    return query.order_by(models.Query.query_id).offset(skip).limit(limit).all()

def get_active_queries(db: Session, user_id: int, brand_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.Query]:
    """Gets a list of active queries for a specific user and optionally a specific brand, with pagination."""
    query = db.query(models.Query).filter(
        models.Query.user_id == user_id,
        models.Query.active == True
    )
    if brand_id is not None:
        query = query.filter(models.Query.brand_id == brand_id)
    return query.order_by(models.Query.query_id).offset(skip).limit(limit).all()

def generate_next_query_id(db: Session, user_id: int, brand_id: Optional[int] = None) -> str:
    """Generates the next sequential query ID (Q001, Q002, etc.) for a specific user and brand."""
    # Get the highest existing query_id for this user and brand
    query = db.query(models.Query).filter(models.Query.user_id == user_id)
    if brand_id is not None:
        query = query.filter(models.Query.brand_id == brand_id)

    last_query = query.order_by(models.Query.query_id.desc()).first()

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

def create_query(db: Session, query: schemas.QueryCreate, user_id: int, brand_id: Optional[int] = None) -> models.Query:
    """Creates a new query in the database for a specific user and brand."""
    from app.utils.query_utils import auto_set_brand_in_query_flag

    query_data = query.model_dump()

    # Auto-generate query_id if not provided
    if not query_data.get('query_id'):
        query_data['query_id'] = generate_next_query_id(db, user_id, brand_id)

    query_data['user_id'] = user_id
    if brand_id is not None:
        query_data['brand_id'] = brand_id

    # Automatically detect if brand name is in the query text
    # Only suggest if the user hasn't explicitly provided a value
    # User can always override by setting brand_in_query explicitly
    if query_data.get('query_text') and query_data.get('brand_in_query') is None:
        query_data['brand_in_query'] = auto_set_brand_in_query_flag(
            query_data['query_text'],
            db,
            user_id,
            brand_id
        )
    elif query_data.get('brand_in_query') is None:
        # Default to False if not detected
        query_data['brand_in_query'] = False

    db_query = models.Query(**query_data)
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return db_query

def update_query(db: Session, query_id: str, query_update: schemas.QueryUpdate, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Query]:
    """Updates an existing query by its user-facing Query ID for a specific user and brand."""
    from app.utils.query_utils import auto_set_brand_in_query_flag

    db_query = get_query_by_query_id(db, query_id=query_id, user_id=user_id, brand_id=brand_id)
    if not db_query:
        return None

    update_data = query_update.model_dump(exclude_unset=True)

    # Only auto-detect brand_in_query if:
    # 1. Query text is being updated AND
    # 2. User hasn't explicitly set brand_in_query in this update
    if 'query_text' in update_data and update_data['query_text'] and 'brand_in_query' not in update_data:
        # Suggest the automatic detection, but user can override
        update_data['brand_in_query'] = auto_set_brand_in_query_flag(
            update_data['query_text'],
            db,
            user_id,
            brand_id
        )
    # If user explicitly sets brand_in_query, respect it (it's already in update_data)
    # Otherwise, keep the existing value (don't add to update_data)

    for key, value in update_data.items():
        setattr(db_query, key, value)

    db.commit()
    db.refresh(db_query)
    return db_query

def delete_query(db: Session, query_id: str, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Query]:
    """Deletes a query by its user-facing Query ID for a specific user and brand. Returns the deleted object."""
    db_query = get_query_by_query_id(db, query_id=query_id, user_id=user_id, brand_id=brand_id)
    if not db_query:
        return None
    db.delete(db_query)
    db.commit()
    return db_query


# === Response CRUD Functions ===

def get_response(db: Session, response_id: int, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Response]:
    """Gets a single response by its internal database ID for a specific user and brand."""
    query = db.query(models.Response).filter(
        models.Response.id == response_id,
        models.Response.user_id == user_id
    )
    if brand_id is not None:
        query = query.filter(models.Response.brand_id == brand_id)
    return query.first()

def get_responses(db: Session, user_id: int, brand_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.Response]:
    """Gets a list of all responses for a specific user and optionally a specific brand, with pagination."""
    query = db.query(models.Response).filter(models.Response.user_id == user_id)
    if brand_id is not None:
        query = query.filter(models.Response.brand_id == brand_id)
    return query.order_by(models.Response.timestamp.desc()).offset(skip).limit(limit).all()

def create_response(db: Session, response: schemas.ResponseCreate, user_id: int, brand_id: Optional[int] = None) -> models.Response:
    """Creates a new response entry for a specific user and brand."""
    response_data = response.model_dump()
    response_data['user_id'] = user_id
    if brand_id is not None:
        response_data['brand_id'] = brand_id
    db_response = models.Response(**response_data)
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

def get_unanalyzed_responses(db: Session, user_id: int, brand_id: Optional[int] = None, limit: int = 100) -> List[models.Response]:
    """Gets responses that haven't been analyzed yet for a specific user and brand."""
    query = db.query(models.Response).filter(
        models.Response.user_id == user_id,
        models.Response.analyzed_at == None
    )
    if brand_id is not None:
        query = query.filter(models.Response.brand_id == brand_id)
    return query.limit(limit).all()

def update_response_analysis(db: Session, response_id: int, analysis_data: dict, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Response]:
    """Updates the analysis fields of a specific response for a specific user and brand."""
    query = db.query(models.Response).filter(
        models.Response.id == response_id,
        models.Response.user_id == user_id
    )
    if brand_id is not None:
        query = query.filter(models.Response.brand_id == brand_id)

    db_response = query.first()
    if not db_response:
        return None
    for key, value in analysis_data.items():
        setattr(db_response, key, value)
    db_response.analyzed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_response)
    return db_response

def delete_response(db: Session, response_id: int, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Response]:
    """Deletes a response by its ID for a specific user and brand. Returns the deleted object."""
    db_response = get_response(db, response_id=response_id, user_id=user_id, brand_id=brand_id)
    if not db_response:
        return None
    db.delete(db_response)
    db.commit()
    return db_response


# === Competitor CRUD Functions ===

def get_competitor(db: Session, competitor_id: int, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Competitor]:
    query = db.query(models.Competitor).filter(
        models.Competitor.id == competitor_id,
        models.Competitor.user_id == user_id
    )
    if brand_id is not None:
        query = query.filter(models.Competitor.brand_id == brand_id)
    return query.first()

def get_competitors(db: Session, user_id: int, brand_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.Competitor]:
    query = db.query(models.Competitor).filter(models.Competitor.user_id == user_id)
    if brand_id is not None:
        query = query.filter(models.Competitor.brand_id == brand_id)
    return query.order_by(models.Competitor.organization).offset(skip).limit(limit).all()

def create_competitor(db: Session, competitor: schemas.CompetitorCreate, user_id: int, brand_id: Optional[int] = None) -> models.Competitor:
    competitor_data = competitor.model_dump()
    competitor_data['user_id'] = user_id
    if brand_id is not None:
        competitor_data['brand_id'] = brand_id
    db_competitor = models.Competitor(**competitor_data)
    db.add(db_competitor)
    db.commit()
    db.refresh(db_competitor)
    return db_competitor

def update_competitor(db: Session, competitor_id: int, competitor_update: schemas.CompetitorUpdate, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Competitor]:
    db_competitor = get_competitor(db, competitor_id, user_id, brand_id)
    if not db_competitor:
        return None
    update_data = competitor_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_competitor, key, value)
    db.commit()
    db.refresh(db_competitor)
    return db_competitor

def delete_competitor(db: Session, competitor_id: int, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Competitor]:
    db_competitor = get_competitor(db, competitor_id, user_id, brand_id)
    if not db_competitor:
        return None
    db.delete(db_competitor)
    db.commit()
    return db_competitor

def get_competitor_by_organization(db: Session, organization: str, user_id: int, brand_id: Optional[int] = None) -> Optional[models.Competitor]:
    """Gets a single competitor by its organization name for a specific user and brand."""
    query = db.query(models.Competitor).filter(
        models.Competitor.organization == organization,
        models.Competitor.user_id == user_id
    )
    if brand_id is not None:
        query = query.filter(models.Competitor.brand_id == brand_id)
    return query.first()


# === TargetDescriptor CRUD Functions ===

def get_descriptor(db: Session, descriptor_id: int, user_id: int, brand_id: Optional[int] = None) -> Optional[models.TargetDescriptor]:
    query = db.query(models.TargetDescriptor).filter(
        models.TargetDescriptor.id == descriptor_id,
        models.TargetDescriptor.user_id == user_id
    )
    if brand_id is not None:
        query = query.filter(models.TargetDescriptor.brand_id == brand_id)
    return query.first()

def get_descriptors(db: Session, user_id: int, brand_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.TargetDescriptor]:
    query = db.query(models.TargetDescriptor).filter(models.TargetDescriptor.user_id == user_id)
    if brand_id is not None:
        query = query.filter(models.TargetDescriptor.brand_id == brand_id)
    return query.order_by(models.TargetDescriptor.descriptor).offset(skip).limit(limit).all()

def get_descriptor_by_name(db: Session, name: str, user_id: int, brand_id: Optional[int] = None) -> Optional[models.TargetDescriptor]:
    """Gets a single descriptor by its name for a specific user and brand."""
    query = db.query(models.TargetDescriptor).filter(
        models.TargetDescriptor.descriptor == name,
        models.TargetDescriptor.user_id == user_id
    )
    if brand_id is not None:
        query = query.filter(models.TargetDescriptor.brand_id == brand_id)
    return query.first()

def create_descriptor(db: Session, descriptor: schemas.TargetDescriptorCreate, user_id: int, brand_id: Optional[int] = None) -> models.TargetDescriptor:
    descriptor_data = descriptor.model_dump()
    descriptor_data['user_id'] = user_id
    if brand_id is not None:
        descriptor_data['brand_id'] = brand_id
    db_descriptor = models.TargetDescriptor(**descriptor_data)
    db.add(db_descriptor)
    db.commit()
    db.refresh(db_descriptor)
    return db_descriptor

def get_target_descriptors(db: Session, user_id: int, brand_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[models.TargetDescriptor]:
    """Gets a list of descriptors that are marked as targets for the user's brand."""
    query = db.query(models.TargetDescriptor).filter(
        models.TargetDescriptor.user_id == user_id,
        models.TargetDescriptor.target_for_pppl == True
    )
    if brand_id is not None:
        query = query.filter(models.TargetDescriptor.brand_id == brand_id)
    return query.order_by(models.TargetDescriptor.priority).offset(skip).limit(limit).all()

def update_descriptor(db: Session, descriptor_id: int, descriptor_update: schemas.TargetDescriptorUpdate, user_id: int, brand_id: Optional[int] = None) -> Optional[models.TargetDescriptor]:
    """Updates an existing descriptor for a specific user and brand."""
    db_descriptor = get_descriptor(db, descriptor_id, user_id, brand_id)
    if not db_descriptor:
        return None
    update_data = descriptor_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_descriptor, key, value)
    db.commit()
    db.refresh(db_descriptor)
    return db_descriptor

def delete_descriptor(db: Session, descriptor_id: int, user_id: int, brand_id: Optional[int] = None) -> Optional[models.TargetDescriptor]:
    """Deletes a descriptor by its ID for a specific user and brand."""
    db_descriptor = get_descriptor(db, descriptor_id, user_id, brand_id)
    if not db_descriptor:
        return None
    db.delete(db_descriptor)
    db.commit()
    return db_descriptor


# === Campaign CRUD Functions ===

def get_campaign(db: Session, campaign_id: int, user_id: int) -> Optional[models.Campaign]:
    return db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id,
        models.Campaign.user_id == user_id
    ).first()

def get_campaigns(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Campaign]:
    return db.query(models.Campaign).filter(
        models.Campaign.user_id == user_id
    ).order_by(models.Campaign.start_date.desc()).offset(skip).limit(limit).all()

def create_campaign(db: Session, campaign: schemas.CampaignCreate, user_id: int) -> models.Campaign:
    campaign_data = campaign.model_dump()
    campaign_data['user_id'] = user_id
    db_campaign = models.Campaign(**campaign_data)
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign


# === Report CRUD Functions ===

def create_report(db: Session, report: schemas.ReportCreate, user_id: int) -> models.Report:
    """Creates a new report for a specific user."""
    report_data = report.model_dump()
    report_data['user_id'] = user_id
    db_report = models.Report(**report_data)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

def get_report(db: Session, report_id: int, user_id: int) -> Optional[models.Report]:
    """Gets a single report by ID for a specific user."""
    return db.query(models.Report).filter(
        models.Report.id == report_id,
        models.Report.user_id == user_id
    ).first()

def get_reports(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Report]:
    """Gets a list of all reports for a specific user, ordered by creation date (newest first)."""
    return db.query(models.Report).filter(
        models.Report.user_id == user_id
    ).order_by(models.Report.created_at.desc()).offset(skip).limit(limit).all()

def update_report(db: Session, report_id: int, report_update: schemas.ReportUpdate, user_id: int) -> Optional[models.Report]:
    """Updates an existing report (mainly for adding Google Doc URL) for a specific user."""
    db_report = get_report(db, report_id=report_id, user_id=user_id)
    if not db_report:
        return None
    update_data = report_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_report, key, value)
    db.commit()
    db.refresh(db_report)
    return db_report

def delete_report(db: Session, report_id: int, user_id: int) -> Optional[models.Report]:
    """Deletes a report by its ID for a specific user."""
    db_report = get_report(db, report_id=report_id, user_id=user_id)
    if not db_report:
        return None
    db.delete(db_report)
    db.commit()
    return db_report


# === AnalysisHistory CRUD Functions ===

def create_analysis_history(db: Session, analysis: schemas.AnalysisHistoryCreate, user_id: int) -> models.AnalysisHistory:
    analysis_data = analysis.model_dump()
    analysis_data['user_id'] = user_id
    db_analysis = models.AnalysisHistory(**analysis_data)
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

def get_analysis_histories(db: Session, user_id: int, skip: int = 0, limit: int = 10) -> List[models.AnalysisHistory]:
    return db.query(models.AnalysisHistory).filter(
        models.AnalysisHistory.user_id == user_id
    ).order_by(models.AnalysisHistory.timestamp.desc()).offset(skip).limit(limit).all()


# === BrandInfo CRUD Functions (Multi-Brand Support) ===

def user_has_brand_access(db: Session, brand_id: int, user_id: int) -> bool:
    """Checks if a user has access to a brand (owns it or has it shared with them)."""
    # Check if user owns the brand
    owns_brand = db.query(models.BrandInfo).filter(
        models.BrandInfo.id == brand_id,
        models.BrandInfo.user_id == user_id
    ).first() is not None

    if owns_brand:
        return True

    # Check if brand is shared with user
    has_shared_access = db.query(models.BrandShare).filter(
        models.BrandShare.brand_id == brand_id,
        models.BrandShare.user_id == user_id
    ).first() is not None

    return has_shared_access

def get_all_brands(db: Session, user_id: int) -> List[models.BrandInfo]:
    """Gets all brands for a specific user - both owned and shared (up to 20 owned)."""
    # Get brands owned by user
    owned_brands = db.query(models.BrandInfo).filter(
        models.BrandInfo.user_id == user_id
    ).all()

    # Get brand IDs that are shared with this user
    shared_brand_ids = db.query(models.BrandShare.brand_id).filter(
        models.BrandShare.user_id == user_id
    ).all()

    shared_brand_ids = [bid[0] for bid in shared_brand_ids]

    # Get the actual shared brands
    shared_brands = []
    if shared_brand_ids:
        shared_brands = db.query(models.BrandInfo).filter(
            models.BrandInfo.id.in_(shared_brand_ids)
        ).all()

    # Combine and sort by created_at
    all_brands = owned_brands + shared_brands
    all_brands.sort(key=lambda x: x.created_at, reverse=True)

    return all_brands

def get_brand_by_id(db: Session, brand_id: int, user_id: int) -> Optional[models.BrandInfo]:
    """Gets a specific brand by ID, ensuring user has access (owns it or it's shared)."""
    if not user_has_brand_access(db, brand_id, user_id):
        return None

    return db.query(models.BrandInfo).filter(
        models.BrandInfo.id == brand_id
    ).first()

def get_active_brand(db: Session, user_id: int) -> Optional[models.BrandInfo]:
    """Gets the currently active brand for a user."""
    return db.query(models.BrandInfo).filter(
        models.BrandInfo.user_id == user_id,
        models.BrandInfo.is_active == True
    ).first()

def get_brand_info(db: Session, user_id: int) -> Optional[models.BrandInfo]:
    """Legacy function - gets active brand for backward compatibility."""
    return get_active_brand(db, user_id)

def create_brand_info(db: Session, brand_info: schemas.BrandInfoCreate, user_id: int) -> models.BrandInfo:
    """Creates a new brand for a user (max 20 brands)."""
    # Check brand limit
    brand_count = db.query(models.BrandInfo).filter(
        models.BrandInfo.user_id == user_id
    ).count()

    if brand_count >= 20:
        raise ValueError("Maximum 20 brands per user")

    brand_data = brand_info.model_dump()
    brand_data['user_id'] = user_id

    # If this is the first brand, make it active
    if brand_count == 0:
        brand_data['is_active'] = True
    else:
        brand_data['is_active'] = False

    db_brand = models.BrandInfo(**brand_data)
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return db_brand

def update_brand_info(db: Session, brand_id: int, brand_info_update: schemas.BrandInfoUpdate, user_id: int) -> Optional[models.BrandInfo]:
    """Updates a specific brand."""
    db_brand = get_brand_by_id(db, brand_id, user_id)
    if not db_brand:
        return None

    update_data = brand_info_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_brand, key, value)

    db.commit()
    db.refresh(db_brand)
    return db_brand

def activate_brand(db: Session, brand_id: int, user_id: int) -> Optional[models.BrandInfo]:
    """Sets a brand as active and deactivates all other brands for the user."""
    # Verify brand belongs to user
    db_brand = get_brand_by_id(db, brand_id, user_id)
    if not db_brand:
        return None

    # Deactivate all other brands
    db.query(models.BrandInfo).filter(
        models.BrandInfo.user_id == user_id
    ).update({models.BrandInfo.is_active: False})

    # Activate this brand
    db_brand.is_active = True
    db.commit()
    db.refresh(db_brand)
    return db_brand

def delete_brand_info(db: Session, brand_id: int, user_id: int) -> Optional[models.BrandInfo]:
    """Deletes a specific brand and all associated data."""
    db_brand = get_brand_by_id(db, brand_id, user_id)
    if not db_brand:
        return None

    # Delete associated data
    db.query(models.Query).filter(models.Query.brand_id == brand_id).delete()
    db.query(models.Response).filter(models.Response.brand_id == brand_id).delete()
    db.query(models.TargetDescriptor).filter(models.TargetDescriptor.brand_id == brand_id).delete()
    db.query(models.Competitor).filter(models.Competitor.brand_id == brand_id).delete()
    db.query(models.Campaign).filter(models.Campaign.brand_id == brand_id).delete()
    db.query(models.Report).filter(models.Report.brand_id == brand_id).delete()
    db.query(models.CitedSource).filter(models.CitedSource.brand_id == brand_id).delete()

    # Delete brand
    db.delete(db_brand)
    db.commit()
    return db_brand

def get_responses_by_ids(db: Session, response_ids: List[int], user_id: int) -> List[models.Response]:
    """Gets a list of responses from a list of IDs for a specific user."""
    if not response_ids:
        return []
    return db.query(models.Response).filter(
        models.Response.id.in_(response_ids),
        models.Response.user_id == user_id
    ).all()


# === User CRUD Functions ===

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Gets a user by email address."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    """Gets a user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Gets all users (admin only)."""
    return db.query(models.User).order_by(models.User.created_at.desc()).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate, hashed_password: str, is_invited: bool = False) -> models.User:
    """Creates a new user."""
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        organization=user.organization,
        is_invited=is_invited,
        is_active=False,  # Must be approved by admin
        is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate, encrypt_keys_func=None) -> Optional[models.User]:
    """Updates user profile and API keys."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)

    # Handle API key encryption if provided
    if encrypt_keys_func:
        if 'openai_api_key' in update_data and update_data['openai_api_key']:
            db_user.openai_api_key_encrypted = encrypt_keys_func(update_data.pop('openai_api_key'))
        if 'anthropic_api_key' in update_data and update_data['anthropic_api_key']:
            db_user.anthropic_api_key_encrypted = encrypt_keys_func(update_data.pop('anthropic_api_key'))
        if 'gemini_api_key' in update_data and update_data['gemini_api_key']:
            db_user.gemini_api_key_encrypted = encrypt_keys_func(update_data.pop('gemini_api_key'))
        if 'perplexity_api_key' in update_data and update_data['perplexity_api_key']:
            db_user.perplexity_api_key_encrypted = encrypt_keys_func(update_data.pop('perplexity_api_key'))

    # Update remaining fields
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

def admin_update_user(db: Session, user_id: int, user_update: schemas.UserAdminUpdate) -> Optional[models.User]:
    """Admin updates user status (is_active, is_admin)."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user
