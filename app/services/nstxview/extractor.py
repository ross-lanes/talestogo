"""
LLM-based Information Extractor for NSTXView

Uses Claude to extract structured information from NSTX/NSTX-U research papers.
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from anthropic import Anthropic

from app.config import ANTHROPIC_API_KEY
from .prompts import (
    METADATA_EXTRACTION_PROMPT,
    SHOT_EXTRACTION_PROMPT,
    PARAMETER_EXTRACTION_PROMPT,
    PHENOMENON_EXTRACTION_PROMPT
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedMetadata:
    """Extracted paper metadata"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    experiment_type: Optional[str] = None
    key_findings: Optional[List[str]] = None


@dataclass
class ExtractedShot:
    """Extracted shot information"""
    shot_number: int
    role: str  # primary, comparison, reference
    context: Optional[str] = None
    characteristics: Optional[Dict[str, Any]] = None


@dataclass
class ExtractedParameter:
    """Extracted parameter value"""
    name: str
    category: str  # plasma, operational, performance
    value: Optional[float] = None
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    unit: Optional[str] = None
    uncertainty: Optional[float] = None
    shot_number: Optional[int] = None
    context: Optional[str] = None


@dataclass
class ExtractedPhenomenon:
    """Extracted phenomenon"""
    type: str
    category: str  # instability, confinement, transport, heating, disruption, divertor
    description: Optional[str] = None
    is_primary_focus: bool = False
    shot_numbers: Optional[List[int]] = None


@dataclass
class PaperExtraction:
    """Complete extraction result for a paper"""
    metadata: ExtractedMetadata
    shots: List[ExtractedShot]
    parameters: List[ExtractedParameter]
    phenomena: List[ExtractedPhenomenon]
    extraction_timestamp: str = None

    def __post_init__(self):
        if self.extraction_timestamp is None:
            self.extraction_timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "metadata": asdict(self.metadata) if self.metadata else None,
            "shots": [asdict(s) for s in self.shots],
            "parameters": [asdict(p) for p in self.parameters],
            "phenomena": [asdict(ph) for ph in self.phenomena],
            "extraction_timestamp": self.extraction_timestamp
        }


class PaperExtractor:
    """
    Extracts structured information from research papers using Claude.

    Uses multi-pass extraction for accuracy:
    1. Metadata extraction
    2. Shot number extraction
    3. Parameter extraction
    4. Phenomenon extraction
    """

    MODEL = "claude-sonnet-4-20250514"  # Using Claude Sonnet for cost efficiency
    MAX_TOKENS = 4096
    TEMPERATURE = 0.1  # Low temperature for more consistent extraction

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the extractor.

        Args:
            api_key: Anthropic API key. Uses ANTHROPIC_API_KEY env var if not provided.
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable."
            )
        self.client = Anthropic(api_key=self.api_key)

    def _call_claude(self, prompt: str, paper_text: str) -> str:
        """
        Make a call to Claude API.

        Args:
            prompt: The prompt template
            paper_text: Paper text to analyze

        Returns:
            Claude's response text
        """
        # Truncate text if too long (Claude has context limits)
        max_text_length = 100000  # ~25k tokens
        if len(paper_text) > max_text_length:
            paper_text = paper_text[:max_text_length] + "\n\n[Text truncated due to length]"

        formatted_prompt = prompt.format(paper_text=paper_text)

        try:
            response = self.client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from Claude's response.

        Handles cases where Claude includes extra text around the JSON.
        """
        # Try to parse directly first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from the response
        # Look for JSON object pattern
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # If all else fails, return empty dict
        logger.warning("Could not parse JSON from Claude response")
        return {}

    def extract_metadata(self, paper_text: str) -> ExtractedMetadata:
        """Extract metadata from paper text"""
        response = self._call_claude(METADATA_EXTRACTION_PROMPT, paper_text)
        data = self._parse_json_response(response)

        return ExtractedMetadata(
            title=data.get("title"),
            authors=data.get("authors"),
            journal=data.get("journal"),
            publication_year=data.get("publication_year"),
            doi=data.get("doi"),
            abstract=data.get("abstract"),
            experiment_type=data.get("experiment_type"),
            key_findings=data.get("key_findings")
        )

    def extract_shots(self, paper_text: str) -> List[ExtractedShot]:
        """Extract shot numbers and their context"""
        response = self._call_claude(SHOT_EXTRACTION_PROMPT, paper_text)
        data = self._parse_json_response(response)

        shots = []

        # Process individual shots
        for shot_data in data.get("shots", []):
            shot_number = shot_data.get("shot_number")
            if shot_number and self._validate_shot_number(shot_number):
                shots.append(ExtractedShot(
                    shot_number=shot_number,
                    role=shot_data.get("role", "reference"),
                    context=shot_data.get("context"),
                    characteristics=shot_data.get("characteristics")
                ))

        # Process shot ranges (expand to individual shots)
        for range_data in data.get("shot_ranges", []):
            start = range_data.get("start")
            end = range_data.get("end")
            if start and end and self._validate_shot_number(start) and self._validate_shot_number(end):
                # Don't expand large ranges
                if end - start <= 100:
                    context = range_data.get("context")
                    for shot_num in range(start, end + 1):
                        if not any(s.shot_number == shot_num for s in shots):
                            shots.append(ExtractedShot(
                                shot_number=shot_num,
                                role="reference",
                                context=context
                            ))

        return shots

    def extract_parameters(self, paper_text: str) -> List[ExtractedParameter]:
        """Extract plasma parameters from paper text"""
        response = self._call_claude(PARAMETER_EXTRACTION_PROMPT, paper_text)
        data = self._parse_json_response(response)

        parameters = []

        for param_data in data.get("parameters", []):
            parameters.append(ExtractedParameter(
                name=param_data.get("name", "unknown"),
                category=param_data.get("category", "plasma"),
                value=param_data.get("value"),
                value_min=param_data.get("value_min"),
                value_max=param_data.get("value_max"),
                unit=param_data.get("unit"),
                uncertainty=param_data.get("uncertainty"),
                shot_number=param_data.get("shot_number"),
                context=param_data.get("context")
            ))

        return parameters

    def extract_phenomena(self, paper_text: str) -> List[ExtractedPhenomenon]:
        """Extract plasma phenomena from paper text"""
        response = self._call_claude(PHENOMENON_EXTRACTION_PROMPT, paper_text)
        data = self._parse_json_response(response)

        phenomena = []

        for phenom_data in data.get("phenomena", []):
            phenomena.append(ExtractedPhenomenon(
                type=phenom_data.get("type", "unknown"),
                category=phenom_data.get("category", "other"),
                description=phenom_data.get("description"),
                is_primary_focus=phenom_data.get("is_primary_focus", False),
                shot_numbers=phenom_data.get("shot_numbers")
            ))

        return phenomena

    def _validate_shot_number(self, shot_number: int) -> bool:
        """Validate that shot number is 6 digits starting with 1"""
        return isinstance(shot_number, int) and 100000 <= shot_number <= 199999

    def extract_all(self, paper_text: str) -> PaperExtraction:
        """
        Perform complete extraction from paper text.

        This runs all extraction passes and combines the results.
        """
        logger.info("Starting paper extraction")

        # Run extractions
        metadata = self.extract_metadata(paper_text)
        logger.info(f"Extracted metadata: {metadata.title}")

        shots = self.extract_shots(paper_text)
        logger.info(f"Extracted {len(shots)} shots")

        parameters = self.extract_parameters(paper_text)
        logger.info(f"Extracted {len(parameters)} parameters")

        phenomena = self.extract_phenomena(paper_text)
        logger.info(f"Extracted {len(phenomena)} phenomena")

        return PaperExtraction(
            metadata=metadata,
            shots=shots,
            parameters=parameters,
            phenomena=phenomena
        )


# Convenience function
def get_extractor() -> PaperExtractor:
    """Get a configured PaperExtractor instance"""
    return PaperExtractor()
