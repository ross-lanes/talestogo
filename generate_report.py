#!/usr/bin/env python3
"""
TALES Report Generation Script
Generates professional analysis reports from analyzed response data using Perplexity API.
Brand-aware version that generates reports for specific brands.
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter
from dotenv import load_dotenv
from openai import OpenAI

from app.database import SessionLocal
from app.models import Response, Query, Competitor, TargetDescriptor, Report, BrandInfo, User, TaskStatus
from app import crud, schemas
from app.services.chart_generator import generate_all_charts

# Load environment variables
load_dotenv()
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found in environment variables")

# Initialize Perplexity client (OpenAI-compatible)
perplexity_client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)


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


# ==================== CONTEXT BUILDERS FOR ENHANCED PROMPTS ====================

def build_brand_context(brand_info: Optional[BrandInfo], brand_name: str) -> str:
    """Build rich brand context string for prompts."""
    if not brand_info:
        return f"Brand Name: {brand_name}"

    context = f"Brand Name: {brand_name}\n"
    if brand_info.industry:
        context += f"Industry: {brand_info.industry}\n"
    if brand_info.description:
        context += f"Description: {brand_info.description}\n"
    if brand_info.strategic_messages:
        context += f"Strategic Messages: {brand_info.strategic_messages}\n"
    if brand_info.website_url:
        context += f"Website: {brand_info.website_url}\n"

    return context.strip()


def build_competitor_context(competitors: List[Competitor]) -> str:
    """Build detailed competitor context for prompts."""
    if not competitors:
        return "No competitors configured."

    context = ""
    for comp in competitors:
        context += f"\n- {comp.organization}"
        if comp.type:
            context += f" (Type: {comp.type})"
        if comp.focus_area:
            context += f"\n  Focus Area: {comp.focus_area}"
        if comp.key_descriptors:
            context += f"\n  Key Descriptors: {comp.key_descriptors}"
        if comp.notes:
            context += f"\n  Notes: {comp.notes}"
        context += "\n"

    return context.strip()


def build_descriptor_context(descriptors: List[TargetDescriptor], descriptor_analysis: Dict[str, int]) -> str:
    """Build detailed descriptor context showing targets vs actual performance."""
    if not descriptors:
        return "No target descriptors configured."

    context = ""
    for desc in descriptors:
        actual_count = descriptor_analysis.get(desc.descriptor, 0)
        context += f"\n- '{desc.descriptor}'"
        if desc.category:
            context += f" (Category: {desc.category})"
        if desc.priority:
            context += f" [Priority: {desc.priority}]"
        context += f"\n  Times associated with brand: {actual_count}"
        if desc.current_ownership:
            context += f"\n  Current owner: {desc.current_ownership}"
        if desc.notes:
            context += f"\n  Strategic notes: {desc.notes}"
        context += "\n"

    return context.strip()


def get_best_performing_responses(responses: List[Response], limit: int = 5) -> List[Response]:
    """Get responses where brand performed best (Leader position, positive sentiment)."""
    best_responses = [
        r for r in responses
        if r.brand_mentioned == "Yes"
        and r.brand_position in ["Leader", "Top 3"]
        and r.sentiment in ["Positive", "Very Positive"]
    ]

    # Sort by position (Leader first) then by sentiment
    position_rank = {"Leader": 0, "Top 3": 1}
    sentiment_rank = {"Very Positive": 0, "Positive": 1}

    best_responses.sort(
        key=lambda r: (position_rank.get(r.brand_position, 10), sentiment_rank.get(r.sentiment, 10))
    )

    return best_responses[:limit]


def get_worst_performing_responses(responses: List[Response], limit: int = 5) -> List[Response]:
    """Get responses where brand performed worst (not mentioned, competitors mentioned instead)."""
    worst_responses = [
        r for r in responses
        if r.brand_mentioned == "No"
        and r.competitors  # Competitors were mentioned instead
    ]

    return worst_responses[:limit]


def get_competitive_loss_examples(responses: List[Response], limit: int = 5) -> List[Response]:
    """Get examples where brand and competitors both mentioned, but competitors positioned better."""
    competitive_losses = [
        r for r in responses
        if r.brand_mentioned in ["Yes", "Indirect"]
        and r.competitors
        and r.brand_position in ["Listed", "Featured", "Not Mentioned"]  # Not leader
    ]

    return competitive_losses[:limit]


def build_response_examples_context(
    best: List[Response],
    worst: List[Response],
    competitive_losses: List[Response],
    brand_name: str
) -> str:
    """Build formatted response examples for prompts."""
    context = ""

    # Best performing examples
    if best:
        context += "\n=== BEST PERFORMING RESPONSES ===\n"
        for i, resp in enumerate(best[:3], 1):
            context += f"\nExample {i}:\n"
            context += f"Query: \"{resp.query_text}\"\n"
            context += f"Platform: {resp.platform}\n"
            context += f"Position: {resp.brand_position}\n"
            context += f"Sentiment: {resp.sentiment}\n"
            if resp.descriptors:
                context += f"Descriptors: {resp.descriptors}\n"
            # Truncate response text
            excerpt = resp.response_text[:400] + "..." if len(resp.response_text) > 400 else resp.response_text
            context += f"Response excerpt: \"{excerpt}\"\n"

    # Worst performing examples
    if worst:
        context += "\n\n=== WORST PERFORMING RESPONSES (Brand Not Mentioned) ===\n"
        for i, resp in enumerate(worst[:3], 1):
            context += f"\nExample {i}:\n"
            context += f"Query: \"{resp.query_text}\"\n"
            context += f"Platform: {resp.platform}\n"
            context += f"Competitors mentioned instead: {resp.competitors}\n"
            excerpt = resp.response_text[:400] + "..." if len(resp.response_text) > 400 else resp.response_text
            context += f"Response excerpt: \"{excerpt}\"\n"

    # Competitive loss examples
    if competitive_losses:
        context += "\n\n=== COMPETITIVE CHALLENGES (Brand + Competitors Mentioned) ===\n"
        for i, resp in enumerate(competitive_losses[:3], 1):
            context += f"\nExample {i}:\n"
            context += f"Query: \"{resp.query_text}\"\n"
            context += f"Platform: {resp.platform}\n"
            context += f"{brand_name} Position: {resp.brand_position}\n"
            context += f"Competitors also mentioned: {resp.competitors}\n"
            excerpt = resp.response_text[:400] + "..." if len(resp.response_text) > 400 else resp.response_text
            context += f"Response excerpt: \"{excerpt}\"\n"

    return context.strip()


def build_platform_performance_context(platform_metrics: Dict[str, Dict[str, Any]]) -> str:
    """Build platform-by-platform performance summary."""
    context = ""
    for platform, metrics in platform_metrics.items():
        if metrics['total'] > 0:
            context += f"\n{platform} (n={metrics['total']}):\n"
            context += f"  - Mention Rate: {metrics['mention']['yes_pct']}%\n"
            context += f"  - Positive Sentiment: {metrics['sentiment']['positive_pct'] + metrics['sentiment']['very_positive_pct']}%\n"
            context += f"  - Leader/Top 3: {metrics['positioning']['leader_pct'] + metrics['positioning']['top_3_pct']}%\n"

    return context.strip()


# ==================== AI-POWERED ANALYSIS ====================

def generate_competitor_threat_analysis(
    competitor_sov: Dict[str, Dict[str, Any]],
    responses: List[Response],
    competitors_list: List[Competitor],
    brand_name: str,
    brand_context_str: str,
    competitor_context: str,
    worst_responses: List[Response],
    competitive_losses: List[Response]
) -> str:
    """Use Claude to generate enhanced competitor threat analysis with concrete examples."""

    # Prepare SOV data
    sov_summary = f"{brand_name}: {competitor_sov.get('brand_sov', 0)}%\n"
    for comp_name, data in list(competitor_sov.items())[:5]:
        if comp_name != 'brand_sov':
            sov_summary += f"{comp_name}: {data['sov']}% ({data['count']} mentions)\n"

    # Build examples of competitive losses
    competitive_examples = ""
    for i, resp in enumerate(worst_responses[:5], 1):
        competitive_examples += f"\nExample {i} - Brand Absent, Competitors Mentioned:\n"
        competitive_examples += f"Query: \"{resp.query_text}\"\n"
        competitive_examples += f"Platform: {resp.platform}\n"
        competitive_examples += f"Competitors mentioned: {resp.competitors}\n"
        excerpt = resp.response_text[:350] + "..." if len(resp.response_text) > 350 else resp.response_text
        competitive_examples += f"Response: \"{excerpt}\"\n"

    for i, resp in enumerate(competitive_losses[:5], 1):
        competitive_examples += f"\nExample {5+i} - Head-to-Head Loss:\n"
        competitive_examples += f"Query: \"{resp.query_text}\"\n"
        competitive_examples += f"Platform: {resp.platform}\n"
        competitive_examples += f"{brand_name} position: {resp.brand_position}\n"
        competitive_examples += f"Competitors also mentioned: {resp.competitors}\n"
        excerpt = resp.response_text[:350] + "..." if len(resp.response_text) > 350 else resp.response_text
        competitive_examples += f"Response: \"{excerpt}\"\n"

    prompt = f"""You are a competitive intelligence analyst for {brand_name}.

{brand_context_str}

YOUR COMPETITORS (with strategic context):
{competitor_context}

SHARE OF VOICE PERFORMANCE:
{sov_summary}

ACTUAL COMPETITIVE EXAMPLES FROM AI RESPONSES:
{competitive_examples}

Based on this detailed competitive intelligence, identify the THREE most significant competitive threats to {brand_name}.

For each threat, provide:

### [Competitor Name]: [Specific Threat Title]

**Threat Analysis** (3-4 sentences with CONCRETE EXAMPLES from the data above)
- What specific queries are they winning?
- What descriptors or positioning are they owning?
- Quote or reference specific AI responses showing their advantage
- Explain why this matters strategically

**Strategic Implications** (2 sentences on why this threatens {brand_name}'s goals)

**Recommended Actions** (4-5 SPECIFIC, tactical recommendations)
- Each action must reference specific platforms, query types, descriptors, or positioning strategies
- Include measurable targets (e.g., "Increase mentions in X category by Y%")
- Be tactical and immediately actionable

Format your response as clean markdown with ### headings for each threat.
Be ruthlessly specific. Use actual data and examples. No generic advice like "improve visibility" - every recommendation must be tailored to the specific competitive threat shown in the data.
Do NOT use emojis or icons.
Do NOT use multiple pound signs (###) or asterisks (***) as decorative elements or dividers."""

    completion = perplexity_client.chat.completions.create(
        model="sonar-pro",  # Using Perplexity Sonar Pro for competitive analysis
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return completion.choices[0].message.content


def generate_strategic_priorities(
    metrics_summary: Dict[str, Any],
    brand_name: str,
    brand_info: Optional[BrandInfo],
    brand_context_str: str,
    descriptor_context: str,
    competitor_context: str,
    platform_performance: str,
    best_responses: List[Response],
    worst_responses: List[Response]
) -> str:
    """Use Claude to generate enhanced strategic priorities with rich context."""

    # Build strengths and weaknesses from actual responses
    strengths = ""
    for i, resp in enumerate(best_responses[:3], 1):
        strengths += f"\n{i}. Query: \"{resp.query_text}\" ({resp.platform})\n"
        strengths += f"   Position: {resp.brand_position}, Sentiment: {resp.sentiment}\n"
        if resp.descriptors:
            strengths += f"   Descriptors: {resp.descriptors}\n"

    weaknesses = ""
    for i, resp in enumerate(worst_responses[:3], 1):
        weaknesses += f"\n{i}. Query: \"{resp.query_text}\" ({resp.platform})\n"
        weaknesses += f"   Brand mentioned: {resp.brand_mentioned}\n"
        if resp.competitors:
            weaknesses += f"   Competitors mentioned instead: {resp.competitors}\n"

    prompt = f"""You are a strategic communications consultant for a major client.

{brand_context_str}

CURRENT PERFORMANCE METRICS:
- Brand Mention Rate: {metrics_summary['mention_metrics']['yes_pct']}%
- Positive Sentiment: {metrics_summary['positive_sentiment_rate']}%
- Share of Voice: {metrics_summary['share_of_voice']['brand_sov']}%
- Positioning Average: {metrics_summary['positioning_average']}/5.0
- Descriptor Match Rate: {metrics_summary['descriptor_match_rate']}%

PLATFORM-BY-PLATFORM PERFORMANCE:
{platform_performance}

TARGET DESCRIPTORS PERFORMANCE:
{descriptor_context}

COMPETITIVE LANDSCAPE:
{competitor_context}

KEY STRENGTHS (Queries where {brand_name} excels):
{strengths}

KEY WEAKNESSES (Queries where {brand_name} is absent):
{weaknesses}

Based on this comprehensive analysis, generate EXACTLY FIVE strategic priorities for {brand_name}.

For each priority:

**[Priority Number]. [Priority Title]** (6-10 words, specific to {brand_name}'s situation)

**Strategic Rationale** (3-4 sentences explaining WHY this matters based on SPECIFIC DATA from above)
- Reference actual metrics, query examples, competitors, or platform performance
- Connect to the brand's strategic messages and goals
- Explain the opportunity cost of not acting

**Key Actions** (4-5 SPECIFIC, measurable actions)
- Each action must reference specific platforms, query categories, descriptors, or competitors
- Include target metrics (e.g., "Increase association with 'X' descriptor from Y% to Z%")
- Specify what content/narratives to create and where to amplify them
- Be tactical and immediately actionable

Format as numbered markdown sections (1., 2., 3., etc.).
Be data-driven and specific. No generic advice like "improve SEO" or "create more content" - every recommendation must be tailored to {brand_name}'s specific situation shown in the data above.
Do NOT use emojis or icons.
Do NOT use multiple pound signs (###) or asterisks (***) as decorative elements or dividers."""

    completion = perplexity_client.chat.completions.create(
        model="sonar-pro",  # Using Perplexity Sonar Pro for strategic depth
        max_tokens=5000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return completion.choices[0].message.content


def generate_executive_summary(
    metrics_summary: Dict[str, Any],
    brand_name: str,
    brand_info: Optional[BrandInfo],
    total_responses: int,
    brand_context_str: str,
    platform_performance: str,
    response_examples: str,
    descriptor_context: str,
    competitor_context: str
) -> str:
    """Use Claude to generate an enhanced executive summary with rich context."""

    prompt = f"""You are a strategic communications analyst writing an executive summary for a major client.

{brand_context_str}

PERFORMANCE METRICS:
- Total Responses Analyzed: {total_responses}
- Brand Mention Rate: {metrics_summary['mention_metrics']['yes_pct']}% (explicit mentions)
- Positive Sentiment Rate: {metrics_summary['positive_sentiment_rate']}%
- Share of Voice: {metrics_summary['share_of_voice']['brand_sov']}%
- Average Positioning Score: {metrics_summary['positioning_average']} out of 5.0
- Target Descriptor Match Rate: {metrics_summary['descriptor_match_rate']}%

PLATFORM-BY-PLATFORM PERFORMANCE:
{platform_performance}

TARGET DESCRIPTORS PERFORMANCE:
{descriptor_context}

COMPETITIVE LANDSCAPE:
{competitor_context}

{response_examples}

Based on this comprehensive analysis, write a 4-6 sentence executive summary that:
1. Assesses {brand_name}'s overall AI reputation performance with SPECIFIC EVIDENCE from the data
2. Identifies the MOST SIGNIFICANT finding - be specific about which queries/platforms/contexts
3. Compares performance against the brand's stated strategic messages and goals
4. Provides strategic context about competitive positioning with concrete examples
5. Highlights ONE concrete opportunity and ONE concrete risk based on actual response data

Be specific, cite examples from the data above, and focus on actionable insights NOT generic observations.
Write in a professional, analytical tone.
Do NOT use emojis or icons.
Do NOT use phrases like "This report" or "This analysis" - write directly about the findings.
Do NOT use multiple pound signs (###) or asterisks (***) as decorative elements or dividers."""

    completion = perplexity_client.chat.completions.create(
        model="sonar-pro",  # Using Perplexity Sonar Pro for strategic analysis
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return completion.choices[0].message.content


def generate_positioning_insights(
    positioning_metrics: Dict[str, Any],
    positioning_average: float,
    platform_metrics: Dict[str, Dict[str, Any]],
    brand_name: str
) -> str:
    """Generate AI-powered insights about brand positioning."""

    prompt = f"""You are analyzing brand positioning performance for {brand_name} in AI platform responses.

POSITIONING DATA:
- Leader: {positioning_metrics['leader']} responses ({positioning_metrics['leader_pct']}%)
- Top 3: {positioning_metrics['top_3']} responses ({positioning_metrics['top_3_pct']}%)
- Featured: {positioning_metrics['featured']} responses ({positioning_metrics['featured_pct']}%)
- Listed: {positioning_metrics['listed']} responses ({positioning_metrics['listed_pct']}%)
- Not Mentioned: {positioning_metrics['not_mentioned']} responses ({positioning_metrics['not_mentioned_pct']}%)
- Average Positioning Score: {positioning_average} out of 5.0

PLATFORM BREAKDOWN:
{chr(10).join([f"- {platform}: Leader/Top 3 = {metrics['positioning']['leader_pct'] + metrics['positioning']['top_3_pct']}%" for platform, metrics in platform_metrics.items() if metrics['total'] > 0])}

Write 3-10 sentences analyzing {brand_name}'s positioning performance. Focus on:
1. Overall positioning strength (is the brand typically leading, featured, or just listed?)
2. Which positioning tiers are most common and what that means
3. Platform-specific patterns (which platforms position the brand better/worse)
4. The significance of the positioning average score
5. Key opportunities or concerns based on this data

Be specific and data-driven. Write in a professional, analytical tone.
Do NOT use emojis or icons.
Do NOT use multiple pound signs or asterisks as decorative elements."""

    completion = perplexity_client.chat.completions.create(
        model="sonar-pro",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return completion.choices[0].message.content


def generate_share_of_voice_insights(
    share_of_voice: Dict[str, Any],
    brand_name: str,
    competitor_analysis: Dict[str, int]
) -> str:
    """Generate AI-powered insights about share of voice."""

    top_competitors = sorted(competitor_analysis.items(), key=lambda x: x[1], reverse=True)[:5]
    competitor_summary = "\n".join([f"- {comp}: {count} mentions" for comp, count in top_competitors])

    prompt = f"""You are analyzing share of voice performance for {brand_name} in AI platform responses.

SHARE OF VOICE DATA:
- {brand_name} Share of Voice: {share_of_voice['brand_sov']}%
- {brand_name} Mentions: {share_of_voice['brand_mentions']}
- Total Organization Mentions: {share_of_voice['total_mentions']}

TOP COMPETITORS MENTIONED:
{competitor_summary}

Write 3-10 sentences analyzing {brand_name}'s share of voice. Focus on:
1. Is the brand's SOV strong, moderate, or weak compared to the competitive landscape?
2. How does the brand compare to its top competitors?
3. What does this SOV tell us about brand awareness and visibility?
4. Are there concerning gaps where competitors dominate?
5. The strategic implications of this SOV positioning

Be specific and data-driven. Write in a professional, analytical tone.
Do NOT use emojis or icons.
Do NOT use multiple pound signs or asterisks as decorative elements."""

    completion = perplexity_client.chat.completions.create(
        model="sonar-pro",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return completion.choices[0].message.content


def generate_descriptor_insights(
    descriptor_analysis: Dict[str, int],
    descriptor_match_rate: float,
    brand_name: str,
    target_descriptors: List[TargetDescriptor]
) -> str:
    """Generate AI-powered insights about descriptor performance."""

    top_descriptors = sorted(descriptor_analysis.items(), key=lambda x: x[1], reverse=True)[:10]
    descriptor_summary = "\n".join([f"- '{desc}': {count} mentions" for desc, count in top_descriptors])

    target_desc_list = [d.descriptor for d in target_descriptors] if target_descriptors else []
    target_summary = ", ".join([f"'{d}'" for d in target_desc_list[:10]]) if target_desc_list else "None configured"

    prompt = f"""You are analyzing descriptor association performance for {brand_name} in AI platform responses.

DESCRIPTOR PERFORMANCE:
- Overall Match Rate: {descriptor_match_rate}% of brand mentions included at least one target descriptor

TOP DESCRIPTORS ASSOCIATED WITH {brand_name}:
{descriptor_summary}

TARGET DESCRIPTORS (what we want to be associated with):
{target_summary}

Write 3-10 sentences analyzing {brand_name}'s descriptor performance. Focus on:
1. Is the descriptor match rate strong? Are we successfully associated with key terms?
2. Which descriptors are performing well (mentioned frequently)?
3. Are there gaps between target descriptors and actual associations?
4. What does this tell us about how AI platforms characterize the brand?
5. Strategic opportunities to strengthen descriptor associations

Be specific and data-driven. Write in a professional, analytical tone.
Do NOT use emojis or icons.
Do NOT use multiple pound signs or asterisks as decorative elements."""

    completion = perplexity_client.chat.completions.create(
        model="sonar-pro",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return completion.choices[0].message.content


def generate_sentiment_insights(
    sentiment_metrics: Dict[str, Any],
    positive_sentiment_rate: float,
    negative_statements: List[Dict[str, str]],
    brand_name: str,
    platform_metrics: Dict[str, Dict[str, Any]]
) -> str:
    """Generate AI-powered insights about sentiment distribution."""

    prompt = f"""You are analyzing sentiment performance for {brand_name} in AI platform responses.

SENTIMENT DATA:
- Very Positive: {sentiment_metrics['very_positive']} ({sentiment_metrics['very_positive_pct']}%)
- Positive: {sentiment_metrics['positive']} ({sentiment_metrics['positive_pct']}%)
- Neutral: {sentiment_metrics['neutral']} ({sentiment_metrics['neutral_pct']}%)
- Negative: {sentiment_metrics['negative']} ({sentiment_metrics['negative_pct']}%)
- Mixed: {sentiment_metrics['mixed']} ({sentiment_metrics['mixed_pct']}%)
- Combined Positive Rate: {positive_sentiment_rate}%

PLATFORM SENTIMENT BREAKDOWN:
{chr(10).join([f"- {platform}: {metrics['sentiment']['positive_pct'] + metrics['sentiment']['very_positive_pct']}% positive" for platform, metrics in platform_metrics.items() if metrics['total'] > 0])}

NUMBER OF NEGATIVE/MIXED EXAMPLES: {len(negative_statements)}

Write 3-10 sentences analyzing {brand_name}'s sentiment performance. Focus on:
1. Overall sentiment health - is it predominantly positive, neutral, or concerning?
2. The balance between very positive, positive, and neutral responses
3. Any negative or mixed sentiment patterns that need attention
4. Platform-specific sentiment differences
5. What this sentiment profile reveals about brand perception

Be specific and data-driven. Write in a professional, analytical tone.
Do NOT use emojis or icons.
Do NOT use multiple pound signs or asterisks as decorative elements."""

    completion = perplexity_client.chat.completions.create(
        model="sonar-pro",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return completion.choices[0].message.content


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
    responses: List[Any] = None,
    chart_paths: Dict[str, str] = None,
    positioning_insights: str = "",
    sov_insights: str = "",
    descriptor_insights: str = "",
    sentiment_insights: str = "",
) -> str:
    """Generate a complete markdown report with embedded charts and insights."""

    # Build brand header with context
    brand_header = f"## {brand_name}"
    if brand_info and brand_info.industry:
        brand_header += f" - AI Reputation Analysis Report"
    else:
        brand_header += " - AI Reputation Analysis Report"

    report = f"""## Executive Summary

{executive_summary}

"""

    # Add Dashboard chart after Executive Summary
    if chart_paths and 'dashboard' in chart_paths:
        report += f"\n![Key Metrics Dashboard]({chart_paths['dashboard']})\n\n"

    report += f"""
---

## Detailed Analysis with Insights

### 1. Positioning Analysis

| Position | Count | Percentage |
|----------|-------|------------|
| Leader | {positioning_metrics['leader']} | {positioning_metrics['leader_pct']}% |
| Top 3 | {positioning_metrics['top_3']} | {positioning_metrics['top_3_pct']}% |
| Featured | {positioning_metrics['featured']} | {positioning_metrics['featured_pct']}% |
| Listed | {positioning_metrics['listed']} | {positioning_metrics['listed_pct']}% |
| Not Mentioned | {positioning_metrics['not_mentioned']} | {positioning_metrics['not_mentioned_pct']}% |

**Average Positioning Score:** {positioning_average} out of 5.0
"""

    # Add positioning chart
    if chart_paths and 'positioning' in chart_paths:
        report += f"\n![Positioning Distribution]({chart_paths['positioning']})\n"

    # Add positioning insights
    report += f"\n**Insights:**\n\n{positioning_insights}\n"

    report += f"""
---

### 2. Share of Voice Analysis

**{brand_name} Share of Voice:** {share_of_voice['brand_sov']}%
**{brand_name} Mentions:** {share_of_voice['brand_mentions']} out of {share_of_voice['total_mentions']} total organization mentions

**Share of Voice Distribution:**

| Organization | Mentions | Share of Voice % |
|-------------|----------|------------------|"""

    # Add competitor breakdown in table format
    if competitor_analysis:
        sorted_competitors = sorted(competitor_analysis.items(), key=lambda x: x[1], reverse=True)
        for competitor, count in sorted_competitors[:10]:  # Top 10
            sov_data = share_of_voice['competitor_sov'].get(competitor, {})
            sov = sov_data.get('sov', 0)
            report += f"\n| {competitor} | {count} | {sov}% |"
    else:
        report += "\n| No data | - | - |"

    # Add share of voice chart
    if chart_paths and 'share_of_voice' in chart_paths:
        report += f"\n\n![Share of Voice]({chart_paths['share_of_voice']})\n"

    # Add SOV insights
    report += f"\n**Insights:**\n\n{sov_insights}\n"

    report += f"""
---

### 3. Descriptor Analysis

**Descriptor Match Rate:** {descriptor_match_rate}% of brand mentions included at least one target descriptor

**Top Descriptors Associated with {brand_name}:**

| Descriptor | Mentions |
|-----------|----------|"""

    # Add descriptor breakdown in table format
    if descriptor_analysis:
        sorted_descriptors = sorted(descriptor_analysis.items(), key=lambda x: x[1], reverse=True)
        for descriptor, count in sorted_descriptors[:10]:  # Top 10
            report += f"\n| {descriptor} | {count} |"
    else:
        report += "\n| No data | - |"

    # Add descriptor performance chart
    if chart_paths and 'descriptor_performance' in chart_paths:
        report += f"\n\n![Descriptor Performance]({chart_paths['descriptor_performance']})\n"

    # Add descriptor insights
    report += f"\n**Insights:**\n\n{descriptor_insights}\n"

    report += f"""
---

### 4. Sentiment Analysis

| Sentiment | Count | Percentage |
|-----------|-------|------------|
| Very Positive | {sentiment_metrics['very_positive']} | {sentiment_metrics['very_positive_pct']}% |
| Positive | {sentiment_metrics['positive']} | {sentiment_metrics['positive_pct']}% |
| Neutral | {sentiment_metrics['neutral']} | {sentiment_metrics['neutral_pct']}% |
| Negative | {sentiment_metrics['negative']} | {sentiment_metrics['negative_pct']}% |
| Mixed | {sentiment_metrics['mixed']} | {sentiment_metrics['mixed_pct']}% |

**Combined Positive Rate:** {positive_sentiment_rate}%
"""

    # Add sentiment chart
    if chart_paths and 'sentiment' in chart_paths:
        report += f"\n![Sentiment Distribution]({chart_paths['sentiment']})\n"

    # Add sentiment insights
    report += f"\n**Insights:**\n\n{sentiment_insights}\n"

    # Add all AI statements sorted by sentiment
    if responses:
        report += "\n\n**AI Statements About the Brand (Sorted by Sentiment)**\n\n"

        # Group responses by sentiment
        sentiment_order = ['Very Positive', 'Positive', 'Neutral', 'Mixed', 'Negative', 'Very Negative']
        statements_by_sentiment = {s: [] for s in sentiment_order}

        for response in responses:
            # Only include responses where brand was mentioned
            if response.brand_mentioned in ['Yes', 'Indirect'] and response.response_text:
                sentiment = response.sentiment if response.sentiment else 'Neutral'
                if sentiment in statements_by_sentiment:
                    statements_by_sentiment[sentiment].append({
                        'platform': response.platform,
                        'query': response.query_text,
                        'text': response.response_text,
                        'positioning': response.positioning if response.positioning else 'Not specified'
                    })

        # Display statements grouped by sentiment
        for sentiment in sentiment_order:
            statements = statements_by_sentiment[sentiment]
            if statements:
                report += f"\n#### {sentiment} ({len(statements)} statements)\n\n"
                for i, statement in enumerate(statements, 1):
                    # Truncate long responses to first 500 characters
                    text_excerpt = statement['text'][:500] + "..." if len(statement['text']) > 500 else statement['text']
                    report += f"**Statement {i}** - {statement['platform']} - Positioning: {statement['positioning']}\n"
                    report += f"- **Query:** {statement['query']}\n"
                    report += f"- **Response:** {text_excerpt}\n\n"

    report += """
---

### 5. Threat Analysis
"""
    report += competitor_threats

    report += """

---

### 6. Recommendations
"""
    report += strategic_priorities

    report += """

---

## Methodology

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

        # Step 3: Build rich context for enhanced prompts
        print("\nBuilding enhanced context for AI analysis...")

        brand_context_str = build_brand_context(brand_info, brand_name)
        competitor_context = build_competitor_context(competitors)
        descriptor_context = build_descriptor_context(descriptors, descriptor_analysis)
        platform_performance = build_platform_performance_context(platform_metrics)

        best_responses = get_best_performing_responses(responses)
        worst_responses = get_worst_performing_responses(responses)
        competitive_losses = get_competitive_loss_examples(responses)

        response_examples = build_response_examples_context(
            best_responses, worst_responses, competitive_losses, brand_name
        )

        print("Context building complete")

        # Step 4: Generate AI insights with enhanced prompts
        print("\nGenerating AI-powered insights with Claude Sonnet 3.5...")
        print("  - Executive summary...")
        executive_summary = generate_executive_summary(
            metrics_summary=metrics_summary,
            brand_name=brand_name,
            brand_info=brand_info,
            total_responses=len(responses),
            brand_context_str=brand_context_str,
            platform_performance=platform_performance,
            response_examples=response_examples,
            descriptor_context=descriptor_context,
            competitor_context=competitor_context
        )

        print("  - Competitor threat analysis...")
        competitor_threats = generate_competitor_threat_analysis(
            competitor_sov=share_of_voice['competitor_sov'],
            responses=responses,
            competitors_list=competitors,
            brand_name=brand_name,
            brand_context_str=brand_context_str,
            competitor_context=competitor_context,
            worst_responses=worst_responses,
            competitive_losses=competitive_losses
        )

        print("  - Strategic recommendations...")
        strategic_priorities = generate_strategic_priorities(
            metrics_summary=metrics_summary,
            brand_name=brand_name,
            brand_info=brand_info,
            brand_context_str=brand_context_str,
            descriptor_context=descriptor_context,
            competitor_context=competitor_context,
            platform_performance=platform_performance,
            best_responses=best_responses,
            worst_responses=worst_responses
        )

        print("AI insights generated")

        # Step 4b: Generate section-specific insights
        print("\nGenerating section insights...")
        print("  - Positioning insights...")
        positioning_insights = generate_positioning_insights(
            positioning_metrics=positioning_metrics,
            positioning_average=positioning_average,
            platform_metrics=platform_metrics,
            brand_name=brand_name
        )

        print("  - Share of voice insights...")
        sov_insights = generate_share_of_voice_insights(
            share_of_voice=share_of_voice,
            brand_name=brand_name,
            competitor_analysis=competitor_analysis
        )

        print("  - Descriptor insights...")
        descriptor_insights = generate_descriptor_insights(
            descriptor_analysis=descriptor_analysis,
            descriptor_match_rate=descriptor_match_rate,
            brand_name=brand_name,
            target_descriptors=descriptors
        )

        print("  - Sentiment insights...")
        sentiment_insights = generate_sentiment_insights(
            sentiment_metrics=sentiment_metrics,
            positive_sentiment_rate=positive_sentiment_rate,
            negative_statements=negative_statements,
            brand_name=brand_name,
            platform_metrics=platform_metrics
        )

        print("Section insights generated")

        # Step 5: Generate charts
        print("\nGenerating visualization charts...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        chart_paths = generate_all_charts(
            mention_metrics=mention_metrics,
            positioning_metrics=positioning_metrics,
            sentiment_metrics=sentiment_metrics,
            platform_metrics=platform_metrics,
            share_of_voice=share_of_voice,
            descriptor_analysis=descriptor_analysis,
            brand_name=brand_name,
            timestamp=timestamp,
            user_id=user_id,
            brand_id=brand_id
        )
        print(f"Total charts available: {len(chart_paths)}")

        # Step 6: Generate report
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
            responses=responses,
            chart_paths=chart_paths,
            positioning_insights=positioning_insights,
            sov_insights=sov_insights,
            descriptor_insights=descriptor_insights,
            sentiment_insights=sentiment_insights,
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
