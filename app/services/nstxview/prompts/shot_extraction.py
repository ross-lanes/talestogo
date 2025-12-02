"""
Prompt for extracting NSTX/NSTX-U shot numbers and their context.
"""

SHOT_EXTRACTION_PROMPT = """You are an expert at analyzing scientific papers about plasma physics experiments on the NSTX and NSTX-U fusion reactors at Princeton Plasma Physics Laboratory.

Given the following text extracted from a research paper, identify all plasma shot numbers mentioned and extract information about each.

<paper_text>
{paper_text}
</paper_text>

IMPORTANT: NSTX/NSTX-U shot numbers are 6-digit integers that start with the digit 1 (range: 100000-199999).

Shot numbers may appear in various formats:
- Plain number: 141234
- With hash: #141234
- With label: shot 141234, Shot #141234
- In ranges: shots 141000-141050
- In lists: shots 141234, 141235, 141236

For each shot found, determine:
1. The shot number (6 digits starting with 1)
2. Its role in the paper:
   - "primary": This shot is a main focus of analysis in the paper
   - "comparison": This shot is used for comparison with primary shots
   - "reference": This shot is mentioned but not analyzed in detail
3. The context: Why was this shot mentioned? What was interesting about it?
4. Any characteristics described for this shot

Return your findings as valid JSON:

{{
    "shots": [
        {{
            "shot_number": 141234,
            "role": "primary",
            "context": "Brief description of why this shot was mentioned and what was studied",
            "characteristics": {{
                "plasma_current_MA": 1.0,
                "magnetic_field_T": 0.5,
                "heating_power_MW": 6.0,
                "confinement_mode": "H-mode",
                "key_features": ["high beta", "ELM-free period"]
            }}
        }}
    ],
    "shot_ranges": [
        {{
            "start": 141000,
            "end": 141050,
            "context": "Description of what this range of shots was used for"
        }}
    ]
}}

Rules:
1. Only include 6-digit numbers starting with 1 (100000-199999)
2. Do NOT include numbers that are clearly not shot numbers (e.g., years like 2015, reference numbers)
3. If a shot number appears multiple times, include it once with the most complete information
4. For characteristics, only include values explicitly mentioned in the paper
5. If no shots are found, return {{"shots": [], "shot_ranges": []}}
6. Return ONLY valid JSON, no additional text

Return the JSON:"""
