#!/usr/bin/env python3
"""
TALES Report Generation Script
Generates professional analysis reports from analyzed response data using Claude AI.
Brand-aware version that generates reports for specific brands.
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter
from dotenv import load_dotenv
from anthropic import Anthropic

from app.database import SessionLocal
from app.models import Response, Query, Competitor, TargetDescriptor, Report, BrandInfo, User, TaskStatus
from app import crud, schemas

# Load environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

# Initialize Claude client
claude_client = Anthropic(api_key=ANTHROPIC_API_KEY)


# ==================== DATA COLLECTION ====================

def get_brand_analyzed_responses(db, user_id: int, brand_id: int) -> List[Response]:
    """Fetch all responses that have been analyzed for specific brand."""
    return db.query(Response).filter(
        Response.user_id == user_id,
        Response.brand_id == brand_id,
        Response.analyzed_at.isnot(None)
    ).all()


def get_brand_queries(db, user_id: int, brand_id: int) -> List[Query]:
    """Fetch all queries for specific brand."""
    return db.query(Query).filter(
        Query.user_id == user_id,
        Query.brand_id == brand_id
    ).all()


def get_brand_competitors(db, user_id: int, brand_id: int) -> List[Competitor]:
    """Fetch all competitors for specific brand."""
    return db.query(Competitor).filter(
        Competitor.user_id == user_id,
        Competitor.brand_id == brand_id
    ).all()


def get_brand_descriptors(db, user_id: int, brand_id: int) -> List[TargetDescriptor]:
    """Fetch all target descriptors for specific brand."""
    return db.query(TargetDescriptor).filter(
        TargetDescriptor.user_id == user_id,
        TargetDescriptor.brand_id == brand_id
    ).all()


def get_brand_info(db, brand_id: int) -> Optional[BrandInfo]:
    """Fetch brand information."""
    return db.query(BrandInfo).filter(BrandInfo.id == brand_id).first()


# ==================== METRIC CALCULATIONS ====================

def calculate_mention_metrics(responses: List[Response]) -> Dict[str, Any]:
    """Calculate brand mention rate metrics."""
    total = len(responses)
    if total == 0:
        return {"total": 0, "yes": 0, "indirect": 0, "no": 0, "yes_pct": 0, "indirect_pct": 0, "no_pct": 0}

    mentions = Counter([r.brand_mentioned for r in responses])

    return {
        "total": total,
        "yes": mentions.get("Yes", 0),
        "indirect": mentions.get("Indirect", 0),
        "no": mentions.get("No", 0),
        "yes_pct": round((mentions.get("Yes", 0) / total) * 100, 1),
        "indirect_pct": round((mentions.get("Indirect", 0) / total) * 100, 1),
        "no_pct": round((mentions.get("No", 0) / total) * 100, 1),
    }


def calculate_positioning_metrics(responses: List[Response]) -> Dict[str, Any]:
    """Calculate brand positioning metrics."""
    total = len(responses)
    if total == 0:
        return {"total": 0, "leader": 0, "top_3": 0, "featured": 0, "listed": 0, "not_mentioned": 0}

    positions = Counter([r.brand_position for r in responses])

    return {
        "total": total,
        "leader": positions.get("Leader", 0),
        "top_3": positions.get("Top 3", 0),
        "featured": positions.get("Featured", 0),
        "listed": positions.get("Listed", 0),
        "not_mentioned": positions.get("Not Mentioned", 0),
        "leader_pct": round((positions.get("Leader", 0) / total) * 100, 1),
        "top_3_pct": round((positions.get("Top 3", 0) / total) * 100, 1),
        "featured_pct": round((positions.get("Featured", 0) / total) * 100, 1),
        "listed_pct": round((positions.get("Listed", 0) / total) * 100, 1),
        "not_mentioned_pct": round((positions.get("Not Mentioned", 0) / total) * 100, 1),
    }


def calculate_sentiment_metrics(responses: List[Response]) -> Dict[str, Any]:
    """Calculate sentiment distribution."""
    total = len(responses)
    if total == 0:
        return {"total": 0}

    sentiments = Counter([r.sentiment for r in responses])

    return {
        "total": total,
        "very_positive": sentiments.get("Very Positive", 0),
        "positive": sentiments.get("Positive", 0),
        "neutral": sentiments.get("Neutral", 0),
        "negative": sentiments.get("Negative", 0),
        "mixed": sentiments.get("Mixed", 0),
        "very_positive_pct": round((sentiments.get("Very Positive", 0) / total) * 100, 1),
        "positive_pct": round((sentiments.get("Positive", 0) / total) * 100, 1),
        "neutral_pct": round((sentiments.get("Neutral", 0) / total) * 100, 1),
        "negative_pct": round((sentiments.get("Negative", 0) / total) * 100, 1),
        "mixed_pct": round((sentiments.get("Mixed", 0) / total) * 100, 1),
    }


def calculate_platform_metrics(responses: List[Response]) -> Dict[str, Dict[str, Any]]:
    """Calculate metrics broken down by platform."""
    platforms = {}

    for platform in ["ChatGPT", "Claude", "Gemini", "Perplexity"]:
        platform_responses = [r for r in responses if r.platform == platform]

        platforms[platform] = {
            "total": len(platform_responses),
            "mention": calculate_mention_metrics(platform_responses),
            "positioning": calculate_positioning_metrics(platform_responses),
            "sentiment": calculate_sentiment_metrics(platform_responses),
        }

    return platforms


def analyze_descriptors(responses: List[Response]) -> Dict[str, int]:
    """Count occurrences of target descriptors."""
    descriptor_counts = Counter()

    for response in responses:
        if hasattr(response, 'descriptors') and response.descriptors:
            # Descriptors are stored as comma-separated strings
            descriptors = [d.strip() for d in response.descriptors.split(',') if d.strip()]
            for descriptor in descriptors:
                descriptor_counts[descriptor] += 1

    return dict(descriptor_counts)


def analyze_competitors(responses: List[Response]) -> Dict[str, int]:
    """Count occurrences of competitors in responses."""
    competitor_counts = Counter()

    for response in responses:
        if hasattr(response, 'competitors') and response.competitors:
            # Competitors are stored as comma-separated strings
            competitors = [c.strip() for c in response.competitors.split(',') if c.strip()]
            for competitor in competitors:
                competitor_counts[competitor] += 1

    return dict(competitor_counts)


def calculate_positive_sentiment_rate(responses: List[Response]) -> float:
    """Calculate percentage of responses with positive or very positive sentiment."""
    brand_responses = [r for r in responses if r.brand_mentioned in ["Yes", "Indirect"]]
    if not brand_responses:
        return 0.0

    positive_count = sum(1 for r in brand_responses if r.sentiment in ["Positive", "Very Positive"])
    return round((positive_count / len(brand_responses)) * 100, 1)


def calculate_descriptor_match_rate(responses: List[Response], descriptors: List[TargetDescriptor]) -> float:
    """Calculate percentage of responses that mention at least one target descriptor."""
    brand_responses = [r for r in responses if r.brand_mentioned in ["Yes", "Indirect"]]
    if not brand_responses:
        return 0.0

    with_descriptors = sum(1 for r in brand_responses if r.descriptors and r.descriptors.strip())
    return round((with_descriptors / len(brand_responses)) * 100, 1)


def calculate_share_of_voice(responses: List[Response], competitors: List[Competitor], brand_name: str) -> Dict[str, Any]:
    """Calculate share of voice for brand vs competitors."""
    # Count total mentions across all organizations
    total_mentions = 0
    brand_mentions = 0
    competitor_mentions = Counter()

    for response in responses:
        # Count brand mentions
        if response.brand_mentioned == "Yes":
            brand_mentions += 1
            total_mentions += 1

        # Count competitor mentions
        if response.competitors:
            comp_list = [c.strip() for c in response.competitors.split(',') if c.strip()]
            for comp in comp_list:
                competitor_mentions[comp] += 1
                total_mentions += 1

    brand_sov = round((brand_mentions / total_mentions) * 100, 1) if total_mentions > 0 else 0.0

    # Build competitor SOV data
    competitor_sov = {}
    for comp_name, count in competitor_mentions.most_common(5):
        sov = round((count / total_mentions) * 100, 1) if total_mentions > 0 else 0.0
        competitor_sov[comp_name] = {"count": count, "sov": sov}

    return {
        "brand_mentions": brand_mentions,
        "total_mentions": total_mentions,
        "brand_sov": brand_sov,
        "competitor_sov": competitor_sov,
    }


def calculate_positioning_average(responses: List[Response]) -> float:
    """Calculate average positioning score (Leader=5, Top 3=4, Featured=3, Listed=2, Not Mentioned=1)."""
    if not responses:
        return 0.0

    position_scores = {
        "Leader": 5,
        "Top 3": 4,
        "Featured": 3,
        "Listed": 2,
        "Not Mentioned": 1,
    }

    total_score = sum(position_scores.get(r.brand_position, 1) for r in responses)
    return round(total_score / len(responses), 2)


def get_negative_sentiment_statements(responses: List[Response]) -> List[Dict[str, str]]:
    """Extract responses with negative or mixed sentiment about the brand."""
    negative_responses = [
        r for r in responses
        if r.brand_mentioned in ["Yes", "Indirect"]
        and r.sentiment in ["Negative", "Mixed"]
    ]

    return [
        {
            "platform": r.platform,
            "query": r.query_text[:100] + "..." if len(r.query_text) > 100 else r.query_text,
            "sentiment": r.sentiment,
            "excerpt": r.response_text[:200] + "..." if len(r.response_text) > 200 else r.response_text,
        }
        for r in negative_responses[:5]  # Limit to 5 examples
    ]


# ==================== AI-POWERED ANALYSIS ====================

def generate_competitor_threat_analysis(
    competitor_sov: Dict[str, Dict[str, Any]],
    responses: List[Response],
    competitors_list: List[Competitor],
    brand_name: str
) -> str:
    """Use Claude to generate competitor threat analysis."""

    # Prepare competitor data
    competitor_data = []
    for comp_name, data in list(competitor_sov.items())[:5]:
        competitor_data.append({
            "name": comp_name,
            "mentions": data["count"],
            "share_of_voice": data["sov"]
        })

    prompt = f"""You are a strategic analyst for {brand_name}.
Based on the competitor mention data below, identify the THREE most significant competitive threats.

COMPETITOR DATA:
{json.dumps(competitor_data, indent=2)}

For each competitor threat, provide:
1. Competitor name as a heading
2. Specific threat description (2-3 sentences explaining why this competitor is a concern)
3. Recommended action (1-2 actionable sentences)

Format your response as clean markdown with ### headings for each threat.
Be specific, strategic, and actionable in your analysis.
Do NOT use emojis or icons.
Focus on concrete business insights and tactical recommendations."""

    response = claude_client.messages.create(
        model="claude-3-haiku-20240307",  # Fast and cost-effective
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def generate_strategic_priorities(metrics_summary: Dict[str, Any], brand_name: str, brand_info: Optional[BrandInfo]) -> str:
    """Use Claude to generate five strategic priorities."""

    # Add brand context to the prompt
    brand_context = f"{brand_name}"
    if brand_info:
        if brand_info.industry:
            brand_context += f" (in the {brand_info.industry} industry)"
        if brand_info.description:
            brand_context += f"\n\nBrand Description: {brand_info.description}"

    prompt = f"""You are a strategic communications consultant for {brand_context}.
Based on the following AI reputation analysis metrics, generate EXACTLY FIVE strategic priorities.

METRICS:
{json.dumps(metrics_summary, indent=2)}

For each priority, provide:
1. Priority Title (5-8 words, use bold markdown)
2. Description (2-3 sentences explaining the strategic rationale and why this matters)
3. Key Actions (2-3 specific, actionable steps)

Format as markdown with numbered sections (1., 2., 3., etc.).
Focus on actionable strategies to improve {brand_name}'s reputation and visibility in AI platforms.
Do NOT use emojis or icons.
Be thoughtful, strategic, and specific in your recommendations."""

    response = claude_client.messages.create(
        model="claude-3-haiku-20240307",  # Fast and cost-effective
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


def generate_executive_summary(
    metrics_summary: Dict[str, Any],
    brand_name: str,
    brand_info: Optional[BrandInfo],
    total_responses: int
) -> str:
    """Use Claude to generate a 3-5 sentence executive summary."""

    brand_context = f"{brand_name}"
    if brand_info:
        if brand_info.industry:
            brand_context += f" in the {brand_info.industry} industry"

    prompt = f"""You are a strategic communications analyst writing an executive summary for {brand_context}.

Based on the AI reputation analysis metrics below, write a concise executive summary of 3-5 sentences that:
1. Highlights the overall performance of {brand_name} across AI platforms
2. Identifies the most significant finding (positive or concerning)
3. Provides context about what this means for the brand's visibility and reputation

METRICS SUMMARY:
- Total Responses Analyzed: {total_responses}
- Brand Mention Rate: {metrics_summary['mention_metrics']['yes_pct']}% (explicit mentions)
- Positive Sentiment Rate: {metrics_summary['positive_sentiment_rate']}%
- Share of Voice: {metrics_summary['share_of_voice']['brand_sov']}%
- Average Positioning Score: {metrics_summary['positioning_average']} out of 5.0
- Target Descriptor Match Rate: {metrics_summary['descriptor_match_rate']}%

Write in a professional, analytical tone. Focus on strategic insights, not just restating numbers.
Do NOT use emojis or icons.
Do NOT use phrases like "This report" or "This analysis" - write directly about the findings."""

    response = claude_client.messages.create(
        model="claude-3-haiku-20240307",  # Fast and cost-effective
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


# ==================== REPORT GENERATION ====================

def generate_markdown_report(
    mention_metrics: Dict[str, Any],
    positioning_metrics: Dict[str, Any],
    sentiment_metrics: Dict[str, Any],
    platform_metrics: Dict[str, Dict[str, Any]],
    descriptor_analysis: Dict[str, int],
    competitor_analysis: Dict[str, int],
    positive_sentiment_rate: float,
    descriptor_match_rate: float,
    share_of_voice: Dict[str, Any],
    positioning_average: float,
    negative_statements: List[Dict[str, str]],
    competitor_threats: str,
    strategic_priorities: str,
    executive_summary: str,
    brand_name: str,
    brand_info: Optional[BrandInfo],
    report_date: str,
    period: str,
) -> str:
    """Generate a complete markdown report."""

    # Build brand header with context
    brand_header = f"## {brand_name}"
    if brand_info and brand_info.industry:
        brand_header += f" - AI Reputation Analysis Report"
    else:
        brand_header += " - AI Reputation Analysis Report"

    report = f"""# AI Reputation Analysis Report

{brand_header}

**Report Generated:** {report_date}
**Analysis Period:** {period}
**Total Responses Analyzed:** {mention_metrics['total']}

---

## Executive Summary

{executive_summary}

---

## 1. Key Performance Indicators (KPIs)

### a. {brand_name} Mentions as Percentage of AI Responses
**{mention_metrics['yes_pct']}%** of AI responses explicitly mentioned {brand_name}

| Mention Type | Count | Percentage |
|-------------|-------|------------|
| Yes (explicit mention) | {mention_metrics['yes']} | {mention_metrics['yes_pct']}% |
| Indirect (work mentioned, not name) | {mention_metrics['indirect']} | {mention_metrics['indirect_pct']}% |
| Not mentioned | {mention_metrics['no']} | {mention_metrics['no_pct']}% |

### b. Positive Sentiment Rate
**{positive_sentiment_rate}%** of AI responses had positive or very positive sentiment about {brand_name}

### c. Target Descriptor Match Rate
**{descriptor_match_rate}%** of AI responses associated {brand_name} with at least one target descriptor

### d. Share of Voice for {brand_name}
**{share_of_voice['brand_sov']}%** - {brand_name} captured {share_of_voice['brand_sov']}% of all mentions ({share_of_voice['brand_mentions']} out of {share_of_voice['total_mentions']} total organization mentions)

### e. {brand_name} Response Positioning Average
**{positioning_average}** out of 5.0 (Leader=5, Top 3=4, Featured=3, Listed=2, Not Mentioned=1)

---

## 2. Detailed Analysis

### a. Mention Analysis

**Overall Mention Rate:** {mention_metrics['yes_pct']}% explicit, {mention_metrics['indirect_pct']}% indirect

### b. Sentiment Breakdown

| Sentiment | Count | Percentage |
|-----------|-------|------------|
| Very Positive | {sentiment_metrics['very_positive']} | {sentiment_metrics['very_positive_pct']}% |
| Positive | {sentiment_metrics['positive']} | {sentiment_metrics['positive_pct']}% |
| Neutral | {sentiment_metrics['neutral']} | {sentiment_metrics['neutral_pct']}% |
| Negative | {sentiment_metrics['negative']} | {sentiment_metrics['negative_pct']}% |
| Mixed | {sentiment_metrics['mixed']} | {sentiment_metrics['mixed_pct']}% |

### c. Platform-by-Platform Breakdown

"""

    # Add platform analysis
    for platform, metrics in platform_metrics.items():
        if metrics['total'] > 0:
            report += f"""
#### {platform} (n={metrics['total']})
- **Mention Rate:** {metrics['mention']['yes_pct']}% (Yes), {metrics['mention']['indirect_pct']}% (Indirect)
- **Positive Sentiment:** {metrics['sentiment']['positive_pct'] + metrics['sentiment']['very_positive_pct']}%
- **Leader/Top 3 Positioning:** {metrics['positioning']['leader_pct'] + metrics['positioning']['top_3_pct']}%
"""

    report += f"""
### g. {brand_name} Response Positioning Breakdown

| Position | Count | Percentage |
|----------|-------|------------|
| Leader | {positioning_metrics['leader']} | {positioning_metrics['leader_pct']}% |
| Featured | {positioning_metrics['featured']} | {positioning_metrics['featured_pct']}% |
| Top 3 | {positioning_metrics['top_3']} | {positioning_metrics['top_3_pct']}% |
| Listed | {positioning_metrics['listed']} | {positioning_metrics['listed_pct']}% |
| Not Mentioned | {positioning_metrics['not_mentioned']} | {positioning_metrics['not_mentioned_pct']}% |

### d. Descriptor Analysis

How often each descriptor was associated with {brand_name} in AI responses:

"""

    # Add descriptor breakdown
    if descriptor_analysis:
        sorted_descriptors = sorted(descriptor_analysis.items(), key=lambda x: x[1], reverse=True)
        for descriptor, count in sorted_descriptors[:10]:  # Top 10
            report += f"- **{descriptor}:** {count} times\n"
    else:
        report += "*No descriptors tracked in responses*\n"

    report += """
### e. Competitor Mentions

Top competitors mentioned alongside or instead of the brand:

"""

    # Add competitor breakdown
    if competitor_analysis:
        sorted_competitors = sorted(competitor_analysis.items(), key=lambda x: x[1], reverse=True)
        for competitor, count in sorted_competitors[:10]:  # Top 10
            sov_data = share_of_voice['competitor_sov'].get(competitor, {})
            sov = sov_data.get('sov', 0)
            report += f"- **{competitor}:** {count} mentions ({sov}% SOV)\n"
    else:
        report += "*No competitors tracked in responses*\n"

    report += """
---

## 3. Competitive Analysis

### Competitor Threat Assessment

"""
    report += competitor_threats

    report += """

### Negative/Mixed Sentiment Examples

"""

    if negative_statements:
        for i, statement in enumerate(negative_statements, 1):
            report += f"""
**Example {i}** ({statement['platform']} - {statement['sentiment']})
- Query: {statement['query']}
- Excerpt: "{statement['excerpt']}"

"""
    else:
        report += "*No negative or mixed sentiment responses found*\n"

    report += """
---

## 4. Strategic Recommendations

"""
    report += strategic_priorities

    report += """
---

## 5. Methodology

This report analyzes AI platform responses (ChatGPT, Claude, Gemini, Perplexity) to strategic queries.
Each response was analyzed for:
- Brand mention type and positioning
- Sentiment and tone
- Target descriptor usage
- Competitor mentions
- Source citations

All metrics are based on actual AI platform responses collected during the analysis period.

---

*Report generated by TALES (AI Reputation Intelligence & Optimization)*
"""

    return report


# ==================== MAIN FUNCTION ====================

def generate_report_main(user_id: int, brand_id: int):
    """Main function to generate the complete report for a specific brand."""
    print(f"Starting TALES Report Generation for Brand ID {brand_id}...")

    db = SessionLocal()
    task = None  # Initialize to avoid UnboundLocalError

    try:
        # Get the most recent task for this user and brand
        task = db.query(TaskStatus).filter(
            TaskStatus.user_id == user_id,
            TaskStatus.brand_id == brand_id,
            TaskStatus.task_type == "analysis_and_report"
        ).order_by(TaskStatus.started_at.desc()).first()

        # Get brand info
        brand_info = get_brand_info(db, brand_id)
        if not brand_info:
            print(f"Error: Brand ID {brand_id} not found")
            if task:
                task.status = "failed"
                task.error_message = f"Brand ID {brand_id} not found"
                db.commit()
            return

        brand_name = brand_info.brand_name
        print(f"Generating report for: {brand_name}")

        # Update task status: starting report generation
        if task:
            task.message = "Generating report..."
            task.processed_items = task.total_items  # Analysis is complete
            db.commit()

        # Step 1: Collect data
        print("\nCollecting data from database...")
        responses = get_brand_analyzed_responses(db, user_id, brand_id)
        queries = get_brand_queries(db, user_id, brand_id)
        competitors = get_brand_competitors(db, user_id, brand_id)
        descriptors = get_brand_descriptors(db, user_id, brand_id)

        if not responses:
            print("Error: No analyzed responses found for this brand. Please run data collection and analysis first.")
            return

        print(f"Found {len(responses)} analyzed responses")
        print(f"Found {len(queries)} queries")
        print(f"Found {len(competitors)} competitors")
        print(f"Found {len(descriptors)} descriptors")

        # Step 2: Calculate metrics
        print("\nCalculating metrics...")
        mention_metrics = calculate_mention_metrics(responses)
        positioning_metrics = calculate_positioning_metrics(responses)
        sentiment_metrics = calculate_sentiment_metrics(responses)
        platform_metrics = calculate_platform_metrics(responses)
        descriptor_analysis = analyze_descriptors(responses)
        competitor_analysis = analyze_competitors(responses)
        positive_sentiment_rate = calculate_positive_sentiment_rate(responses)
        descriptor_match_rate = calculate_descriptor_match_rate(responses, descriptors)
        share_of_voice = calculate_share_of_voice(responses, competitors, brand_name)
        positioning_average = calculate_positioning_average(responses)
        negative_statements = get_negative_sentiment_statements(responses)

        print("All metrics calculated")

        # Prepare metrics summary for AI generation
        metrics_summary = {
            "brand_name": brand_name,
            "mention_metrics": mention_metrics,
            "positioning_metrics": positioning_metrics,
            "sentiment_metrics": sentiment_metrics,
            "positive_sentiment_rate": positive_sentiment_rate,
            "descriptor_match_rate": descriptor_match_rate,
            "share_of_voice": share_of_voice,
            "positioning_average": positioning_average,
        }

        # Step 3: Generate AI insights
        print("\nGenerating AI-powered insights with Claude...")
        print("  - Executive summary...")
        executive_summary = generate_executive_summary(metrics_summary, brand_name, brand_info, len(responses))

        print("  - Competitor threat analysis...")
        competitor_threats = generate_competitor_threat_analysis(
            share_of_voice['competitor_sov'], responses, competitors, brand_name
        )

        print("  - Strategic recommendations...")
        strategic_priorities = generate_strategic_priorities(metrics_summary, brand_name, brand_info)

        print("AI insights generated")

        # Step 4: Generate report
        print("\nGenerating markdown report...")
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        period = "Last analysis run"  # Could be made dynamic

        markdown_report = generate_markdown_report(
            mention_metrics=mention_metrics,
            positioning_metrics=positioning_metrics,
            sentiment_metrics=sentiment_metrics,
            platform_metrics=platform_metrics,
            descriptor_analysis=descriptor_analysis,
            competitor_analysis=competitor_analysis,
            positive_sentiment_rate=positive_sentiment_rate,
            descriptor_match_rate=descriptor_match_rate,
            share_of_voice=share_of_voice,
            positioning_average=positioning_average,
            negative_statements=negative_statements,
            competitor_threats=competitor_threats,
            strategic_priorities=strategic_priorities,
            executive_summary=executive_summary,
            brand_name=brand_name,
            brand_info=brand_info,
            report_date=report_date,
            period=period,
        )

        # Step 5: Save to database
        print("\nSaving report to database...")

        # Update task status: saving report
        if task:
            task.message = "Saving report to database..."
            db.commit()

        report_title = f"{brand_name} AI Reputation Analysis - {datetime.now().strftime('%Y-%m-%d')}"

        report_obj = Report(
            user_id=user_id,
            brand_id=brand_id,
            title=report_title,
            report_content=markdown_report,
            total_responses=len(responses),
            mention_rate=metrics_summary.get('mention_rate', 0),
        )

        db.add(report_obj)
        db.commit()
        db.refresh(report_obj)

        print(f"Report saved to database (ID: {report_obj.id})")

        # Step 6: Save to file
        filename = f"report_{brand_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w') as f:
            f.write(markdown_report)

        print(f"Report saved to file: {filename}")
        print("\nReport generation complete!")

        # Update task status: completed
        if task:
            task.status = "completed"
            task.completed_at = datetime.now()
            task.message = "Analysis and report generation completed"
            db.commit()

        print(f"\nReport Preview (first 500 chars):")
        print("-" * 60)
        print(markdown_report[:500] + "...")
        print("-" * 60)

    except Exception as e:
        print(f"\nError generating report: {e}")
        import traceback
        traceback.print_exc()

        # Update task status: failed
        if task:
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.now()
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='TALES Report Generation Tool')
    parser.add_argument('--user-id', type=int, required=True, help='User ID to generate report for')
    parser.add_argument('--brand-id', type=int, required=True, help='Brand ID to generate report for')
    args = parser.parse_args()

    generate_report_main(args.user_id, args.brand_id)
