# TALES Automated Report Generation Plan

## Overview
Generate professional AI reputation analysis reports based on collected and analyzed response data from ChatGPT, Claude, Gemini, and Perplexity.

## Report Structure

### 1. Executive Summary
- **Overall PPPL Mention Rate**: Percentage across all platforms
- **Key Findings**: Top 3 strengths and weaknesses
- **Critical Insights**: Most important discoveries
- **Strategic Recommendations Preview**: Brief list of top recommendations

### 2. Methodology
- **Analysis Period**: Date range
- **Platforms Analyzed**: ChatGPT (OpenAI GPT-4), Claude (Anthropic), Gemini (Google), Perplexity (AI Search)
- **Query Universe**: 22 strategic queries across multiple categories
- **Total Responses Analyzed**: 88 (22 queries × 4 platforms)
- **Analysis Approach**: Automated AI-powered content analysis

### 3. Key Metrics Dashboard

#### 3.1 PPPL Visibility Metrics
- **Mention Rate**: XX% (percentage of responses mentioning PPPL)
  - Yes (explicit mention): XX%
  - Indirect (work mentioned, not name): XX%
  - Not Mentioned: XX%

#### 3.2 Positioning Analysis
- **Leader**: XX% (described as top/leading institution)
- **Top 3**: XX% (listed among 2-4 top institutions)
- **Featured**: XX% (dedicated paragraph/significant discussion)
- **Listed**: XX% (mentioned in a list)
- **Not Mentioned**: XX%

#### 3.3 Sentiment Analysis
- **Very Positive**: XX% (exceptional praise)
- **Positive**: XX% (favorable)
- **Neutral**: XX% (factual, no clear sentiment)
- **Negative**: XX% (critical)
- **Mixed**: XX%

#### 3.4 Share of Voice
- **PPPL**: XX% of total institution mentions
- **Top Competitors**:
  - Competitor 1: XX%
  - Competitor 2: XX%
  - Competitor 3: XX%

#### 3.5 Target Descriptor Adoption
Analysis of which brand/positioning descriptors are used:
- "pioneering": XX times
- "innovative": XX times
- "spherical tokamak": XX times
- "liquid lithium": XX times
- etc.

### 4. Platform-by-Platform Analysis

#### 4.1 ChatGPT (OpenAI GPT-4)
- Mention Rate: XX%
- Average Position: XX
- Typical Sentiment: XX
- Notable Patterns: ...
- Sample Response: [quote]

#### 4.2 Claude (Anthropic)
- Mention Rate: XX%
- Average Position: XX
- Typical Sentiment: XX
- Notable Patterns: ...
- Sample Response: [quote]

#### 4.3 Gemini (Google)
- Mention Rate: XX%
- Average Position: XX
- Typical Sentiment: XX
- Notable Patterns: ...
- Sample Response: [quote]

#### 4.4 Perplexity (AI-Powered Search)
- Mention Rate: XX%
- Average Position: XX
- Typical Sentiment: XX
- Notable Patterns: ...
- Sample Response: [quote]

#### 4.5 Cross-Platform Comparison
- Which platform mentions PPPL most frequently?
- Which gives most positive sentiment?
- Platform-specific opportunities

### 5. Query Category Performance

#### 5.1 Leadership & General Positioning Queries
- Queries: "leading institutions," "top laboratories," "leaders in fusion"
- PPPL Performance: ...
- Key Findings: ...

#### 5.2 Technical Capability Queries
- Queries: "spherical tokamak," "NSTX-U," "liquid lithium," "plasma-facing materials"
- PPPL Performance: ...
- Key Findings: ...

#### 5.3 Innovation & Future Focus Queries
- Queries: "AI in fusion," "challenges," "timeline"
- PPPL Performance: ...
- Key Findings: ...

#### 5.4 Partnership & Collaboration Queries
- Queries: "who to partner with," "public-private collaboration"
- PPPL Performance: ...
- Key Findings: ...

### 6. Competitor Analysis

#### 6.1 Co-Mention Analysis
Which competitors appear alongside PPPL in responses:
- [Competitor Name]: XX times
  - Context: leadership, technical capability, partnership, etc.

#### 6.2 Competitive Threats
Competitors mentioned MORE frequently than PPPL:
- [Competitor]: mentioned in XX% of responses vs PPPL's XX%
  - Why: ...

#### 6.3 Competitive Advantages
Areas where PPPL is mentioned more prominently than competitors:
- Spherical tokamaks: PPPL XX% vs competitors XX%
- etc.

### 7. Strategic Recommendations

**Recommendation 1: [Title]**
- **Current State**: [What the data shows]
- **Gap Identified**: [Specific problem]
- **Recommended Action**: [Specific, actionable steps]
- **Expected Impact**: [Measurable outcomes]
- **Priority**: High/Medium/Low
- **Resources Required**: [Time, budget, personnel]

**Recommendation 2: [Title]**
[Same structure]

**Recommendation 3: [Title]**
[Same structure]

**Recommendation 4: [Title]** (if applicable)
[Same structure]

**Recommendation 5: [Title]** (if applicable)
[Same structure]

### 8. Appendices

#### Appendix A: Complete Query List
1. What institutions are leading fusion energy research?
2. Who are the top fusion energy laboratories?
[...all 22 queries]

#### Appendix B: Detailed Metrics Tables
[Raw data tables with all calculated metrics]

#### Appendix C: Sample Responses
[Representative responses from each platform for key queries]

#### Appendix D: Methodology Details
[Technical details of collection and analysis process]

---

## Implementation Technical Plan

### Script: `generate_report.py`

```python
#!/usr/bin/env python3
"""
TALES Report Generation Script
Generates professional analysis reports from analyzed response data.
"""

# Steps:
# 1. Query database for all analyzed responses
# 2. Calculate all metrics programmatically
# 3. Build data structures for each report section
# 4. Use Gemini API to generate:
#    - Executive summary (synthesize findings)
#    - Strategic recommendations (analyze gaps, suggest actions)
#    - Professional narrative connecting metrics
# 5. Format as Markdown
# 6. Export to PDF/Google Docs format

# Sections:
# - calculate_mention_metrics()
# - calculate_positioning_metrics()
# - calculate_sentiment_metrics()
# - calculate_share_of_voice()
# - analyze_descriptors()
# - analyze_competitors()
# - generate_platform_analysis()
# - generate_category_analysis()
# - generate_recommendations() <- Uses Gemini AI
# - generate_executive_summary() <- Uses Gemini AI
# - compile_report()
# - export_to_markdown()
# - export_to_google_docs() [future]
```

### Recommendation Generation Logic

The AI will analyze gaps and generate recommendations based on:

**If mention rate < 50%:**
→ Recommend: Increase thought leadership content, press releases, strategic partnerships

**If positioned as "Listed" > "Featured":**
→ Recommend: Develop hero stories, case studies, breakthrough announcements

**If target descriptors rarely used:**
→ Recommend: Content strategy emphasizing specific terms, SEO optimization

**If competitors mentioned more:**
→ Recommend: Competitive positioning strategy, differentiation messaging

**If platform-specific gaps (e.g., low on Perplexity):**
→ Recommend: Platform-specific SEO, ensure presence in cited sources

**If negative/mixed sentiment:**
→ Recommend: Address specific concerns, proactive communication strategy

---

## Output Formats

### Primary: Markdown Report
- Clean, professional markdown format
- Can be converted to PDF, HTML, Google Docs
- Version controlled in git

### Future: Google Docs Integration
- Use Google Docs API to create formatted document
- Include charts/graphs
- Shareable link for stakeholders

### Future: PDF Export
- Professional PDF with PPPL branding
- Charts and visualizations
- Print-ready format
