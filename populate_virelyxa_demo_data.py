"""
Generate realistic demo data for Virelyxa brand showing 8 months of improvement.

This script creates:
- Collection batches (one per month for 8 months)
- Responses with realistic AI model outputs
- Batch analytics showing improving metrics over time
- Demonstrates the value of Tales with clear upward trends
"""
import os
import sys
import random
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models


# Virelyxa's competitors in the biotech space
COMPETITORS = [
    "BioGen Therapeutics",
    "Novacure Biotech",
    "GeneSys Labs",
    "Molecular Dynamics Inc",
    "BioFusion Research",
    "Quantum Therapeutics"
]

# Descriptors that Virelyxa wants to own
TARGET_DESCRIPTORS = [
    "innovative",
    "cutting-edge",
    "patient-focused",
    "breakthrough therapy",
    "precision medicine",
    "clinical excellence",
    "research-driven",
    "trusted partner"
]

# Sample queries (mix of branded and unbranded)
SAMPLE_QUERIES = [
    {"id": "Q001", "text": "What are the leading companies in precision medicine?", "branded": False},
    {"id": "Q002", "text": "Tell me about Virelyxa's breakthrough therapies", "branded": True},
    {"id": "Q003", "text": "Who are the top biotech companies in oncology research?", "branded": False},
    {"id": "Q004", "text": "What innovations has Virelyxa made in patient care?", "branded": True},
    {"id": "Q005", "text": "Which companies are leaders in clinical trial innovation?", "branded": False},
    {"id": "Q006", "text": "What is Virelyxa known for in the biotech industry?", "branded": True},
    {"id": "Q007", "text": "Who are the most trusted biotech research partners?", "branded": False},
    {"id": "Q008", "text": "What makes Virelyxa different from other biotech companies?", "branded": True},
    {"id": "Q009", "text": "Which biotech firms focus on precision medicine?", "branded": False},
    {"id": "Q010", "text": "How does Virelyxa approach patient-focused care?", "branded": True},
]

PLATFORMS = ["ChatGPT", "Claude", "Gemini", "Perplexity"]


def generate_response_text(query: dict, month_index: int, platform: str, brand_position: str) -> str:
    """
    Generate realistic AI response text based on query, time period, and brand position.
    Early months: less favorable, fewer mentions
    Later months: more favorable, better positioning
    """
    query_text = query["text"]
    is_branded = query["branded"]

    # Base responses by platform style
    if platform == "ChatGPT":
        intro = "Based on current information,"
    elif platform == "Claude":
        intro = "Looking at the biotech landscape,"
    elif platform == "Gemini":
        intro = "According to recent developments,"
    else:  # Perplexity
        intro = "Research indicates that"

    # Early months (0-2): Minimal or no Virelyxa mention
    if month_index <= 2:
        if is_branded:
            # Branded queries still get answers, but brief
            return f"{intro} Virelyxa is a biotech company operating in the precision medicine space. They are working on various therapeutic approaches and conducting clinical research."
        else:
            # Unbranded: rarely mentioned, if at all
            if brand_position == "Not Mentioned":
                competitors_list = random.sample(COMPETITORS, 3)
                return f"{intro} the leading companies in this space include {', '.join(competitors_list[:2])}, and {competitors_list[2]}. These organizations are known for their innovative approaches and clinical excellence."
            else:
                # Occasionally listed at the bottom
                competitors_list = random.sample(COMPETITORS, 2)
                return f"{intro} several companies are making strides including {', '.join(competitors_list)}, and Virelyxa, among others."

    # Middle months (3-5): Growing presence
    elif month_index <= 5:
        if is_branded:
            descriptors = random.sample(TARGET_DESCRIPTORS, 2)
            return f"{intro} Virelyxa has been gaining recognition for its {descriptors[0]} approach to {descriptors[1]}. The company is establishing itself as a notable player in precision medicine with several promising clinical trials underway."
        else:
            if brand_position in ["Leader", "Featured"]:
                competitors_list = random.sample(COMPETITORS, 2)
                descriptor = random.choice(TARGET_DESCRIPTORS)
                return f"{intro} Virelyxa is emerging as a {descriptor} company in this field, alongside established players like {' and '.join(competitors_list)}. Their patient-focused approach is gaining attention."
            else:
                competitors_list = random.sample(COMPETITORS, 3)
                return f"{intro} key players include {', '.join(competitors_list[:2])}, Virelyxa, and {competitors_list[2]}."

    # Later months (6-7): Strong presence and positive positioning
    else:
        if is_branded:
            descriptors = random.sample(TARGET_DESCRIPTORS, 3)
            return f"{intro} Virelyxa has established itself as a {descriptors[0]} leader in precision medicine. The company is recognized for its {descriptors[1]} and {descriptors[2]}, with multiple breakthrough therapies in development. Industry experts frequently cite Virelyxa's patient-focused approach and clinical excellence as setting new standards in biotech research."
        else:
            if brand_position in ["Leader", "Featured"]:
                competitors_list = random.sample(COMPETITORS, 2)
                descriptors = random.sample(TARGET_DESCRIPTORS, 2)
                return f"{intro} Virelyxa stands out as one of the leading companies, known for being {descriptors[0]} and {descriptors[1]}. While {competitors_list[0]} and {competitors_list[1]} are also major players, Virelyxa's unique approach to precision medicine and clinical excellence has positioned it at the forefront of the industry."
            else:
                competitors_list = random.sample(COMPETITORS, 2)
                return f"{intro} notable companies in this space include Virelyxa, {competitors_list[0]}, and {competitors_list[1]}, all contributing to advances in precision medicine."


def calculate_brand_position(month_index: int, is_branded: bool) -> str:
    """
    Determine brand position based on progress over time.
    Shows clear improvement from "Not Mentioned" to "Leader"
    """
    if is_branded:
        # Branded queries always mention the brand
        if month_index <= 2:
            return "Featured"
        elif month_index <= 5:
            return "Leader"
        else:
            return "Leader"
    else:
        # Unbranded queries show progression
        if month_index <= 1:
            # Very early: mostly not mentioned
            return random.choice(["Not Mentioned", "Not Mentioned", "Not Mentioned", "Listed"])
        elif month_index <= 3:
            # Early: occasionally listed
            return random.choice(["Not Mentioned", "Not Mentioned", "Listed", "Listed"])
        elif month_index <= 5:
            # Middle: more featured, occasional leader
            return random.choice(["Listed", "Listed", "Featured", "Featured", "Leader"])
        else:
            # Late: frequently leader or featured
            return random.choice(["Featured", "Featured", "Leader", "Leader", "Leader"])


def calculate_sentiment(month_index: int, brand_mentioned: str) -> str:
    """
    Determine sentiment, improving over time.
    """
    if brand_mentioned == "No":
        return "Neutral"

    if month_index <= 2:
        return random.choice(["Neutral", "Neutral", "Positive"])
    elif month_index <= 5:
        return random.choice(["Neutral", "Positive", "Positive", "Very Positive"])
    else:
        return random.choice(["Positive", "Positive", "Very Positive", "Very Positive"])


def get_descriptors(month_index: int, brand_mentioned: str) -> str:
    """
    Return descriptors used for Virelyxa, improving over time.
    """
    if brand_mentioned == "No":
        return ""

    if month_index <= 2:
        count = random.randint(0, 1)
    elif month_index <= 5:
        count = random.randint(1, 3)
    else:
        count = random.randint(2, 4)

    return ", ".join(random.sample(TARGET_DESCRIPTORS, min(count, len(TARGET_DESCRIPTORS))))


def get_competitors_mentioned(month_index: int) -> str:
    """
    Return competitors mentioned, slightly decreasing over time as Virelyxa gains dominance.
    """
    if month_index <= 2:
        count = random.randint(2, 4)
    elif month_index <= 5:
        count = random.randint(2, 3)
    else:
        count = random.randint(1, 3)

    return ", ".join(random.sample(COMPETITORS, min(count, len(COMPETITORS))))


def create_collection_batch(db: Session, user_id: int, brand_id: int, month_offset: int):
    """
    Create a collection batch for a specific month in the past.
    """
    # Calculate the date (first day of the month, going back from today)
    today = datetime.now()
    target_date = today - timedelta(days=30 * month_offset)
    # Set to first day of that month
    batch_date = target_date.replace(day=1, hour=10, minute=0, second=0, microsecond=0)

    batch_name = f"Monthly Collection - {batch_date.strftime('%B %Y')}"

    print(f"\nCreating batch for {batch_date.strftime('%B %Y')}...")

    # Create the collection batch
    batch = models.CollectionBatch(
        user_id=user_id,
        brand_id=brand_id,
        batch_name=batch_name,
        description=f"Automated monthly collection for {batch_date.strftime('%B %Y')}",
        started_at=batch_date,
        completed_at=batch_date + timedelta(hours=2),
        status="completed",
        total_queries=len(SAMPLE_QUERIES),
        total_responses=len(SAMPLE_QUERIES) * len(PLATFORMS),
        platforms=",".join(PLATFORMS),
        created_at=batch_date
    )
    db.add(batch)
    db.flush()

    # Generate responses for this batch
    total_responses = 0
    mention_count = 0
    leader_count = 0
    featured_count = 0
    listed_count = 0
    not_mentioned_count = 0

    very_positive_count = 0
    positive_count = 0
    neutral_count = 0
    negative_count = 0
    very_negative_count = 0
    mixed_count = 0

    sov_data = {}
    descriptor_counts = {}

    for query in SAMPLE_QUERIES:
        for platform in PLATFORMS:
            # Determine brand position
            brand_position = calculate_brand_position(7 - month_offset, query["branded"])
            brand_mentioned = "Yes" if brand_position != "Not Mentioned" else "No"

            # Generate response text
            response_text = generate_response_text(
                query,
                7 - month_offset,
                platform,
                brand_position
            )

            # Determine sentiment
            sentiment = calculate_sentiment(7 - month_offset, brand_mentioned)

            # Get descriptors and competitors
            descriptors = get_descriptors(7 - month_offset, brand_mentioned)
            competitors = get_competitors_mentioned(7 - month_offset)

            # Create response
            response = models.Response(
                user_id=user_id,
                brand_id=brand_id,
                batch_id=batch.id,
                query_id=query["id"],
                query_text=query["text"],
                platform=platform,
                response_text=response_text,
                timestamp=batch_date + timedelta(minutes=random.randint(0, 120)),
                brand_mentioned=brand_mentioned,
                brand_position=brand_position,
                sentiment=sentiment,
                descriptors=descriptors,
                competitors=competitors,
                sources="",
                analyzed_at=batch_date + timedelta(hours=2, minutes=30)
            )
            db.add(response)

            total_responses += 1

            # Track metrics (excluding branded queries)
            if not query["branded"]:
                if brand_mentioned == "Yes":
                    mention_count += 1

                # Position counts
                if brand_position == "Leader":
                    leader_count += 1
                elif brand_position == "Featured":
                    featured_count += 1
                elif brand_position == "Listed":
                    listed_count += 1
                else:
                    not_mentioned_count += 1

                # Sentiment counts (only for mentioned)
                if brand_mentioned == "Yes":
                    if sentiment == "Very Positive":
                        very_positive_count += 1
                    elif sentiment == "Positive":
                        positive_count += 1
                    elif sentiment == "Neutral":
                        neutral_count += 1
                    elif sentiment == "Negative":
                        negative_count += 1
                    elif sentiment == "Very Negative":
                        very_negative_count += 1
                    else:
                        mixed_count += 1

                # Track SOV (count Virelyxa)
                if brand_mentioned == "Yes":
                    sov_data["Virelyxa"] = sov_data.get("Virelyxa", 0) + 1

                # Track competitors
                for comp in competitors.split(", "):
                    if comp:
                        sov_data[comp] = sov_data.get(comp, 0) + 1

                # Track descriptors
                for desc in descriptors.split(", "):
                    if desc:
                        descriptor_counts[desc] = descriptor_counts.get(desc, 0) + 1

    # Calculate mention rate (excluding branded queries)
    unbranded_responses = len(SAMPLE_QUERIES) * len(PLATFORMS) - sum(1 for q in SAMPLE_QUERIES if q["branded"]) * len(PLATFORMS)
    mention_rate = (mention_count / unbranded_responses * 100) if unbranded_responses > 0 else 0

    # Create batch analytics
    analytics = models.BatchAnalytics(
        user_id=user_id,
        brand_id=brand_id,
        batch_id=batch.id,
        collection_date=batch_date,
        total_responses=total_responses,
        mention_count=mention_count,
        mention_rate=mention_rate,
        leader_count=leader_count,
        featured_count=featured_count,
        listed_count=listed_count,
        not_mentioned_count=not_mentioned_count,
        very_positive_count=very_positive_count,
        positive_count=positive_count,
        neutral_count=neutral_count,
        negative_count=negative_count,
        very_negative_count=very_negative_count,
        mixed_count=mixed_count,
        sov_data=json.dumps(sov_data),
        descriptor_data=json.dumps(descriptor_counts),
        computed_at=batch_date + timedelta(hours=3)
    )
    db.add(analytics)

    print(f"  ✓ Created {total_responses} responses")
    print(f"  ✓ Mention rate: {mention_rate:.1f}%")
    print(f"  ✓ Leader positions: {leader_count}")
    print(f"  ✓ Featured positions: {featured_count}")

    return batch


def main():
    """
    Main function to populate demo data for Virelyxa.
    """
    print("=" * 60)
    print("Virelyxa Demo Data Generator")
    print("=" * 60)

    # Get database session
    db = SessionLocal()

    try:
        # Get user (assuming you have a user - replace with your actual user_id)
        user = db.query(models.User).filter(models.User.email == "robotrachel@gmail.com").first()
        if not user:
            print("Error: User not found. Please update the email in the script.")
            return

        print(f"\nUser: {user.email} (ID: {user.id})")

        # Get or create Virelyxa brand
        brand = db.query(models.BrandInfo).filter(
            models.BrandInfo.brand_name == "Virelyxa",
            models.BrandInfo.user_id == user.id
        ).first()

        if not brand:
            print("\nCreating Virelyxa brand...")
            brand = models.BrandInfo(
                user_id=user.id,
                brand_name="Virelyxa",
                website_url="https://virelyxa.com",
                industry="Biotechnology / Pharmaceuticals",
                description="A precision medicine company developing breakthrough therapies for oncology patients.",
                strategic_messages="Patient-focused care, clinical excellence, innovative research, trusted biotech partner",
                is_active=False
            )
            db.add(brand)
            db.commit()
            print(f"  ✓ Virelyxa brand created (ID: {brand.id})")
        print(f"Brand: {brand.brand_name} (ID: {brand.id})")

        # Delete existing Virelyxa data to start fresh
        print("\nCleaning up existing Virelyxa data...")
        db.query(models.BatchAnalytics).filter(models.BatchAnalytics.brand_id == brand.id).delete()
        db.query(models.Response).filter(models.Response.brand_id == brand.id).delete()
        db.query(models.CollectionBatch).filter(models.CollectionBatch.brand_id == brand.id).delete()
        db.commit()
        print("  ✓ Existing data cleaned")

        # Create 8 months of historical data (most recent month = 0, oldest = 7)
        print("\nGenerating 8 months of historical data...")
        for month_offset in range(7, -1, -1):  # 7 months ago to current month
            create_collection_batch(db, user.id, brand.id, month_offset)
            db.commit()

        print("\n" + "=" * 60)
        print("✓ Demo data generation complete!")
        print("=" * 60)
        print("\nVirelyxa now has 8 months of realistic data showing:")
        print("  • Increasing mention rates over time")
        print("  • Improving brand positioning (Not Mentioned → Leader)")
        print("  • Better sentiment scores")
        print("  • Growing descriptor ownership")
        print("  • Stronger share of voice")
        print("\nYou can now demo Tales to prospective users!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
