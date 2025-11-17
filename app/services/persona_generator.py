"""
Persona generation service using LLM APIs
"""
import json
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import PersonaType


class PersonaGenerator:
    """Generate healthcare personas using LLM APIs"""

    def __init__(self, provider: str = None):
        """Initialize the generator with specified provider"""
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER

    def _get_patient_prompt(
        self, brand_info: Dict[str, Any], inputs: Dict[str, Any]
    ) -> str:
        """Generate prompt for patient personas"""
        return f"""You are a professional healthcare marketer with extensive experience in pharmaceutical marketing.

Your task is to create 4 detailed patient personas for the pharmaceutical brand "{brand_info['brand_name']}" ({brand_info.get('generic_name', '')}).

Brand Information:
- Therapeutic Area: {brand_info.get('therapeutic_area', 'N/A')}
- Indication: {brand_info.get('indication', 'N/A')}
- Manufacturer: {brand_info.get('manufacturer', 'N/A')}
- Target Audience: {brand_info.get('target_audience', 'N/A')}
- Key Messages: {brand_info.get('key_messages', 'N/A')}

Patient Characteristics to Consider:
- Occupation: {inputs.get('patient_occupation', 'Various')}
- Clinical Scenario/Diagnosis: {inputs.get('patient_clinical_scenario', 'N/A')}
- Gender: {inputs.get('patient_gender', 'Mixed')}
- Symptoms: {inputs.get('patient_symptoms', 'N/A')}
- Age Range: {inputs.get('patient_age_range', '40-70')}

Create 4 DISTINCT patient personas, each representing a different patient archetype. Each persona should include:

1. **Basic Information:**
   - Name (realistic, diverse)
   - Age (within the specified range)
   - Location (US city and state)
   - Quote (a memorable quote that captures their perspective)

2. **Demographics:**
   - Family Status (e.g., "Married with 2 children", "Single", "Widowed")
   - Occupation (consider the specified occupation)
   - Tech Savviness (e.g., "High - Early adopter", "Medium - Selective user", "Low - Prefers traditional methods")

3. **Clinical Profile:**
   - Scenario (detailed patient journey/story)
   - Recent Diagnosis (specific to the condition)
   - Mindset (their emotional state and attitude toward treatment)

4. **Goals & Fears:**
   - Goals (3-4 specific, actionable goals related to their health and life)
   - Fears (3-4 specific concerns related to their condition, treatment, or future)

5. **Information Journey:**
   - Channels (where they seek health information: e.g., "Online forums, doctor consultations, support groups")
   - Key Question for their Doctor (the most important question they want answered)

6. **Marketing/Messaging Cues:**
   - Message (the key message that will resonate with this persona for {brand_info['brand_name']})
   - Tone (the appropriate tone: e.g., "Empowering and optimistic", "Straightforward and clinical", "Warm and supportive")
   - Call to Action (specific action they should take)
   - How They View {brand_info['brand_name']} (their perspective on this treatment option)

7. **Personality Traits:**
   - List 3-4 key personality traits (e.g., "Proactive", "Analytical", "Cautious", "Optimistic")

Return ONLY a valid JSON array with 4 persona objects. Each object should have these exact keys:
{{
  "name": string,
  "age": number,
  "location": string,
  "quote": string,
  "family_status": string,
  "occupation": string,
  "tech_savviness": string,
  "clinical_scenario": string,
  "recent_diagnosis": string,
  "mindset": string,
  "goals": string (newline-separated list),
  "fears": string (newline-separated list),
  "information_channels": string,
  "key_question_for_doctor": string,
  "marketing_message": string,
  "marketing_tone": string,
  "call_to_action": string,
  "how_they_view_brand": string,
  "personality_traits": string (comma-separated),
  "about": string (2-3 sentence biography)
}}

Ensure the personas are diverse, realistic, and professionally written from a healthcare marketing perspective."""

    def _get_hcp_prompt(
        self, brand_info: Dict[str, Any], inputs: Dict[str, Any]
    ) -> str:
        """Generate prompt for HCP personas"""
        return f"""You are a professional healthcare marketer with extensive experience in pharmaceutical marketing to healthcare professionals.

Your task is to create 4 detailed Healthcare Professional (HCP) personas for the pharmaceutical brand "{brand_info['brand_name']}" ({brand_info.get('generic_name', '')}).

Brand Information:
- Therapeutic Area: {brand_info.get('therapeutic_area', 'N/A')}
- Indication: {brand_info.get('indication', 'N/A')}
- Manufacturer: {brand_info.get('manufacturer', 'N/A')}
- Target Audience: {brand_info.get('target_audience', 'N/A')}
- Key Messages: {brand_info.get('key_messages', 'N/A')}

HCP Characteristics to Consider:
- Type of Doctor: {inputs.get('hcp_doctor_type', 'Various specialties')}
- Disease Area: {inputs.get('hcp_disease', 'N/A')}
- Location: {inputs.get('hcp_location', 'US (various)')}

Create 4 DISTINCT HCP personas representing different types of prescribers/influencers. Consider archetypes like:
- The Paradigm Pioneer (early adopter, academic leader)
- The Cautious Strategist (evidence-based, careful)
- The Protocol Unifier (systems-focused, collaborative)
- The Patient Advocate (patient-centric, relationship-focused)

Each persona should include:

1. **Basic Information:**
   - Name (realistic, professional: Dr. [First] [Last])
   - Age (typically 35-65)
   - Job Title (e.g., "Director of Urologic Oncology", "Partner in Private Practice")
   - Location (US city and state)
   - Quote (captures their professional philosophy)

2. **Demographics:**
   - Practice Type (e.g., "Academic Medical Center", "Large Private Practice", "Community Hospital")
   - Specialty (specific medical specialty)

3. **Profile/About:**
   - Detailed background paragraph describing their career, experience, and current role

4. **Goals & Motivations:**
   - 3-4 professional goals related to patient care, research, practice management, or career advancement

5. **Frustrations & Pain Points:**
   - 3-4 specific challenges they face in their practice related to the disease area

6. **How They View {brand_info['brand_name']}:**
   - Their perspective on this treatment option and how they might use it in practice

7. **Marketing & Engagement Strategy:**
   - Channels (where to reach them: e.g., "Top-tier journals, AUA conference, KOL roundtables")
   - Messaging (the key message that will resonate)
   - Tactics (specific engagement approaches for this persona)

8. **Personality Traits:**
   - List 3-4 key professional traits (e.g., "Visionary", "Pragmatic", "Collaborative", "Patient-focused")

Return ONLY a valid JSON array with 4 persona objects. Each object should have these exact keys:
{{
  "name": string,
  "age": number,
  "location": string,
  "job_title": string,
  "specialty": string,
  "practice_type": string,
  "quote": string,
  "about": string (detailed paragraph),
  "motivations": string (newline-separated list of goals),
  "frustrations": string (newline-separated list of pain points),
  "how_they_view_brand": string,
  "marketing_channels": string (newline-separated list),
  "marketing_messaging": string,
  "marketing_tactics": string (newline-separated list),
  "personality_traits": string (comma-separated)
}}

Ensure the personas are diverse, realistic, and professionally written from a pharmaceutical marketing perspective."""

    async def generate_patient_personas(
        self, brand_info: Dict[str, Any], inputs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate 4 patient personas"""
        prompt = self._get_patient_prompt(brand_info, inputs)

        if self.provider == "openai":
            personas = await self._generate_with_openai(prompt)
        elif self.provider == "anthropic":
            personas = await self._generate_with_anthropic(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        return personas

    async def generate_hcp_personas(
        self, brand_info: Dict[str, Any], inputs: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate 4 HCP personas"""
        prompt = self._get_hcp_prompt(brand_info, inputs)

        if self.provider == "openai":
            personas = await self._generate_with_openai(prompt)
        elif self.provider == "anthropic":
            personas = await self._generate_with_anthropic(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        return personas

    async def _generate_with_openai(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate personas using OpenAI API"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional healthcare marketing expert specializing in pharmaceutical persona development."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            # Handle different response structures
            if isinstance(data, list):
                return data
            elif "personas" in data:
                return data["personas"]
            else:
                # Assume the data is a dict with personas at the top level
                return [data]

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def _generate_with_anthropic(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate personas using Anthropic API"""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=8000,
                temperature=0.8,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text

            # Extract JSON from response (Claude might include markdown)
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()

            data = json.loads(content)

            # Handle different response structures
            if isinstance(data, list):
                return data
            elif "personas" in data:
                return data["personas"]
            else:
                return [data]

        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")

    async def generate_ai_patient_personas(
        self,
        brand_info: Dict[str, Any],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate patient personas using AI research via Perplexity

        Args:
            brand_info: Brand information dictionary
            count: Number of personas to generate (1-10)

        Returns:
            List of patient persona dictionaries
        """
        from app.services.perplexity_service import PerplexityService

        perplexity = PerplexityService()

        # Step 1: Research disease demographics
        demographics_data = await perplexity.research_disease_demographics(
            brand_name=brand_info.get("brand_name", ""),
            therapeutic_area=brand_info.get("therapeutic_area", ""),
            indication=brand_info.get("indication", ""),
            persona_type="patient"
        )

        # Step 2: Generate individual personas based on research
        personas = []
        for i in range(count):
            persona_data = await perplexity.generate_persona_details(
                demographics_data=demographics_data,
                brand_info=brand_info,
                persona_number=i + 1,
                persona_type="patient"
            )
            personas.append(persona_data)

        return personas

    async def generate_ai_hcp_personas(
        self,
        brand_info: Dict[str, Any],
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate HCP personas using AI research via Perplexity

        Args:
            brand_info: Brand information dictionary
            count: Number of personas to generate (1-10)

        Returns:
            List of HCP persona dictionaries
        """
        from app.services.perplexity_service import PerplexityService

        perplexity = PerplexityService()

        # Step 1: Research HCP demographics
        demographics_data = await perplexity.research_disease_demographics(
            brand_name=brand_info.get("brand_name", ""),
            therapeutic_area=brand_info.get("therapeutic_area", ""),
            indication=brand_info.get("indication", ""),
            persona_type="hcp"
        )

        # Step 2: Generate individual personas based on research
        personas = []
        for i in range(count):
            persona_data = await perplexity.generate_persona_details(
                demographics_data=demographics_data,
                brand_info=brand_info,
                persona_number=i + 1,
                persona_type="hcp"
            )
            personas.append(persona_data)

        return personas

    async def generate_manual_patient_personas(
        self,
        brand_info: Dict[str, Any],
        persona_inputs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate patient personas from manual form inputs

        Args:
            brand_info: Brand information dictionary
            persona_inputs: List of persona input dictionaries from frontend forms

        Returns:
            List of patient persona dictionaries
        """
        personas = []

        for i, inputs in enumerate(persona_inputs):
            # Use existing generation method with single persona inputs
            prompt = self._get_patient_prompt(brand_info, inputs)

            if self.provider == "openai":
                result_personas = await self._generate_with_openai(prompt)
            elif self.provider == "anthropic":
                result_personas = await self._generate_with_anthropic(prompt)
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")

            # Take first persona from result (we asked for 1)
            if result_personas and len(result_personas) > 0:
                personas.append(result_personas[0])

        return personas

    async def generate_manual_hcp_personas(
        self,
        brand_info: Dict[str, Any],
        persona_inputs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate HCP personas from manual form inputs

        Args:
            brand_info: Brand information dictionary
            persona_inputs: List of persona input dictionaries from frontend forms

        Returns:
            List of HCP persona dictionaries
        """
        personas = []

        for i, inputs in enumerate(persona_inputs):
            # Use existing generation method with single persona inputs
            prompt = self._get_hcp_prompt(brand_info, inputs)

            if self.provider == "openai":
                result_personas = await self._generate_with_openai(prompt)
            elif self.provider == "anthropic":
                result_personas = await self._generate_with_anthropic(prompt)
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")

            # Take first persona from result (we asked for 1)
            if result_personas and len(result_personas) > 0:
                personas.append(result_personas[0])

        return personas
