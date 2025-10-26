#!/usr/bin/env python3
"""
AIRO Report Generation Script
Generates professional analysis reports from analyzed response data using Gemini AI.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter
from dotenv import load_dotenv
import google.generativeai as genai

from app.database import SessionLocal
from app.models import Response, Query, Competitor, TargetDescriptor, Report
from app import crud, schemas

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)


# ==================== DATA COLLECTION ====================

def get_all_analyzed_responses(db) -> List[Response]:
    """Fetch all responses that have been analyzed."""
    return db.query(Response).filter(Response.analyzed_at.isnot(None)).all()


def get_all_queries(db) -> List[Query]:
    """Fetch all queries."""
    return db.query(Query).all()


def get_all_competitors(db) -> List[Competitor]:
    """Fetch all competitors."""
    return db.query(Competitor).all()


def get_all_descriptors(db) -> List[TargetDescriptor]:
    """Fetch all target descriptors."""
    return db.query(TargetDescriptor).all()


# ==================== METRIC CALCULATIONS ====================

def calculate_mention_metrics(responses: List[Response]) -> Dict[str, Any]:
    """Calculate PPPL mention rate metrics."""
    total = len(responses)
    if total == 0:
        return {"total": 0, "yes": 0, "indirect": 0, "no": 0, "yes_pct": 0, "indirect_pct": 0, "no_pct": 0}

    mentions = Counter([r.pppl_mentioned for r in responses])

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
    """Calculate PPPL positioning metrics."""
    total = len(responses)
    if total == 0:
        return {"total": 0, "leader": 0, "top_3": 0, "featured": 0, "listed": 0, "not_mentioned": 0}

    positions = Counter([r.pppl_position for r in responses])

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
            # Assuming descriptors are stored as JSON array
            try:
                descriptors = json.loads(response.descriptors) if isinstance(response.descriptors, str) else response.descriptors
                for descriptor in descriptors:
                    descriptor_counts[descriptor] += 1
            except:
                pass

    return dict(descriptor_counts)


def analyze_competitors(responses: List[Response]) -> Dict[str, int]:
    """Count mentions of each competitor."""
    competitor_counts = Counter()

    for response in responses:
        if hasattr(response, 'competitors') and response.competitors:
            # Assuming competitors are stored as JSON array
            try:
                competitors = json.loads(response.competitors) if isinstance(response.competitors, str) else response.competitors
                for competitor in competitors:
                    competitor_counts[competitor] += 1
            except:
                pass

    return dict(competitor_counts)


def calculate_positive_sentiment_rate(responses: List[Response]) -> float:
    """Calculate percentage of responses with positive or very positive sentiment."""
    total = len(responses)
    if total == 0:
        return 0.0

    positive_count = sum(1 for r in responses if r.sentiment in ["Positive", "Very Positive"])
    return round((positive_count / total) * 100, 1)


def calculate_descriptor_match_rate(responses: List[Response], target_descriptors: List[TargetDescriptor]) -> float:
    """Calculate percentage of responses that include at least one target descriptor."""
    total = len(responses)
    if total == 0:
        return 0.0

    target_descriptor_names = {d.descriptor.lower() for d in target_descriptors if d.target_for_pppl}

    responses_with_descriptors = 0
    for response in responses:
        if hasattr(response, 'descriptors') and response.descriptors:
            try:
                descriptors = json.loads(response.descriptors) if isinstance(response.descriptors, str) else response.descriptors
                if any(d.lower() in target_descriptor_names for d in descriptors):
                    responses_with_descriptors += 1
            except:
                pass

    return round((responses_with_descriptors / total) * 100, 1)


def calculate_share_of_voice(responses: List[Response], competitors: List[Competitor]) -> Dict[str, Any]:
    """Calculate share of voice for PPPL vs competitors."""
    # Count total mentions across all organizations
    total_mentions = 0
    pppl_mentions = 0
    competitor_mentions = Counter()

    for response in responses:
        # Count PPPL mentions
        if response.pppl_mentioned == "Yes":
            pppl_mentions += 1
            total_mentions += 1

        # Count competitor mentions
        if hasattr(response, 'competitors') and response.competitors:
            try:
                comp_list = json.loads(response.competitors) if isinstance(response.competitors, str) else response.competitors
                for comp in comp_list:
                    competitor_mentions[comp] += 1
                    total_mentions += 1
            except:
                pass

    if total_mentions == 0:
        return {
            "pppl_sov": 0.0,
            "pppl_mentions": 0,
            "total_mentions": 0,
            "competitor_sov": {}
        }

    pppl_sov = round((pppl_mentions / total_mentions) * 100, 1)

    competitor_sov = {}
    for comp, count in competitor_mentions.items():
        competitor_sov[comp] = {
            "mentions": count,
            "sov": round((count / total_mentions) * 100, 1)
        }

    return {
        "pppl_sov": pppl_sov,
        "pppl_mentions": pppl_mentions,
        "total_mentions": total_mentions,
        "competitor_sov": competitor_sov
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
        "Not Mentioned": 1
    }

    total_score = sum(position_scores.get(r.pppl_position, 0) for r in responses)
    return round(total_score / len(responses), 2)


def get_negative_sentiment_statements(responses: List[Response]) -> List[Dict[str, str]]:
    """Get list of responses with negative sentiment."""
    negative_responses = []

    for response in responses:
        if response.sentiment == "Negative":
            negative_responses.append({
                "platform": response.platform,
                "query": response.query_text,
                "response_text": response.response_text[:500] + "..." if len(response.response_text) > 500 else response.response_text,
                "notes": response.notes if hasattr(response, 'notes') and response.notes else ""
            })

    return negative_responses


# ==================== AI-POWERED GENERATION ====================

def generate_competitor_threat_analysis(
    competitor_sov: Dict[str, Dict[str, Any]],
    responses: List[Response],
    competitors_list: List[Competitor]
) -> str:
    """Use Gemini to generate competitor threat analysis."""

    # Prepare competitor data
    competitor_data = []
    for comp_name, data in competitor_sov.items():
        comp_info = next((c for c in competitors_list if c.organization == comp_name), None)
        competitor_data.append({
            "name": comp_name,
            "mentions": data["mentions"],
            "share_of_voice": data["sov"],
            "type": comp_info.type if comp_info else "Unknown"
        })

    prompt = f"""
You are a strategic analyst for Princeton Plasma Physics Laboratory (PPPL).
Based on the competitor mention data below, identify THREE specific threats:

COMPETITOR DATA:
{json.dumps(competitor_data, indent=2)}

Provide EXACTLY the following three threat assessments:

1. Primary Public Threat: Which national laboratory or university poses the biggest public perception threat and why (1-2 sentences)

2. Primary Private Threat: Which private company poses the biggest competitive threat and why (1-2 sentences)

3. Primary Narrative Threat: Which organization is most successfully owning the fusion narrative in AI responses and why (1-2 sentences)

Be specific, data-driven, and concise. Reference the actual share of voice percentages in your analysis.
"""

    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt)
    return response.text


def generate_strategic_priorities(metrics_summary: Dict[str, Any]) -> str:
    """Use Gemini to generate five strategic priorities."""

    prompt = f"""
You are a strategic communications consultant for Princeton Plasma Physics Laboratory (PPPL).
Based on the following AI reputation analysis metrics, generate EXACTLY FIVE strategic priorities.

METRICS:
{json.dumps(metrics_summary, indent=2)}

For each of the five priorities, provide:
- A clear, action-oriented title
- 2-5 sentences explaining the priority, the data driving it, and the expected impact

Focus on:
- Increasing visibility where mention rates are low
- Improving positioning (moving from "Listed" to "Featured" or "Leader")
- Addressing platform-specific gaps
- Leveraging competitive advantages
- Addressing sentiment issues if present
- Increasing target descriptor usage

Write in a professional, strategic consulting style with specific, actionable priorities.
Format as:

Priority 1: [Title]
[2-5 sentences]

Priority 2: [Title]
[2-5 sentences]

...and so on for all five priorities.
"""

    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt)
    return response.text


# ==================== REPORT COMPILATION ====================

def compile_report(
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
    competitor_threat_analysis: str,
    strategic_priorities: str,
    queries: List[Query],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    """Compile all sections into a complete markdown report."""

    report_date = datetime.now().strftime("%B %d, %Y")

    # Determine analysis period
    if start_date and end_date:
        period = f"{start_date} to {end_date}"
    else:
        period = "Most Recent Collection"

    report = f"""# AIRO: AI Reputation Intelligence & Optimization Report
## Princeton Plasma Physics Laboratory (PPPL)

**Report Generated:** {report_date}
**Analysis Period:** {period}
**Total Responses Analyzed:** {mention_metrics['total']}

---

## 1. Key Metrics Dashboard

### a. PPPL Mentions as Percentage of AI Responses
**{mention_metrics['yes_pct']}%** of AI responses explicitly mentioned PPPL

| Mention Type | Count | Percentage |
|-------------|-------|------------|
| Yes (explicit mention) | {mention_metrics['yes']} | {mention_metrics['yes_pct']}% |
| Indirect (work mentioned, not name) | {mention_metrics['indirect']} | {mention_metrics['indirect_pct']}% |
| Not Mentioned | {mention_metrics['no']} | {mention_metrics['no_pct']}% |

### b. Positive Sentiment Rate
**{positive_sentiment_rate}%** of AI responses had positive or very positive sentiment about PPPL

### c. Target Descriptor Match Rate
**{descriptor_match_rate}%** of AI responses associated PPPL with at least one target descriptor

### d. Share of Voice for PPPL
**{share_of_voice['pppl_sov']}%** - PPPL captured {share_of_voice['pppl_sov']}% of all mentions ({share_of_voice['pppl_mentions']} out of {share_of_voice['total_mentions']} total organization mentions)

### e. PPPL Response Positioning Average
**{positioning_average}** out of 5.0 (Leader=5, Top 3=4, Featured=3, Listed=2, Not Mentioned=1)

---

## 2. Detailed Analysis

### Sentiment Breakdown

| Sentiment | Count | Percentage |
|-----------|-------|------------|
| Very Positive | {sentiment_metrics['very_positive']} | {sentiment_metrics['very_positive_pct']}% |
| Positive | {sentiment_metrics['positive']} | {sentiment_metrics['positive_pct']}% |
| Neutral | {sentiment_metrics['neutral']} | {sentiment_metrics['neutral_pct']}% |
| Negative | {sentiment_metrics['negative']} | {sentiment_metrics['negative_pct']}% |
| Mixed | {sentiment_metrics['mixed']} | {sentiment_metrics['mixed_pct']}% |

### f. Share of Voice - All Competitors

"""

    # Add competitor share of voice
    if share_of_voice['competitor_sov']:
        for comp, data in sorted(share_of_voice['competitor_sov'].items(), key=lambda x: x[1]['sov'], reverse=True):
            report += f"- {comp}: {data['sov']}% ({data['mentions']} mentions)\n"
    else:
        report += "_No competitor mentions found_\n"

    report += f"""

### g. PPPL Response Positioning Breakdown

| Position | Count | Percentage |
|----------|-------|------------|
| Featured | {positioning_metrics['featured']} | {positioning_metrics['featured_pct']}% |
| Top 3 | {positioning_metrics['top_3']} | {positioning_metrics['top_3_pct']}% |
| Included Among Others (Listed) | {positioning_metrics['listed']} | {positioning_metrics['listed_pct']}% |
| Not Mentioned | {positioning_metrics['not_mentioned']} | {positioning_metrics['not_mentioned_pct']}% |

Note: "Leader" positioning ({positioning_metrics['leader']} responses, {positioning_metrics['leader_pct']}%) represents the highest tier

### h. Descriptors Breakdown

How often each descriptor was associated with PPPL in AI responses:

"""

    # Add descriptor breakdown
    if descriptor_analysis:
        for descriptor, count in sorted(descriptor_analysis.items(), key=lambda x: x[1], reverse=True):
            total_responses = mention_metrics['total']
            pct = round((count / total_responses) * 100, 1) if total_responses > 0 else 0
            report += f"- {descriptor}: {count} mentions ({pct}% of responses)\n"
    else:
        report += "_No descriptor data available_\n"

    report += "\n### i. Statements with Negative Sentiment\n\n"

    # Add negative sentiment statements
    if negative_statements:
        for idx, stmt in enumerate(negative_statements, 1):
            report += f"""
#### Negative Statement {idx}
- Platform: {stmt['platform']}
- Query: {stmt['query']}
- Response: {stmt['response_text']}
"""
            if stmt['notes']:
                report += f"- Analysis Notes: {stmt['notes']}\n"
    else:
        report += "_No negative sentiment responses found_\n"

    report += "\n---\n\n## 3. Platform-by-Platform Analysis\n\n"

    # Add platform analysis
    for platform_name in ["ChatGPT", "Claude", "Gemini", "Perplexity"]:
        if platform_name in platform_metrics:
            pm = platform_metrics[platform_name]
            # Calculate platform-specific positioning average from positioning_metrics
            platform_avg = "N/A"
            if pm['positioning'] and pm['total'] > 0:
                position_scores = {"leader": 5, "top_3": 4, "featured": 3, "listed": 2, "not_mentioned": 1}
                total_score = sum(pm['positioning'].get(pos, 0) * score for pos, score in position_scores.items())
                platform_avg = round(total_score / pm['total'], 2)

            positive_sent_rate = round(((pm['sentiment'].get('very_positive', 0) + pm['sentiment'].get('positive', 0)) / pm['total'] * 100) if pm['total'] > 0 else 0, 1)

            report += f"""### {platform_name}

- Total Responses: {pm['total']}
- Mention Rate: {pm['mention']['yes_pct']}% (Yes) + {pm['mention']['indirect_pct']}% (Indirect)
- Positive Sentiment Rate: {positive_sent_rate}%
- Average Position: {platform_avg}

"""

    report += f"""
---

## 4. Competitor Threat Analysis

{competitor_threat_analysis}

---

## 5. Strategic Priorities

{strategic_priorities}

---

## 6. Methodology

### Analysis Period
{period}

### Platforms Analyzed
- ChatGPT (OpenAI GPT-4)
- Claude (Anthropic)
- Gemini (Google)
- Perplexity (AI-Powered Search)

### Query Universe
{len(queries)} strategic queries across multiple categories

### Total Responses Analyzed
{mention_metrics['total']} responses ({len(queries)} queries × 4 platforms)

### Analysis Approach
Automated AI-powered content analysis using Google Gemini 1.5 Pro

---

## 7. Appendix: Query List

"""

    for i, query in enumerate(queries, 1):
        report += f"{i}. {query.query_text}\n"

    report += f"""

---

Report generated automatically by AIRO (AI Reputation Intelligence & Optimization)
Powered by Google Gemini 1.5 Pro
Generation Date: {report_date}
"""

    return report


# ==================== MAIN FUNCTION ====================

def generate_report_main():
    """Main function to generate the complete report."""
    print("🚀 Starting AIRO Report Generation...")

    db = SessionLocal()

    try:
        # Step 1: Collect data
        print("📊 Collecting data from database...")
        responses = get_all_analyzed_responses(db)
        queries = get_all_queries(db)
        competitors = get_all_competitors(db)
        descriptors = get_all_descriptors(db)

        if not responses:
            print("❌ No analyzed responses found. Please run data collection and analysis first.")
            return

        print(f"✓ Found {len(responses)} analyzed responses")
        print(f"✓ Found {len(queries)} queries")

        # Step 2: Calculate metrics
        print("\n📈 Calculating metrics...")
        mention_metrics = calculate_mention_metrics(responses)
        positioning_metrics = calculate_positioning_metrics(responses)
        sentiment_metrics = calculate_sentiment_metrics(responses)
        platform_metrics = calculate_platform_metrics(responses)
        descriptor_analysis = analyze_descriptors(responses)
        competitor_analysis = analyze_competitors(responses)
        positive_sentiment_rate = calculate_positive_sentiment_rate(responses)
        descriptor_match_rate = calculate_descriptor_match_rate(responses, descriptors)
        share_of_voice = calculate_share_of_voice(responses, competitors)
        positioning_average = calculate_positioning_average(responses)
        negative_statements = get_negative_sentiment_statements(responses)

        print("✓ All metrics calculated")

        # Prepare metrics summary for AI generation
        metrics_summary = {
            "mention_metrics": mention_metrics,
            "positioning_metrics": positioning_metrics,
            "sentiment_metrics": sentiment_metrics,
            "platform_metrics": platform_metrics,
            "descriptor_analysis": descriptor_analysis,
            "competitor_analysis": competitor_analysis,
            "positive_sentiment_rate": positive_sentiment_rate,
            "descriptor_match_rate": descriptor_match_rate,
            "share_of_voice": share_of_voice,
            "positioning_average": positioning_average,
        }

        # Step 3: Generate AI content (ONLY for qualitative analysis)
        print("\n🤖 Generating competitor threat analysis with Gemini...")
        competitor_threat_analysis = generate_competitor_threat_analysis(
            share_of_voice['competitor_sov'],
            responses,
            competitors
        )
        print("✓ Competitor threat analysis generated")

        print("\n🤖 Generating strategic priorities with Gemini...")
        strategic_priorities = generate_strategic_priorities(metrics_summary)
        print("✓ Strategic priorities generated")

        # Step 4: Compile report
        print("\n📝 Compiling final report...")
        report = compile_report(
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
            competitor_threat_analysis=competitor_threat_analysis,
            strategic_priorities=strategic_priorities,
            queries=queries,
        )

        # Step 5: Save report to database
        print("\n💾 Saving report to database...")
        report_title = f"AIRO Report - {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"

        report_data = schemas.ReportCreate(
            title=report_title,
            report_content=report,
            total_responses=mention_metrics['total'],
            mention_rate=mention_metrics['yes_pct'],
        )

        db_report = crud.create_report(db, report_data)
        print(f"✓ Report saved to database with ID: {db_report.id}")

        print(f"\n✅ Report generated successfully!")
        print(f"📊 Report ID: {db_report.id}")
        print(f"📄 Title: {report_title}")
        print(f"📈 Total Responses Analyzed: {mention_metrics['total']}")
        print(f"📍 Mention Rate: {mention_metrics['yes_pct']}%")

    except Exception as e:
        print(f"\n❌ Error generating report: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    generate_report_main()
