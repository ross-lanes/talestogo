#!/usr/bin/env python3
"""
Batch Embedding Generation Script for NSTXView

This script generates embeddings for papers that don't have them yet.
Useful for:
- Migrating existing papers to use RAG
- Regenerating embeddings after model changes
- Catching up after processing pipeline failures

Usage:
    python scripts/admin/generate_embeddings.py --all                  # All papers without embeddings
    python scripts/admin/generate_embeddings.py --paper-ids 1 2 3      # Specific papers
    python scripts/admin/generate_embeddings.py --all --force          # Regenerate all (even if exists)
    python scripts/admin/generate_embeddings.py --all --workers 4      # Parallel processing
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

# Load environment
from dotenv import load_dotenv
env_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_embeddings_for_papers(
    paper_ids: List[int],
    force: bool = False,
    show_progress: bool = True
):
    """
    Generate embeddings for a list of papers.

    Args:
        paper_ids: List of paper IDs to process
        force: If True, regenerate even if embeddings exist
        show_progress: Show progress bars during processing
    """
    from app.database import SessionLocal
    from app.models import NSTXPaper, NSTXPaperChunk
    from app.services.nstxview.pdf_processor import PDFProcessor
    from app.services.nstxview.embedding_service import get_embedding_service, is_available
    from app.services.nstxview.vector_store import get_vector_store, is_available as vector_store_available
    from app.config import CHUNK_SIZE, CHUNK_OVERLAP

    # Check if services are available
    if not is_available():
        logger.error("Embedding service not available. Install sentence-transformers:")
        logger.error("  pip install sentence-transformers")
        return 0

    if not vector_store_available():
        logger.error("Vector store not available. Install chromadb:")
        logger.error("  pip install chromadb")
        return 0

    db = SessionLocal()
    pdf_processor = PDFProcessor()
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    processed_count = 0
    skipped_count = 0
    error_count = 0

    try:
        for i, paper_id in enumerate(paper_ids):
            paper = db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()
            if not paper:
                logger.warning(f"Paper {paper_id} not found, skipping")
                continue

            # Skip if already has embeddings (unless force)
            if paper.embedding_date and not force:
                logger.info(f"[{i+1}/{len(paper_ids)}] Paper {paper_id} already has embeddings, skipping")
                skipped_count += 1
                continue

            # Skip if doesn't have extracted text
            if not paper.extracted_text:
                logger.warning(f"[{i+1}/{len(paper_ids)}] Paper {paper_id} has no extracted text, skipping")
                skipped_count += 1
                continue

            try:
                logger.info(f"[{i+1}/{len(paper_ids)}] Processing paper {paper_id}: {paper.original_filename}")

                # Delete existing chunks if regenerating
                if force and paper.embedding_date:
                    logger.info(f"  Deleting existing chunks for paper {paper_id}")
                    vector_store.delete_paper(paper_id)
                    db.query(NSTXPaperChunk).filter(NSTXPaperChunk.paper_id == paper_id).delete()
                    db.commit()

                # Generate chunks
                logger.info(f"  Chunking text...")
                chunks = pdf_processor.chunk_text(
                    paper.extracted_text,
                    chunk_size=CHUNK_SIZE,
                    overlap=CHUNK_OVERLAP
                )

                if not chunks:
                    logger.warning(f"  No chunks generated for paper {paper_id}")
                    continue

                logger.info(f"  Generated {len(chunks)} chunks")

                # Generate embeddings
                logger.info(f"  Generating embeddings...")
                chunks_with_embeddings = embedding_service.generate_chunk_embeddings(
                    chunks,
                    batch_size=32
                )

                # Store in vector store
                logger.info(f"  Storing in ChromaDB...")
                embeddings = [chunk["embedding"] for chunk in chunks_with_embeddings]
                chunk_ids = vector_store.add_paper_chunks(
                    paper_id=paper_id,
                    chunks=chunks_with_embeddings,
                    embeddings=embeddings
                )

                # Store chunk metadata in PostgreSQL
                logger.info(f"  Saving chunk metadata...")
                for chunk, chromadb_id in zip(chunks_with_embeddings, chunk_ids):
                    chunk_record = NSTXPaperChunk(
                        paper_id=paper_id,
                        chunk_index=chunk['index'],
                        content=chunk['content'],
                        section=chunk.get('section'),
                        chromadb_id=chromadb_id
                    )
                    db.add(chunk_record)

                # Update paper
                paper.embedding_date = datetime.utcnow()
                db.commit()

                processed_count += 1
                logger.info(f"  ✓ Successfully generated {len(chunks)} chunks with embeddings")

            except Exception as e:
                logger.error(f"  ✗ Failed to process paper {paper_id}: {e}")
                error_count += 1
                db.rollback()

    finally:
        db.close()

    return processed_count, skipped_count, error_count


def main():
    parser = argparse.ArgumentParser(
        description="Generate embeddings for NSTXView papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate embeddings for all papers without them
  python scripts/admin/generate_embeddings.py --all

  # Generate for specific papers
  python scripts/admin/generate_embeddings.py --paper-ids 1 2 3 5 8

  # Regenerate embeddings for all papers (force)
  python scripts/admin/generate_embeddings.py --all --force

  # Check what would be processed (dry run)
  python scripts/admin/generate_embeddings.py --all --dry-run
        """
    )

    parser.add_argument('--all', action='store_true',
                       help='Process all papers without embeddings')
    parser.add_argument('--paper-ids', type=int, nargs='+',
                       help='Specific paper IDs to process')
    parser.add_argument('--force', action='store_true',
                       help='Regenerate embeddings even if they exist')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without actually doing it')
    parser.add_argument('--workers', type=int, default=1,
                       help='Number of parallel workers (default 1)')

    args = parser.parse_args()

    if not args.all and not args.paper_ids:
        parser.error("Must specify either --all or --paper-ids")

    # Get list of papers to process
    from app.database import SessionLocal
    from app.models import NSTXPaper

    db = SessionLocal()

    try:
        if args.all:
            # Get all papers without embeddings (or all if force)
            if args.force:
                query = db.query(NSTXPaper.id).filter(
                    NSTXPaper.extracted_text.isnot(None)
                )
                logger.info("Getting all papers with extracted text (force mode)...")
            else:
                query = db.query(NSTXPaper.id).filter(
                    NSTXPaper.extracted_text.isnot(None),
                    NSTXPaper.embedding_date.is_(None)
                )
                logger.info("Getting all papers without embeddings...")

            paper_ids = [row[0] for row in query.all()]
        else:
            paper_ids = args.paper_ids

        logger.info(f"Found {len(paper_ids)} papers to process")

        if args.dry_run:
            logger.info("DRY RUN - would process the following papers:")
            for paper_id in paper_ids:
                paper = db.query(NSTXPaper).filter(NSTXPaper.id == paper_id).first()
                if paper:
                    status = "✓ has embeddings" if paper.embedding_date else "○ no embeddings"
                    logger.info(f"  Paper {paper_id}: {paper.original_filename} [{status}]")
            logger.info(f"\nTotal: {len(paper_ids)} papers")
            return

        if not paper_ids:
            logger.info("No papers to process!")
            return

        # Show summary and confirm
        logger.info(f"\nAbout to process {len(paper_ids)} papers")
        if args.force:
            logger.info("FORCE MODE: Will regenerate embeddings even if they exist")
        logger.info("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")

        import time
        try:
            time.sleep(3)
        except KeyboardInterrupt:
            logger.info("\nCancelled by user")
            return

        # Process papers
        logger.info("\n" + "="*60)
        logger.info("Starting embedding generation...")
        logger.info("="*60 + "\n")

        start_time = datetime.now()

        if args.workers > 1:
            logger.warning("Parallel processing not yet implemented, using single worker")
            # TODO: Implement parallel processing with multiprocessing

        processed, skipped, errors = generate_embeddings_for_papers(
            paper_ids=paper_ids,
            force=args.force,
            show_progress=True
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info(f"Total papers:     {len(paper_ids)}")
        logger.info(f"Processed:        {processed}")
        logger.info(f"Skipped:          {skipped}")
        logger.info(f"Errors:           {errors}")
        logger.info(f"Duration:         {duration:.1f} seconds")
        if processed > 0:
            logger.info(f"Avg per paper:    {duration/processed:.1f} seconds")
        logger.info("="*60)

        if errors > 0:
            logger.warning(f"\n{errors} papers had errors. Check logs above for details.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
