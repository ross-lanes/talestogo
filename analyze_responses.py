#!/usr/bin/env python3
"""
Response Analysis Script for AIRO Project
Analyzes collected LLM responses for PPPL mentions, sentiment, descriptors, and competitors.
Uses Gemini AI for analysis.
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional
import time

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

# Import Gemini
try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️  Google AI not available. Install with: pip install google-generativeai")
    sys.exit(1)

# Target descriptors and competitors (loaded from database)
TARGET_DESCRIPTORS = []
COMPETITORS = []

class ResponseAnalyzer:
    """Analyzes responses using Gemini AI."""

    def __init__(self, db: Session):
        self.db = db
        self.google_model = None

        # Set up Google Gemini
        if GOOGLE_AVAILABLE:
            google_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if google_key:
                genai.configure(api_key=google_key)
                self.google_model = genai.GenerativeModel('gemini-2.5-flash')
                print("✓ Google Gemini configured for analysis (gemini-2.5-flash)")
            else:
                print("⚠️  GEMINI_API_KEY not found in environment")
                sys.exit(1)

        # Load descriptors and competitors from database
        self.load_reference_data()

    def load_reference_data(self):
        """Load target descriptors and competitors from database."""
        global TARGET_DESCRIPTORS, COMPETITORS

        descriptors = self.db.query(models.TargetDescriptor).filter(
            models.TargetDescriptor.target_for_pppl == True
        ).all()
        TARGET_DESCRIPTORS = [d.descriptor for d in descriptors]

        competitors = self.db.query(models.Competitor).all()
        COMPETITORS = [c.organization for c in competitors]

        print(f"✓ Loaded {len(TARGET_DESCRIPTORS)} target descriptors")
        print(f"✓ Loaded {len(COMPETITORS)} competitors")

    def build_analysis_prompt(self, query_text: str, response_text: str) -> str:
        """Build a detailed prompt for Gemini to analyze the response."""

        descriptors_list = "\n".join([f"  - {d}" for d in TARGET_DESCRIPTORS])
        competitors_list = "\n".join([f"  - {c}" for c in COMPETITORS])

        prompt = f"""You are analyzing an AI platform's response to a fusion energy query to determine how it depicts the Princeton Plasma Physics Laboratory (PPPL).

QUERY: {query_text}

RESPONSE TO ANALYZE:
{response_text}

Please analyze this response and provide a JSON object with the following fields:

1. **pppl_mentioned**: Is PPPL mentioned in the response?
   - "Yes" if PPPL is explicitly mentioned by name
   - "Indirect" if the response discusses PPPL's work without naming it (e.g., mentions NSTX-U, spherical tokamaks at Princeton, etc.)
   - "No" if PPPL is not mentioned at all

2. **pppl_position**: How prominently is PPPL featured? (only if mentioned)
   - "Leader" if PPPL is described as a top/leading institution
   - "Top 3" if PPPL is listed among 2-4 top institutions
   - "Featured" if PPPL gets a dedicated paragraph or significant discussion
   - "Listed" if PPPL is just mentioned in a list
   - "Not Mentioned" if not mentioned

3. **sentiment**: What is the sentiment toward PPPL? (only if mentioned)
   - "Very Positive" - exceptional praise, leader/pioneer language
   - "Positive" - favorable but not exceptional
   - "Neutral" - factual, no clear positive or negative tone
   - "Negative" - critical or unfavorable
   - "Mixed" - both positive and negative elements

4. **descriptors**: Which of these target descriptors are used in connection with PPPL?
   Return as a comma-separated list or empty string if none match.
{descriptors_list}

5. **competitors**: Which of these competitor organizations are mentioned?
   Return as a comma-separated list or empty string if none mentioned.
{competitors_list}

6. **sources**: Are any sources cited for information about PPPL or fusion research?
   List any URLs, papers, organizations, or attributions mentioned.
   Return as a comma-separated list or empty string if none.

7. **notes**: Any other relevant observations about how PPPL is depicted.
   Keep this brief (1-2 sentences max).

IMPORTANT: Return ONLY a valid JSON object with these exact field names. No additional text.

Example format:
{{
  "pppl_mentioned": "Yes",
  "pppl_position": "Featured",
  "sentiment": "Very Positive",
  "descriptors": "pioneering, innovative, spherical tokamak",
  "competitors": "MIT Plasma Science and Fusion Center, ITER",
  "sources": "https://pppl.gov, Department of Energy",
  "notes": "PPPL is described as a leader in spherical tokamak research."
}}"""

        return prompt

    def analyze_response(self, response: models.Response) -> Optional[Dict]:
        """Analyze a single response using Gemini."""
        if not self.google_model:
            return None

        try:
            prompt = self.build_analysis_prompt(response.query_text, response.response_text)

            result = self.google_model.generate_content(prompt)
            analysis_text = result.text.strip()

            # Try to extract JSON from the response
            # Sometimes the model wraps JSON in markdown code blocks
            if "```json" in analysis_text:
                analysis_text = analysis_text.split("```json")[1].split("```")[0].strip()
            elif "```" in analysis_text:
                analysis_text = analysis_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            analysis_data = json.loads(analysis_text)

            return analysis_data

        except json.JSONDecodeError as e:
            print(f"    ⚠️  JSON parse error: {e}")
            print(f"    Response text: {analysis_text[:200]}...")
            return None
        except Exception as e:
            print(f"    ✗ Analysis error: {e}")
            return None

    def save_analysis(self, response: models.Response, analysis_data: Dict) -> bool:
        """Save analysis results to the database."""
        try:
            response.pppl_mentioned = analysis_data.get('pppl_mentioned', '')
            response.pppl_position = analysis_data.get('pppl_position', '')
            response.sentiment = analysis_data.get('sentiment', '')
            response.descriptors = analysis_data.get('descriptors', '')
            response.competitors = analysis_data.get('competitors', '')
            response.sources = analysis_data.get('sources', '')
            response.notes = analysis_data.get('notes', '')
            response.analyzed_at = datetime.utcnow()

            self.db.commit()
            return True
        except Exception as e:
            print(f"    ✗ Database error: {e}")
            self.db.rollback()
            return False

    def analyze_single(self, response_id: int) -> bool:
        """Analyze a single response by ID."""
        response = self.db.query(models.Response).filter(models.Response.id == response_id).first()
        if not response:
            print(f"Response {response_id} not found")
            return False

        print(f"\n📊 Analyzing Response {response.id} ({response.platform})...")
        print(f"   Query: {response.query_text[:60]}...")

        analysis_data = self.analyze_response(response)
        if analysis_data:
            success = self.save_analysis(response, analysis_data)
            if success:
                print(f"   ✓ Analysis saved")
                print(f"     PPPL: {analysis_data.get('pppl_mentioned')}")
                if analysis_data.get('pppl_mentioned') in ['Yes', 'Indirect']:
                    print(f"     Position: {analysis_data.get('pppl_position')}")
                    print(f"     Sentiment: {analysis_data.get('sentiment')}")
                return True

        return False

    def analyze_batch(self, limit: Optional[int] = None) -> Dict[str, int]:
        """Analyze all unanalyzed responses."""
        # Get unanalyzed responses
        query = self.db.query(models.Response).filter(models.Response.analyzed_at.is_(None))
        if limit:
            query = query.limit(limit)

        responses = query.all()

        print(f"\n{'='*60}")
        print(f"Response Analysis Started")
        print(f"{'='*60}")
        print(f"Responses to analyze: {len(responses)}")
        print(f"{'='*60}")

        stats = {
            'total': len(responses),
            'successful': 0,
            'failed': 0,
            'pppl_yes': 0,
            'pppl_indirect': 0,
            'pppl_no': 0,
        }

        for i, response in enumerate(responses, 1):
            print(f"\n[{i}/{len(responses)}] Response {response.id} ({response.platform})")
            print(f"  Query: {response.query_text[:70]}...")

            analysis_data = self.analyze_response(response)
            if analysis_data:
                success = self.save_analysis(response, analysis_data)
                if success:
                    stats['successful'] += 1

                    # Track PPPL mention stats
                    pppl_mentioned = analysis_data.get('pppl_mentioned', '')
                    if pppl_mentioned == 'Yes':
                        stats['pppl_yes'] += 1
                    elif pppl_mentioned == 'Indirect':
                        stats['pppl_indirect'] += 1
                    elif pppl_mentioned == 'No':
                        stats['pppl_no'] += 1

                    print(f"  ✓ Analyzed - PPPL: {pppl_mentioned}", end="")
                    if pppl_mentioned in ['Yes', 'Indirect']:
                        print(f", Sentiment: {analysis_data.get('sentiment')}")
                    else:
                        print()
                else:
                    stats['failed'] += 1
            else:
                stats['failed'] += 1

            # Rate limiting - be nice to the API (2 seconds to avoid quota errors)
            time.sleep(2)

        print(f"\n{'='*60}")
        print(f"Analysis Summary")
        print(f"{'='*60}")
        print(f"  • Total responses analyzed: {stats['total']}")
        print(f"  • Successful: {stats['successful']}")
        print(f"  • Failed: {stats['failed']}")
        print(f"  • PPPL mentioned (Yes): {stats['pppl_yes']}")
        print(f"  • PPPL mentioned (Indirect): {stats['pppl_indirect']}")
        print(f"  • PPPL not mentioned: {stats['pppl_no']}")
        if stats['successful'] > 0:
            mention_rate = (stats['pppl_yes'] + stats['pppl_indirect']) / stats['successful'] * 100
            print(f"  • PPPL mention rate: {mention_rate:.1f}%")
        print(f"{'='*60}\n")

        return stats


def main():
    """Main entry point for the analysis script."""
    import argparse

    parser = argparse.ArgumentParser(description='AIRO Response Analysis Tool')
    parser.add_argument('--all', action='store_true', help='Analyze all unanalyzed responses')
    parser.add_argument('--limit', type=int, help='Limit number of responses to analyze')
    args = parser.parse_args()

    print("\n🔍 AIRO Response Analysis Tool\n")

    db = SessionLocal()
    try:
        analyzer = ResponseAnalyzer(db)

        # Get count of unanalyzed responses
        unanalyzed_count = db.query(models.Response).filter(
            models.Response.analyzed_at.is_(None)
        ).count()

        if unanalyzed_count == 0:
            print("✓ All responses are already analyzed!")
            return

        # Determine limit based on arguments or user input
        limit = None
        if args.all:
            limit = None
            print(f"Analyzing ALL {unanalyzed_count} responses...")
        elif args.limit:
            limit = args.limit
            print(f"Analyzing up to {limit} responses...")
        else:
            # Interactive mode
            print(f"Found {unanalyzed_count} unanalyzed responses\n")
            print("Options:")
            print(f"  1. Analyze ALL {unanalyzed_count} responses (recommended)")
            print("  2. Test with first 3 responses only")
            print("  3. Custom number of responses")

            choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"

            if choice == "2":
                limit = 3
            elif choice == "3":
                limit = int(input("How many responses to analyze? ").strip())

        # Run analysis
        stats = analyzer.analyze_batch(limit=limit)

        print("\n✅ Analysis complete!")
        print(f"\nNext steps:")
        print(f"  1. View analyzed responses at http://localhost:5173/data/responses")
        print(f"  2. Check updated dashboard at http://localhost:5173/")

    finally:
        db.close()


if __name__ == "__main__":
    main()
