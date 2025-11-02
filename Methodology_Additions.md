# Additional Sections for Analysis Methodology Document

## Section on Priority Level

### Role of Priority Levels in Analysis

The Tales platform allows users to assign priority levels (High, Medium, Low) to both target descriptors and queries for organizational purposes. However, it is important to note that **priority levels do not impact the quantitative analysis or metric calculations in any way**. All descriptors are weighted equally when calculating descriptor match rates, all queries contribute equally to mention rates and positioning metrics, and no preferential weighting is applied based on priority designation. The priority field serves two limited functions: (1) as a display sorting mechanism when viewing lists of descriptors or queries in the administrative interface, and (2) as contextual metadata included in the text provided to AI models during qualitative report generation. In the latter case, the AI-generated narrative insights may reference higher-priority descriptors to emphasize their strategic importance, but this does not algorithmically affect the underlying calculations. This design choice ensures that all metrics remain objective and free from subjective weighting, while still allowing stakeholders to mentally organize and prioritize strategic goals.

---

## Mathematical Formulas for Metric Calculations

### Brand Mentions (Mention Rate)

The mention rate quantifies how frequently Physics of Plasmas is referenced by AI platforms when the brand name is not explicitly included in the query, measuring organic visibility.

**Formula:**
```
Mention Rate (%) = (Number of Mentions / Total Qualifying Responses) × 100
```

**Calculation Details:**
- **Numerator:** Count of responses where `brand_mentioned` field equals 'Yes' OR 'Indirect'
- **Denominator:** Total count of all responses in the analysis period
- **Critical Exclusion:** Both numerator and denominator exclude responses from queries where `brand_in_query = True` (queries that explicitly mentioned Physics of Plasmas by name)
- **Rationale:** Excluding branded queries prevents inflated mention rates and isolates organic AI platform behavior

**Example:** If there were 85 total responses from non-branded queries, and Physics of Plasmas was mentioned (directly or indirectly) in 34 of them, the mention rate would be (34/85) × 100 = 40.0%

---

### Positioning Score

The positioning metric evaluates where Physics of Plasmas appears in AI-generated responses, with higher scores indicating more prominent placement.

**Average Positioning Score Formula:**
```
Average Positioning Score = (Sum of Individual Position Scores) / Total Responses

Position Scoring System:
• Leader = 5 points
• Top 3 = 4 points
• Featured = 3 points
• Listed = 2 points
• Not Mentioned = 1 point
```

**Calculation Details:**
- Each response receives a score (1-5) based on how Physics of Plasmas was positioned
- The scores are summed across all qualifying responses
- Divided by total response count to produce an average (range: 1.0 to 5.0)
- **Exclusion:** Responses from queries where `brand_in_query = True` are excluded
- A higher average indicates stronger positioning across AI platforms

**Positioning Breakdown Percentages:**
```
Positioning Category Percentage = (Count in Category / Total Responses) × 100
```

Each positioning category (Leader, Top 3, Featured, Listed, Not Mentioned) is also reported as a percentage of total responses, showing the distribution of positioning outcomes.

**Leadership Visibility (Sub-metric):**
```
Leadership Visibility (%) = ((Leader Count + Top 3 Count) / Total Responses) × 100
```

This metric specifically measures high-quality visibility by combining the top two positioning categories.

---

### Share of Voice

Share of Voice quantifies Physics of Plasmas' relative visibility compared to all organizations (including competitors) mentioned across AI responses.

**Formula:**
```
Share of Voice (%) = (Brand Mentions / Total All Organization Mentions) × 100
```

**Calculation Details:**
- **Brand Mentions (Numerator):** Count of responses where Physics of Plasmas achieved positioning of 'Leader', 'Top 3', 'Featured', or 'Listed' (excludes 'Not Mentioned')
- **Total All Organization Mentions (Denominator):** Sum of all organization mentions including:
  - Physics of Plasmas mentions (from numerator)
  - All competitor mentions extracted from the `competitors` field across all responses
- **Competitor Counting:** The competitors field contains comma-separated organization names; each occurrence increments that competitor's mention count
- **Exclusion:** Only responses from queries where `brand_in_query = False` are included
- **Interpretation:** A 25% share of voice means Physics of Plasmas accounts for 25% of all organization mentions, with competitors collectively representing the remaining 75%

**Example:** If Physics of Plasmas appeared in 34 responses with qualifying positioning, Competitor A appeared in 18 responses, Competitor B in 22 responses, and Competitor C in 16 responses, the total mentions would be 90. Physics of Plasmas' share of voice would be (34/90) × 100 = 37.8%

---

### Target Descriptor Adoption

Target descriptor adoption measures how successfully Physics of Plasmas has become associated with the specific descriptors and attributes it aims to own strategically.

**Formula:**
```
Descriptor Match Rate (%) = (Number of Target Descriptors Found / Total Target Descriptors) × 100
```

**Calculation Details:**
- **Total Target Descriptors (Denominator):** Count of all descriptors configured as strategic targets for Physics of Plasmas in the platform
- **Target Descriptors Found (Numerator):** Count of unique target descriptors that appear in at least one AI response
- **Matching Logic:**
  - Searches the `descriptors` field from each response (comma-separated list)
  - Case-insensitive matching
  - A target descriptor is counted as "found" if it appears in any response where Physics of Plasmas was mentioned (brand_mentioned = 'Yes' or 'Indirect')
- **Inclusion:** Unlike mention/positioning metrics, this calculation INCLUDES responses from queries where `brand_in_query = True`, since descriptors reflect the quality of associations regardless of how the brand was introduced
- **Interpretation:** A 65% descriptor match rate means that 65% of the target descriptors Physics of Plasmas aims to be known for actually appeared in AI-generated content

**Example:** If Physics of Plasmas has 20 target descriptors ("innovative", "leading", "cutting-edge", "authoritative", etc.) and 13 of those descriptors appeared in at least one response, the descriptor match rate would be (13/20) × 100 = 65.0%

**Descriptor Frequency:** The platform also tracks how many times each descriptor appeared, allowing identification of the strongest vs. weakest descriptor associations.

---

### Competitive Threat Analysis

Unlike the quantitative metrics above, competitive threat analysis is **not based on a mathematical formula**. Instead, it employs a qualitative AI-powered methodology to identify strategic competitive risks.

**Process (Not a Formula):**

1. **Data Collection Phase:**
   - Gathers Share of Voice data showing competitor mention frequencies
   - Identifies specific query-response pairs where Physics of Plasmas was not mentioned but competitors were
   - Extracts "competitive loss" examples where Physics of Plasmas appeared but was poorly positioned relative to competitors
   - Compiles competitor strategic context (focus areas, target descriptors, positioning goals)

2. **AI Analysis Phase:**
   - Submits concrete response examples and competitive data to Perplexity Sonar Pro model
   - AI identifies patterns in which competitors consistently outperform Physics of Plasmas
   - Analyzes the specific descriptors, positioning, and strategic territory competitors have claimed
   - Synthesizes threat landscape based on actual response content rather than calculated scores

3. **Output:**
   - Qualitative descriptions of top 3-5 competitive threats
   - Specific examples of queries/responses where competitors won visibility
   - Strategic implications of competitive positioning
   - Recommended counter-actions to address competitive gaps

**Rationale for Qualitative Approach:** Competitive threats involve nuanced strategic considerations that resist reduction to single numerical scores. A competitor with lower share of voice but stronger positioning on a critical strategic descriptor may pose a greater threat than a competitor with higher overall visibility. The AI-powered qualitative analysis can weigh these multidimensional factors more effectively than a predetermined formula.

**Key Insight:** While threat "level" is not quantified, the analysis is still data-driven, grounded in actual response examples and measurable share of voice differentials, making it actionable rather than speculative.

---

## Summary of Metric Calculation Approaches

| Metric | Type | Includes Branded Queries? | Rationale |
|--------|------|---------------------------|-----------|
| **Mention Rate** | Quantitative Formula | No (Excluded) | Measures organic visibility without bias from explicitly branded queries |
| **Positioning Score** | Quantitative Formula | No (Excluded) | Assesses natural positioning when brand is not prompted |
| **Share of Voice** | Quantitative Formula | No (Excluded) | Compares competitive visibility in organic contexts |
| **Descriptor Match** | Quantitative Formula | Yes (Included) | Quality of associations matters regardless of query type |
| **Sentiment Distribution** | Quantitative Formula | Yes (Included) | Sentiment reflects brand perception across all mention contexts |
| **Competitive Threats** | Qualitative AI Analysis | Context-dependent | Strategic nuance requires pattern recognition beyond formulas |

This methodological framework balances quantitative rigor (for metrics amenable to precise calculation) with qualitative depth (for strategic insights requiring contextual interpretation), ensuring both statistical validity and actionable strategic intelligence.
