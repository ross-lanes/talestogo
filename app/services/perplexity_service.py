"""
Perplexity AI service for research and information gathering
"""
import os
import httpx
import json
from typing import Dict, Any, Optional
from app.config import settings


class PerplexityService:
    """Service for interacting with Perplexity AI API"""

    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not set")

        self.base_url = "https://api.perplexity.ai"
        self.model = "llama-3.1-sonar-large-128k-online"  # Use online model for research

    async def research_disease_demographics(
        self,
        brand_name: str,
        therapeutic_area: str,
        indication: str,
        persona_type: str = "patient"
    ) -> Dict[str, Any]:
        """
        Research disease demographics and patient/HCP characteristics using Perplexity

        Args:
            brand_name: Name of the pharmaceutical brand
            therapeutic_area: The therapeutic area (e.g., "Oncology", "Urology")
            indication: The disease/indication being treated
            persona_type: Either "patient" or "hcp"

        Returns:
            Dictionary with demographic and characteristic data
        """
        if persona_type == "patient":
            prompt = f"""Research the typical patient demographics and characteristics for {indication} ({therapeutic_area}).

For patients with {indication}, provide comprehensive information about:

1. **Demographics**:
   - Typical age range(s) - be specific (e.g., "45-65" or "50-70")
   - Gender distribution - specify percentages or predominant gender
   - Geographic distribution (if relevant)

2. **Clinical Characteristics**:
   - Most common symptoms patients experience
   - Disease stage variations (early, moderate, advanced/late-stage)
   - How symptoms differ by disease stage

3. **Socioeconomic Factors**:
   - Common occupations for this patient population
   - For late-stage/advanced disease: employment status (e.g., "Former accountant", "Unemployed", "Retired")
   - Consider if occupation might be related to disease (occupational hazards)
   - Income levels and insurance coverage patterns

4. **Lifestyle & Psychosocial**:
   - Family status (married, single, caregivers)
   - Tech savviness levels
   - Information-seeking behaviors
   - Common fears and concerns
   - Treatment goals and priorities

Provide specific, evidence-based information. Use percentages where available. Format as a structured JSON response."""

        else:  # HCP
            prompt = f"""Research the typical healthcare professional characteristics who treat {indication} ({therapeutic_area}).

For HCPs who treat {indication}, provide comprehensive information about:

1. **Professional Characteristics**:
   - Types of doctors who typically treat this condition (specialists)
   - Practice settings (academic centers, community hospitals, private practice, rural)
   - Years of experience typical for these specialists
   - Geographic distribution patterns

2. **Practice Patterns**:
   - Patient volume for this condition
   - Typical treatment approaches
   - Referral patterns
   - Multidisciplinary team involvement

3. **Information & Education**:
   - How HCPs stay informed about this therapeutic area
   - Key medical journals and conferences
   - Opinion leader influence
   - Digital vs. traditional information preferences

4. **Challenges & Motivations**:
   - Common frustrations in treating this condition
   - What motivates their treatment decisions
   - Barriers to adopting new therapies
   - Patient communication challenges

Provide specific, evidence-based information. Format as a structured JSON response."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a medical research expert providing accurate, evidence-based information about patient demographics and healthcare professional characteristics for pharmaceutical brands. Always provide specific, actionable data."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.2,  # Lower temperature for more factual responses
                        "max_tokens": 2000
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    raise Exception(f"Perplexity API error: {response.status_code} - {response.text}")

                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Try to parse as JSON, if it fails return as plain text
                try:
                    data = json.loads(content)
                    return data
                except json.JSONDecodeError:
                    # If not JSON, return structured text
                    return {
                        "raw_research": content,
                        "persona_type": persona_type
                    }

        except Exception as e:
            # Return minimal fallback data if API fails
            return {
                "error": str(e),
                "fallback": True,
                "persona_type": persona_type,
                "demographics": {
                    "age_range": "50-70" if persona_type == "patient" else "35-55",
                    "gender": "Mixed",
                },
                "note": "Using fallback data due to API error"
            }

    async def generate_persona_details(
        self,
        demographics_data: Dict[str, Any],
        brand_info: Dict[str, Any],
        persona_number: int,
        persona_type: str = "patient"
    ) -> Dict[str, Any]:
        """
        Generate specific persona details based on demographic research

        Args:
            demographics_data: Research data from research_disease_demographics
            brand_info: Brand information dict
            persona_number: Which persona this is (1, 2, 3, etc.)
            persona_type: Either "patient" or "hcp"

        Returns:
            Dictionary with specific persona characteristics
        """
        if persona_type == "patient":
            prompt = f"""Based on this research about {brand_info['indication']}:

{json.dumps(demographics_data, indent=2)}

Create Patient Persona #{persona_number} with these specific details:
- Name (realistic, diverse)
- Age (within typical range)
- Gender
- Location (city/state)
- Occupation (or "Former [occupation]" or "Unemployed" if late-stage disease affects work)
- Family status
- Clinical scenario (specific to their disease stage)
- Symptoms (realistic for their stage)
- Recent diagnosis timeline
- Mindset and emotional state
- Goals and priorities
- Fears and concerns
- Tech savviness level
- Information channels they use
- Key questions for their doctor
- A memorable quote that captures their perspective

Make this persona feel real and distinct from other personas. Vary disease stages, demographics, and circumstances.

Format as JSON."""

        else:  # HCP
            prompt = f"""Based on this research about HCPs who treat {brand_info['indication']}:

{json.dumps(demographics_data, indent=2)}

Create HCP Persona #{persona_number} with these specific details:
- Name (realistic, diverse, professional)
- Age
- Location
- Job title / Specialty
- Practice type (academic, community, private, rural)
- Years in practice
- About (brief professional bio)
- Quote (their perspective on treating this condition)
- Motivations (what drives their practice)
- Frustrations (challenges they face)
- How they view {brand_info['brand_name']}
- Marketing channels (how to reach them)
- Marketing messaging (what resonates)
- Marketing tactics (what works)
- Personality traits

Make this HCP persona distinct. Vary practice settings, experience levels, and perspectives.

Format as JSON."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert in creating detailed, realistic healthcare personas for pharmaceutical marketing. Create diverse, authentic personas that feel like real people."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,  # Higher temperature for creative persona generation
                        "max_tokens": 2000
                    },
                    timeout=60.0
                )

                if response.status_code != 200:
                    raise Exception(f"Perplexity API error: {response.status_code} - {response.text}")

                result = response.json()
                content = result["choices"][0]["message"]["content"]

                # Parse JSON response
                try:
                    persona_data = json.loads(content)
                    return persona_data
                except json.JSONDecodeError:
                    # Fallback minimal persona
                    return {
                        "name": f"Persona {persona_number}",
                        "error": "Failed to parse persona details",
                        "raw_content": content
                    }

        except Exception as e:
            return {
                "name": f"Persona {persona_number}",
                "error": str(e),
                "fallback": True
            }
