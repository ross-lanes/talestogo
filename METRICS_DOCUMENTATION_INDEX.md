# TALES Metrics System - Documentation Index

This directory contains comprehensive documentation of the TALES metrics system architecture and implementation.

## Documents Included

### 1. **METRICS_ARCHITECTURE_SUMMARY.md** (Primary Document)
Comprehensive 13-section analysis covering:
- Executive overview with data collection frequency notes
- Detailed breakdown of all 4 core metrics (Brand Mentions, Positioning, SOV, Sentiment)
- Data models and schema
- API endpoints and data flow
- Charting libraries (Recharts frontend, Matplotlib backend)
- State management and React Query patterns
- Report generation architecture
- Complete UI structure for all analytics pages
- Time-series trend tracking
- Analytics Cache Service design
- Web app to report generation relationship
- Multi-tenancy and brand isolation
- Key insights and patterns

**Use this for**: Understanding the complete system, design decisions, and implementation details.

### 2. **QUICK_REFERENCE_METRICS.md** (Developer Guide)
Quick-access reference with:
- File locations for all backend and frontend code
- Key calculation functions
- API endpoints table
- Frontend components pattern
- Data filtering rules by metric type
- Report generation flow
- Routing and navigation
- Database schema reference
- Color palette
- Common tasks with code examples
- Performance notes
- Testing checklist

**Use this for**: Daily development work, quick lookups, and code examples.

---

## Key Points to Remember

### Brand Mentions Implementation
- **NEW dedicated analytics page needed**: `/analytics/brand-mentions`
- **NEW frontend component needed**: `BrandMentions.tsx`
- **Uses existing calculation**: `calculate_mention_metrics()` in `metrics.py`
- **Filtering rule**: Excludes `brand_in_query=True` (same as Positioning & SOV)
- **Treatment**: Identical to Positioning in all respects
  - Dedicated analytics page with pie chart + trend chart
  - Dedicated report section with matplotlib chart
  - Full batch filtering support
  - PNG download capability

### Data Collection Model
- **Primary**: Monthly collections via scheduled batches
- **Secondary**: Optional ad-hoc manual collections on specific days
- **Performance**: Slower growth pattern - optimization not critical

### Core Architecture Principles
1. **Single source of truth**: All metrics in `metrics.py`
2. **Pure functions**: No DB calls in metrics module
3. **Centralized caching**: `AnalyticsCache` prevents redundant calculations
4. **Consistent filtering**: Same rules applied in web app AND reports
5. **Shared infrastructure**: Web app pages use same metrics as report generation

### Critical Filtering Rules
| Metric | Exclude brand_in_query | Direct Mentions | Behavior |
|--------|---|---|---|
| Brand Mentions | YES | No | Count Yes + Indirect |
| Positioning | YES | No | Count Yes + Indirect |
| SOV | YES | No | Count Yes + Indirect |
| Sentiment | NO | YES | Only Yes mentions |
| Descriptors | NO | YES | Only Yes mentions |

---

## File Structure

```
TALES Project Root/
├── METRICS_ARCHITECTURE_SUMMARY.md  ← Main reference
├── QUICK_REFERENCE_METRICS.md       ← Developer guide
├── METRICS_DOCUMENTATION_INDEX.md   ← This file
│
├── app/
│   ├── models.py                    ← Response, Query, BrandInfo schemas
│   ├── services/
│   │   ├── metrics.py               ← All calculation functions
│   │   ├── analytics_cache.py        ← Caching service
│   │   └── chart_generator.py        ← Matplotlib charts for reports
│   └── routers/
│       └── analytics.py              ← API endpoints
│
├── frontend/src/
│   ├── services/
│   │   └── api.ts                   ← Axios API client
│   ├── pages/
│   │   ├── Dashboard.tsx            ← Home page metrics
│   │   ├── CollectAndAnalyze.tsx    ← Data collection & reports
│   │   └── analytics/
│   │       ├── BrandMentions.tsx    ← [NEW FILE NEEDED]
│   │       ├── PositioningAnalysis.tsx
│   │       ├── ShareOfVoice.tsx
│   │       ├── SentimentAnalysis.tsx
│   │       ├── DescriptorAnalysis.tsx
│   │       ├── CompetitorThreats.tsx
│   │       └── Recommendations.tsx
│   └── components/
│       └── BatchSelector.tsx        ← Filter by collection batch
│
└── generate_report.py               ← Report generation script
```

---

## Implementation Checklist for Brand Mentions

If Brand Mentions is not yet fully implemented as a dedicated page, follow this checklist:

### Frontend
- [ ] Create `/frontend/src/pages/analytics/BrandMentions.tsx`
  - [ ] Import useQuery, BatchSelector, Recharts
  - [ ] Create chart ref for PNG download
  - [ ] Query `/analytics/brand-mentions` endpoint
  - [ ] Display pie chart (Yes/Indirect/No)
  - [ ] Display metric cards (count, rate %)
  - [ ] Display 30-day trend line chart
  - [ ] Add batch selector
  - [ ] Add PNG download button

### Backend - Metrics Module
- [ ] Verify `calculate_mention_metrics()` exists and is correct in `metrics.py`
- [ ] Check filtering excludes `brand_in_query=True`
- [ ] Test calculation with sample data

### Backend - Cache Service
- [ ] Add `_calculate_brand_mentions()` method to `AnalyticsCache`
- [ ] Add `get_brand_mentions_data()` method to return cached results
- [ ] Call from `calculate_all()`

### Backend - Chart Generator
- [ ] Add `generate_mention_rate_pie_chart()` function to `chart_generator.py`
- [ ] Implement pie chart showing Yes/Indirect/No distribution
- [ ] Use TALES color palette

### Backend - API Endpoint
- [ ] Add `@router.get("/brand-mentions")` to `/app/routers/analytics.py`
- [ ] Call `AnalyticsCache.get_brand_mentions_data()`
- [ ] Support `batch_id` query parameter

### Frontend - Routing
- [ ] Add route in `App.tsx`: `/analytics/brand-mentions` → `BrandMentions`

### Report Generation
- [ ] Update `generate_report.py` to include Brand Mentions section
- [ ] Call `chart_generator.generate_mention_rate_pie_chart()`
- [ ] Insert into report markdown with explanatory text
- [ ] Add to report export (DOCX/PDF)

### Testing
- [ ] [ ] Run pytest on metrics calculation
- [ ] [ ] Test API endpoint with/without batch_id
- [ ] [ ] Verify frontend displays correctly
- [ ] [ ] Test PNG download
- [ ] [ ] Verify report includes Brand Mentions section
- [ ] [ ] Compare web app metrics with report metrics (should match)

---

## Common Integration Points

### Adding New Query Parameter
```python
# In app/routers/analytics.py
@router.get("/new-endpoint")
def get_new_metric(..., new_param: Optional[str] = None):
    # Use new_param in cache initialization
```

### Adding to Dashboard
```typescript
// In Dashboard.tsx
const { data: newMetric } = useQuery({
  queryKey: ['new-metric'],
  queryFn: () => api.get('/analytics/new-endpoint')
});
```

### Adding to Report
```python
# In generate_report.py
metrics = cache.calculate_all()
chart_path = generate_new_metric_chart(metrics)
report += f"\n## New Metric Section\n"
report += f"![New Metric]({chart_path})\n"
```

---

## Performance Characteristics

| Operation | Performance | Notes |
|-----------|-------------|-------|
| Dashboard metrics | ~100ms | Cached in single AnalyticsCache call |
| Analytics page load | ~200ms | API call + React render |
| Trend calculation | ~300-500ms | Groups responses by date (on-demand) |
| Report generation | ~2-5s | Generates charts + markdown + exports |
| Monthly batch | ~50K-500K rows | Performance remains good |

---

## Future Enhancements

1. **Pre-calculated trends**: Store daily aggregates in Trend table to speed up trend queries
2. **Chart upload**: Frontend can upload charts to report instead of regenerating in matplotlib
3. **Custom date ranges**: Allow filtering by date range in addition to batch ID
4. **Comparative analysis**: Compare metrics across multiple batches
5. **Export templates**: Custom report templates (PDF, HTML, PPTX)

---

## Support & Questions

For questions about:
- **System architecture**: See METRICS_ARCHITECTURE_SUMMARY.md sections 1-13
- **Implementation details**: See QUICK_REFERENCE_METRICS.md
- **Specific file locations**: See QUICK_REFERENCE_METRICS.md File Locations section
- **Code examples**: See QUICK_REFERENCE_METRICS.md Common Tasks section

---

**Last Updated**: November 4, 2025
**Scope**: Complete metrics system analysis including data collection patterns and Brand Mentions implementation guidance

