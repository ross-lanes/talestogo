"""
Generate fake trend data for testing time-series visualizations.
This script creates 12 months of collection batches with realistic data.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app import models
from sqlalchemy import text

# Sample data pools
PLATFORMS = ['ChatGPT', 'Claude', 'Gemini', 'Perplexity']

SAMPLE_QUERIES = [
    "What are the best project management tools?",
    "Which CRM software should I use?",
    "What's the best marketing automation platform?",
    "Top collaboration tools for remote teams",
    "Best customer support software",
    "Which analytics platform should I choose?",
    "What are the leading business intelligence tools?",
    "Best email marketing platforms",
    "Top social media management tools",
    "Which productivity software is most popular?",
]

SAMPLE_COMPETITORS = [
    "Asana", "Monday.com", "Trello", "Jira", "ClickUp",
    "Salesforce", "HubSpot", "Zoho", "Pipedrive", "Freshworks",
    "Slack", "Microsoft Teams", "Zoom", "Google Workspace",
    "Zendesk", "Intercom", "Drift", "Help Scout"
]

BRAND_POSITIONS = ['Leader', 'Featured', 'Listed', 'Not Mentioned']
SENTIMENTS = ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative']

SAMPLE_DESCRIPTORS = [
    "user-friendly", "intuitive", "powerful", "flexible", "affordable",
    "scalable", "reliable", "innovative", "comprehensive", "easy-to-use",
    "feature-rich", "customizable", "efficient", "modern", "robust"
]


def generate_response_text(brand_name: str, position: str, sentiment: str, competitors: list) -> str:
    """Generate realistic response text based on position and sentiment."""

    if position == 'Leader':
        if sentiment in ['Very Positive', 'Positive']:
            text = f"{brand_name} is widely regarded as the industry leader in this space. "
            text += f"It offers exceptional features including {random.choice(SAMPLE_DESCRIPTORS)} interface and {random.choice(SAMPLE_DESCRIPTORS)} functionality. "
        elif sentiment == 'Neutral':
            text = f"{brand_name} is a leading option with solid capabilities. "
        else:
            text = f"While {brand_name} is a major player, some users report concerns about pricing and complexity. "

    elif position == 'Featured':
        text = f"Top options include {brand_name}"
        if competitors:
            text += f", {competitors[0]}, and {competitors[1] if len(competitors) > 1 else 'others'}"
        text += ". "
        if sentiment in ['Very Positive', 'Positive']:
            text += f"{brand_name} stands out for its {random.choice(SAMPLE_DESCRIPTORS)} design. "

    elif position == 'Listed':
        text = f"Popular choices in this category include "
        if competitors:
            text += f"{competitors[0]}, {competitors[1] if len(competitors) > 1 else 'alternatives'}, "
        text += f"and {brand_name}. "

    else:  # Not Mentioned
        text = f"The leading options are "
        if competitors:
            text += f"{competitors[0]}, {competitors[1] if len(competitors) > 1 else 'and others'}"
        else:
            text += "various established platforms"
        text += ". "

    # Add sentiment-specific content
    if sentiment == 'Very Positive':
        text += f"Users consistently praise {brand_name} for its outstanding performance and support."
    elif sentiment == 'Positive':
        text += f"{brand_name} receives positive feedback from its user base."
    elif sentiment == 'Neutral':
        text += f"{brand_name} provides standard functionality for most use cases."
    elif sentiment == 'Negative':
        text += f"However, {brand_name} has received criticism for certain limitations."
    elif sentiment == 'Very Negative':
        text += f"Unfortunately, {brand_name} has significant drawbacks that concern many users."

    return text


def generate_batch_data(user_id: int, brand_id: int, brand_name: str, month_offset: int, base_date: datetime):
    """
    Generate data for one collection batch.
    Creates realistic trends:
    - Gradual improvement in brand mentions over time
    - Shifts in positioning
    - Evolving sentiment
    - Changing competitor landscape
    """

    # Calculate date for this batch (going backwards from base_date)
    batch_date = base_date - timedelta(days=30 * month_offset)

    # Trend parameters (improve over time as month_offset decreases)
    progress_factor = 1 - (month_offset / 12)  # 0 at oldest, 1 at newest

    # Mention rate: grows from 40% to 70%
    base_mention_rate = 0.40 + (0.30 * progress_factor)

    # Position distribution shifts toward Leader over time
    position_weights = {
        'Leader': 0.10 + (0.20 * progress_factor),      # 10% -> 30%
        'Featured': 0.25 + (0.10 * progress_factor),    # 25% -> 35%
        'Listed': 0.40 - (0.15 * progress_factor),      # 40% -> 25%
        'Not Mentioned': 0.25 - (0.15 * progress_factor) # 25% -> 10%
    }

    # Sentiment improves over time
    sentiment_weights = {
        'Very Positive': 0.15 + (0.15 * progress_factor),  # 15% -> 30%
        'Positive': 0.30 + (0.10 * progress_factor),       # 30% -> 40%
        'Neutral': 0.40 - (0.10 * progress_factor),        # 40% -> 30%
        'Negative': 0.10 - (0.08 * progress_factor),       # 10% -> 2%
        'Very Negative': 0.05 - (0.03 * progress_factor)   # 5% -> 2%
    }

    batch_data = {
        'date': batch_date,
        'responses': [],
        'mention_rate': base_mention_rate,
        'position_weights': position_weights,
        'sentiment_weights': sentiment_weights
    }

    # Generate 50 responses per batch
    num_responses = 50

    for i in range(num_responses):
        # Determine if brand is mentioned
        brand_mentioned = random.random() < base_mention_rate

        if brand_mentioned:
            mention_type = random.choice(['Yes', 'Yes', 'Yes', 'Indirect'])  # 75% direct, 25% indirect

            # Pick position based on weights
            position = random.choices(
                list(position_weights.keys()),
                weights=list(position_weights.values())
            )[0]

            # Pick sentiment based on weights (only for direct mentions)
            if mention_type == 'Yes':
                sentiment = random.choices(
                    list(sentiment_weights.keys()),
                    weights=list(sentiment_weights.values())
                )[0]
            else:
                sentiment = 'Neutral'
        else:
            mention_type = 'No'
            position = 'Not Mentioned'
            sentiment = 'Neutral'

        # Pick 2-4 competitors
        num_competitors = random.randint(2, 4)
        competitors = random.sample(SAMPLE_COMPETITORS, num_competitors)

        # Pick 2-3 descriptors
        descriptors = random.sample(SAMPLE_DESCRIPTORS, random.randint(2, 3))

        response_data = {
            'query_text': random.choice(SAMPLE_QUERIES),
            'platform': random.choice(PLATFORMS),
            'brand_mentioned': mention_type,
            'brand_position': position,
            'sentiment': sentiment,
            'competitors': ', '.join(competitors),
            'descriptors': ', '.join(descriptors),
            'response_text': generate_response_text(brand_name, position, sentiment, competitors),
            'timestamp': batch_date + timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
        }

        batch_data['responses'].append(response_data)

    return batch_data


def create_fake_trend_data(email: str, brand_name: str = "YourBrand"):
    """Create 12 months of fake trend data for a user."""

    db = SessionLocal()

    try:
        # Find user
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            print(f"Error: User with email {email} not found")
            return

        print(f"Found user: {user.email} (ID: {user.id})")

        # Find or create brand
        brand = db.query(models.BrandInfo).filter(
            models.BrandInfo.user_id == user.id,
            models.BrandInfo.brand_name == brand_name
        ).first()

        if not brand:
            print(f"Creating brand: {brand_name}")
            brand = models.BrandInfo(
                user_id=user.id,
                brand_name=brand_name,
                industry="Software",
                website_url="https://example.com"
            )
            db.add(brand)
            db.commit()
            db.refresh(brand)

        print(f"Using brand: {brand.brand_name} (ID: {brand.id})")

        # Create sample queries first
        print("Creating sample queries...")
        query_objects = []

        # Get the highest existing query_id to generate new ones (format: Q001, Q002, etc.)
        max_query_id_result = db.execute(text("SELECT query_id FROM queries ORDER BY query_id DESC LIMIT 1")).fetchone()
        if max_query_id_result and max_query_id_result[0]:
            # Extract number from format "Q001" -> 1
            last_num = int(max_query_id_result[0].replace('Q', ''))
            next_query_num = last_num + 1
        else:
            next_query_num = 1

        for query_text in SAMPLE_QUERIES:
            # Check if query exists
            existing = db.query(models.Query).filter(
                models.Query.user_id == user.id,
                models.Query.brand_id == brand.id,
                models.Query.query_text == query_text
            ).first()

            if not existing:
                query_id = f"Q{next_query_num:03d}"  # Format as Q001, Q002, etc.
                query = models.Query(
                    user_id=user.id,
                    brand_id=brand.id,
                    query_id=query_id,
                    query_text=query_text,
                    brand_in_query=False,  # No branded queries for clean trend data
                    created_at=datetime.now()
                )
                db.add(query)
                query_objects.append(query)
                next_query_num += 1
            else:
                query_objects.append(existing)

        db.commit()
        print(f"Created/found {len(query_objects)} queries")

        # Generate 12 months of data
        base_date = datetime.now()
        print(f"\nGenerating 12 months of collection batches (starting from {base_date.strftime('%Y-%m-%d')})...")

        for month in range(11, -1, -1):  # 11 months ago to now
            print(f"\n=== Month {12 - month}/12 ===")

            batch_data = generate_batch_data(user.id, brand.id, brand_name, month, base_date)

            # Create batch
            batch_name = f"Trend Data {batch_data['date'].strftime('%B %Y')}"
            batch = models.CollectionBatch(
                user_id=user.id,
                brand_id=brand.id,
                batch_name=batch_name,
                status='completed',
                started_at=batch_data['date'],
                completed_at=batch_data['date'] + timedelta(hours=2)
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)

            print(f"Created batch {batch.id} for {batch_data['date'].strftime('%Y-%m-%d')}")

            # Create responses
            for i, response_data in enumerate(batch_data['responses']):
                # Pick a random query
                query = random.choice(query_objects)

                response = models.Response(
                    user_id=user.id,
                    brand_id=brand.id,
                    batch_id=batch.id,
                    query_id=query.query_id,
                    query_text=response_data['query_text'],
                    platform=response_data['platform'],
                    response_text=response_data['response_text'],
                    brand_mentioned=response_data['brand_mentioned'],
                    brand_position=response_data['brand_position'],
                    sentiment=response_data['sentiment'],
                    competitors=response_data['competitors'],
                    descriptors=response_data['descriptors'],
                    timestamp=response_data['timestamp']
                )
                db.add(response)

            db.commit()

            # Print summary
            mention_count = sum(1 for r in batch_data['responses'] if r['brand_mentioned'] in ['Yes', 'Indirect'])
            print(f"  Created {len(batch_data['responses'])} responses")
            print(f"  Mention rate: {mention_count}/{len(batch_data['responses'])} ({mention_count/len(batch_data['responses'])*100:.1f}%)")

        print(f"\n✓ Successfully generated 12 months of trend data!")
        print(f"  Total batches: 12")
        print(f"  Total responses: {12 * 50}")
        print(f"\nYou can now view the trends at:")
        print(f"  - http://localhost:5173/analytics/brand-mentions")
        print(f"  - http://localhost:5173/analytics/positioning")
        print(f"  - http://localhost:5173/analytics/sentiment")
        print(f"  - http://localhost:5173/analytics/share-of-voice")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_fake_trend_data.py <user_email> [brand_name]")
        print("Example: python generate_fake_trend_data.py user@example.com MyBrand")
        sys.exit(1)

    email = sys.argv[1]
    brand_name = sys.argv[2] if len(sys.argv) > 2 else "YourBrand"

    print(f"Generating fake trend data for user: {email}")
    print(f"Brand: {brand_name}")
    print("-" * 50)

    create_fake_trend_data(email, brand_name)
