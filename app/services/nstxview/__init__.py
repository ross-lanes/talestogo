"""
NSTXView Services

This package contains services for processing and analyzing NSTX/NSTX-U
plasma physics research papers.

Modules:
- drive_client: Google Drive integration for paper retrieval
- pdf_processor: PDF text and metadata extraction
- extractor: LLM-based information extraction
- vector_store: ChromaDB integration for semantic search
"""

from .drive_client import DriveClient, get_drive_client
from .pdf_processor import PDFProcessor, get_pdf_processor
from .extractor import PaperExtractor, get_extractor, PaperExtraction
from .vector_store import VectorStore, get_vector_store, is_available as vector_store_available

__all__ = [
    'DriveClient',
    'get_drive_client',
    'PDFProcessor',
    'get_pdf_processor',
    'PaperExtractor',
    'get_extractor',
    'PaperExtraction',
    'VectorStore',
    'get_vector_store',
    'vector_store_available'
]
