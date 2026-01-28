# Automatic Chart Capture for Reports - Implementation Guide

## Overview
This system automatically captures charts from the TALES website after data analysis completes and saves them as PNG files for use in Word document reports.

## Current Status

### ✅ Already Implemented
1. **Backend API Endpoint**: `/reports/upload-charts` (app/routers/reports.py, line 98)
   - Receives base64 chart images
   - Saves them with predictable naming: `{user_id}_{brand_id}_latest_{chart_name}.png`
   - Stores in `frontend/public/report_charts/`

2. **Backend Chart Detection**: `check_for_uploaded_charts()` (app/services/chart_generator.py, line 53)
   - Report generation checks for uploaded charts before generating new ones
   - If uploaded charts exist and are < 60 minutes old, they're used instead of matplotlib-generated charts

3. **Frontend Chart Capture Utility**: `captureAndUploadCharts()` (frontend/src/utils/chartCapture.ts, line 85)
   - Uses html2canvas to capture rendered charts
   - Converts to base64
   - Uploads to backend API
   - Fully implemented and ready to use

## What Still Needs to Be Done

### Step 1: Add IDs to Chart Containers in Dashboard

**File**: `frontend/src/pages/Dashboard.tsx`

Add `id` attributes to the chart container `<Paper>` elements:

```tsx
// Around line 467 - Sentiment Chart
<Paper id="dashboard-sentiment-chart" sx={{ p: 3, height: 300, border: '1px solid #e0e0e0', boxShadow: 'none' }}>

// Around line 520 - Positioning Chart
<Paper id="dashboard-positioning-chart" sx={{ p: 3, height: 300, border: '1px solid #e0e0e0', boxShadow: 'none' }}>

// Around line 593 - Share of Voice Chart
<Paper id="dashboard-sov-chart" sx={{ p: 3, height: 300, border: '1px solid #e0e0e0', boxShadow: 'none' }}>
```

Also add an ID to the main dashboard container:
```tsx
// Around line 269 - Main dashboard reference
<Box ref={dashboardRef} id="dashboard-main" sx={{ ...}}>
```

### Step 2: Trigger Chart Capture After Analysis Completes

**File**: `frontend/src/pages/Dashboard.tsx`

**Import the utility** at the top of the file (around line 18):
```tsx
import { captureAndUploadCharts } from '../utils/chartCapture';
```

**Add automatic capture** in the analysis mutation's onSuccess handler (around line 230-240):

```tsx
onSuccess: async (data) => {
  setSnackbar({
    open: true,
    message: data.message + ' ' + (data.note || ''),
    severity: 'info',
  });

  // Wait for charts to render
  setTimeout(async () => {
    queryClient.invalidateQueries({ queryKey: ['dashboard-metrics'] });
    queryClient.invalidateQueries({ queryKey: ['responses'] });

    // Automatically capture and upload charts for report generation
    try {
      console.log('📸 Auto-capturing charts after analysis...');
      const result = await captureAndUploadCharts(
        {
          dashboard: 'dashboard-main',
          sentiment: 'dashboard-sentiment-chart',
          positioning: 'dashboard-positioning-chart',
          share_of_voice: 'dashboard-sov-chart',
        },
        api
      );

      if (result.success) {
        console.log('✅ Charts captured and uploaded for reports');
      } else {
        console.warn('⚠️ Chart capture incomplete:', result.message);
      }
    } catch (error) {
      console.error('❌ Error auto-capturing charts:', error);
      // Don't show error to user - this is a background process
    }
  }, 3000); // Wait 3 seconds for charts to fully render
},
```

### Step 3: Test the Implementation

1. **Start a Data Collection**:
   - Go to Dashboard
   - Click "Run Collection"
   - Wait for collection to complete

2. **Run Analysis**:
   - Click "Run Analysis"
   - Wait for analysis to complete
   - Check browser console for chart capture messages

3. **Verify Charts Were Uploaded**:
   ```bash
   ls -la frontend/public/report_charts/
   ```
   - Should see files like `2_3_latest_dashboard.png`, `2_3_latest_sentiment.png`, etc.

4. **Generate a Report**:
   ```bash
   PYTHONPATH=/Users/rachelkremen/Documents/Code/tales_project python scripts/admin/generate_report.py --user-id 2 --brand-id 3
   ```
   - Check console output for "Using uploaded X chart from frontend"
   - Download the Word document
   - Verify charts appear correctly in Word

## Chart Naming Convention

**Frontend chart names** (what you pass to `captureAndUploadCharts`):
- `dashboard` - Main dashboard/key metrics
- `sentiment` - Sentiment pie chart
- `positioning` - Positioning bar chart
- `share_of_voice` - Share of voice chart

**Backend expects these names** (app/routers/reports.py, line 123):
- `dashboard`, `sentiment`, `positioning`, `share_of_voice`

**Backend saves as** (line 142):
- `{user_id}_{brand_id}_latest_dashboard.png`
- `{user_id}_{brand_id}_latest_sentiment.png`
- `{user_id}_{brand_id}_latest_positioning.png`
- `{user_id}_{brand_id}_latest_share_of_voice.png`

**Backend report generation looks for** (app/services/chart_generator.py, line 75):
- Maps `dashboard` → `mention_rate` (used in reports)
- Maps `sentiment` → `sentiment`
- Maps `positioning` → `positioning`
- Maps `share_of_voice` → `share_of_voice`

## How It Works (Full Flow)

1. **User runs analysis** → Analysis completes
2. **Dashboard component** → Waits 3 seconds for charts to render
3. **captureAndUploadCharts()** → Captures each chart as PNG using html2canvas
4. **POST /reports/upload-charts** → Uploads base64 images to backend
5. **Backend saves PNGs** → Stores in `frontend/public/report_charts/`
6. **User generates report** → Report generation script runs
7. **check_for_uploaded_charts()** → Finds uploaded charts (< 60 min old)
8. **Report uses uploaded charts** → Instead of generating new matplotlib charts
9. **Charts embedded in Word doc** → Via base64 or file reference

## Benefits

- **Higher quality charts**: Actual rendered charts from the website
- **Consistent branding**: Charts match exactly what users see on the site
- **Automatic process**: No manual intervention required
- **Fallback system**: If upload fails, matplotlib charts are still generated

## Troubleshooting

**Charts not appearing in reports:**
1. Check `frontend/public/report_charts/` for PNG files
2. Verify filenames match pattern: `{user_id}_{brand_id}_latest_*.png`
3. Check chart age (must be < 60 minutes)
4. Look at report generation console output for "Using uploaded" messages

**Charts not being captured:**
1. Check browser console for capture errors
2. Verify element IDs are correct
3. Ensure charts are visible/rendered before capture
4. Check network tab for upload API call

**Upload failing:**
1. Check backend logs for errors
2. Verify `frontend/public/report_charts/` directory exists and is writable
3. Check API authentication
