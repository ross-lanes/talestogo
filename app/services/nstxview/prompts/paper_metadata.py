"""
Prompt for extracting paper metadata from NSTX/NSTX-U research papers.
"""

METADATA_EXTRACTION_PROMPT = """You are an expert at extracting metadata from scientific papers about plasma physics experiments on the NSTX and NSTX-U fusion reactors at Princeton Plasma Physics Laboratory.

Given the following text extracted from a research paper, extract the metadata in JSON format.

<paper_text>
{paper_text}
</paper_text>

Extract the following information and return it as valid JSON:

{{
    "title": "Full title of the paper",
    "authors": ["Author 1", "Author 2", ...],
    "journal": "Name of the journal",
    "publication_year": 2023,
    "doi": "DOI if present (e.g., 10.1088/...)",
    "abstract": "The paper's abstract (full text)",
    "experiment_type": "Primary type of experiment (see categories below)",
    "key_findings": ["Key finding 1", "Key finding 2", ...]
}}

For experiment_type, use one of these categories:
- "confinement": Studies of plasma confinement, H-mode, energy/particle confinement
- "stability": Studies of MHD stability, disruptions, instabilities
- "heating": Studies of NBI, RF heating, current drive
- "transport": Studies of energy/particle transport
- "divertor": Studies of divertor physics, heat flux, SOL
- "diagnostics": Studies focused on diagnostic development/measurement techniques
- "operations": Studies of plasma operations, scenarios, control
- "other": If none of the above fit

Rules:
1. Extract exact text for title and abstract when possible
2. For authors, include full names if available
3. If information is not found, use null for that field
4. For key_findings, extract 2-5 main conclusions or discoveries from the paper
5. Return ONLY valid JSON, no additional text

Return the JSON:"""
