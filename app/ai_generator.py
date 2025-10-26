"""
AI Generation Service for AIRO Project
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
                self.google_model = genai.GenerativeModel('gemini-1.5-flash')
            else:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
        else:
            raise ImportError("google-generativeai package not installed")

    def generate_queries(self, brand_info: models.BrandInfo) -> List[str]:
        """Generate relevant queries based on brand information."""
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

Return ONLY a JSON array of 10 query strings, nothing else. Format: ["query 1", "query 2", ...]
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

    def generate_descriptors(self, brand_info: models.BrandInfo) -> List[str]:
        """Generate ideal descriptive language based on brand information."""
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

Return ONLY a JSON array of 15 descriptor strings, nothing else. Format: ["descriptor 1", "descriptor 2", ...]
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

    def generate_competitors(self, brand_info: models.BrandInfo) -> List[str]:
        """Generate list of competitors based on brand information."""
        prompt = f"""Based on the following brand information, generate a list of 8-12 competitor organizations or institutions that operate in the same space.

Brand Name: {brand_info.brand_name}
Website: {brand_info.website_url or 'N/A'}
Industry: {brand_info.industry or 'N/A'}
Description: {brand_info.description or 'N/A'}

The competitors should:
1. Be actual organizations that work in similar areas
2. Include both direct competitors and adjacent players
3. Range from well-known leaders to emerging organizations
4. Be realistic and verifiable entities
5. Include both commercial and non-commercial entities if applicable

Return ONLY a JSON array of competitor name strings, nothing else. Format: ["competitor 1", "competitor 2", ...]
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

    def generate_all(self, user_id: int) -> Dict[str, int]:
        """
        Generate queries, descriptors, and competitors for a user based on their brand info.
        Returns count of items created for each category.
        """
        # Get brand info
        brand_info = self.db.query(models.BrandInfo).filter(
            models.BrandInfo.user_id == user_id
        ).first()

        if not brand_info:
            raise ValueError("Brand information not found. Please save brand info first.")

        # Delete existing queries, descriptors, and competitors for this user
        self.db.query(models.Query).filter(models.Query.user_id == user_id).delete()
        self.db.query(models.Descriptor).filter(models.Descriptor.user_id == user_id).delete()
        self.db.query(models.Competitor).filter(models.Competitor.user_id == user_id).delete()
        self.db.commit()

        # Generate queries
        queries = self.generate_queries(brand_info)
        for query_text in queries:
            query = models.Query(
                user_id=user_id,
                query_text=query_text,
                is_active=True
            )
            self.db.add(query)

        # Generate descriptors
        descriptors = self.generate_descriptors(brand_info)
        for descriptor_text in descriptors:
            descriptor = models.Descriptor(
                user_id=user_id,
                descriptor_text=descriptor_text
            )
            self.db.add(descriptor)

        # Generate competitors
        competitors = self.generate_competitors(brand_info)
        for competitor_name in competitors:
            competitor = models.Competitor(
                user_id=user_id,
                name=competitor_name
            )
            self.db.add(competitor)

        self.db.commit()

        return {
            "queries_created": len(queries),
            "descriptors_created": len(descriptors),
            "competitors_created": len(competitors)
        }
