"""
AI Generation Service for TALES Project
Generates queries, descriptors, and competitors based on brand information using Gemini AI.
"""

import os
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

from sqlalchemy.orm import Session
from app import models


class AIGenerator:
    """Generates content using Gemini AI based on brand information."""

    def __init__(self, db: Session):
        self.db = db
        self.google_model = None

        # Set up Google Gemini
        if GOOGLE_AVAILABLE:
            google_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if google_key:
                genai.configure(api_key=google_key)
                # Use gemini-2.5-flash (Gemini 1.5 models are retired)
                self.google_model = genai.GenerativeModel('gemini-2.5-flash')
            else:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
        else:
            raise ImportError("google-generativeai package not installed")

    def generate_queries(self, brand_info: models.BrandInfo) -> List[Dict[str, str]]:
        """Generate relevant queries with metadata based on brand information."""
        prompt = f"""Based on the following brand information, generate 10 relevant search queries that would help understand how AI assistants discuss this brand.

Brand Name: {brand_info.brand_name}
Website: {brand_info.website_url or 'N/A'}
Industry: {brand_info.industry or 'N/A'}
Description: {brand_info.description or 'N/A'}
Strategic Messages: {brand_info.strategic_messages or 'N/A'}

The queries should:
1. Ask about the brand's key capabilities and achievements
2. Compare the brand to industry trends or needs
3. Ask about the brand's role in solving industry challenges
4. Be natural questions someone might ask an AI assistant
5. Cover different aspects of the brand's work and impact

Return ONLY a JSON array of 10 query objects with the following fields:
- "query_text": The actual question to ask
- "category": What the query is about (e.g., "Technology & Innovation", "Impact & Applications", "Leadership & Reputation", "Partnerships & Collaborations", "Research & Development", "Industry Position")
- "target_outcome": What you hope to learn from the response (1 sentence)

Format example:
[
  {{
    "query_text": "What are the latest breakthroughs in...",
    "category": "Technology & Innovation",
    "target_outcome": "Understand how AI discusses the brand's technical achievements."
  }}
]
"""

        response = self.google_model.generate_content(prompt)
        result_text = response.text.strip()

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

        response = self.google_model.generate_content(prompt)
        result_text = response.text.strip()

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

        response = self.google_model.generate_content(prompt)
        result_text = response.text.strip()

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
        Returns count of items created for each category.
        """
        # Get brand info
        brand_info = self.db.query(models.BrandInfo).filter(
            models.BrandInfo.id == brand_id,
            models.BrandInfo.user_id == user_id
        ).first()

        if not brand_info:
            raise ValueError("Brand information not found. Please save brand info first.")

        # Delete existing queries, descriptors, and competitors for this brand
        self.db.query(models.Query).filter(
            models.Query.user_id == user_id,
            models.Query.brand_id == brand_id
        ).delete()
        self.db.query(models.TargetDescriptor).filter(
            models.TargetDescriptor.user_id == user_id,
            models.TargetDescriptor.brand_id == brand_id
        ).delete()
        self.db.query(models.Competitor).filter(
            models.Competitor.user_id == user_id,
            models.Competitor.brand_id == brand_id
        ).delete()
        self.db.commit()

        # Generate queries
        queries = self.generate_queries(brand_info)
        query_counter = 1
        for query_data in queries:
            query = models.Query(
                user_id=user_id,
                brand_id=brand_id,
                query_id=f"Q{query_counter:03d}",
                query_text=query_data.get("query_text", ""),
                category=query_data.get("category"),
                target_outcome=query_data.get("target_outcome"),
                active=True
            )
            self.db.add(query)
            query_counter += 1

        # Generate descriptors
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

        # Generate competitors
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
