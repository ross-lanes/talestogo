#!/usr/bin/env python3
"""
TALES Report Generation Script
Generates professional analysis reports from analyzed response data using Gemini 2.5 Pro.
Brand-aware version that generates reports for specific brands.
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter
from dotenv import load_dotenv
import google.generativeai as genai

from app.database import SessionLocal
from app.models import Response, Query, Competitor, TargetDescriptor, Report, BrandInfo, User, TaskStatus
from app import crud, schemas
from app.services.chart_generator import generate_all_charts
from app.services.metrics import (
    calculate_mention_metrics,
    calculate_positioning_metrics,
    calculate_positioning_average,
    calculate_sentiment_metrics,
    calculate_positive_sentiment_rate,
    calculate_platform_metrics,
    analyze_descriptors,
    analyze_competitors,
    calculate_descriptor_match_rate,
    calculate_share_of_voice,
    calculate_competitor_threats,
    get_negative_sentiment_statements,
    normalize_organization_name,
)
from app.services.cached_metrics import (
    get_brand_mentions_trend_cached,
    get_positioning_trend_cached,
    get_sentiment_trend_cached,
    get_share_of_voice_trend_cached,
)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


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


# ==================== LLM BREAKDOWN DATA COLLECTION ====================

def get_llm_breakdown_data(db, user_id: int, brand_id: int, brand_name: str) -> Dict[str, Any]:
    """
    Collect all LLM-specific breakdown data for the report.
    This mirrors the analytics endpoints used in the UI.
    """
    from sqlalchemy import func, case

    llm_data = {
        'brand_mentions': [],
        'positioning': [],
        'sentiment': [],
        'share_of_voice': [],
        'descriptors': [],
        'threats': []
    }

    # 1. Brand Mentions by LLM
    platform_stats = db.query(
        Response.platform,
        func.count(Response.id).label('total'),
        func.sum(
            case(
                (Response.brand_mentioned == 'Yes', 1),
                else_=0
            )
        ).label('mentioned')
    ).filter(
        Response.user_id == user_id,
        Response.brand_id == brand_id,
        Response.platform.isnot(None)
    ).group_by(
        Response.platform
    ).all()

    for platform, total, mentioned in platform_stats:
        mention_rate = (mentioned / total * 100) if total > 0 else 0
        llm_data['brand_mentions'].append({
            'platform': platform,
            'total_responses': total,
            'mentions': mentioned,
            'mention_rate': round(mention_rate, 1)
        })

    # 2. Positioning by LLM
    platform_positioning = db.query(
        Response.platform,
        Response.brand_position,
        func.count(Response.id).label('count')
    ).filter(
        Response.user_id == user_id,
        Response.brand_id == brand_id,
        Response.platform.isnot(None),
        Response.brand_position.isnot(None)
    ).group_by(
        Response.platform,
        Response.brand_position
    ).all()

    platforms_positioning = {}
    for platform, position, count in platform_positioning:
        if platform not in platforms_positioning:
            platforms_positioning[platform] = {
                'platform': platform,
                'Leader': 0,
                'Featured': 0,
                'Listed': 0,
                'Not Mentioned': 0,
                'total': 0
            }
        if position in ['Leader', 'Featured', 'Listed', 'Not Mentioned']:
            platforms_positioning[platform][position] = count
            platforms_positioning[platform]['total'] += count

    llm_data['positioning'] = list(platforms_positioning.values())

    # 3. Sentiment by LLM
    platform_sentiment = db.query(
        Response.platform,
        Response.sentiment,
        func.count(Response.id).label('count')
    ).filter(
        Response.user_id == user_id,
        Response.brand_id == brand_id,
        Response.platform.isnot(None),
        Response.sentiment.isnot(None),
        Response.brand_mentioned == 'Yes'
    ).group_by(
        Response.platform,
        Response.sentiment
    ).all()

    platforms_sentiment = {}
    for platform, sentiment, count in platform_sentiment:
        if platform not in platforms_sentiment:
            platforms_sentiment[platform] = {
                'platform': platform,
                'Very Positive': 0,
                'Positive': 0,
                'Neutral': 0,
                'Negative': 0,
                'Very Negative': 0,
                'Mixed': 0,
                'total': 0
            }
        if sentiment in ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative', 'Mixed']:
            platforms_sentiment[platform][sentiment] = count
            platforms_sentiment[platform]['total'] += count

    llm_data['sentiment'] = list(platforms_sentiment.values())

    # 4. Share of Voice by LLM
    brand_mentions = db.query(
        Response.platform,
        func.count(Response.id).label('brand_mentions')
    ).filter(
        Response.user_id == user_id,
        Response.brand_id == brand_id,
        Response.platform.isnot(None),
        Response.brand_mentioned == 'Yes'
    ).group_by(
        Response.platform
    ).all()

    competitor_mentions = db.query(
        Response.platform,
        func.count(Response.id).label('competitor_mentions')
    ).filter(
        Response.user_id == user_id,
        Response.brand_id == brand_id,
        Response.platform.isnot(None),
        Response.competitors.isnot(None),
        Response.competitors != ''
    ).group_by(
        Response.platform
    ).all()

    platforms_sov = {}
    for platform, count in brand_mentions:
        if platform not in platforms_sov:
            platforms_sov[platform] = {'platform': platform, 'brand': 0, 'competitors': 0}
        platforms_sov[platform]['brand'] = count

    for platform, count in competitor_mentions:
        if platform not in platforms_sov:
            platforms_sov[platform] = {'platform': platform, 'brand': 0, 'competitors': 0}
        platforms_sov[platform]['competitors'] = count

    llm_data['share_of_voice'] = list(platforms_sov.values())

    # 5. Descriptors by LLM
    responses_descriptors = db.query(
        Response.platform,
        Response.descriptors
    ).filter(
        Response.user_id == user_id,
        Response.brand_id == brand_id,
        Response.platform.isnot(None),
        Response.descriptors.isnot(None),
        Response.descriptors != ''
    ).all()

    platform_descriptors = {}
    for platform, descriptors_str in responses_descriptors:
        if platform not in platform_descriptors:
            platform_descriptors[platform] = {}
        if descriptors_str:
            descriptors = [d.strip() for d in descriptors_str.split(',') if d.strip()]
            for descriptor in descriptors:
                if descriptor not in platform_descriptors[platform]:
                    platform_descriptors[platform][descriptor] = 0
                platform_descriptors[platform][descriptor] += 1

    for platform, descriptors in platform_descriptors.items():
        top_descriptors = sorted(descriptors.items(), key=lambda x: x[1], reverse=True)[:5]
        llm_data['descriptors'].append({
            'platform': platform,
            'descriptors': [{'descriptor': d, 'count': c} for d, c in top_descriptors],
            'total_mentions': sum(descriptors.values())
        })

    # 6. Competitor Threats by LLM
    responses_threats = db.query(
        Response.platform,
        Response.competitors,
        Response.sentiment
    ).filter(
        Response.user_id == user_id,
        Response.brand_id == brand_id,
        Response.platform.isnot(None),
        Response.competitors.isnot(None),
        Response.competitors != ''
    ).all()

    platform_competitors = {}
    for platform, competitors_str, sentiment in responses_threats:
        if platform not in platform_competitors:
            platform_competitors[platform] = {}
        if competitors_str:
            competitors = [c.strip() for c in competitors_str.split(',') if c.strip()]
            for competitor in competitors:
                if competitor not in platform_competitors[platform]:
                    platform_competitors[platform][competitor] = {'count': 0, 'negative_overlap': 0}
                platform_competitors[platform][competitor]['count'] += 1
                if sentiment in ['Negative', 'Very Negative']:
                    platform_competitors[platform][competitor]['negative_overlap'] += 1

    for platform, competitors in platform_competitors.items():
        top_competitors = sorted(
            competitors.items(),
            key=lambda x: (x[1]['count'], x[1]['negative_overlap']),
            reverse=True
        )[:5]
        llm_data['threats'].append({
            'platform': platform,
            'competitors': [
                {'name': name, 'mentions': data['count'], 'negative_overlap': data['negative_overlap']}
                for name, data in top_competitors
            ],
            'total_competitor_mentions': sum(c['count'] for c in competitors.values())
        })

    return llm_data


# ==================== METRIC CALCULATIONS ====================
# All metric calculation functions have been moved to app/services/metrics.py
# for single source of truth across dashboard, analytics pages, and reports.
# Import functions from metrics module (see imports at top of file).


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
            context += f"  - Leader/Featured: {metrics['positioning']['leader_pct'] + metrics['positioning']['featured_pct']}%\n"

    return context.strip()


# ==================== AI-POWERED ANALYSIS ====================

def generate_competitor_threat_analysis(
    top_threats: List[Dict[str, Any]],
    competitor_sov: Dict[str, Dict[str, Any]],
    responses: List[Response],
    competitors_list: List[Competitor],
    brand_name: str,
    brand_context_str: str,
    competitor_context: str,
    worst_responses: List[Response],
    competitive_losses: List[Response]
) -> str:
    """
    Use Gemini to generate enhanced competitor threat analysis.
    Focuses on the top 3 threats as calculated by calculate_competitor_threats().
    """

    # Prepare SOV data for top 3 threats
    sov_summary = f"{brand_name}: {competitor_sov.get('brand_sov', 0)}%\n"
    for threat in top_threats[:3]:
        sov_summary += f"{threat['name']}: {threat['share_of_voice']}% ({threat['mention_count']} mentions, Threat Score: {threat['threat_score']} - {threat['threat_level']})\n"

    # Build examples of competitive losses - filter to focus on top 3 threats
    top_threat_names = [threat['name'].lower() for threat in top_threats[:3]]

    # Filter worst_responses to only include top 3 threats
    relevant_worst = [
        r for r in worst_responses
        if r.competitors and any(threat_name in r.competitors.lower() for threat_name in top_threat_names)
    ][:5]

    # Filter competitive_losses to only include top 3 threats
    relevant_losses = [
        r for r in competitive_losses
        if r.competitors and any(threat_name in r.competitors.lower() for threat_name in top_threat_names)
    ][:5]

    competitive_examples = ""
    for i, resp in enumerate(relevant_worst, 1):
        competitive_examples += f"\nExample {i} - Brand Absent, Competitors Mentioned:\n"
        competitive_examples += f"Query: \"{resp.query_text}\"\n"
        competitive_examples += f"Platform: {resp.platform}\n"
        competitive_examples += f"Competitors mentioned: {resp.competitors}\n"
        excerpt = resp.response_text[:350] + "..." if len(resp.response_text) > 350 else resp.response_text
        competitive_examples += f"Response: \"{excerpt}\"\n"

    offset = len(relevant_worst)
    for i, resp in enumerate(relevant_losses, 1):
        competitive_examples += f"\nExample {offset+i} - Head-to-Head Loss:\n"
        competitive_examples += f"Query: \"{resp.query_text}\"\n"
        competitive_examples += f"Platform: {resp.platform}\n"
        competitive_examples += f"{brand_name} position: {resp.brand_position}\n"
        competitive_examples += f"Competitors also mentioned: {resp.competitors}\n"
        excerpt = resp.response_text[:350] + "..." if len(resp.response_text) > 350 else resp.response_text
        competitive_examples += f"Response: \"{excerpt}\"\n"

    # Get names of top 3 threats for the prompt
    top_3_names = [threat['name'] for threat in top_threats[:3]]

    prompt = f"""You are a competitive intelligence analyst for {brand_name}.

{brand_context_str}

YOUR COMPETITORS (with strategic context):
{competitor_context}

TOP 3 COMPETITIVE THREATS (based on quantitative threat analysis):
The following competitors have been identified as the top 3 threats based on their mention frequency, share of voice, and sentiment patterns:

1. {top_3_names[0] if len(top_3_names) > 0 else 'N/A'}
2. {top_3_names[1] if len(top_3_names) > 1 else 'N/A'}
3. {top_3_names[2] if len(top_3_names) > 2 else 'N/A'}

SHARE OF VOICE PERFORMANCE:
{sov_summary}

ACTUAL COMPETITIVE EXAMPLES FROM AI RESPONSES:
{competitive_examples}

Based on this detailed competitive intelligence, analyze each of the THREE identified competitive threats to {brand_name} listed above.

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

    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)

    return response.text


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
    """Use Gemini to generate enhanced strategic priorities with rich context."""

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

    # Fetch recent industry news using Gemini
    industry = brand_info.industry if brand_info and brand_info.industry else "the industry"
    news_query = f"Recent news and developments in {industry} in the last 30 days, particularly related to {brand_name} or its competitors"

    try:
        news_model = genai.GenerativeModel('gemini-2.5-pro')
        news_response = news_model.generate_content(news_query)
        recent_news = news_response.text
    except Exception as e:
        print(f"Warning: Could not fetch recent news: {e}")
        recent_news = "No recent news data available."

    prompt = f"""You are a strategic communications consultant analyzing AI-generated responses about a brand.

CRITICAL CONTEXT: This analysis examines how Large Language Models (LLMs like ChatGPT, Claude, Perplexity, Gemini) describe {brand_name} when users ask questions. Brands CANNOT directly publish content to LLMs. Instead, LLMs generate responses based on the authoritative sources they reference.

IMPORTANT: Different LLMs prioritize different source types. Your recommendations must be data-driven and strategic:
- Analyze the PLATFORM-BY-PLATFORM PERFORMANCE data below to identify which LLMs perform well vs. poorly for {brand_name}
- Look at the actual response examples to understand what sources those LLMs are likely citing
- Consider that different LLMs may favor different sources:
  * Academic/research-focused LLMs may prioritize peer-reviewed papers, .edu domains, research institutions
  * Search-augmented LLMs (like Perplexity) may prioritize recent news articles, authoritative websites, Reddit discussions
  * Some may favor Wikipedia, government sources (.gov), or technical documentation
- If {brand_name} performs poorly on a specific platform, diagnose WHY by examining the queries and recommend targeted strategies for the SOURCE TYPES that platform likely values

Your recommendations should be specific about:
1. WHAT content to create (research papers vs. blog posts vs. technical docs vs. media outreach)
2. WHERE to publish it (academic journals, tech blogs, Reddit, news outlets, .gov partnerships, etc.)
3. WHY that approach targets the specific LLMs where {brand_name} underperforms

DO NOT give generic advice like "improve online presence" - every recommendation must be tied to specific patterns in the data

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

RECENT INDUSTRY NEWS & DEVELOPMENTS (Last 30 Days):
{recent_news}

Based on this comprehensive analysis, generate EXACTLY FIVE strategic priorities for {brand_name}.

IMPORTANT: Consider how recent industry news creates opportunities or threats:
- If there's a major development, breakthrough, or trend in the industry, recommend how {brand_name} can position itself in relation to it
- If competitors made news, identify opportunities to counter-program or claim related positioning
- If there are emerging topics or conversations, recommend getting ahead of them with authoritative content
- Consider whether recent events change the urgency or approach for any communications goals

CRITICAL: Your priorities must focus on achieving {brand_name}'s strategic messaging goals:
- Identify TARGET DESCRIPTORS that are underperforming (low match rate, absent from responses, or competitors own them)
- Recommend specific content strategies to associate {brand_name} with those missing descriptors
- If a descriptor appears frequently for competitors but not {brand_name}, explain how to claim that positioning
- Address platform-specific weaknesses with targeted source strategies for those LLMs
- Connect every recommendation back to increasing the presence of specific target descriptors in AI responses

For each priority:

**[Priority Number]. [Priority Title]** (6-10 words, specific to {brand_name}'s situation)

**Strategic Rationale** (3-4 sentences explaining WHY this matters based on SPECIFIC DATA from above)
- Reference actual metrics, query examples, competitors, or platform performance
- MUST identify which target descriptor(s) this addresses and current vs. desired state
- Connect to the brand's strategic messages and positioning goals
- Explain the opportunity cost of not acting

**Key Actions** (4-5 SPECIFIC, measurable actions)
- Each action must specify which target descriptor(s) to emphasize
- Include target metrics (e.g., "Increase 'innovative' descriptor association from 12% to 35% by creating...")
- Specify WHAT content to create, WHERE to publish it, and HOW it reinforces target descriptors
- Reference specific platforms, query categories, competitors, or source types that LLMs prioritize
- Be tactical and immediately actionable

Format as numbered markdown sections (1., 2., 3., etc.).
Be data-driven and specific. No generic advice like "improve SEO" or "create more content" - every recommendation must be tailored to {brand_name}'s specific situation shown in the data above.
Do NOT use emojis or icons.
Do NOT use multiple pound signs (###) or asterisks (***) as decorative elements or dividers.

IMPORTANT - Citations: DO NOT include any citations, references, or external sources. Base all analysis solely on the data provided above. Do NOT add a "References" section at the end."""

    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)

    return response.text


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
    """Use Gemini to generate an enhanced executive summary with rich context."""

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

    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)

    return response.text


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
- Featured: {positioning_metrics['featured']} responses ({positioning_metrics['featured_pct']}%)
- Listed: {positioning_metrics['listed']} responses ({positioning_metrics['listed_pct']}%)
- Not Mentioned: {positioning_metrics['not_mentioned']} responses ({positioning_metrics['not_mentioned_pct']}%)
- Average Positioning Score: {positioning_average} out of 5.0

PLATFORM BREAKDOWN:
{chr(10).join([f"- {platform}: Leader/Featured = {metrics['positioning']['leader_pct'] + metrics['positioning']['featured_pct']}%" for platform, metrics in platform_metrics.items() if metrics['total'] > 0])}

Write 3-10 sentences analyzing {brand_name}'s positioning performance. Focus on:
1. Overall positioning strength (is the brand typically leading, featured, or just listed?)
2. Which positioning tiers are most common and what that means
3. Platform-specific patterns (which platforms position the brand better/worse)
4. The significance of the positioning average score
5. Key opportunities or concerns based on this data

Be specific and data-driven. Write in a professional, analytical tone.
Do NOT use emojis or icons.
Do NOT use multiple pound signs or asterisks as decorative elements."""

    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)

    return response.text


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

    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)

    return response.text


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

    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)

    return response.text


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
Do NOT use multiple pound signs or asterisks as decorative elements.
Do NOT include any additional sections, headers, tables, or lists of AI statements.
Do NOT include an appendix section.
Do NOT list individual AI responses or statements.
ONLY provide the paragraph analysis - nothing else after your analysis."""

    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)

    return response.text


# ==================== REPORT GENERATION ====================

def embed_chart_as_base64(chart_path: str) -> str:
    """Convert a chart image to base64 for embedding in Markdown."""
    import base64
    try:
        with open(chart_path, 'rb') as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
    except Exception as e:
        print(f"Warning: Could not embed chart {chart_path}: {e}")
        return ""


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
    queries: List[Any] = None,
    descriptors: List[Any] = None,
    competitors: List[Any] = None,
    competitor_threats_data: List[Dict[str, Any]] = None,
    llm_breakdown_data: Dict[str, Any] = None,
) -> str:
    """Generate a complete markdown report with embedded charts and insights."""

    # Build brand header with context
    brand_header = f"# {brand_name} - AI Reputation Analysis Report"

    report = f"""{brand_header}

## Executive Summary

{executive_summary}

"""

    # Add Key Metrics charts after Executive Summary (embedded as base64)
    if chart_paths and 'mention_rate' in chart_paths:
        base64_data = embed_chart_as_base64(chart_paths['mention_rate'])
        if base64_data:
            report += f'\n<img src="{base64_data}" alt="Key Metrics Dashboard" style="max-width: 800px; margin: 20px auto;" />\n\n'
        else:
            report += f"\n![Key Metrics Dashboard]({chart_paths['mention_rate']})\n\n"

    if chart_paths and 'share_of_voice' in chart_paths:
        base64_data = embed_chart_as_base64(chart_paths['share_of_voice'])
        if base64_data:
            report += f'\n<img src="{base64_data}" alt="Share of Voice" style="max-width: 800px; margin: 20px auto;" />\n\n'
        else:
            report += f"\n![Share of Voice]({chart_paths['share_of_voice']})\n\n"

    report += f"""
---

## Detailed Analysis with Insights

### 1. Positioning Analysis

| Position | Count | Percentage |
|----------|-------|------------|
| Leader | {positioning_metrics['leader']} | {positioning_metrics['leader_pct']}% |
| Featured | {positioning_metrics['featured']} | {positioning_metrics['featured_pct']}% |
| Listed | {positioning_metrics['listed']} | {positioning_metrics['listed_pct']}% |
| Not Mentioned | {positioning_metrics['not_mentioned']} | {positioning_metrics['not_mentioned_pct']}% |

**Average Positioning Score:** {positioning_average} out of 5.0
"""

    # Add positioning chart (embedded as base64)
    if chart_paths and 'positioning' in chart_paths:
        base64_data = embed_chart_as_base64(chart_paths['positioning'])
        if base64_data:
            report += f'\n<img src="{base64_data}" alt="Positioning Distribution" style="max-width: 800px; margin: 20px auto;" />\n'
        else:
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

    # Add share of voice chart (embedded as base64)
    if chart_paths and 'share_of_voice' in chart_paths:
        base64_data = embed_chart_as_base64(chart_paths['share_of_voice'])
        if base64_data:
            report += f'\n\n<img src="{base64_data}" alt="Share of Voice" style="max-width: 800px; margin: 20px auto;" />\n'
        else:
            report += f"\n\n![Share of Voice]({chart_paths['share_of_voice']})\n"

    # Add SOV insights
    report += f"\n**Insights:**\n\n{sov_insights}\n"

    report += f"""
---

### 3. Descriptor Analysis

**Target Descriptor Adoption:** {descriptor_match_rate}% of your target descriptors appeared in AI responses where the brand was directly mentioned

**Top Descriptors Used by AI Platforms When Mentioning {brand_name}:**

*Note: Counts reflect direct brand mentions only (indirect mentions excluded)*
"""

    # Add descriptor breakdown in list format (not table) to avoid truncation of long names
    if descriptor_analysis:
        sorted_descriptors = sorted(descriptor_analysis.items(), key=lambda x: x[1], reverse=True)
        for descriptor, count in sorted_descriptors[:10]:  # Top 10
            report += f"\n- **{descriptor}**: {count} mentions"
    else:
        report += "\n- No data available"

    # Add descriptor performance chart (embedded as base64)
    if chart_paths and 'descriptor_performance' in chart_paths:
        base64_data = embed_chart_as_base64(chart_paths['descriptor_performance'])
        if base64_data:
            report += f'\n\n<img src="{base64_data}" alt="Descriptor Performance" style="max-width: 800px; margin: 20px auto;" />\n'
        else:
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

    # Add sentiment chart (embedded as base64)
    if chart_paths and 'sentiment' in chart_paths:
        base64_data = embed_chart_as_base64(chart_paths['sentiment'])
        if base64_data:
            report += f'\n<img src="{base64_data}" alt="Sentiment Distribution" style="max-width: 800px; margin: 20px auto;" />\n'
        else:
            report += f"\n![Sentiment Distribution]({chart_paths['sentiment']})\n"

    # Add sentiment insights
    report += f"\n**Insights:**\n\n{sentiment_insights}\n"

    report += """
---

### 5. LLM Platform Analysis

This section breaks down brand performance by individual LLM platforms (ChatGPT, Claude, Gemini, Perplexity) to identify platform-specific strengths and opportunities.

"""

    # Add LLM breakdown sections if data is available
    if llm_breakdown_data:
        # Sort platforms alphabetically for consistency
        platforms_order = ['ChatGPT', 'Claude', 'Gemini', 'Perplexity']

        # 5.1 Brand Mentions by LLM
        report += "#### 5.1 Brand Mention Rates by LLM Platform\n\n"
        report += "| Platform | Total Responses | Brand Mentions | Mention Rate |\n"
        report += "|----------|----------------|----------------|-------------|\n"

        mentions_by_platform = {item['platform']: item for item in llm_breakdown_data.get('brand_mentions', [])}
        for platform in platforms_order:
            if platform in mentions_by_platform:
                data = mentions_by_platform[platform]
                report += f"| {data['platform']} | {data['total_responses']} | {data['mentions']} | {data['mention_rate']}% |\n"

        # 5.2 Positioning by LLM
        report += "\n#### 5.2 Brand Positioning by LLM Platform\n\n"
        report += "| Platform | Leader | Featured | Listed | Not Mentioned | Total |\n"
        report += "|----------|--------|----------|--------|---------------|-------|\n"

        positioning_by_platform = {item['platform']: item for item in llm_breakdown_data.get('positioning', [])}
        for platform in platforms_order:
            if platform in positioning_by_platform:
                data = positioning_by_platform[platform]
                report += f"| {data['platform']} | {data['Leader']} | {data['Featured']} | {data['Listed']} | {data['Not Mentioned']} | {data['total']} |\n"

        # 5.3 Sentiment by LLM
        report += "\n#### 5.3 Sentiment Distribution by LLM Platform\n\n"
        report += "*For responses where brand was mentioned*\n\n"
        report += "| Platform | Very Positive | Positive | Neutral | Negative | Very Negative | Mixed | Total |\n"
        report += "|----------|---------------|----------|---------|----------|---------------|-------|-------|\n"

        sentiment_by_platform = {item['platform']: item for item in llm_breakdown_data.get('sentiment', [])}
        for platform in platforms_order:
            if platform in sentiment_by_platform:
                data = sentiment_by_platform[platform]
                report += f"| {data['platform']} | {data['Very Positive']} | {data['Positive']} | {data['Neutral']} | {data['Negative']} | {data['Very Negative']} | {data['Mixed']} | {data['total']} |\n"

        # 5.4 Share of Voice by LLM
        report += "\n#### 5.4 Share of Voice by LLM Platform\n\n"
        report += "| Platform | Brand Mentions | Competitor Mentions |\n"
        report += "|----------|----------------|--------------------|\n"

        sov_by_platform = {item['platform']: item for item in llm_breakdown_data.get('share_of_voice', [])}
        for platform in platforms_order:
            if platform in sov_by_platform:
                data = sov_by_platform[platform]
                report += f"| {data['platform']} | {data['brand']} | {data['competitors']} |\n"

        # 5.5 Top Descriptors by LLM
        report += "\n#### 5.5 Top Descriptors by LLM Platform\n\n"

        descriptors_by_platform = {item['platform']: item for item in llm_breakdown_data.get('descriptors', [])}
        for platform in platforms_order:
            if platform in descriptors_by_platform:
                data = descriptors_by_platform[platform]
                report += f"\n**{data['platform']}** (Total descriptor mentions: {data['total_mentions']})\n\n"
                for desc in data['descriptors']:
                    report += f"- **{desc['descriptor']}**: {desc['count']} mentions\n"

        # 5.6 Top Competitor Threats by LLM
        report += "\n#### 5.6 Competitor Mentions by LLM Platform\n\n"

        threats_by_platform = {item['platform']: item for item in llm_breakdown_data.get('threats', [])}
        for platform in platforms_order:
            if platform in threats_by_platform:
                data = threats_by_platform[platform]
                report += f"\n**{data['platform']}** (Total competitor mentions: {data['total_competitor_mentions']})\n\n"
                report += "| Competitor | Mentions | Negative Overlap |\n"
                report += "|-----------|----------|------------------|\n"
                for comp in data['competitors']:
                    report += f"| {comp['name']} | {comp['mentions']} | {comp['negative_overlap']} |\n"

    report += """

---

### 6. Threat Analysis

**Competitor Threat Summary:**

Threats are calculated based on three factors: mention frequency (weight: 0.7), negative sentiment when competitor is present (weight: 2.0), and positive sentiment for competitor (weight: 1.5). Threat levels: High (score > 50), Medium (20-50), Low (< 20).

| Rank | Competitor | Threat Level | Threat Score | Mentions | Share of Voice |
|------|-----------|--------------|--------------|----------|----------------|"""

    # Add threat table data
    if competitor_threats_data:
        for i, threat in enumerate(competitor_threats_data[:10], 1):  # Top 10
            report += f"\n| {i} | {threat['name']} | {threat['threat_level']} | {threat['threat_score']} | {threat['mention_count']} | {threat['share_of_voice']}% |"
    else:
        report += "\n| - | No data | - | - | - | - |"

    report += "\n\n**Detailed Threat Analysis:**\n\n"
    report += competitor_threats

    report += """

---

### 7. Recommendations
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
        positioning_metrics = calculate_positioning_metrics(responses, queries)
        sentiment_metrics = calculate_sentiment_metrics(responses)
        platform_metrics = calculate_platform_metrics(responses, queries)
        descriptor_analysis = analyze_descriptors(responses)
        competitor_analysis = analyze_competitors(responses)
        positive_sentiment_rate = calculate_positive_sentiment_rate(responses)
        descriptor_match_rate = calculate_descriptor_match_rate(responses, descriptors)
        share_of_voice = calculate_share_of_voice(responses, queries, competitors, brand_name)
        positioning_average = calculate_positioning_average(responses, queries)
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

        # Step 3b: Calculate competitor threats using CompetitorThreats page logic
        print("\nCalculating competitor threat scores...")
        competitor_threats_data = calculate_competitor_threats(
            competitor_sov=share_of_voice['competitor_sov'],
            responses=responses,
            brand_name=brand_name
        )
        print(f"  - {len(competitor_threats_data)} competitors analyzed")
        if competitor_threats_data:
            print(f"  - Top 3 threats: {', '.join([t['name'] for t in competitor_threats_data[:3]])}")

        # Step 4: Generate AI insights with enhanced prompts
        print("\nGenerating AI-powered insights with Gemini 2.5 Pro...")
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

        print("  - Competitor threat analysis (top 3 threats)...")
        competitor_threats = generate_competitor_threat_analysis(
            top_threats=competitor_threats_data,
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

        # Step 4c: Collect LLM breakdown data
        print("\nCollecting LLM platform breakdown data...")
        llm_breakdown_data = get_llm_breakdown_data(db, user_id, brand_id, brand_name)
        print(f"  - Brand mention data for {len(llm_breakdown_data['brand_mentions'])} platforms")
        print(f"  - Positioning data for {len(llm_breakdown_data['positioning'])} platforms")
        print(f"  - Sentiment data for {len(llm_breakdown_data['sentiment'])} platforms")
        print(f"  - Share of voice data for {len(llm_breakdown_data['share_of_voice'])} platforms")
        print(f"  - Descriptor data for {len(llm_breakdown_data['descriptors'])} platforms")
        print(f"  - Threat data for {len(llm_breakdown_data['threats'])} platforms")

        # Step 5: Collect trend data for charts
        print("\nCollecting trend data for visualization...")
        trend_data = None
        try:
            brand_mentions_trend = get_brand_mentions_trend_cached(db, user_id, brand_id)
            positioning_trend = get_positioning_trend_cached(db, user_id, brand_id)
            sentiment_trend = get_sentiment_trend_cached(db, user_id, brand_id)
            sov_trend = get_share_of_voice_trend_cached(db, user_id, brand_id, brand_name)

            # Format trend data for chart generator
            if brand_mentions_trend:
                trend_data = {
                    'brand_mentions': [
                        {
                            'date': str(item['date']),
                            'mention_percentage': item['mention_rate']
                        }
                        for item in brand_mentions_trend
                    ] if brand_mentions_trend else None,
                    'positioning': positioning_trend if positioning_trend else None,
                    'sentiment': sentiment_trend if sentiment_trend else None,
                    'share_of_voice': [
                        {
                            'date': str(item['date']),
                            'brand_sov': item.get(brand_name, 0),
                            'competitors': {k: v for k, v in item.items() if k != 'date' and k != brand_name}
                        }
                        for item in sov_trend
                    ] if sov_trend else None
                }
                print(f"  - Collected trend data for {len(brand_mentions_trend)} time periods")
        except Exception as e:
            print(f"  - Could not collect trend data: {e}")
            print("  - Charts will be generated without trend lines")
            trend_data = None

        # Step 6: Generate charts
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
            brand_id=brand_id,
            trend_data=trend_data,
            competitor_threats=competitor_threats_data
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
            queries=queries,
            descriptors=descriptors,
            competitors=competitors,
            competitor_threats_data=competitor_threats_data,
            llm_breakdown_data=llm_breakdown_data,
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
