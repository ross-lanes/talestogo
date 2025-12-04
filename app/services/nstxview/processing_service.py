"""
Processing Service for NSTXView

Handles background tasks for syncing papers from Google Drive and
running extraction pipelines.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import NSTXPaper, NSTXPaperChunk, NSTXProcessingTask, NSTXProcessingStatus
from app.services.nstxview.drive_client import get_drive_client
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


def perform_drive_sync(task_id: int) -> None:
    """
    Background task to sync papers from Google Drive.

    This function:
    1. Lists all PDFs in the configured Drive folder
    2. Compares with existing papers in the database
    3. Creates new NSTXPaper records for any new PDFs found
    4. Updates the task status throughout the process

    Args:
        task_id: ID of the NSTXProcessingTask to update
    """
    db: Session = SessionLocal()

    try:
        # Get the task and mark as running
        task = db.query(NSTXProcessingTask).filter(NSTXProcessingTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.status = 'running'
        task.started_at = datetime.utcnow()
        task.message = 'Connecting to Google Drive...'
        db.commit()

        # Get Drive client
        try:
            drive_client = get_drive_client()
        except Exception as e:
            task.status = 'error'
            task.message = f'Failed to connect to Google Drive: {str(e)}'
            task.completed_at = datetime.utcnow()
            db.commit()
            logger.error(f"Drive connection failed: {e}")
            return

        # Update status
        task.message = 'Listing PDFs in Drive folder...'
        db.commit()

        # Get existing file IDs from database
        existing_file_ids = set(
            row[0] for row in db.query(NSTXPaper.drive_file_id).all()
        )

        # Sync with Drive
        try:
            sync_result = drive_client.sync_with_database(existing_file_ids)
        except Exception as e:
            task.status = 'error'
            task.message = f'Failed to list files from Drive: {str(e)}'
            task.completed_at = datetime.utcnow()
            db.commit()
            logger.error(f"Drive sync failed: {e}")
            return

        new_files = sync_result['new']
        task.total_items = len(new_files)
        task.message = f'Found {len(new_files)} new papers to add'
        db.commit()

        # Get folder structure for subfolder tracking
        folder_paths = {}
        try:
            folder_paths = drive_client.get_folder_structure()
        except Exception as e:
            logger.warning(f"Could not get folder structure: {e}")

        # Add new papers to database
        added_count = 0
        for i, drive_file in enumerate(new_files):
            try:
                # Determine subfolder path
                subfolder = None
                if drive_file.parents:
                    subfolder = folder_paths.get(drive_file.parents[0], '')

                # Create new paper record
                paper = NSTXPaper(
                    drive_file_id=drive_file.id,
                    original_filename=drive_file.name,
                    subfolder=subfolder,
                    status=NSTXProcessingStatus.PENDING.value
                )
                db.add(paper)
                added_count += 1

                # Update progress
                task.processed_items = i + 1
                task.message = f'Added {added_count} of {len(new_files)} papers'

                # Commit in batches of 10
                if (i + 1) % 10 == 0:
                    db.commit()

            except Exception as e:
                logger.warning(f"Failed to add paper {drive_file.name}: {e}")
                continue

        # Final commit
        db.commit()

        # Mark task as completed
        task.status = 'completed'
        task.processed_items = len(new_files)
        task.message = f'Sync complete. Added {added_count} new papers.'
        task.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Drive sync completed: added {added_count} papers")

    except Exception as e:
        logger.error(f"Unexpected error in drive sync: {e}")
        try:
            task = db.query(NSTXProcessingTask).filter(NSTXProcessingTask.id == task_id).first()
            if task:
                task.status = 'error'
                task.message = f'Unexpected error: {str(e)}'
                task.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def perform_extraction(task_id: int, paper_ids: list) -> None:
    """
    Background task to extract data from papers.

    This function:
    1. Downloads PDFs from Drive
    2. Extracts text using PyMuPDF
    3. Extracts metadata, shots, parameters, and phenomena using Claude
    4. Updates paper records with extracted data

    Args:
        task_id: ID of the NSTXProcessingTask to update
        paper_ids: List of paper IDs to process
    """
    db: Session = SessionLocal()

    try:
        # Get the task and mark as running
        task = db.query(NSTXProcessingTask).filter(NSTXProcessingTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.status = 'running'
        task.started_at = datetime.utcnow()
        task.total_items = len(paper_ids)
        task.message = f'Starting extraction for {len(paper_ids)} papers...'
        db.commit()

        # Import processing modules
        from app.services.nstxview.pdf_processor import PDFProcessor
        from app.services.nstxview.extractor import PaperExtractor
        from app.services.nstxview.drive_client import get_drive_client

        drive_client = get_drive_client()
        pdf_processor = PDFProcessor()
        extractor = PaperExtractor()

        processed_count = 0
        error_count = 0

        for i, paper_id in enumerate(paper_ids):
            paper = db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()
            if not paper:
                continue

            try:
                # Update paper status
                paper.status = NSTXProcessingStatus.DOWNLOADING.value
                task.message = f'Processing paper {i+1}/{len(paper_ids)}: {paper.original_filename}'
                db.commit()

                # Download PDF to memory
                pdf_bytes = drive_client.download_to_bytes(paper.drive_file_id)

                # Extract text
                paper.status = NSTXProcessingStatus.EXTRACTING_TEXT.value
                db.commit()

                text_result = pdf_processor.extract_text(pdf_bytes)
                paper.extracted_text = text_result.get('text', '')
                paper.text_extraction_date = datetime.utcnow()

                # Extract structured data using Claude
                paper.status = NSTXProcessingStatus.EXTRACTING_DATA.value
                db.commit()

                extraction_result = extractor.extract_all(
                    paper.extracted_text,
                    paper.original_filename
                )

                # Update paper with extracted metadata
                if extraction_result.get('metadata'):
                    metadata = extraction_result['metadata']
                    paper.title = metadata.get('title')
                    paper.authors = str(metadata.get('authors', []))
                    paper.journal = metadata.get('journal')
                    paper.doi = metadata.get('doi')
                    paper.abstract = metadata.get('abstract')

                paper.data_extraction_date = datetime.utcnow()

                # Generate chunks and embeddings
                try:
                    paper.status = NSTXProcessingStatus.GENERATING_EMBEDDINGS.value
                    db.commit()

                    chunks_generated = _generate_and_store_embeddings(
                        db, paper, text_result, pdf_processor
                    )
                    if chunks_generated:
                        paper.embedding_date = datetime.utcnow()
                        logger.info(f"Generated {chunks_generated} chunks with embeddings for paper {paper_id}")
                except Exception as embed_error:
                    # Don't fail the whole extraction if embeddings fail
                    logger.warning(f"Failed to generate embeddings for paper {paper_id}: {embed_error}")

                paper.status = NSTXProcessingStatus.COMPLETED.value
                processed_count += 1

            except Exception as e:
                logger.error(f"Failed to process paper {paper_id}: {e}")
                paper.status = NSTXProcessingStatus.ERROR.value
                paper.error_message = str(e)
                error_count += 1

            # Update task progress
            task.processed_items = i + 1
            db.commit()

        # Mark task as completed
        task.status = 'completed'
        task.message = f'Extraction complete. Processed {processed_count} papers, {error_count} errors.'
        task.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Extraction completed: {processed_count} processed, {error_count} errors")

    except Exception as e:
        logger.error(f"Unexpected error in extraction: {e}")
        try:
            task = db.query(NSTXProcessingTask).filter(NSTXProcessingTask.id == task_id).first()
            if task:
                task.status = 'error'
                task.message = f'Unexpected error: {str(e)}'
                task.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


def _generate_and_store_embeddings(
    db: Session,
    paper: NSTXPaper,
    text_result: dict,
    pdf_processor
) -> int:
    """
    Internal helper to generate chunks and embeddings for a paper.

    Args:
        db: Database session
        paper: NSTXPaper object
        text_result: Result from pdf_processor.extract_text()
        pdf_processor: PDFProcessor instance

    Returns:
        Number of chunks generated
    """
    from app.services.nstxview.embedding_service import get_embedding_service, is_available
    from app.services.nstxview.vector_store import get_vector_store, is_available as vector_store_available

    # Check if services are available
    if not is_available():
        logger.warning("Embedding service not available, skipping embeddings")
        return 0

    if not vector_store_available():
        logger.warning("Vector store not available, skipping embeddings")
        return 0

    # Generate chunks
    sections = text_result.get('sections', [])
    if sections:
        # Use section-aware chunking
        chunks = pdf_processor.chunk_by_sections(sections, chunk_size=CHUNK_SIZE)
    else:
        # Fall back to simple chunking
        full_text = text_result.get('text', '')
        chunks = pdf_processor.chunk_text(full_text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

    if not chunks:
        logger.warning(f"No chunks generated for paper {paper.id}")
        return 0

    logger.info(f"Generated {len(chunks)} chunks for paper {paper.id}")

    # Generate embeddings
    embedding_service = get_embedding_service()
    chunks_with_embeddings = embedding_service.generate_chunk_embeddings(chunks, batch_size=32)

    # Store in vector store
    vector_store = get_vector_store()

    # Prepare embeddings list
    embeddings = [chunk["embedding"] for chunk in chunks_with_embeddings]

    # Add to vector store
    chunk_ids = vector_store.add_paper_chunks(
        paper_id=paper.id,
        chunks=chunks_with_embeddings,
        embeddings=embeddings
    )

    # Store chunk metadata in PostgreSQL
    for i, (chunk, chromadb_id) in enumerate(zip(chunks_with_embeddings, chunk_ids)):
        chunk_record = NSTXPaperChunk(
            paper_id=paper.id,
            chunk_index=chunk['index'],
            content=chunk['content'],
            section=chunk.get('section'),
            chromadb_id=chromadb_id
        )
        db.add(chunk_record)

    db.commit()

    return len(chunks)


def perform_embedding_generation(task_id: int, paper_ids: list) -> None:
    """
    Background task to generate embeddings for papers that don't have them.

    This function:
    1. Loads papers that already have extracted text
    2. Generates chunks from the text
    3. Generates embeddings for the chunks
    4. Stores embeddings in ChromaDB and metadata in PostgreSQL

    Args:
        task_id: ID of the NSTXProcessingTask to update
        paper_ids: List of paper IDs to process
    """
    db: Session = SessionLocal()

    try:
        # Get the task and mark as running
        task = db.query(NSTXProcessingTask).filter(NSTXProcessingTask.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.status = 'running'
        task.started_at = datetime.utcnow()
        task.total_items = len(paper_ids)
        task.message = f'Starting embedding generation for {len(paper_ids)} papers...'
        db.commit()

        # Import required modules
        from app.services.nstxview.pdf_processor import PDFProcessor

        pdf_processor = PDFProcessor()
        processed_count = 0
        error_count = 0

        for i, paper_id in enumerate(paper_ids):
            paper = db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()
            if not paper:
                continue

            # Skip if already has embeddings
            if paper.embedding_date:
                logger.info(f"Paper {paper_id} already has embeddings, skipping")
                continue

            # Skip if doesn't have extracted text
            if not paper.extracted_text:
                logger.warning(f"Paper {paper_id} has no extracted text, skipping")
                continue

            try:
                task.message = f'Generating embeddings for paper {i+1}/{len(paper_ids)}: {paper.original_filename}'
                db.commit()

                # Create a text_result dict for compatibility
                text_result = {
                    'text': paper.extracted_text,
                    'sections': []  # We don't have sections saved, so use simple chunking
                }

                # Generate and store embeddings
                chunks_generated = _generate_and_store_embeddings(
                    db, paper, text_result, pdf_processor
                )

                if chunks_generated:
                    paper.embedding_date = datetime.utcnow()
                    processed_count += 1
                    logger.info(f"Generated {chunks_generated} chunks for paper {paper_id}")

            except Exception as e:
                logger.error(f"Failed to generate embeddings for paper {paper_id}: {e}")
                error_count += 1

            # Update task progress
            task.processed_items = i + 1
            db.commit()

        # Mark task as completed
        task.status = 'completed'
        task.message = f'Embedding generation complete. Processed {processed_count} papers, {error_count} errors.'
        task.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Embedding generation completed: {processed_count} processed, {error_count} errors")

    except Exception as e:
        logger.error(f"Unexpected error in embedding generation: {e}")
        try:
            task = db.query(NSTXProcessingTask).filter(NSTXProcessingTask.id == task_id).first()
            if task:
                task.status = 'error'
                task.message = f'Unexpected error: {str(e)}'
                task.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
