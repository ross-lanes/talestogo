"""
Generate realistic demo data for Virelyxa brand showing 4 months of improvement.

This script creates:
- Collection batches (one per month for 4 months)
- Responses with realistic AI model outputs
- Batch analytics showing improving metrics over time
- Monthly reports with insights and recommendations
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
    Month 0 = oldest, Month 3 = most recent (4 months total)
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

    # Month 0-1: Minimal or no Virelyxa mention
    if month_index <= 1:
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

    # Month 2: Growing presence
    elif month_index == 2:
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

    # Month 3 (most recent): Strong presence and positive positioning
    else:  # month_index == 3
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
    Determine brand position based on progress over time (4 months).
    Shows clear improvement from "Not Mentioned" to "Leader"
    Month 0 = oldest, Month 3 = most recent
    """
    if is_branded:
        # Branded queries always mention the brand
        if month_index <= 1:
            return "Featured"
        else:
            return "Leader"
    else:
        # Unbranded queries show progression over 4 months
        if month_index == 0:
            # Month 1: mostly not mentioned
            return random.choice(["Not Mentioned", "Not Mentioned", "Not Mentioned", "Listed"])
        elif month_index == 1:
            # Month 2: occasionally listed
            return random.choice(["Not Mentioned", "Listed", "Listed", "Featured"])
        elif month_index == 2:
            # Month 3: more featured, some leader
            return random.choice(["Listed", "Featured", "Featured", "Leader"])
        else:  # month_index == 3
            # Month 4: frequently leader or featured
            return random.choice(["Featured", "Leader", "Leader", "Leader"])


def calculate_sentiment(month_index: int, brand_mentioned: str) -> str:
    """
    Determine sentiment, improving over time (4 months).
    """
    if brand_mentioned == "No":
        return "Neutral"

    if month_index == 0:
        return random.choice(["Neutral", "Neutral", "Positive"])
    elif month_index == 1:
        return random.choice(["Neutral", "Positive", "Positive"])
    elif month_index == 2:
        return random.choice(["Positive", "Positive", "Very Positive"])
    else:  # month_index == 3
        return random.choice(["Positive", "Very Positive", "Very Positive", "Very Positive"])


def get_descriptors(month_index: int, brand_mentioned: str) -> str:
    """
    Return descriptors used for Virelyxa, improving over time (4 months).
    """
    if brand_mentioned == "No":
        return ""

    if month_index == 0:
        count = random.randint(0, 1)
    elif month_index == 1:
        count = random.randint(1, 2)
    elif month_index == 2:
        count = random.randint(2, 3)
    else:  # month_index == 3
        count = random.randint(3, 4)

    return ", ".join(random.sample(TARGET_DESCRIPTORS, min(count, len(TARGET_DESCRIPTORS))))


def get_competitors_mentioned(month_index: int) -> str:
    """
    Return competitors mentioned, slightly decreasing over time as Virelyxa gains dominance (4 months).
    """
    if month_index == 0:
        count = random.randint(3, 4)
    elif month_index == 1:
        count = random.randint(2, 3)
    elif month_index == 2:
        count = random.randint(2, 3)
    else:  # month_index == 3
        count = random.randint(1, 2)

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
            # Calculate month index (0 = oldest, 3 = newest for 4 months)
            month_index = 3 - month_offset

            # Determine brand position
            brand_position = calculate_brand_position(month_index, query["branded"])
            brand_mentioned = "Yes" if brand_position != "Not Mentioned" else "No"

            # Generate response text
            response_text = generate_response_text(
                query,
                month_index,
                platform,
                brand_position
            )

            # Determine sentiment
            sentiment = calculate_sentiment(month_index, brand_mentioned)

            # Get descriptors and competitors
            descriptors = get_descriptors(month_index, brand_mentioned)
            competitors = get_competitors_mentioned(month_index)

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
    db.flush()  # Ensure analytics is committed so we can query it

    print(f"  ✓ Created {total_responses} responses")
    print(f"  ✓ Mention rate: {mention_rate:.1f}%")
    print(f"  ✓ Leader positions: {leader_count}")
    print(f"  ✓ Featured positions: {featured_count}")

    return batch, analytics


def generate_monthly_report(db: Session, user_id: int, brand_id: int, batch: models.CollectionBatch, analytics: models.BatchAnalytics, month_index: int):
    """
    Generate a realistic monthly report based on the batch analytics.
    Month 0 = oldest, Month 3 = most recent (4 months total)
    """
    month_name = batch.started_at.strftime("%B %Y")
    mention_rate = analytics.mention_rate

    # Generate insights based on month progression
    if month_index == 0:
        trend = "initial"
        tone = "We're establishing baseline metrics and beginning to track AI visibility."
        outlook = "As we implement strategic recommendations, we expect to see gradual improvement in mention rates and positioning."
    elif month_index == 1:
        trend = "emerging"
        tone = "We're seeing early signs of improved visibility, with mention rates beginning to climb."
        outlook = "Continue current strategies with focus on target descriptors. We expect further improvements in positioning next month."
    elif month_index == 2:
        trend = "growing"
        tone = "Significant progress is evident, with Virelyxa appearing more frequently in leadership positions."
        outlook = "Momentum is building. Maintain focus on owning target descriptors and we anticipate continued strong performance."
    else:  # month_index == 3
        trend = "strong"
        tone = "Excellent results this month, with Virelyxa consistently appearing as a leader in AI responses."
        outlook = "Continue current strategies to maintain and build upon this strong positioning. Consider expanding into adjacent market segments."

    # Generate descriptors summary
    descriptor_data = json.loads(analytics.sov_data) if analytics.sov_data else {}
    top_descriptors = sorted(descriptor_data.items(), key=lambda x: x[1], reverse=True)[:3] if descriptor_data else []

    # Create report content
    report_content = f"""# Monthly AI Visibility Report - {month_name}

## Executive Summary

{tone}

**Key Metrics:**
- **Mention Rate:** {mention_rate:.1f}%
- **Total Responses Analyzed:** {analytics.total_responses}
- **Brand Mentions:** {analytics.mention_count}
- **Leadership Positions:** {analytics.leader_count}
- **Featured Positions:** {analytics.featured_count}

---

## Performance Overview

### Brand Positioning

This month, Virelyxa appeared in **{analytics.mention_count} of {analytics.total_responses} responses** ({mention_rate:.1f}% mention rate).

**Position Breakdown:**
- 🏆 Leader: {analytics.leader_count} responses
- ⭐ Featured: {analytics.featured_count} responses
- 📋 Listed: {analytics.listed_count} responses
- ❌ Not Mentioned: {analytics.not_mentioned_count} responses

### Sentiment Analysis

When Virelyxa was mentioned, the sentiment breakdown was:
- Very Positive: {analytics.very_positive_count}
- Positive: {analytics.positive_count}
- Neutral: {analytics.neutral_count}
- Negative: {analytics.negative_count}

**Overall sentiment is {"very strong" if analytics.very_positive_count > analytics.positive_count else "positive"}**, indicating that AI models associate Virelyxa with favorable characteristics.

---

## 4. Strategic Recommendations

### Strengthen "Patient-Focused Care" and "Clinical Excellence" Association on ChatGPT and Claude

**Strategic Rationale**
Virelyxa is currently underrepresented in ChatGPT and Claude responses to queries about patient-focused biotech companies, despite this being a core brand differentiator. Competitors like BioGen Therapeutics and Novacure Biotech are frequently cited instead, capturing these valuable descriptors. The "patient-focused care" descriptor has only {analytics.descriptor_data.get('patient-focused care', 0) if analytics.descriptor_data else 0} associations, while "clinical excellence" appears {analytics.descriptor_data.get('clinical excellence', 0) if analytics.descriptor_data else 0} times—significantly lower than competitors. Without proactive content strategy, Virelyxa will continue to lose share of voice in these high-value search contexts.

**Key Actions**
- Develop a series of patient success stories and case studies highlighting precision medicine outcomes, explicitly using "patient-focused care" and "clinical excellence" in titles and content
- Publish these stories on the Virelyxa website, Medium, and LinkedIn, ensuring they are indexed by Google and accessible to LLM training pipelines
- Pitch feature stories to BioPharm Insight, FierceBiotech, and MedCity News about Virelyxa's patient-centric approach to precision medicine
- Submit posts to relevant Reddit communities (r/biotech, r/medicine) and Hacker News, emphasizing the patient outcomes and clinical rigor
- Collaborate with patient advocacy groups to co-author content that reinforces Virelyxa's commitment to patient-focused innovation

**Target:** Increase "patient-focused care" descriptor associations from {analytics.descriptor_data.get('patient-focused care', 0) if analytics.descriptor_data else 0} to 25+ and "clinical excellence" from {analytics.descriptor_data.get('clinical excellence', 0) if analytics.descriptor_data else 0} to 30+ by next quarter.

### Claim "Innovative Research" and "Breakthrough Therapies" Positioning via High-Profile Research Publications

**Strategic Rationale**
Virelyxa is not strongly associated with "innovative research" (only {analytics.descriptor_data.get('innovative research', 0) if analytics.descriptor_data else 0} associations) or "breakthrough therapies" descriptors, while competitors frequently appear in LLM responses to queries about biotech innovation. Recent clinical trials and pipeline developments represent genuine breakthroughs in precision oncology, but these are not being surfaced in LLM outputs. Without proactive content distribution, competitors will continue to dominate the "innovative" and "breakthrough" narrative.

**Key Actions**
- Issue press releases for each major clinical trial milestone or FDA filing, explicitly using "innovative research" and "breakthrough therapy" language in headlines and body copy
- Publish research summaries and white papers on arXiv, bioRxiv, and institutional repositories to ensure academic indexing
- Secure speaking opportunities at major oncology and biotech conferences (ASCO, ASH, BIO International) to establish thought leadership
- Encourage principal investigators to publish accessible blog posts and Twitter threads about trial results, linking back to official Virelyxa communications
- Partner with science journalists to cover pipeline developments in Nature Biotechnology, Science Translational Medicine, and GenomeWeb

**Target:** Achieve at least 20 LLM associations with "innovative research" and 15 with "breakthrough therapies" by Q3, as measured in sampled LLM outputs.

### Expand "Precision Medicine Leadership" Presence in Wikipedia and Medical Reference Sources

**Strategic Rationale**
The "precision medicine" descriptor has only {analytics.descriptor_data.get('precision medicine', 0) if analytics.descriptor_data else 0} associations, despite this being Virelyxa's core focus. Competitors are more frequently cited as precision medicine leaders in Wikipedia, medical encyclopedias, and .edu sources—key references for ChatGPT and Claude. If Virelyxa does not improve its representation in these authoritative sources, it risks being overlooked in fundamental queries about precision oncology.

**Key Actions**
- Create or significantly expand a Wikipedia entry for Virelyxa, emphasizing precision medicine platform, clinical approach, and published outcomes
- Collaborate with medical faculty and oncology departments to ensure Virelyxa is cited in course materials, grand rounds presentations, and continuing medical education (CME) programs
- Submit comprehensive articles about Virelyxa's precision medicine approach to medical reference works and specialty encyclopedias
- Ensure Virelyxa therapies are properly documented in clinical databases (ClinicalTrials.gov, DrugBank) with detailed mechanism of action and precision medicine categorization
- Encourage citation in peer-reviewed review articles and meta-analyses in high-impact oncology journals

**Target:** Triple "precision medicine" descriptor associations in LLM outputs by end of next quarter, with presence in at least 5 major medical reference sources.

### Dominate "Trusted Biotech Partner" Positioning in Perplexity and Gemini

**Strategic Rationale**
While Virelyxa shows some traction on search-augmented LLMs like Perplexity and Gemini, the "trusted biotech partner" positioning (currently {analytics.descriptor_data.get('trusted biotech partner', 0) if analytics.descriptor_data else 0} associations) needs significant strengthening. Competitors are actively building trust through partnerships, industry collaborations, and thought leadership—creating a perception gap that affects business development opportunities and investor confidence.

**Key Actions**
- Announce and publicize strategic partnerships with academic medical centers, pharmaceutical companies, and patient advocacy organizations
- Launch a "Virelyxa Insights" blog featuring expert commentary on precision medicine trends, regulatory developments, and clinical trial design
- Secure placements in industry roundups and "companies to watch" lists in BioCentury, Endpoints News, and STAT News
- Develop case studies and testimonials from clinical collaborators and research partners, distributed through LinkedIn and biotech community forums
- Submit thought leadership articles to The New England Journal of Medicine Catalyst, JAMA Oncology, and other high-authority medical publications

**Target:** Increase "trusted biotech partner" descriptor associations by 200% in Perplexity and Gemini outputs by next quarter, with at least 10 high-authority source citations.

---

## Outlook

{outlook}

**Next Steps:**
1. Monitor weekly trends in AI visibility
2. Continue tracking competitor mentions and positioning
3. Adjust messaging based on sentiment analysis
4. {"Establish baseline content in key areas" if month_index == 0 else "Expand content in high-performing areas"}

---

*Report generated by TALES - Tracking AI LLM Engagement Strategies*
"""

    # Create report
    report = models.Report(
        user_id=user_id,
        brand_id=brand_id,
        title=f"Monthly AI Visibility Report - {month_name}",
        report_content=report_content,
        start_date=batch.started_at,
        end_date=batch.completed_at,
        total_responses=analytics.total_responses,
        mention_rate=mention_rate,
        created_at=batch.completed_at + timedelta(hours=4)
    )
    db.add(report)

    return report


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
                is_active=True
            )
            db.add(brand)
            db.commit()
            print(f"  ✓ Virelyxa brand created (ID: {brand.id})")
        else:
            # Update existing brand to be active
            if not brand.is_active:
                brand.is_active = True
                db.commit()
                print(f"  ✓ Virelyxa brand set to active")
        print(f"Brand: {brand.brand_name} (ID: {brand.id})")

        # Delete existing Virelyxa data to start fresh
        print("\nCleaning up existing Virelyxa data...")
        db.query(models.Report).filter(models.Report.brand_id == brand.id).delete()
        db.query(models.BatchAnalytics).filter(models.BatchAnalytics.brand_id == brand.id).delete()
        db.query(models.Response).filter(models.Response.brand_id == brand.id).delete()
        db.query(models.CollectionBatch).filter(models.CollectionBatch.brand_id == brand.id).delete()
        db.commit()
        print("  ✓ Existing data cleaned")

        # Create 4 months of historical data (most recent month = 0, oldest = 3)
        print("\nGenerating 4 months of historical data with reports...")
        for month_offset in range(3, -1, -1):  # 3 months ago to current month
            month_index = 3 - month_offset
            batch, analytics = create_collection_batch(db, user.id, brand.id, month_offset)

            # Generate monthly report
            report = generate_monthly_report(db, user.id, brand.id, batch, analytics, month_index)
            print(f"  ✓ Monthly report generated")

            db.commit()

        print("\n" + "=" * 60)
        print("✓ Demo data generation complete!")
        print("=" * 60)
        print("\nVirelyxa now has 4 months of complete demo data:")
        print("  • 4 collection batches with realistic AI responses")
        print("  • Batch analytics showing improving metrics")
        print("  • 4 monthly reports with insights and recommendations")
        print("  • Clear upward trends in:")
        print("    - Mention rates (improving over time)")
        print("    - Brand positioning (Not Mentioned → Leader)")
        print("    - Sentiment scores (Neutral → Very Positive)")
        print("    - Descriptor ownership (0-1 → 3-4 descriptors)")
        print("    - Share of voice")
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
