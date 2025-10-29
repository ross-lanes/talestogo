#!/usr/bin/env python3
"""
Export data from SQLite database to JSON for migration to PostgreSQL.
"""
import json
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models

# Create SQLite engine
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SQLITE_URL = f"sqlite:///{os.path.join(PROJECT_ROOT, 'tales.db')}"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def serialize_datetime(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_data():
    """Export all data from SQLite database to JSON file."""
    db = SessionLocal()

    try:
        data = {
            "users": [],
            "brand_info": [],
            "queries": [],
            "responses": [],
            "competitors": [],
            "target_descriptors": [],
            "campaigns": [],
            "reports": [],
            "cited_sources": []
        }

        # Export users
        users = db.query(models.User).all()
        for user in users:
            data["users"].append({
                "id": user.id,
                "email": user.email,
                "hashed_password": user.hashed_password,
                "full_name": user.full_name,
                "organization": user.organization,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "is_invited": user.is_invited,
                "google_id": user.google_id,
                "oauth_provider": user.oauth_provider,
                "picture_url": user.picture_url,
                "openai_api_key_encrypted": user.openai_api_key_encrypted,
                "anthropic_api_key_encrypted": user.anthropic_api_key_encrypted,
                "gemini_api_key_encrypted": user.gemini_api_key_encrypted,
                "perplexity_api_key_encrypted": user.perplexity_api_key_encrypted,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            })

        # Export brand_info
        brands = db.query(models.BrandInfo).all()
        for brand in brands:
            data["brand_info"].append({
                "id": brand.id,
                "user_id": brand.user_id,
                "brand_name": brand.brand_name,
                "industry": brand.industry,
                "description": brand.description,
                "strategic_messages": brand.strategic_messages,
                "is_active": brand.is_active,
                "created_at": brand.created_at.isoformat() if brand.created_at else None,
                "updated_at": brand.updated_at.isoformat() if brand.updated_at else None,
            })

        # Export queries
        queries = db.query(models.Query).all()
        for query in queries:
            data["queries"].append({
                "id": query.id,
                "user_id": query.user_id,
                "brand_id": query.brand_id,
                "query_id": query.query_id,
                "query_text": query.query_text,
                "category": query.category,
                "priority": query.priority,
                "target_outcome": query.target_outcome,
                "active": query.active,
                "notes": query.notes,
                "created_at": query.created_at.isoformat() if query.created_at else None,
                "updated_at": query.updated_at.isoformat() if query.updated_at else None,
            })

        # Export responses
        responses = db.query(models.Response).all()
        for response in responses:
            data["responses"].append({
                "id": response.id,
                "user_id": response.user_id,
                "brand_id": response.brand_id,
                "query_id": response.query_id,
                "query_text": response.query_text,
                "platform": response.platform,
                "response_text": response.response_text,
                "timestamp": response.timestamp.isoformat() if response.timestamp else None,
                "brand_mentioned": response.brand_mentioned,
                "brand_position": response.brand_position,
                "sentiment": response.sentiment,
                "descriptors": response.descriptors,
                "competitors": response.competitors,
                "sources": response.sources,
                "campaign_period": response.campaign_period,
                "notes": response.notes,
                "analyzed_at": response.analyzed_at.isoformat() if response.analyzed_at else None,
            })

        # Export competitors
        competitors = db.query(models.Competitor).all()
        for competitor in competitors:
            data["competitors"].append({
                "id": competitor.id,
                "user_id": competitor.user_id,
                "brand_id": competitor.brand_id,
                "organization": competitor.organization,
                "type": competitor.type,
                "focus_area": competitor.focus_area,
                "track": competitor.track,
                "key_descriptors": competitor.key_descriptors,
                "website": competitor.website,
                "notes": competitor.notes,
                "created_at": competitor.created_at.isoformat() if competitor.created_at else None,
            })

        # Export target_descriptors
        descriptors = db.query(models.TargetDescriptor).all()
        for descriptor in descriptors:
            data["target_descriptors"].append({
                "id": descriptor.id,
                "user_id": descriptor.user_id,
                "brand_id": descriptor.brand_id,
                "descriptor": descriptor.descriptor,
                "category": descriptor.category,
                "is_target": descriptor.is_target,
                "current_ownership": descriptor.current_ownership,
                "priority": descriptor.priority,
                "notes": descriptor.notes,
                "created_at": descriptor.created_at.isoformat() if descriptor.created_at else None,
            })

        # Export campaigns
        campaigns = db.query(models.Campaign).all()
        for campaign in campaigns:
            data["campaigns"].append({
                "id": campaign.id,
                "user_id": campaign.user_id,
                "brand_id": campaign.brand_id,
                "campaign_name": campaign.campaign_name,
                "start_date": campaign.start_date.isoformat() if campaign.start_date else None,
                "end_date": campaign.end_date.isoformat() if campaign.end_date else None,
                "status": campaign.status,
                "target_narrative": campaign.target_narrative,
                "key_messages": campaign.key_messages,
                "success_metrics": campaign.success_metrics,
                "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
            })

        # Export reports
        reports = db.query(models.Report).all()
        for report in reports:
            data["reports"].append({
                "id": report.id,
                "user_id": report.user_id,
                "brand_id": report.brand_id,
                "title": report.title,
                "report_content": report.report_content,
                "start_date": report.start_date.isoformat() if report.start_date else None,
                "end_date": report.end_date.isoformat() if report.end_date else None,
                "total_responses": report.total_responses,
                "mention_rate": report.mention_rate,
                "google_doc_url": report.google_doc_url,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "updated_at": report.updated_at.isoformat() if report.updated_at else None,
            })

        # Export cited_sources
        sources = db.query(models.CitedSource).all()
        for source in sources:
            data["cited_sources"].append({
                "id": source.id,
                "user_id": source.user_id,
                "brand_id": source.brand_id,
                "source_name": source.source_name,
                "source_type": source.source_type,
                "authority_level": source.authority_level,
                "brand_coverage": source.brand_coverage,
                "last_cited": source.last_cited.isoformat() if source.last_cited else None,
                "notes": source.notes,
                "created_at": source.created_at.isoformat() if source.created_at else None,
            })

        # Save to JSON file
        output_file = os.path.join(PROJECT_ROOT, "sqlite_export.json")
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2, default=serialize_datetime)

        print(f"✓ Data exported successfully to {output_file}")
        print(f"  - Users: {len(data['users'])}")
        print(f"  - Brand Info: {len(data['brand_info'])}")
        print(f"  - Queries: {len(data['queries'])}")
        print(f"  - Responses: {len(data['responses'])}")
        print(f"  - Competitors: {len(data['competitors'])}")
        print(f"  - Target Descriptors: {len(data['target_descriptors'])}")
        print(f"  - Campaigns: {len(data['campaigns'])}")
        print(f"  - Reports: {len(data['reports'])}")
        print(f"  - Cited Sources: {len(data['cited_sources'])}")

    except Exception as e:
        print(f"✗ Error exporting data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    export_data()
