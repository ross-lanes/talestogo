"""
PDF Processor for NSTXView

Extracts text, tables, and metadata from scientific PDF papers.
Handles complex layouts common in plasma physics publications.
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import io

logger = logging.getLogger(__name__)

# Try to import fitz (PyMuPDF)
try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    logger.warning("PyMuPDF not installed. PDF processing will be limited.")


@dataclass
class ExtractedSection:
    """A section of extracted text from a paper"""
    name: str  # Section name (e.g., 'abstract', 'introduction', 'methods')
    content: str
    page_start: int
    page_end: int


@dataclass
class ExtractedTable:
    """An extracted table from a paper"""
    content: str  # Table as text
    caption: Optional[str]
    page: int


@dataclass
class PDFMetadata:
    """Metadata extracted from PDF"""
    title: Optional[str]
    authors: Optional[List[str]]
    creation_date: Optional[str]
    modification_date: Optional[str]
    producer: Optional[str]
    page_count: int


@dataclass
class ExtractionResult:
    """Complete extraction result from a PDF"""
    full_text: str
    sections: List[ExtractedSection]
    tables: List[ExtractedTable]
    metadata: PDFMetadata
    figure_captions: List[str]


class PDFProcessor:
    """
    Extracts text and structured data from scientific PDFs.

    Handles:
    - Multi-column layouts
    - Section detection
    - Table extraction
    - Figure caption extraction
    - Metadata parsing
    """

    # Common section headers in scientific papers
    SECTION_PATTERNS = [
        r'^\s*(?:I\.?\s+)?ABSTRACT\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?INTRODUCTION\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?BACKGROUND\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?EXPERIMENT(?:AL)?\s*(?:SETUP)?\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?METHOD(?:S|OLOGY)?\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?RESULT(?:S)?\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?DISCUSSION\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?CONCLUSION(?:S)?\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?ACKNOWLEDGMENT(?:S)?\s*$',
        r'^\s*(?:I{1,3}\.?\s+)?REFERENCE(?:S)?\s*$',
    ]

    # Shot number pattern - 6 digits starting with 1
    SHOT_NUMBER_PATTERN = r'\b(?:shot\s*#?\s*|#)?([1][0-9]{5})\b'

    def __init__(self):
        if not HAS_PYMUPDF:
            raise ImportError(
                "PyMuPDF is required for PDF processing. "
                "Install it with: pip install pymupdf"
            )

    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extract text and structured data from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            ExtractionResult with all extracted data
        """
        with open(file_path, 'rb') as f:
            return self.extract_from_bytes(f.read())

    def extract_from_bytes(self, pdf_bytes: bytes) -> ExtractionResult:
        """
        Extract text and structured data from PDF bytes.

        Args:
            pdf_bytes: PDF file contents as bytes

        Returns:
            ExtractionResult with all extracted data
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        try:
            # Extract metadata
            metadata = self._extract_metadata(doc)

            # Extract all text
            full_text, page_texts = self._extract_text(doc)

            # Identify sections
            sections = self._identify_sections(page_texts)

            # Extract tables (basic)
            tables = self._extract_tables(doc)

            # Extract figure captions
            figure_captions = self._extract_figure_captions(full_text)

            return ExtractionResult(
                full_text=full_text,
                sections=sections,
                tables=tables,
                metadata=metadata,
                figure_captions=figure_captions
            )

        finally:
            doc.close()

    def _extract_metadata(self, doc: fitz.Document) -> PDFMetadata:
        """Extract metadata from PDF document"""
        meta = doc.metadata

        # Try to extract title from metadata or first page
        title = meta.get('title')
        if not title or len(title) < 5:
            # Try to get title from first page (usually largest text)
            title = self._extract_title_from_first_page(doc)

        # Try to extract authors
        authors = None
        author_str = meta.get('author')
        if author_str:
            # Split on common separators
            authors = [a.strip() for a in re.split(r'[,;]|and', author_str) if a.strip()]

        return PDFMetadata(
            title=title,
            authors=authors,
            creation_date=meta.get('creationDate'),
            modification_date=meta.get('modDate'),
            producer=meta.get('producer'),
            page_count=len(doc)
        )

    def _extract_title_from_first_page(self, doc: fitz.Document) -> Optional[str]:
        """Try to extract title from the first page by finding largest text"""
        if len(doc) == 0:
            return None

        page = doc[0]
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

        # Find text blocks with largest font size
        text_items = []
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text_items.append({
                        "text": span["text"].strip(),
                        "size": span["size"],
                        "y": span["bbox"][1]
                    })

        if not text_items:
            return None

        # Sort by font size (descending) and y position (ascending - top of page)
        text_items.sort(key=lambda x: (-x["size"], x["y"]))

        # Take the largest text from the top of the page
        for item in text_items[:5]:
            text = item["text"]
            # Filter out short texts and page numbers
            if len(text) > 10 and not text.isdigit():
                return text

        return None

    def _extract_text(self, doc: fitz.Document) -> Tuple[str, List[Dict]]:
        """
        Extract all text from document.

        Returns:
            Tuple of (full_text, list of page_data dicts)
        """
        all_text = []
        page_texts = []

        for page_num, page in enumerate(doc):
            # Get text preserving layout
            text = page.get_text("text", sort=True)
            all_text.append(text)

            page_texts.append({
                "page": page_num,
                "text": text
            })

        full_text = "\n\n".join(all_text)

        # Clean up common OCR/extraction issues
        full_text = self._clean_text(full_text)

        return full_text, page_texts

    def _clean_text(self, text: str) -> str:
        """Clean up extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        # Fix common ligature issues
        text = text.replace('ﬁ', 'fi')
        text = text.replace('ﬂ', 'fl')
        text = text.replace('ﬀ', 'ff')

        # Remove page numbers that appear alone
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)

        return text.strip()

    def _identify_sections(self, page_texts: List[Dict]) -> List[ExtractedSection]:
        """Identify and extract sections from the text"""
        sections = []
        current_section = None
        current_content = []
        current_start_page = 0

        for page_data in page_texts:
            page_num = page_data["page"]
            lines = page_data["text"].split('\n')

            for line in lines:
                # Check if this line is a section header
                section_name = self._detect_section_header(line)

                if section_name:
                    # Save previous section
                    if current_section:
                        sections.append(ExtractedSection(
                            name=current_section,
                            content='\n'.join(current_content).strip(),
                            page_start=current_start_page,
                            page_end=page_num
                        ))

                    # Start new section
                    current_section = section_name
                    current_content = []
                    current_start_page = page_num
                else:
                    current_content.append(line)

        # Save final section
        if current_section and current_content:
            sections.append(ExtractedSection(
                name=current_section,
                content='\n'.join(current_content).strip(),
                page_start=current_start_page,
                page_end=len(page_texts) - 1
            ))

        return sections

    def _detect_section_header(self, line: str) -> Optional[str]:
        """Detect if a line is a section header"""
        line_upper = line.strip().upper()

        for pattern in self.SECTION_PATTERNS:
            if re.match(pattern, line_upper, re.IGNORECASE):
                # Extract the section name
                match = re.search(r'(?:I{1,3}\.?\s+)?(\w+)', line_upper)
                if match:
                    return match.group(1).lower()

        return None

    def _extract_tables(self, doc: fitz.Document) -> List[ExtractedTable]:
        """
        Extract tables from the document.

        Note: This is a basic implementation. For complex tables,
        consider using tabula-py or camelot.
        """
        tables = []

        for page_num, page in enumerate(doc):
            # Look for table-like structures
            # This is a simplified approach - looks for "Table" captions
            text = page.get_text()

            # Find table captions
            table_matches = re.finditer(
                r'Table\s+(\d+|[IVX]+)[.:]\s*(.+?)(?=\n\n|\Z)',
                text,
                re.IGNORECASE | re.DOTALL
            )

            for match in table_matches:
                caption = match.group(0).strip()
                tables.append(ExtractedTable(
                    content="",  # Would need more sophisticated extraction
                    caption=caption,
                    page=page_num
                ))

        return tables

    def _extract_figure_captions(self, text: str) -> List[str]:
        """Extract figure captions from text"""
        captions = []

        # Pattern for figure captions
        pattern = r'(?:Fig(?:ure)?\.?\s*\d+|FIG\.?\s*\d+)[.:]\s*(.+?)(?=\n\n|Fig(?:ure)?\.?\s*\d+|FIG\.?\s*\d+|\Z)'

        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)

        for match in matches:
            caption = match.group(0).strip()
            # Clean up caption
            caption = re.sub(r'\s+', ' ', caption)
            if len(caption) > 20:  # Filter out very short matches
                captions.append(caption)

        return captions

    def extract_shot_numbers(self, text: str) -> List[int]:
        """
        Extract NSTX shot numbers from text.

        Shot numbers are 6-digit integers starting with 1 (100000-199999).

        Returns:
            List of unique shot numbers found
        """
        matches = re.findall(self.SHOT_NUMBER_PATTERN, text, re.IGNORECASE)

        # Convert to integers and filter valid range
        shot_numbers = []
        for match in matches:
            try:
                num = int(match)
                if 100000 <= num <= 199999:
                    shot_numbers.append(num)
            except ValueError:
                continue

        # Return unique sorted list
        return sorted(set(shot_numbers))

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Split text into chunks for embedding.

        Args:
            text: Text to chunk
            chunk_size: Target size for each chunk (in words)
            overlap: Number of words to overlap between chunks

        Returns:
            List of dicts with 'content' and 'index' keys
        """
        words = text.split()
        chunks = []

        if len(words) <= chunk_size:
            return [{"content": text, "index": 0, "section": None}]

        start = 0
        index = 0

        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunk_text = ' '.join(chunk_words)

            chunks.append({
                "content": chunk_text,
                "index": index,
                "section": None
            })

            start = end - overlap
            index += 1

        return chunks

    def chunk_by_sections(
        self,
        sections: List[ExtractedSection],
        chunk_size: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Chunk text by sections, preserving section boundaries.

        Args:
            sections: List of extracted sections
            chunk_size: Target size for each chunk

        Returns:
            List of chunk dicts with section information
        """
        chunks = []
        index = 0

        for section in sections:
            section_chunks = self.chunk_text(section.content, chunk_size)

            for chunk in section_chunks:
                chunk["section"] = section.name
                chunk["index"] = index
                chunks.append(chunk)
                index += 1

        return chunks


# Convenience function
def get_pdf_processor() -> PDFProcessor:
    """Get a PDFProcessor instance"""
    return PDFProcessor()
