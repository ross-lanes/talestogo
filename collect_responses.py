#!/usr/bin/env python3
"""
Response Collection Script for AIRO Project
Queries AI platforms (ChatGPT, Claude, Gemini) and records responses.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import time

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, crud


# API clients
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not available. Install with: pip install openai")

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic not available. Install with: pip install anthropic")

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️  Google AI not available. Install with: pip install google-generativeai")

# Perplexity uses OpenAI-compatible API
PERPLEXITY_AVAILABLE = OPENAI_AVAILABLE


class ResponseCollector:
    """Collects responses from AI platforms."""

    def __init__(self, db: Session):
        self.db = db

        # Initialize API clients
        self.openai_client = None
        self.anthropic_client = None
        self.google_model = None
        self.perplexity_client = None

        # Set up OpenAI
        if OPENAI_AVAILABLE:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("✓ OpenAI (ChatGPT) configured")
            else:
                print("⚠️  OPENAI_API_KEY not found in environment")

        # Set up Anthropic
        if ANTHROPIC_AVAILABLE:
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_key:
                self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                print("✓ Anthropic (Claude) configured")
            else:
                print("⚠️  ANTHROPIC_API_KEY not found in environment")

        # Set up Google
        if GOOGLE_AVAILABLE:
            google_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            if google_key:
                genai.configure(api_key=google_key)
                self.google_model = genai.GenerativeModel('gemini-2.5-flash')
                print("✓ Google (Gemini) configured")
            else:
                print("⚠️  GEMINI_API_KEY not found in environment")

        # Set up Perplexity (uses OpenAI-compatible API)
        if PERPLEXITY_AVAILABLE:
            perplexity_key = os.getenv('PERPLEXITY_API_KEY')
            if perplexity_key:
                # Import httpx for custom timeout
                import httpx
                # Perplexity needs longer timeout (30s) as it searches the web
                http_client = httpx.Client(timeout=30.0)
                self.perplexity_client = openai.OpenAI(
                    api_key=perplexity_key,
                    base_url="https://api.perplexity.ai",
                    http_client=http_client
                )
                print("✓ Perplexity configured (with extended timeout for web search)")
            else:
                print("⚠️  PERPLEXITY_API_KEY not found in environment")

    def query_chatgpt(self, query_text: str) -> Optional[str]:
        """Query OpenAI ChatGPT."""
        if not self.openai_client:
            return None

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",  # or "gpt-3.5-turbo" for faster/cheaper
                messages=[
                    {"role": "user", "content": query_text}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  ✗ ChatGPT error: {e}")
            return None

    def query_claude(self, query_text: str) -> Optional[str]:
        """Query Anthropic Claude."""
        if not self.anthropic_client:
            return None

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": query_text}
                ]
            )
            return response.content[0].text
        except Exception as e:
            print(f"  ✗ Claude error: {e}")
            return None

    def query_gemini(self, query_text: str) -> Optional[str]:
        """Query Google Gemini."""
        if not self.google_model:
            return None

        try:
            response = self.google_model.generate_content(query_text)
            return response.text
        except Exception as e:
            print(f"  ✗ Gemini error: {e}")
            return None

    def query_perplexity(self, query_text: str) -> Optional[str]:
        """Query Perplexity AI."""
        if not self.perplexity_client:
            return None

        try:
            response = self.perplexity_client.chat.completions.create(
                model="sonar",  # Updated to new model naming (was llama-3.1-sonar-large-128k-online)
                messages=[
                    {"role": "user", "content": query_text}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  ✗ Perplexity error: {e}")
            return None

    def save_response(self, query_id: str, query_text: str, platform: str,
                     response_text: str) -> models.Response:
        """Save a response to the database."""
        response = models.Response(
            query_id=query_id,
            query_text=query_text,
            platform=platform,
            response_text=response_text,
            timestamp=datetime.utcnow()
        )
        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)
        return response

    def collect_for_query(self, query: models.Query, platforms: List[str] = None) -> Dict[str, bool]:
        """Collect responses for a single query across specified platforms."""
        if platforms is None:
            platforms = ['ChatGPT', 'Claude', 'Gemini', 'Perplexity']

        results = {}
        print(f"\n📝 Query {query.query_id}: {query.query_text[:60]}...")

        for platform in platforms:
            print(f"  → {platform}...", end=" ", flush=True)

            response_text = None
            if platform == 'ChatGPT':
                response_text = self.query_chatgpt(query.query_text)
            elif platform == 'Claude':
                response_text = self.query_claude(query.query_text)
            elif platform == 'Gemini':
                response_text = self.query_gemini(query.query_text)
            elif platform == 'Perplexity':
                response_text = self.query_perplexity(query.query_text)

            if response_text:
                self.save_response(query.query_id, query.query_text, platform, response_text)
                print(f"✓ ({len(response_text)} chars)")
                results[platform] = True
            else:
                print("✗ No response")
                results[platform] = False

            # Rate limiting - be nice to APIs
            time.sleep(1)

        return results

    def collect_all(self, limit: Optional[int] = None, platforms: List[str] = None) -> Dict[str, int]:
        """Collect responses for all active queries."""
        queries = self.db.query(models.Query).filter(models.Query.active == True).all()

        if limit:
            queries = queries[:limit]

        print(f"\n{'='*60}")
        print(f"Response Collection Started")
        print(f"{'='*60}")
        print(f"Queries to process: {len(queries)}")
        print(f"Platforms: {platforms or ['ChatGPT', 'Claude', 'Gemini', 'Perplexity']}")
        print(f"{'='*60}")

        stats = {
            'total_queries': len(queries),
            'successful': 0,
            'failed': 0,
            'ChatGPT': 0,
            'Claude': 0,
            'Gemini': 0,
            'Perplexity': 0
        }

        for query in queries:
            results = self.collect_for_query(query, platforms)

            if any(results.values()):
                stats['successful'] += 1
            else:
                stats['failed'] += 1

            for platform, success in results.items():
                if success:
                    stats[platform] += 1

        print(f"\n{'='*60}")
        print(f"Collection Summary")
        print(f"{'='*60}")
        print(f"  • Total queries processed: {stats['total_queries']}")
        print(f"  • Successful: {stats['successful']}")
        print(f"  • Failed: {stats['failed']}")
        print(f"  • ChatGPT responses: {stats['ChatGPT']}")
        print(f"  • Claude responses: {stats['Claude']}")
        print(f"  • Gemini responses: {stats['Gemini']}")
        print(f"  • Perplexity responses: {stats['Perplexity']}")
        print(f"{'='*60}\n")

        return stats


def main():
    """Main function to run response collection."""
    print("\n🚀 AIRO Response Collection Tool\n")

    # Check for API keys
    print("Checking API keys...")
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
    has_google = bool(os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY'))

    if not any([has_openai, has_anthropic, has_google]):
        print("\n❌ ERROR: No API keys found in .env file!")
        print("\nPlease add at least one of these to your .env file:")
        print("  OPENAI_API_KEY=your-key-here")
        print("  ANTHROPIC_API_KEY=your-key-here")
        print("  GEMINI_API_KEY=your-key-here")
        print("\nYour .env file is located at: /Users/rkremen/Documents/Code/airo_project/.env")
        sys.exit(1)

    print()

    # Create database session
    db = SessionLocal()

    try:
        # Initialize collector
        collector = ResponseCollector(db)

        # Check if we have queries
        query_count = db.query(models.Query).filter(models.Query.active == True).count()
        if query_count == 0:
            print("❌ No active queries found in database!")
            print("Please add queries through the web interface at http://localhost:5173/manage/queries")
            sys.exit(1)

        print(f"Found {query_count} active queries\n")

        # Prompt for what to do
        print("Options:")
        print("  1. Collect responses for ALL queries (recommended for first run)")
        print("  2. Test with first 3 queries only")
        print("  3. Custom number of queries")

        choice = input("\nEnter choice (1-3) [1]: ").strip() or "1"

        limit = None
        if choice == "2":
            limit = 3
        elif choice == "3":
            limit = int(input("How many queries? "))

        # Collect responses
        stats = collector.collect_all(limit=limit)

        # Show next steps
        print("\n✅ Collection complete!")
        print("\nNext steps:")
        print("  1. View responses at http://localhost:5173/data/responses")
        print("  2. Analyze responses (coming soon)")
        print("  3. Check dashboard at http://localhost:5173/")

    except KeyboardInterrupt:
        print("\n\n⚠️  Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
