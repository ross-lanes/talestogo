"""
AI Generation Service for TALES Project
Generates queries, descriptors, and competitors based on brand information using
whichever LLM is designated as the analysis provider (use_for_analysis=True) in
Admin → LLM Providers. Works with any configured provider (OpenAI, Anthropic,
Gemini, Azure OpenAI, or an OpenAI-compatible endpoint).
"""

from typing import List, Dict, Optional

import json

from sqlalchemy.orm import Session
from app import models
from app.services.llm_provider_manager import LLMProviderManager
from app.services.generic_llm_client import LLMAPIError, LLMConfigurationError


class AIGenerator:
    """Generates content from brand info using the configured analysis LLM."""

    def __init__(self, db: Session, user: Optional[models.User] = None):
        self.db = db
        tenant_id = user.tenant_id if user else None
        self.provider_manager = LLMProviderManager(db, tenant_id)
        self.provider = self.provider_manager.get_analysis_provider()

        if self.provider is None:
            raise ValueError(
                "No analysis LLM configured. Configure one in Admin → LLM Providers "
                "(set use_for_analysis=True on the provider you want to use)."
            )

    def _generate(self, prompt: str) -> str:
        """Invoke the configured analysis provider and return text."""
        try:
            return self.provider.call(prompt=prompt, max_tokens=4000, temperature=0.7)
        except (LLMAPIError, LLMConfigurationError) as e:
            raise ValueError(
                f"Analysis LLM ({self.provider.display_name}) failed: {str(e)}"
            )

    def generate_queries(self, brand_info: models.BrandInfo) -> List[Dict[str, str]]:
        """Generate relevant queries with metadata based on brand information."""
        prompt = f"""Based on the following brand information, generate 10 relevant search queries that would help understand how AI assistants discuss this brand.

Brand Name: {brand_info.brand_name}
Website: {brand_info.website_url or 'N/A'}
Industry: {brand_info.industry or 'N/A'}
Description: {brand_info.description or 'N/A'}
Strategic Messages: {brand_info.strategic_messages or 'N/A'}

CRITICAL: These queries will be used to test whether AI assistants mention the brand "{brand_info.brand_name}" when it's relevant, and if so, in what context (positive, negative, or neutral).

IMPORTANT RULES:
1. MOST QUERIES should NOT explicitly include the brand name "{brand_info.brand_name}" in the question
2. Instead, ask open-ended questions about the industry/field where the brand SHOULD be mentioned as a relevant player
3. These are "visibility tests" - testing whether AI knows to mention this brand when answering general industry questions
4. Be natural questions someone might actually ask an AI assistant
5. The AI response might mention the brand positively, negatively, or not at all - we want to test this

Examples of GOOD query patterns (note: brand name is NOT in the question):
- "Which are the best/most reputable {brand_info.industry or 'organizations'} for [relevant purpose]?"
- "What are the key players in {brand_info.industry or 'this field'}?"
- "Which {brand_info.industry or 'organizations'} has the best reviews for [relevant aspect]?"
- "Tell me about the pluses and minuses of each of the major players in {brand_info.industry or 'this field'}?"
- "What are the most important developments in {brand_info.industry or 'this field'} and which organizations are behind them?"
- "Which {brand_info.industry or 'organizations'} gets the highest scores for [relevant metric]?"
- "Where should I [relevant action related to the industry]?"
- "What are the top-rated {brand_info.industry or 'options'} for [use case]?"

A few queries (1-2 out of 10) MAY directly mention the brand name for comparison purposes:
- "How does {brand_info.brand_name} compare to other leaders in {brand_info.industry or 'the field'}?"

Return ONLY a JSON array of 10 query objects with the following fields:
- "query_text": The actual question to ask (usually WITHOUT the brand name)
- "category": What the query is about (e.g., "Technology & Innovation", "Impact & Applications", "Leadership & Reputation", "Industry Position", "Comparative Analysis", "Best Practices", "Quality & Reputation")
- "target_outcome": What you hope to learn from the response (1 sentence)

Format example:
[
  {{
    "query_text": "Which are the most reputable organizations in {brand_info.industry or 'this field'} for cutting-edge research?",
    "category": "Leadership & Reputation",
    "target_outcome": "Test whether AI mentions {brand_info.brand_name} as a leader without prompting."
  }}
]
"""

        result_text = self._generate(prompt).strip()

        # Remove markdown code blocks if present
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]

        queries = json.loads(result_text.strip())
        return queries

    def generate_descriptors(self, brand_info: models.BrandInfo) -> List[Dict[str, str]]:
        """Generate ideal descriptive language with priority based on brand information."""
        prompt = f"""Based on the following brand information, generate 15 ideal descriptive words and short phrases that would be positive to see when people describe this brand.

Brand Name: {brand_info.brand_name}
Website: {brand_info.website_url or 'N/A'}
Industry: {brand_info.industry or 'N/A'}
Description: {brand_info.description or 'N/A'}
Strategic Messages: {brand_info.strategic_messages or 'N/A'}

The descriptors should:
1. Reflect the brand's key strengths and values
2. Include both single words and short phrases (2-4 words)
3. Be aspirational but realistic based on the brand description
4. Cover technical excellence, innovation, impact, and leadership
5. Align with the strategic messages if provided

Return ONLY a JSON array of 15 descriptor objects with the following fields:
- "descriptor": The descriptive word or phrase
- "priority": Priority level based on strategic importance ("High" for core brand attributes that align with strategic messages, "Medium" for important but secondary attributes, "Low" for nice-to-have descriptors)

Format example:
[
  {{
    "descriptor": "innovative",
    "priority": "High"
  }},
  {{
    "descriptor": "cutting-edge research",
    "priority": "Medium"
  }}
]
"""

        result_text = self._generate(prompt).strip()

        # Remove markdown code blocks if present
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]

        descriptors = json.loads(result_text.strip())
        return descriptors

    def generate_competitors(self, brand_info: models.BrandInfo) -> List[Dict[str, str]]:
        """Generate list of competitors with details based on brand information."""
        prompt = f"""Based on the following brand information, generate a list of 8-12 competitors at the SAME LEVEL OF SPECIFICITY as the brand.

Brand Name: {brand_info.brand_name}
Website: {brand_info.website_url or 'N/A'}
Industry: {brand_info.industry or 'N/A'}
Description: {brand_info.description or 'N/A'}

CRITICAL INSTRUCTIONS - Match the specificity level:
- If the brand is a SPECIFIC PRODUCT (like a journal, drug, or software tool), competitors should be OTHER PRODUCTS in the same category, NOT the companies that make them
- If the brand is an ORGANIZATION (like a lab, company, or university), competitors should be OTHER ORGANIZATIONS in the same space
- If the brand is a SERVICE, competitors should be OTHER SERVICES

Examples:
- Brand: "Physics of Plasmas" (a journal) → Competitors: Other physics journals like "Plasma Physics and Controlled Fusion", "Journal of Plasma Physics", etc. NOT publishing companies
- Brand: "Drug X" (treats diabetes) → Competitors: Other diabetes drugs like "Metformin", "Insulin", etc. NOT pharmaceutical companies
- Brand: "Princeton Plasma Physics Laboratory" (a lab) → Competitors: Other plasma physics labs like "MIT Plasma Science", "Oak Ridge National Lab", etc. NOT the Department of Energy
- Brand: "Photoshop" (software) → Competitors: Other image editing software like "GIMP", "Affinity Photo", etc. NOT Adobe Corporation

The competitors should:
1. Be at the EXACT SAME LEVEL as the brand (product-to-product, organization-to-organization, service-to-service)
2. Operate in the same industry: "{brand_info.industry or 'same industry'}"
3. Include both direct competitors and adjacent alternatives
4. Be realistic and verifiable entities
5. Range from well-known leaders to emerging alternatives

Return ONLY a JSON array of competitor objects with the following fields:
- "organization": The competitor's name (use the specific product/service/organization name, not the parent company)
- "type": Type of entity that matches the brand's type (e.g., "Journal", "Drug", "Software", "National Lab", "University Research Group", "Company")
- "focus_area": Brief description of their main focus area (1-2 sentences)
- "website": Their website URL (use your knowledge of real entities)

Format example:
[
  {{
    "organization": "Example Journal Name",
    "type": "Journal",
    "focus_area": "Publishes research on...",
    "website": "https://www.example.com"
  }}
]
"""

        result_text = self._generate(prompt).strip()

        # Remove markdown code blocks if present
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        if result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]

        competitors = json.loads(result_text.strip())
        return competitors

    def generate_all(self, user_id: int, brand_id: int) -> Dict[str, int]:
        """
        Generate queries, descriptors, and competitors for a specific brand.
        APPENDS new items to existing ones instead of replacing them.
        Returns count of items created for each category.
        """
        from app.crud import generate_next_query_id
        from app.utils.query_utils import auto_set_brand_in_query_flag

        # Get brand info
        brand_info = self.db.query(models.BrandInfo).filter(
            models.BrandInfo.id == brand_id,
            models.BrandInfo.user_id == user_id
        ).first()

        if not brand_info:
            raise ValueError("Brand information not found. Please save brand info first.")

        # DO NOT DELETE - just append new items to existing ones
        # This allows users to keep their manually created items

        # Generate queries and append with proper sequential IDs
        queries = self.generate_queries(brand_info)
        for query_data in queries:
            # Generate next available query_id
            next_query_id = generate_next_query_id(self.db, user_id, brand_id)

            # Auto-detect brand_in_query flag
            brand_in_query = auto_set_brand_in_query_flag(
                query_data.get("query_text", ""),
                self.db,
                user_id,
                brand_id
            )

            query = models.Query(
                user_id=user_id,
                brand_id=brand_id,
                query_id=next_query_id,
                query_text=query_data.get("query_text", ""),
                category=query_data.get("category"),
                target_outcome=query_data.get("target_outcome"),
                brand_in_query=brand_in_query,
                active=True
            )
            self.db.add(query)
            # Flush to get the query in the DB so next generate_next_query_id sees it
            self.db.flush()

        # Generate descriptors and append
        descriptors = self.generate_descriptors(brand_info)
        for descriptor_data in descriptors:
            descriptor = models.TargetDescriptor(
                user_id=user_id,
                brand_id=brand_id,
                descriptor=descriptor_data.get("descriptor", ""),
                priority=descriptor_data.get("priority", "Medium"),
                is_target=True
            )
            self.db.add(descriptor)

        # Generate competitors and append
        competitors = self.generate_competitors(brand_info)
        for competitor_data in competitors:
            competitor = models.Competitor(
                user_id=user_id,
                brand_id=brand_id,
                organization=competitor_data.get("organization", ""),
                type=competitor_data.get("type"),
                focus_area=competitor_data.get("focus_area"),
                website=competitor_data.get("website"),
                track=True
            )
            self.db.add(competitor)

        self.db.commit()

        return {
            "queries_created": len(queries),
            "descriptors_created": len(descriptors),
            "competitors_created": len(competitors)
        }
