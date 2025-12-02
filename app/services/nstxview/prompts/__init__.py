"""
Extraction Prompts for NSTXView

This package contains prompt templates for Claude-based extraction
of structured data from NSTX/NSTX-U plasma physics papers.
"""

from .paper_metadata import METADATA_EXTRACTION_PROMPT
from .shot_extraction import SHOT_EXTRACTION_PROMPT
from .parameter_extraction import PARAMETER_EXTRACTION_PROMPT
from .phenomenon_extraction import PHENOMENON_EXTRACTION_PROMPT

__all__ = [
    'METADATA_EXTRACTION_PROMPT',
    'SHOT_EXTRACTION_PROMPT',
    'PARAMETER_EXTRACTION_PROMPT',
    'PHENOMENON_EXTRACTION_PROMPT'
]
