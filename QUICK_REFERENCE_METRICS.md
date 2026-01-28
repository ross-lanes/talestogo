# TALES Metrics System - Quick Reference Guide

## File Locations

### Backend Core Files
- **Data Models**: `/app/models.py`
- **Metrics Calculations**: `/app/services/metrics.py`
- **Analytics Cache Service**: `/app/services/analytics_cache.py`
- **Chart Generator**: `/app/services/chart_generator.py`
- **API Endpoints**: `/app/routers/analytics.py`
- **Report Generation**: `/generate_report.py`

### Frontend Files
- **API Client**: `/frontend/src/services/api.ts`
- **Dashboard**: `/frontend/src/pages/Dashboard.tsx`

### Analytics Pages
- **Brand Mentions**: `/frontend/src/pages/analytics/BrandMentions.tsx` (CREATE NEW)
- **Positioning**: `/frontend/src/pages/analytics/PositioningAnalysis.tsx`
- **Share of Voice**: `/frontend/src/pages/analytics/ShareOfVoice.tsx`
- **Sentiment**: `/frontend/src/pages/analytics/SentimentAnalysis.tsx`
- **Descriptors**: `/frontend/src/pages/analytics/DescriptorAnalysis.tsx`
- **Threats**: `/frontend/src/pages/analytics/CompetitorThreats.tsx`
- **Recommendations**: `/frontend/src/pages/analytics/Recommendations.tsx`

---

## Key Calculation Functions

### In `metrics.py`:
```
calculate_mention_metrics()           # Brand Mentions breakdown
calculate_positioning_metrics()       # Positioning breakdown  
calculate_positioning_average()       # Average positioning score
calculate_share_of_voice()            # SOV % and competitor comparison
calculate_sentiment_metrics()         # Sentiment distribution
calculate_positive_sentiment_rate()   # % positive mentions
calculate_competitor_threats()        # Threat scores
analyze_descriptors()                 # Descriptor frequency
```

### In `chart_generator.py`:
```
generate_mention_rate_pie_chart()     # Brand Mentions pie chart
generate_sentiment_pie_chart()        # Sentiment pie chart
generate_positioning_bar_chart()      # Positioning bar chart
generate_share_of_voice_chart()       # SOV chart
```

---

## API Endpoints

| Endpoint | Method | Returns | Purpose |
|----------|--------|---------|---------|
| `/analytics/dashboard` | GET | DashboardMetrics | Key metrics for homepage |
| `/analytics/brand-mentions` | GET | Mention breakdown | Brand Mentions page |
| `/analytics/positioning/breakdown` | GET | Positioning breakdown | Positioning Analysis page |
| `/analytics/sentiment/breakdown` | GET | Sentiment breakdown | Sentiment Analysis page |
| `/analytics/share-of-voice` | GET | SOV list | Share of Voice page |
| `/analytics/trends/mentions` | GET | Time series | Trend line charts |
| `/analytics/competitor-threats` | GET | Threats list | Competitor Threats page |

All endpoints accept optional `batch_id` query parameter for filtering.

---

## Frontend Components Pattern

### Standard Analytics Page Structure:
```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import BatchSelector from '../../components/BatchSelector';

export default function MetricPage() {
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  
  const { data, isLoading, error } = useQuery({
    queryKey: ['metric-name', selectedBatchId],
    queryFn: async () => {
      const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
      const response = await api.get('/analytics/endpoint', { params });
      return response.data;
    },
  });
  
  // Chart elements wrapped in useRef for download capability
  const chartRef = useRef<HTMLDivElement>(null);
  
  // Download handler
  const handleDownload = async () => {
    const canvas = await html2canvas(chartRef.current);
    // Save as PNG
  };
  
  return (
    <Box>
      <BatchSelector selectedBatchId={selectedBatchId} onBatchChange={setSelectedBatchId} />
      <Box ref={chartRef}>{/* Chart component */}</Box>
      <Button onClick={handleDownload}>Download Chart</Button>
    </Box>
  );
}
```

---

## Data Filtering Rules

### By Metric Type:

| Metric | Exclude brand_in_query | Direct Mentions Only | Mentions | Include All |
|--------|----------------------|---------------------|----------|------------|
| Brand Mentions | YES | - | Count Yes + Indirect | - |
| Positioning | YES | - | Count Yes + Indirect | - |
| Share of Voice | YES | - | Count Yes + Indirect | - |
| Sentiment | NO | YES | Only count Yes | - |
| Descriptors | NO | YES | Only count Yes | - |
| Threats | YES | - | Computed from SOV | - |

**Notes**:
- "Exclude brand_in_query": Skip responses from queries where brand name appears in query
- "Direct Mentions Only": Only count responses with `brand_mentioned == 'Yes'`
- "Count Yes + Indirect": Include both explicit and indirect mentions

---

## Report Generation Flow

1. User clicks "Generate Report" in CollectAndAnalyze page
2. POST `/reports/generate` → Backend starts Celery task
3. `generate_report.py` execution:
   - Load all user responses from DB
   - Create AnalyticsCache(db, user_id, brand_id)
   - Call cache.calculate_all() for all metrics
   - Generate matplotlib charts via chart_generator
   - Build markdown report with metrics + charts
   - Export to DOCX/PDF
   - Store in Report table
4. User sees download link in Report Archive tab

---

## Routing & Navigation

### App.tsx Routes:
```
/                           → Dashboard (home)
/analytics/brand-mentions   → Brand Mentions page (NEW)
/analytics/positioning      → Positioning Analysis
/analytics/sentiment        → Sentiment Analysis
/analytics/share-of-voice   → Share of Voice
/analytics/descriptors      → Descriptor Analysis
/analytics/threats          → Competitor Threats
/analytics/recommendations  → Strategic Recommendations
/manage/queries             → Manage queries
/manage/competitors         → Manage competitors
/manage/descriptors         → Manage descriptors
/manage/brand-info          → Manage brand
/collect-analyze            → Data collection & analysis
/reports                    → Report archive
```

---

## Database Schema Quick Reference

### Key Fields in Response Table:
```
Response.brand_mentioned    → "Yes" | "Indirect" | "No"
Response.brand_position     → "Leader" | "Featured" | "Top 3" | "Listed" | "Not Mentioned"
Response.sentiment          → "Very Positive" | "Positive" | "Neutral" | "Negative" | "Very Negative"
Response.descriptors        → "Comma, separated, list"
Response.competitors        → "Competitor A, Competitor B"
Response.batch_id           → Links to CollectionBatch for filtering
```

### Key Fields in Query Table:
```
Query.brand_in_query        → Boolean (CRITICAL for filtering!)
Query.query_id              → Identifier (Q001, Q002, etc.)
```

---

## Color Palette (Consistent across web app & reports)

```
Brand Color:        #665775 (Purple)
Primary:            #58A13B (Green)
Secondary:          #80a1d4 (Blue)
Teal:               #75c9c8 (Teal)
Dark Green:         #116C29 (Dark Green)
Orange:             #ffa726 (Orange)
Red:                #E04320 (Red)
Light Red:          #EA4A4A (Light Red)
Periwinkle:         #9FA8DA (Periwinkle)
```

---

## Common Tasks & Code Examples

### 1. Add a new metric to analytics page:
```typescript
// 1. Add useQuery in component
const { data: newMetric } = useQuery({
  queryKey: ['new-metric', selectedBatchId],
  queryFn: async () => {
    const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
    return api.get('/analytics/new-endpoint', { params });
  }
});

// 2. Add endpoint in app/routers/analytics.py
@router.get("/new-endpoint")
def get_new_metric(
  db: Session = Depends(get_db),
  current_user: models.User = Depends(get_current_user),
  brand_id: Optional[int] = Depends(get_active_brand_id),
  batch_id: Optional[int] = None
):
  cache = AnalyticsCache(db, current_user.id, brand_id, batch_id)
  return cache.get_new_metric_data()  # Add method to cache

// 3. Add calculation in AnalyticsCache
def get_new_metric_data(self):
  if not self._calculated:
    self.calculate_all()
  return self._cache['new_metric_data']

// 4. Add pure calculation in metrics.py
def calculate_new_metric(responses, queries):
  # Apply appropriate filters
  # Calculate metric
  # Return dict with results
```

### 2. Download chart as PNG:
```typescript
const chartRef = useRef<HTMLDivElement>(null);

const handleDownload = async () => {
  const canvas = await html2canvas(chartRef.current, {
    backgroundColor: '#ffffff',
    scale: 2,
  });
  const link = document.createElement('a');
  const dateStr = `${month}_${day}_${year}`;
  link.download = `MetricName_${brandName}_${dateStr}.png`;
  link.href = canvas.toDataURL();
  link.click();
};

// In JSX:
<Box ref={chartRef}>{/* Chart goes here */}</Box>
<Button onClick={handleDownload}>Download Chart</Button>
```

### 3. Query with batch filtering:
```typescript
const { data } = useQuery({
  queryKey: ['metric', selectedBatchId],
  queryFn: async () => {
    const params = selectedBatchId ? { batch_id: selectedBatchId } : {};
    return api.get('/analytics/endpoint', { params });
  }
});
```

---

## Performance Notes

- **AnalyticsCache**: Calculates all metrics once per request, stores in memory
- **30-second refetch**: Dashboard auto-refreshes every 30 seconds (configurable)
- **Trend data**: Calculated on-demand from Response table (not pre-cached)
- **Monthly collections**: Data grows slowly, performance should remain good

---

## Testing Checklist for New Metric

- [ ] Calculation function returns expected values
- [ ] Filtering (brand_in_query, mention type) applied correctly
- [ ] Analytics page displays data and chart
- [ ] Batch selector filters data properly
- [ ] Download as PNG works
- [ ] Report section includes metric
- [ ] Report chart generates via matplotlib
- [ ] Data in web app matches report values
- [ ] Multi-tenant filtering (user_id, brand_id) works
- [ ] Error handling for empty data sets

---

## Key Insights

1. **Brand Mentions == Positioning in treatment**: Both get dedicated pages, charts, reports, and use same filtering
2. **Sentiment is unique**: Includes all queries, not just those without brand in query
3. **AnalyticsCache is your friend**: Use it for all metric calculations to avoid redundancy
4. **Pure functions in metrics.py**: Database operations happen in AnalyticsCache, not metrics.py
5. **Filtering consistency**: Same filters must be applied in web app AND report generation
6. **Monthly data pattern**: Don't over-optimize for real-time; monthly batch processing is the use case

