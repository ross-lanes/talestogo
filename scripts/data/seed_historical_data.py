#!/usr/bin/env python3
"""
Seed Historical Data for Demo Purposes
Creates 8 months of backdated collection and analysis data for demonstration.
"""

import os
import sys
from datetime import datetime, timedelta
from random import randint, choice, uniform
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models

# Sample data for generating realistic responses
PLATFORMS = ['ChatGPT', 'Claude', 'Gemini', 'Perplexity']

SAMPLE_QUERIES = [
    "What are the leading fusion energy research organizations?",
    "Which institutions are pioneering spherical tokamak technology?",
    "What organizations are advancing plasma physics research?",
    "Who are the key players in magnetic confinement fusion?",
    "What labs are developing liquid lithium divertor technology?",
    "Which research facilities focus on fusion energy science?",
    "What are the most innovative plasma research centers?",
    "Who leads in stellarator and tokamak development?",
]

DESCRIPTORS = [
    "pioneering", "innovative", "cutting-edge", "leading",
    "world-class", "groundbreaking", "advanced", "state-of-the-art"
]

COMPETITORS = [
    "MIT PSFC", "ITER", "UKAEA", "Commonwealth Fusion Systems",
    "Tokamak Energy", "General Atomics", "Lawrence Livermore"
]

def generate_response_text(brand_name, query, mention_brand=True, position=None):
    """Generate a realistic AI response."""
    if not mention_brand:
        return f"The fusion energy landscape includes several key players. {choice(COMPETITORS)} is making significant progress in magnetic confinement fusion. Various research institutions worldwide are contributing to advancements in plasma physics and fusion technology."

    descriptor = choice(DESCRIPTORS)
    competitor1 = choice(COMPETITORS)
    competitor2 = choice([c for c in COMPETITORS if c != competitor1])

    if position == 1:  # Leader
        return f"{brand_name} stands out as a {descriptor} institution in fusion energy research. As a U.S. Department of Energy national laboratory, {brand_name} has been at the forefront of spherical tokamak development and plasma physics research. The lab's work on liquid lithium technology and advanced diagnostics represents significant contributions to the field, alongside efforts by {competitor1} and {competitor2}."
    elif position == 2:  # Featured
        return f"Several organizations are leading fusion energy research. {brand_name}, {competitor1}, and {competitor2} are among the prominent institutions advancing magnetic confinement fusion. {brand_name} has made notable contributions to spherical tokamak technology and plasma science."
    elif position in [3, 4, 5]:  # Listed
        return f"The fusion energy field includes many research organizations. {competitor1} and {competitor2} are working on various fusion approaches. {brand_name} is also involved in fusion research, particularly in plasma physics studies."
    else:
        return generate_response_text(brand_name, query, mention_brand=False)


def seed_historical_data(db_url: str, user_id: int, brand_id: int, months: int = 8):
    """
    Seed historical data for demonstration purposes.

    Args:
        db_url: PostgreSQL database URL
        user_id: User ID to associate data with
        brand_id: Brand ID to associate data with
        months: Number of months of historical data to generate
    """
    print("="*60)
    print("Historical Data Seeding Tool")
    print("="*60)
    print(f"\nDatabase: {db_url[:50]}...")
    print(f"User ID: {user_id}")
    print(f"Brand ID: {brand_id}")
    print(f"Months: {months}")
    print()

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Verify user and brand exist
        user = session.query(models.User).filter_by(id=user_id).first()
        brand = session.query(models.BrandInfo).filter_by(id=brand_id).first()

        if not user:
            print(f"❌ User {user_id} not found!")
            return
        if not brand:
            print(f"❌ Brand {brand_id} not found!")
            return

        print(f"✓ User: {user.email}")
        print(f"✓ Brand: {brand.brand_name}\n")

        brand_name = brand.brand_name

        # Generate monthly data going backwards from now
        stats_summary = []

        for month_offset in range(months - 1, -1, -1):
            # Calculate date for this batch (first day of month)
            batch_date = datetime.now() - timedelta(days=30 * month_offset)
            batch_date = batch_date.replace(day=1, hour=9, minute=0, second=0, microsecond=0)

            print(f"Generating data for {batch_date.strftime('%B %Y')}...")

            # Create collection batch
            batch_name = f"Monthly Collection - {batch_date.strftime('%B %Y')}"
            batch = models.CollectionBatch(
                user_id=user_id,
                brand_id=brand_id,
                batch_name=batch_name,
                description=f"Automated monthly collection for {batch_date.strftime('%B %Y')}",
                platforms=", ".join(PLATFORMS),
                started_at=batch_date,
                completed_at=batch_date + timedelta(minutes=15),
                status='completed',
                total_queries=len(SAMPLE_QUERIES),
                total_responses=len(SAMPLE_QUERIES) * len(PLATFORMS)
            )
            session.add(batch)
            session.flush()

            # Generate responses for this month
            # Vary metrics over time to show trends
            mention_rate_base = 0.50 + (month_offset * 0.03)  # Improving over time
            leader_rate = 0.15 + (month_offset * 0.02)
            positive_rate = 0.60 + (month_offset * 0.02)

            responses_created = 0
            mentions = 0
            leader_count = 0
            featured_count = 0
            listed_count = 0
            positive_count = 0

            for query_text in SAMPLE_QUERIES:
                query_id = f"Q{randint(1000, 9999)}"

                for platform in PLATFORMS:
                    # Determine if brand is mentioned
                    mention_brand = uniform(0, 1) < mention_rate_base

                    if mention_brand:
                        mentions += 1
                        # Determine position
                        rand_pos = uniform(0, 1)
                        if rand_pos < leader_rate:
                            position = 1
                            leader_count += 1
                        elif rand_pos < leader_rate + 0.25:
                            position = 2
                            featured_count += 1
                        else:
                            position = choice([3, 4, 5])
                            listed_count += 1

                        sentiment = "Positive" if uniform(0, 1) < positive_rate else choice(["Neutral", "Mixed"])
                        if sentiment == "Positive":
                            positive_count += 1

                        descriptors_used = ", ".join([choice(DESCRIPTORS) for _ in range(randint(1, 3))])
                        competitors_mentioned = ", ".join([choice(COMPETITORS) for _ in range(randint(1, 2))])
                    else:
                        position = None
                        sentiment = None
                        descriptors_used = None
                        competitors_mentioned = choice(COMPETITORS)

                    response_text = generate_response_text(brand_name, query_text, mention_brand, position)

                    response = models.Response(
                        user_id=user_id,
                        brand_id=brand_id,
                        batch_id=batch.id,
                        query_id=query_id,
                        query_text=query_text,
                        platform=platform,
                        response_text=response_text,
                        timestamp=batch_date + timedelta(minutes=randint(0, 15)),
                        brand_mentioned=mention_brand,
                        brand_position=position,
                        sentiment=sentiment,
                        descriptors=descriptors_used,
                        competitors=competitors_mentioned,
                        analyzed_at=batch_date + timedelta(minutes=20)
                    )
                    session.add(response)
                    responses_created += 1

            session.flush()

            # Create batch analytics
            total_responses = len(SAMPLE_QUERIES) * len(PLATFORMS)
            analytics = models.BatchAnalytics(
                user_id=user_id,
                brand_id=brand_id,
                batch_id=batch.id,
                collection_date=batch_date.date(),
                total_responses=total_responses,
                mention_count=mentions,
                mention_rate=round(mentions / total_responses, 3),
                leader_count=leader_count,
                featured_count=featured_count,
                listed_count=listed_count,
                not_mentioned_count=total_responses - mentions,
                positive_count=positive_count,
                neutral_count=mentions - positive_count,
                negative_count=0,
                very_positive_count=0,
                very_negative_count=0,
                mixed_count=0,
                computed_at=batch_date + timedelta(minutes=25)
            )
            session.add(analytics)

            session.commit()

            stats_summary.append({
                'month': batch_date.strftime('%B %Y'),
                'responses': total_responses,
                'mentions': mentions,
                'mention_rate': f"{(mentions/total_responses*100):.1f}%",
                'leaders': leader_count
            })

            print(f"  ✓ Created {responses_created} responses")
            print(f"  ✓ Mention rate: {mentions}/{total_responses} ({mentions/total_responses*100:.1f}%)")
            print(f"  ✓ Leader positions: {leader_count}")
            print()

        print("="*60)
        print("Summary of Generated Data")
        print("="*60)
        for stat in stats_summary:
            print(f"{stat['month']:>15} | {stat['responses']:>3} responses | "
                  f"{stat['mention_rate']:>6} mentions | {stat['leaders']:>2} leaders")
        print("="*60)
        print(f"\n✅ Successfully seeded {months} months of historical data!")
        print(f"\nTotal records created:")
        print(f"  • {months} collection batches")
        print(f"  • {months * len(SAMPLE_QUERIES) * len(PLATFORMS)} responses")
        print(f"  • {months} batch analytics")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()

    finally:
        session.close()


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Seed historical data for demo')
    parser.add_argument('--user-id', type=int, required=True, help='User ID')
    parser.add_argument('--brand-id', type=int, required=True, help='Brand ID')
    parser.add_argument('--months', type=int, default=8, help='Number of months (default: 8)')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    args = parser.parse_args()

    db_url = os.getenv("RENDER_DATABASE_URL")

    if not db_url:
        print("❌ RENDER_DATABASE_URL environment variable not set!")
        print("\nUsage:")
        print("  export RENDER_DATABASE_URL='your-postgres-url'")
        print(f"  python3 seed_historical_data.py --user-id {args.user_id} --brand-id {args.brand_id} --months {args.months} --yes")
        sys.exit(1)

    print("\n🌱 TALES Historical Data Seeding Tool\n")
    print(f"This will create {args.months} months of backdated demo data")
    print(f"for user {args.user_id} and brand {args.brand_id}.")
    print("\n⚠️  This is for DEMO purposes only!")

    if not args.yes:
        response = input("\nProceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            sys.exit(0)

    seed_historical_data(db_url, args.user_id, args.brand_id, args.months)


if __name__ == "__main__":
    main()
