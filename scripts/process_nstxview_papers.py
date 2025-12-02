#!/usr/bin/env python3
"""
NSTXView Paper Processing Script

This script:
1. Syncs papers from Google Drive to the database
2. Downloads PDFs and extracts text
3. Uses Claude to extract structured information (shots, parameters, phenomena)
4. Generates embeddings for semantic search

Usage:
    python scripts/process_nstxview_papers.py --sync           # Just sync from Drive
    python scripts/process_nstxview_papers.py --extract        # Extract from pending papers
    python scripts/process_nstxview_papers.py --all            # Full pipeline
    python scripts/process_nstxview_papers.py --paper-id 123   # Process specific paper
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add the app directory to the path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Default Railway dev database URL for NSTXView
NSTXVIEW_DEV_DATABASE_URL = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway"

# Preserve DATABASE_URL if provided via command line
_db_url_override = os.environ.get('DATABASE_URL')

# Load .env file if it exists (for API keys etc)
from dotenv import load_dotenv
env_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# Restore DATABASE_URL: prefer command-line override, then use NSTXView dev DB
# (ignoring .env's local DATABASE_URL for this script)
if _db_url_override:
    os.environ['DATABASE_URL'] = _db_url_override
else:
    os.environ['DATABASE_URL'] = NSTXVIEW_DEV_DATABASE_URL

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway"
)

# Google credentials
GOOGLE_CREDENTIALS_PATH = os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "/Users/rachelkremen/Documents/Code/NSTXView/talesai111-c6195629d677.json"
)

# Storage directory for downloaded PDFs
STORAGE_DIR = Path(__file__).parent.parent / "data" / "nstxview_pdfs"


def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


def sync_from_drive(db):
    """Sync papers from Google Drive to database"""
    from app.services.nstxview.drive_client import DriveClient
    from app.models import NSTXPaper, NSTXProcessingStatus

    logger.info("Starting sync from Google Drive...")

    # Initialize Drive client
    client = DriveClient(credentials_path=GOOGLE_CREDENTIALS_PATH)

    # Get all PDFs from Drive
    try:
        pdf_files = client.list_pdfs()
        logger.info(f"Found {len(pdf_files)} PDF files in Drive")
    except Exception as e:
        logger.error(f"Error listing files from Drive: {e}")
        return 0

    # Get folder structure for subfolder tracking
    folder_paths = client.get_folder_structure()

    # Get existing papers
    existing = {p.drive_file_id: p for p in db.query(NSTXPaper).all()}

    new_count = 0
    for pdf_file in pdf_files:
        if pdf_file.id in existing:
            logger.debug(f"Skipping existing paper: {pdf_file.name}")
            continue

        # Determine subfolder
        subfolder = None
        if pdf_file.parents:
            parent_id = pdf_file.parents[0]
            subfolder = folder_paths.get(parent_id, "")

        # Create new paper record
        paper = NSTXPaper(
            drive_file_id=pdf_file.id,
            original_filename=pdf_file.name,
            subfolder=subfolder,
            status=NSTXProcessingStatus.PENDING.value,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(paper)
        new_count += 1
        logger.info(f"Added new paper: {pdf_file.name}")

    db.commit()
    logger.info(f"Sync complete. Added {new_count} new papers.")
    return new_count


def download_and_extract_text(db, paper):
    """Download PDF and extract text"""
    from app.services.nstxview.drive_client import DriveClient
    from app.services.nstxview.pdf_processor import PDFProcessor
    from app.models import NSTXProcessingStatus

    logger.info(f"Processing paper: {paper.original_filename}")

    # Update status
    paper.status = NSTXProcessingStatus.DOWNLOADING.value
    db.commit()

    # Download PDF
    client = DriveClient(credentials_path=GOOGLE_CREDENTIALS_PATH)

    try:
        pdf_bytes = client.download_to_bytes(paper.drive_file_id)
        logger.info(f"Downloaded {len(pdf_bytes)} bytes")
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        paper.status = NSTXProcessingStatus.ERROR.value
        paper.error_message = f"Download error: {str(e)}"
        db.commit()
        return False

    # Extract text
    paper.status = NSTXProcessingStatus.EXTRACTING_TEXT.value
    db.commit()

    try:
        processor = PDFProcessor()
        result = processor.extract_from_bytes(pdf_bytes)

        paper.extracted_text = result.full_text
        paper.page_count = result.metadata.page_count

        # Try to get title from PDF metadata
        if result.metadata.title:
            paper.title = result.metadata.title

        logger.info(f"Extracted {len(result.full_text)} characters, {result.metadata.page_count} pages")

        db.commit()
        return True

    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        paper.status = NSTXProcessingStatus.ERROR.value
        paper.error_message = f"Text extraction error: {str(e)}"
        db.commit()
        return False


def extract_structured_data(db, paper):
    """Extract structured data using Claude"""
    from app.services.nstxview.extractor import PaperExtractor
    from app.models import (
        NSTXShot, NSTXParameter, NSTXPhenomenon,
        NSTXProcessingStatus
    )

    if not paper.extracted_text:
        logger.warning(f"No extracted text for paper {paper.id}")
        return False

    logger.info(f"Extracting structured data from: {paper.original_filename}")

    paper.status = NSTXProcessingStatus.EXTRACTING_DATA.value
    db.commit()

    try:
        extractor = PaperExtractor()
        extraction = extractor.extract_all(paper.extracted_text)

        # Update paper metadata from extraction
        if extraction.metadata:
            meta = extraction.metadata
            if meta.title:
                paper.title = meta.title
            if meta.authors:
                paper.authors = json.dumps(meta.authors)
            if meta.journal:
                paper.journal = meta.journal
            if meta.publication_year:
                paper.publication_date = f"{meta.publication_year}-01-01"
            if meta.doi:
                paper.doi = meta.doi
            if meta.abstract:
                paper.abstract = meta.abstract
            if meta.key_findings:
                paper.key_findings = json.dumps(meta.key_findings)
            if meta.experiment_type:
                paper.experiment_type = meta.experiment_type

        # Create shot records
        shot_map = {}  # Maps shot_number to shot record for linking
        for shot_data in extraction.shots:
            shot = NSTXShot(
                paper_id=paper.id,
                shot_number=shot_data.shot_number,
                role=shot_data.role,
                context=shot_data.context,
                characteristics=json.dumps(shot_data.characteristics) if shot_data.characteristics else None
            )
            db.add(shot)
            db.flush()  # Get the ID
            shot_map[shot_data.shot_number] = shot

        logger.info(f"Created {len(extraction.shots)} shot records")

        # Create parameter records
        for param_data in extraction.parameters:
            # Try to link to shot if shot_number provided
            shot_id = None
            if param_data.shot_number and param_data.shot_number in shot_map:
                shot_id = shot_map[param_data.shot_number].id

            # Validate numeric values - skip parameters with non-numeric values
            # (the LLM sometimes extracts text values like "He/D" for gas species)
            value = param_data.value
            value_min = param_data.value_min
            value_max = param_data.value_max
            uncertainty = param_data.uncertainty

            # Convert to float if possible, otherwise set to None
            def safe_float(v):
                if v is None:
                    return None
                try:
                    return float(v)
                except (ValueError, TypeError):
                    return None

            value = safe_float(value)
            value_min = safe_float(value_min)
            value_max = safe_float(value_max)
            uncertainty = safe_float(uncertainty)

            # Skip if all numeric values are None (parameter has no usable data)
            if value is None and value_min is None and value_max is None:
                logger.debug(f"Skipping non-numeric parameter: {param_data.name} = {param_data.value}")
                continue

            param = NSTXParameter(
                paper_id=paper.id,
                shot_id=shot_id,
                parameter_name=param_data.name,
                parameter_category=param_data.category,
                value=value,
                value_min=value_min,
                value_max=value_max,
                unit=param_data.unit,
                uncertainty=uncertainty,
                context=param_data.context
            )
            db.add(param)

        logger.info(f"Created {len(extraction.parameters)} parameter records")

        # Create phenomenon records
        for phenom_data in extraction.phenomena:
            # Link to shots if shot_numbers provided
            shot_ids = []
            if phenom_data.shot_numbers:
                for sn in phenom_data.shot_numbers:
                    if sn in shot_map:
                        shot_ids.append(shot_map[sn].id)

            # Create one record per shot, or one without shot if none
            if shot_ids:
                for shot_id in shot_ids:
                    phenom = NSTXPhenomenon(
                        paper_id=paper.id,
                        shot_id=shot_id,
                        phenomenon_type=phenom_data.type,
                        phenomenon_category=phenom_data.category,
                        description=phenom_data.description,
                        is_primary_focus=phenom_data.is_primary_focus
                    )
                    db.add(phenom)
            else:
                phenom = NSTXPhenomenon(
                    paper_id=paper.id,
                    shot_id=None,
                    phenomenon_type=phenom_data.type,
                    phenomenon_category=phenom_data.category,
                    description=phenom_data.description,
                    is_primary_focus=phenom_data.is_primary_focus
                )
                db.add(phenom)

        logger.info(f"Created {len(extraction.phenomena)} phenomenon records")

        paper.status = NSTXProcessingStatus.COMPLETED.value
        paper.updated_at = datetime.now(timezone.utc)
        db.commit()

        return True

    except Exception as e:
        logger.error(f"Error extracting data: {e}")
        import traceback
        traceback.print_exc()
        paper.status = NSTXProcessingStatus.ERROR.value
        paper.error_message = f"Data extraction error: {str(e)}"
        db.commit()
        return False


def process_paper(db, paper_id: int):
    """Process a single paper through the full pipeline"""
    from app.models import NSTXPaper

    paper = db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()
    if not paper:
        logger.error(f"Paper {paper_id} not found")
        return False

    # Download and extract text
    if not paper.extracted_text:
        success = download_and_extract_text(db, paper)
        if not success:
            return False

    # Extract structured data
    success = extract_structured_data(db, paper)
    return success


def process_pending_papers(db, limit: int = None):
    """Process all pending papers"""
    from app.models import NSTXPaper, NSTXProcessingStatus

    query = db.query(NSTXPaper).filter(
        NSTXPaper.status == NSTXProcessingStatus.PENDING.value
    )

    if limit:
        query = query.limit(limit)

    papers = query.all()
    logger.info(f"Found {len(papers)} pending papers to process")

    success_count = 0
    error_count = 0

    for i, paper in enumerate(papers):
        logger.info(f"Processing paper {i+1}/{len(papers)}: {paper.original_filename}")

        try:
            # Download and extract text
            if not paper.extracted_text:
                text_ok = download_and_extract_text(db, paper)
                if not text_ok:
                    error_count += 1
                    continue

            # Extract structured data
            data_ok = extract_structured_data(db, paper)
            if data_ok:
                success_count += 1
            else:
                error_count += 1

        except Exception as e:
            logger.error(f"Unexpected error processing paper {paper.id}: {e}")
            error_count += 1

    logger.info(f"Processing complete. Success: {success_count}, Errors: {error_count}")
    return success_count, error_count


def show_status(db):
    """Show current processing status"""
    from app.models import NSTXPaper, NSTXShot, NSTXParameter, NSTXPhenomenon
    from sqlalchemy import func

    total = db.query(func.count(NSTXPaper.id)).scalar()
    pending = db.query(func.count(NSTXPaper.id)).filter(NSTXPaper.status == 'pending').scalar()
    completed = db.query(func.count(NSTXPaper.id)).filter(NSTXPaper.status == 'completed').scalar()
    errors = db.query(func.count(NSTXPaper.id)).filter(NSTXPaper.status == 'error').scalar()

    shots = db.query(func.count(NSTXShot.id)).scalar()
    unique_shots = db.query(func.count(func.distinct(NSTXShot.shot_number))).scalar()
    params = db.query(func.count(NSTXParameter.id)).scalar()
    phenomena = db.query(func.count(NSTXPhenomenon.id)).scalar()

    print("\n=== NSTXView Processing Status ===")
    print(f"Papers: {total} total, {pending} pending, {completed} completed, {errors} errors")
    print(f"Shots: {shots} mentions, {unique_shots} unique")
    print(f"Parameters: {params}")
    print(f"Phenomena: {phenomena}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Process NSTXView papers")
    parser.add_argument("--sync", action="store_true", help="Sync papers from Google Drive")
    parser.add_argument("--extract", action="store_true", help="Extract from pending papers")
    parser.add_argument("--all", action="store_true", help="Full pipeline: sync + extract")
    parser.add_argument("--paper-id", type=int, help="Process a specific paper by ID")
    parser.add_argument("--limit", type=int, help="Limit number of papers to process")
    parser.add_argument("--status", action="store_true", help="Show current status")

    args = parser.parse_args()

    # Default to showing status if no args
    if not any([args.sync, args.extract, args.all, args.paper_id, args.status]):
        args.status = True

    db = get_db_session()

    try:
        if args.status:
            show_status(db)

        if args.sync or args.all:
            sync_from_drive(db)

        if args.paper_id:
            process_paper(db, args.paper_id)
        elif args.extract or args.all:
            process_pending_papers(db, limit=args.limit)

        if args.sync or args.extract or args.all or args.paper_id:
            show_status(db)

    finally:
        db.close()


if __name__ == "__main__":
    main()
