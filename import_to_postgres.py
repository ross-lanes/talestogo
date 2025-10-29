#!/usr/bin/env python3
"""
Import data from JSON export into PostgreSQL database.
Run this script AFTER setting up PostgreSQL database and setting DATABASE_URL environment variable.
"""
import json
import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal
from app.models import Base
from app import models

def parse_datetime(dt_string):
    """Parse ISO datetime string."""
    if dt_string:
        return datetime.fromisoformat(dt_string)
    return None

def import_data():
    """Import data from JSON file into PostgreSQL database."""
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(PROJECT_ROOT, "sqlite_export.json")

    if not os.path.exists(input_file):
        print(f"✗ Error: {input_file} not found. Run export_sqlite_data.py first.")
        return

    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    # Load JSON data
    with open(input_file, "r") as f:
        data = json.load(f)

    db = SessionLocal()

    try:
        # Import users
        print(f"Importing {len(data['users'])} users...")
        for user_data in data['users']:
            user = models.User(
                id=user_data['id'],
                email=user_data['email'],
                hashed_password=user_data['hashed_password'],
                full_name=user_data['full_name'],
                organization=user_data['organization'],
                is_admin=user_data['is_admin'],
                is_active=user_data['is_active'],
                is_invited=user_data['is_invited'],
                google_id=user_data['google_id'],
                oauth_provider=user_data['oauth_provider'],
                picture_url=user_data['picture_url'],
                openai_api_key_encrypted=user_data['openai_api_key_encrypted'],
                anthropic_api_key_encrypted=user_data['anthropic_api_key_encrypted'],
                gemini_api_key_encrypted=user_data['gemini_api_key_encrypted'],
                perplexity_api_key_encrypted=user_data['perplexity_api_key_encrypted'],
                created_at=parse_datetime(user_data['created_at']),
                updated_at=parse_datetime(user_data['updated_at']),
            )
            db.add(user)

        # Import brand_info
        print(f"Importing {len(data['brand_info'])} brand info records...")
        for brand_data in data['brand_info']:
            brand = models.BrandInfo(
                id=brand_data['id'],
                user_id=brand_data['user_id'],
                brand_name=brand_data['brand_name'],
                industry=brand_data['industry'],
                description=brand_data['description'],
                strategic_messages=brand_data['strategic_messages'],
                is_active=brand_data['is_active'],
                created_at=parse_datetime(brand_data['created_at']),
                updated_at=parse_datetime(brand_data['updated_at']),
            )
            db.add(brand)

        # Import queries
        print(f"Importing {len(data['queries'])} queries...")
        for query_data in data['queries']:
            query = models.Query(
                id=query_data['id'],
                user_id=query_data['user_id'],
                brand_id=query_data['brand_id'],
                query_id=query_data['query_id'],
                query_text=query_data['query_text'],
                category=query_data['category'],
                priority=query_data['priority'],
                target_outcome=query_data['target_outcome'],
                active=query_data['active'],
                notes=query_data['notes'],
                created_at=parse_datetime(query_data['created_at']),
                updated_at=parse_datetime(query_data['updated_at']),
            )
            db.add(query)

        # Import responses
        print(f"Importing {len(data['responses'])} responses...")
        for response_data in data['responses']:
            response = models.Response(
                id=response_data['id'],
                user_id=response_data['user_id'],
                brand_id=response_data['brand_id'],
                query_id=response_data['query_id'],
                query_text=response_data['query_text'],
                platform=response_data['platform'],
                response_text=response_data['response_text'],
                timestamp=parse_datetime(response_data['timestamp']),
                brand_mentioned=response_data['brand_mentioned'],
                brand_position=response_data['brand_position'],
                sentiment=response_data['sentiment'],
                descriptors=response_data['descriptors'],
                competitors=response_data['competitors'],
                sources=response_data['sources'],
                campaign_period=response_data['campaign_period'],
                notes=response_data['notes'],
                analyzed_at=parse_datetime(response_data['analyzed_at']),
            )
            db.add(response)

        # Import competitors
        print(f"Importing {len(data['competitors'])} competitors...")
        for comp_data in data['competitors']:
            competitor = models.Competitor(
                id=comp_data['id'],
                user_id=comp_data['user_id'],
                brand_id=comp_data['brand_id'],
                organization=comp_data['organization'],
                type=comp_data['type'],
                focus_area=comp_data['focus_area'],
                track=comp_data['track'],
                key_descriptors=comp_data['key_descriptors'],
                website=comp_data['website'],
                notes=comp_data['notes'],
                created_at=parse_datetime(comp_data['created_at']),
            )
            db.add(competitor)

        # Import target_descriptors
        print(f"Importing {len(data['target_descriptors'])} target descriptors...")
        for desc_data in data['target_descriptors']:
            descriptor = models.TargetDescriptor(
                id=desc_data['id'],
                user_id=desc_data['user_id'],
                brand_id=desc_data['brand_id'],
                descriptor=desc_data['descriptor'],
                category=desc_data['category'],
                is_target=desc_data['is_target'],
                current_ownership=desc_data['current_ownership'],
                priority=desc_data['priority'],
                notes=desc_data['notes'],
                created_at=parse_datetime(desc_data['created_at']),
            )
            db.add(descriptor)

        # Import campaigns
        print(f"Importing {len(data['campaigns'])} campaigns...")
        for campaign_data in data['campaigns']:
            campaign = models.Campaign(
                id=campaign_data['id'],
                user_id=campaign_data['user_id'],
                brand_id=campaign_data['brand_id'],
                campaign_name=campaign_data['campaign_name'],
                start_date=parse_datetime(campaign_data['start_date']),
                end_date=parse_datetime(campaign_data['end_date']),
                status=campaign_data['status'],
                target_narrative=campaign_data['target_narrative'],
                key_messages=campaign_data['key_messages'],
                success_metrics=campaign_data['success_metrics'],
                created_at=parse_datetime(campaign_data['created_at']),
            )
            db.add(campaign)

        # Import reports
        print(f"Importing {len(data['reports'])} reports...")
        for report_data in data['reports']:
            report = models.Report(
                id=report_data['id'],
                user_id=report_data['user_id'],
                brand_id=report_data['brand_id'],
                title=report_data['title'],
                report_content=report_data['report_content'],
                start_date=parse_datetime(report_data['start_date']),
                end_date=parse_datetime(report_data['end_date']),
                total_responses=report_data['total_responses'],
                mention_rate=report_data['mention_rate'],
                google_doc_url=report_data['google_doc_url'],
                created_at=parse_datetime(report_data['created_at']),
                updated_at=parse_datetime(report_data['updated_at']),
            )
            db.add(report)

        # Import cited_sources
        print(f"Importing {len(data['cited_sources'])} cited sources...")
        for source_data in data['cited_sources']:
            source = models.CitedSource(
                id=source_data['id'],
                user_id=source_data['user_id'],
                brand_id=source_data['brand_id'],
                source_name=source_data['source_name'],
                source_type=source_data['source_type'],
                authority_level=source_data['authority_level'],
                brand_coverage=source_data['brand_coverage'],
                last_cited=parse_datetime(source_data['last_cited']),
                notes=source_data['notes'],
                created_at=parse_datetime(source_data['created_at']),
            )
            db.add(source)

        # Commit all changes
        print("Committing changes to database...")
        db.commit()

        print("✓ Data import completed successfully!")
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
        print(f"✗ Error importing data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # Check if DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("✗ Error: DATABASE_URL environment variable not set.")
        print("Set it to your PostgreSQL connection string before running this script.")
        print("Example: export DATABASE_URL='postgresql://user:password@host:port/database'")
        sys.exit(1)

    import_data()
