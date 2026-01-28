# TALES Metrics System Architecture Summary

## Executive Overview
The TALES system implements a comprehensive metrics infrastructure tracking Brand Mentions, Positioning, Share of Voice, and Sentiment across AI-generated content. The architecture uses a centralized caching system to avoid redundant calculations and provides both real-time dashboard visualizations and report generation capabilities.

**Important Note on Data Collection**: Data is collected primarily once per month with optional ad-hoc manual collections and analysis on additional days.

---

## 1. KEY METRICS IMPLEMENTATION

### 1.1 Brand Mentions
**Definition**: Percentage and count of responses that mention the brand (explicitly or indirectly).

**Current Implementation**:
- **Data Model**: `Response.brand_mentioned` field (values: "Yes", "Indirect", "No")
- **Calculation Location**: 
  - Backend: `app/services/metrics.py` - `calculate_mention_metrics()`
  - Frontend: Dedicated page at `/analytics/brand-mentions`
- **Filtering Rules**: 
  - EXCLUDES responses where `Query.brand_in_query = True`
  - Rationale: Fair comparison - when brand name is in query, mention is guaranteed
- **UI Structure**:
  - **Dedicated Analytics Page** (`BrandMentions.tsx`): Similar to Positioning Analysis
    - Pie chart showing Yes/Indirect/No distribution
    - Key metrics cards with counts and percentages
    - 30-day trend line chart
    - Batch selector for filtering by collection period
- **Report Section**: 
  - Dedicated section in generated reports with:
    - Brand Mentions pie chart (matplotlib)
    - Table with breakdown and percentages
    - Trend analysis over analysis period

### 1.2 Positioning
**Definition**: How the brand is ranked within each response (Leader > Featured > Listed > Not Mentioned).

**Current Implementation**:
- **Data Model**: `Response.brand_position` field 
  - Values: "Leader", "Featured", "Top 3", "Listed", "Not Mentioned"
  - Position Scores: Leader=4, Featured=3, Listed=2, Not Mentioned=1
- **Calculation Location**:
  - Backend: `app/services/metrics.py` - `calculate_positioning_metrics()`, `calculate_positioning_average()`
  - Frontend: Dedicated page at `/analytics/positioning`
- **Filtering Rules**:
  - EXCLUDES `brand_in_query = True` responses (same as Brand Mentions)
  - Only counts mentions where `brand_mentioned in ['Yes', 'Indirect']`
- **UI Structure** (`PositioningAnalysis.tsx`):
  - Horizontal bar chart showing distribution across 4 position tiers
  - Table with rank, count, and percentage for each position
  - Position definitions section (explanatory content)
  - 30-day trend line chart showing mention rate changes
  - Batch selector for filtering by collection period
- **Report Section**: 
  - Horizontal bar chart (matplotlib)
  - Position distribution table
  - Trend analysis

### 1.3 Share of Voice
**Definition**: Percentage of total mentions that reference your brand vs. competitors.

**Current Implementation**:
- **Data Model**: 
  - Brand: `Response.brand_mentioned`, `Response.competitors` (comma-separated)
  - Competitors: Primarily extracted from `Response.competitors` field
- **Calculation Location**:
  - Backend: `app/services/metrics.py` - `calculate_share_of_voice()`
  - Frontend: Dedicated page at `/analytics/share-of-voice`
- **Filtering Rules**:
  - EXCLUDES `brand_in_query = True` responses (same as Positioning and Brand Mentions)
  - Only counts responses where `brand_mentioned in ['Yes', 'Indirect']`
  - Parses competitor names from `Response.competitors` field
- **Metrics Calculated**:
  - Brand SOV percentage (vs. all competitors)
  - Leadership Visibility: % of brand mentions in Leader/Featured positions
  - Competitor ranking table with mention counts and SOV %
- **UI Structure** (`ShareOfVoice.tsx`):
  - Brand SOV metric card with ranking (e.g., "45% - Rank #2 of 15")
  - Leadership Visibility card (quality metric)
  - Top 10 organizations bar chart by SOV
  - Full distribution: Pie chart (≤5 competitors) or table (>5 competitors)
  - Batch selector for filtering
- **Report Section**: 
  - SOV bar chart (top organizations)
  - Full distribution table with all competitors
  - Leadership visibility insights

### 1.4 Sentiment Analysis
**Definition**: Tone and attitude expressed toward the brand (Very Positive, Positive, Neutral, Negative, Very Negative).

**Current Implementation**:
- **Data Model**: `Response.sentiment` field
- **Calculation Location**:
  - Backend: `app/services/metrics.py` - `calculate_sentiment_metrics()`, `calculate_positive_sentiment_rate()`
  - Frontend: Dedicated page at `/analytics/sentiment`
- **Filtering Rules**:
  - Only counts direct mentions (`brand_mentioned == 'Yes'`)
  - INCLUDES all queries (even `brand_in_query = True`)
  - Rationale: Sentiment applies to all brand mentions regardless of query type
- **UI Structure** (`SentimentAnalysis.tsx`):
  - Sentiment distribution pie chart with 5-color palette
  - Key insights section with sentiment-specific text analysis
  - Negative statements section (extracted examples with query context)
  - CSV download for negative statements
  - Batch selector
- **Report Section**: 
  - Sentiment pie chart (matplotlib)
  - Breakdown table with counts and percentages
  - Key insights per sentiment level
  - Sample negative statements

---

## 2. DATA MODELS & SCHEMA

### Core Tables:
```python
# Response Model (app/models.py)
- id: Primary Key
- user_id: Multi-tenancy
- brand_id: Multi-brand support
- batch_id: Collection batch tracking
- query_id: Reference to Query
- query_text: Denormalized query text
- platform: "ChatGPT" | "Claude" | "Gemini" | "Perplexity"
- response_text: Full AI response
- timestamp: When response was collected
- brand_mentioned: "Yes" | "Indirect" | "No"
- brand_position: "Leader" | "Featured" | "Top 3" | "Listed" | "Not Mentioned"
- sentiment: "Very Positive" | "Positive" | "Neutral" | "Negative" | "Very Negative"
- descriptors: Comma-separated list of identified descriptors
- competitors: Comma-separated list of mentioned competitors
- analyzed_at: Timestamp when AI analysis was completed

# Query Model
- query_id: Unique per user+brand (e.g., "Q001")
- user_id: Reference to User
- brand_id: Reference to Brand
- query_text: The search/query text used to collect responses
- brand_in_query: Boolean (True if brand name appears in query text)
- active: Boolean (whether to include in current analysis)
- category: Query category/grouping
- priority: Priority level

# BrandInfo Model
- brand_name: User's brand being tracked
- is_active: Which brand is currently selected (user can have up to 20)

# CollectionBatch Model
- batch_name: Name of this collection period
- started_at: When collection began
- completed_at: When collection finished
- status: "in_progress" | "completed" | "failed"
- total_queries: Number of queries in batch
- total_responses: Number of responses collected
```

---

## 3. API ENDPOINTS & DATA FLOW

### Analytics API Endpoints (app/routers/analytics.py)

```
GET /analytics/dashboard
  - Returns: DashboardMetrics (mention_rate, sentiment, descriptor_match, share_of_voice)
  - Query Params: batch_id (optional)
  
GET /analytics/brand-mentions
  - Returns: Brand mention breakdown with Yes/Indirect/No counts and percentages
  
GET /analytics/positioning/breakdown
  - Returns: Distribution across 4 position tiers with counts/percentages
  
GET /analytics/sentiment/breakdown
  - Returns: Sentiment distribution with counts, percentages, and insights
  - Includes: sentiment_insights (AI-generated insights per sentiment level)
  
GET /analytics/share-of-voice
  - Returns: Array of organizations with mention counts, SOV %, leadership visibility
  
GET /analytics/trends/mentions?days=30
  - Returns: Daily mention rate trend data for line chart
  
GET /analytics/competitor-threats
  - Returns: Competitor threat scores and rankings
```

### Data Flow Pattern:
1. Frontend calls API endpoint with optional `batch_id` filter
2. Backend uses `AnalyticsCache` class to calculate metrics once and cache
3. `AnalyticsCache` applies appropriate filters (brand_in_query, mention type, etc.)
4. Metrics are calculated using pure functions in `metrics.py` module
5. Results returned as JSON; frontend formats for display

---

## 4. CHARTING LIBRARIES & VISUALIZATION

### Frontend Charting:
- **Library**: Recharts (React component library for interactive charts)
- **Chart Types Used**:
  - **PieChart**: Brand Mentions distribution, Sentiment distribution, SOV distribution (≤5 competitors)
  - **BarChart**: Positioning distribution, Top 10 organizations by SOV, Threat scores
  - **LineChart**: 30-day mention rate/brand mention trends
  
- **Examples per Metric**:
  - **Brand Mentions**: PieChart (Yes/Indirect/No) + LineChart (30-day trend)
  - **Positioning**: Horizontal BarChart (4 tiers) + LineChart (trend)
  - **Sentiment**: PieChart (5 sentiments)
  - **Share of Voice**: BarChart (top 10) + PieChart or Table (full distribution)

### Chart Download:
- **Tool**: `html2canvas` library (captures DOM elements as PNG)
- **Implementation Pattern**: 
  ```javascript
  // Wrap chart in ref
  const chartRef = useRef<HTMLDivElement>(null);
  
  // Download on button click
  const canvas = await html2canvas(chartRef.current, {
    backgroundColor: '#ffffff',
    scale: 2  // 2x quality
  });
  link.href = canvas.toDataURL();
  link.click();
  ```
- **Naming Convention**: `{MetricType}_{BrandName}_{MM_DD_YYYY}.png`

### Backend Report Charts:
- **Library**: Matplotlib + Seaborn (for static report embedding)
- **Purpose**: Embedded in PDF/Word reports
- **Chart Generation File**: `app/services/chart_generator.py`
- **Functions**:
  - `generate_mention_rate_pie_chart()` - For Brand Mentions section
  - `generate_sentiment_pie_chart()` - For Sentiment section
  - `generate_positioning_bar_chart()` - For Positioning section
  - `generate_share_of_voice_chart()` - For SOV section
- **Color Palette**: Matches frontend TALES brand colors
- **Storage**: Generated to `report_charts/` directory with naming: `{user_id}_{brand_id}_{chart_type}.png`

---

## 5. STATE MANAGEMENT & DATA FETCHING

### React Query Implementation:
```typescript
// Example: Brand Mentions metrics query
const { data: brandMentions, isLoading, error } = useQuery({
  queryKey: ['brand-mentions', selectedBatchId],
  queryFn: async () => {
    const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
    const response = await api.get('/analytics/brand-mentions', { params });
    return response.data;
  },
  refetchInterval: 30000, // Auto-refresh every 30 seconds
});

// Pattern: Conditional queries based on batch selection
const { data: sentimentData } = useQuery({
  queryKey: ['sentiment-breakdown', selectedBatchId],
  queryFn: async () => {
    const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
    return await api.get('/analytics/sentiment/breakdown', { params });
  }
});
```

### State Management:
- **Brand Selection**: `BrandContext` (which brand is active)
- **Batch Selection**: Local component state (useState) in analytics pages for filtering by collection period
- **API Client**: Axios with JWT token interceptor (`api.ts`)

---

## 6. REPORT GENERATION ARCHITECTURE

### Report Generation Flow:
1. **Trigger**: User clicks "Generate Full Report" in CollectAndAnalyze page
2. **Backend Task**: 
   - `generate_report.py` is called as background task (Celery)
   - Calls `AnalyticsCache` to get all metrics
   - Uses metrics module to calculate: brand mentions, positioning, sentiment, SOV, threats
3. **Report Structure** (Markdown):
   ```
   1. Executive Summary
   2. Key Metrics
   3. Brand Mentions Analysis (NEW DEDICATED SECTION)
   4. Positioning Analysis
   5. Share of Voice Analysis
   6. Sentiment Analysis
   7. Descriptor Insights
   8. Competitor Threats
   9. Strategic Recommendations (AI-generated)
   ```
4. **Chart Embedding**:
   - Matplotlib charts generated for all metrics with dedicated sections
   - Brand Mentions chart generated via `chart_generator.generate_mention_rate_pie_chart()`
   - Charts embedded as image references in markdown
   - Option to check for frontend-generated charts and reuse them
5. **Export Formats**:
   - Markdown (primary storage in DB)
   - HTML (via markdown-to-html conversion)
   - DOCX (via python-docx with embedded charts)
   - PDF (via DOCX → PDF conversion)

---

## 7. CURRENT UI STRUCTURE FOR METRICS

### Dashboard Page (`/`)
**Displays**: Key metrics summary with visual indicators
- **Components**:
  - KPI Cards: Mention rate, sentiment positive %, descriptor match, share of voice
  - Mini Charts: Sentiment pie chart, positioning bar chart
  - Batch Selector: Filter by collection period
  - Download Button: Save dashboard as PNG

### Dedicated Analytics Pages:
1. **Brand Mentions** (`/analytics/brand-mentions`) - NEW PAGE
   - Pie chart showing Yes/Indirect/No distribution
   - Key metrics cards: Total mentions, mention rate %, explicit vs. indirect breakdown
   - 30-day trend line chart
   - Explanatory text about mention types
   - Batch selector

2. **Positioning** (`/analytics/positioning`)
   - Horizontal bar chart: Distribution across 4 position tiers (Leader/Featured/Listed/Not Mentioned)
   - Position definitions section (explanatory cards)
   - 30-day trend line chart showing positioning changes
   - Batch selector

3. **Share of Voice** (`/analytics/share-of-voice`)
   - Brand SOV card with ranking (e.g., "45% - Rank #2 of 15")
   - Leadership Visibility card (% in Leader/Featured positions)
   - Top 10 organizations bar chart by SOV
   - Full distribution: Pie chart (≤5 competitors) or table (>5 competitors)
   - Batch selector

4. **Sentiment Analysis** (`/analytics/sentiment`)
   - Sentiment distribution pie chart with 5 colors
   - Key insights per sentiment level
   - Negative statements section (with query context)
   - CSV download button
   - Batch selector

5. **Descriptor Analysis** (`/analytics/descriptors`)
   - Top 10 descriptors bar chart
   - Full descriptor table with usage rates and status
   - Status indicators (Strong/Moderate/Weak/Not Used)

6. **Competitor Threats** (`/analytics/threats`)
   - Threat scores bar chart (top 10)
   - Full competitor table with threat levels and rankings
   - CSV export of threat data

7. **Recommendations** (`/analytics/recommendations`)
   - Displays AI-generated strategic recommendations from latest report
   - Markdown-formatted text

### Collect & Analyze Page (`/collect-analyze`)
**Consolidated page** combining:
- Data Collection tab (manual/scheduled)
- Data Analysis tab
- Scheduled Tasks tab
- Report Archive tab (generation and download history)

---

## 8. METRICS IMPLEMENTATION SUMMARY

| Metric | Location in Code | Calculation Function | API Endpoint | Analytics Page | Report Section | Filters |
|--------|-----------------|----------------------|--------------|-----------------|----------------|---------|
| Brand Mentions | `metrics.py` | `calculate_mention_metrics()` | `/analytics/brand-mentions` | `BrandMentions.tsx` | Dedicated | Exclude brand_in_query |
| Positioning | `metrics.py` | `calculate_positioning_metrics()` | `/analytics/positioning/breakdown` | `PositioningAnalysis.tsx` | Dedicated | Exclude brand_in_query |
| Share of Voice | `metrics.py` | `calculate_share_of_voice()` | `/analytics/share-of-voice` | `ShareOfVoice.tsx` | Dedicated | Exclude brand_in_query |
| Sentiment | `metrics.py` | `calculate_sentiment_metrics()` | `/analytics/sentiment/breakdown` | `SentimentAnalysis.tsx` | Dedicated | Direct mentions only |
| Descriptors | `metrics.py` | `analyze_descriptors()` | `/descriptors/insights` | `DescriptorAnalysis.tsx` | Table | Direct mentions |
| Threats | `metrics.py` | `calculate_competitor_threats()` | `/analytics/competitor-threats` | `CompetitorThreats.tsx` | Table | Exclude brand_in_query |

---

## 9. TIME-SERIES & TREND TRACKING

### Trend Data:
- **30-Day Window**: All primary analytics pages support 30-day trend visualization
- **Granularity**: Daily (calculated from response timestamps)
- **Metrics Trended**:
  - Brand Mention Rate over time
  - Mention Rate (positioning average) over time
  - Share of Voice comparison trends
- **Data Collection Frequency**: Monthly primary collections with optional ad-hoc collections on specific days

### Implementation:
```python
# Backend (app/analytics.py - get_mention_trend)
def get_mention_trend(db, user_id, days=30, brand_id=None):
    # Groups responses by date
    # Calculates daily mention count and rate
    # Returns: [{ date, mentions, mention_rate, total_responses }, ...]

# Frontend (PositioningAnalysis.tsx / BrandMentions.tsx)
const { data: mentionTrends } = useQuery({
  queryKey: ['mention-trends'],
  queryFn: async () => {
    const response = await api.get('/analytics/trends/mentions?days=30');
    return response.data;
  }
});

// Renders LineChart with date on X-axis, mention_rate on Y-axis
```

---

## 10. ANALYTICS CACHE SERVICE

### Purpose:
Centralized calculation to avoid redundant metric computations across different endpoints.

### Architecture (app/services/analytics_cache.py):
```python
class AnalyticsCache:
  def __init__(self, db, user_id, brand_id=None, batch_id=None):
    # Filters automatically applied based on context
    
  def calculate_all():
    # Single call calculates all metrics:
    # - brand mentions
    # - positioning breakdown
    # - sentiment breakdown
    # - share of voice
    # - descriptor metrics
    # - competitor threats
    # - trend data
    # Results cached in _cache dict
    
  def get_dashboard_data()
  def get_brand_mentions_data()
  def get_sentiment_data()
  def get_positioning_data()
  def get_share_of_voice_data()
  # Each method returns pre-calculated cached results
```

### Filter Application Logic:
- **For Mentions/Positioning/SOV**: Applies `include_brand_in_query=False`
- **For Sentiment/Descriptors**: Applies `include_brand_in_query=True`
- **For All**: Applies user_id, brand_id, batch_id filters

---

## 11. RELATIONSHIP: WEB APP VIEWS → REPORT GENERATION

### Shared Components:
1. **Metrics Module** (`app/services/metrics.py`)
   - Pure calculation functions used by both:
     - Live dashboard/analytics API endpoints
     - Report generation script
   - Ensures consistency between web views and reports
   - Functions:
     - `calculate_mention_metrics()` - Brand Mentions
     - `calculate_positioning_metrics()` - Positioning
     - `calculate_share_of_voice()` - SOV
     - `calculate_sentiment_metrics()` - Sentiment
     - `calculate_competitor_threats()` - Threats

2. **Chart Generator** (`app/services/chart_generator.py`)
   - Matplotlib-based chart generation for reports
   - Functions for each metric type:
     - `generate_mention_rate_pie_chart()` - Brand Mentions chart
     - `generate_sentiment_pie_chart()` - Sentiment chart
     - `generate_positioning_bar_chart()` - Positioning chart
     - `generate_share_of_voice_chart()` - SOV chart

3. **Data Models** (`app/models.py`)
   - Same Response, Query, BrandInfo tables used by both
   - Guarantees data consistency

4. **AnalyticsCache** (`app/services/analytics_cache.py`)
   - Called by analytics API endpoints
   - Also called during report generation to get latest metrics

### Data Flow for Reports:
```
User clicks "Generate Report"
  ↓
Backend calls generate_report.py (Celery task)
  ↓
Creates AnalyticsCache instance with user_id + brand_id
  ↓
Calls metrics functions to get:
  - mention_metrics
  - positioning_breakdown
  - sentiment_breakdown
  - share_of_voice
  - competitor_threats
  ↓
For each metric:
  - Calls chart_generator function to create matplotlib chart
  - Embeds PNG image path in report markdown
  ↓
Builds markdown report with:
  1. Metrics data
  2. Embedded charts
  3. AI-generated insights and recommendations
  ↓
Exports to multiple formats (DOCX, PDF, etc.)
  ↓
Stores in Report table with markdown content
  ↓
Returns download links to user via API
```

### Consistency Guarantee:
Web app analytics pages and generated reports show identical metrics because they both:
1. Use same data models (Response table)
2. Apply same filtering logic (brand_in_query, mention type)
3. Call same calculation functions (metrics.py)
4. Use same caching strategy (AnalyticsCache)

---

## 12. MULTI-TENANCY & BRAND ISOLATION

### Implementation:
- **User Isolation**: All queries filtered by `user_id`
- **Brand Isolation**: All queries filtered by `brand_id` (when brand selected)
- **Multi-Brand Support**: 
  - User can create up to 20 brands
  - Dashboard/analytics switch to active brand via BrandContext
  - Batch selector allows filtering by collection period

### Filtering Pattern:
```python
# Every API endpoint applies these filters:
query = query.filter(Response.user_id == current_user.id)
if brand_id:
  query = query.filter(Response.brand_id == brand_id)
if batch_id:
  query = query.filter(Response.batch_id == batch_id)
```

---

## 13. KEY INSIGHTS & PATTERNS

### Metric Calculation Philosophy:
1. **Single Source of Truth**: All metrics calculated in `metrics.py` module
2. **Pure Functions**: Functions take Response/Query objects, don't call DB
3. **Caching**: AnalyticsCache calculates once per request
4. **Flexibility**: Same functions used for dashboard, analytics pages, and reports

### Data Quality Considerations:
1. **brand_in_query Flag**: Ensures fair comparison by excluding "guaranteed" mentions
   - Applied to: Brand Mentions, Positioning, Share of Voice
   - NOT applied to: Sentiment, Descriptors
2. **Sentiment on Direct Mentions Only**: More reliable sentiment analysis
3. **Leadership Visibility Tracking**: Distinguishes between quantity (mentions) and quality (positioning)

### Performance:
- AnalyticsCache prevents redundant calculations
- Batch ID filtering enables user to isolate specific collection periods (e.g., individual monthly batches)
- 30-second refetch interval for dashboard (balances freshness vs. load)
- Trend queries calculate on-demand from Response timestamps
- Monthly collection pattern means slower growth of data requiring optimization

### Report Generation:
- Reports capture snapshot of metrics at generation time
- All metrics in reports use same calculation functions as web app
- Charts generated fresh for each report via matplotlib
- Reports stored in DB for historical tracking

---

## Summary: Brand Mentions Treatment

Brand Mentions should be treated identically to Positioning:

1. **Dedicated Analytics Page**: `/analytics/brand-mentions` with `BrandMentions.tsx`
2. **Chart in chart_generator.py**: `generate_mention_rate_pie_chart()` function
3. **Calculation Function**: `calculate_mention_metrics()` in `metrics.py`
4. **Report Section**: Dedicated section in generated reports with chart and table
5. **Filtering**: Excludes `brand_in_query=True` responses (same as Positioning and SOV)
6. **Trend Visualization**: 30-day trend line chart on dedicated page
7. **API Endpoint**: `/analytics/brand-mentions` returning breakdown data

This ensures consistency and parity across the metrics system.

