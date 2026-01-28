# How Tales Works - Download Feature Implementation

## Summary

Added a "Download as Word" button to the How Tales Works page that allows users to export the methodology documentation as a Word document (.docx).

## Changes Made

### 1. Frontend Component Update
**File:** `frontend/src/pages/HowTalesWorks.tsx`

**Changes:**
- Removed the subtitle "AI Reputation Intelligence Methodology"
- Added a "Download as Word" button in the page header
- Button positioned in the upper right, next to the page title
- Implemented download handler that calls the backend API
- Uses Material-UI Download icon
- Shows error alert if download fails

**Button Styling:**
- Purple (secondary.main) background color
- Hover effect with darker purple
- Download icon on the left side of button text

### 2. Backend API Endpoint
**File:** `app/main.py`

**New Endpoint:**
```
GET /api/export/how-tales-works/word
```

**Features:**
- Requires authentication (uses `get_current_user` dependency)
- Contains the complete "How Tales Works" methodology content in markdown format
- Uses existing `export_to_word` function from `app/services/report_export.py`
- Returns Word document (.docx) as StreamingResponse
- Filename: `How_Tales_Works.docx`

**Content Included:**
- Data Collection Methods
- Analytical Framework
- Key Performance Metrics
- Mathematical Formulas for Metric Calculations
  - Brand Mentions (Mention Rate)
  - Positioning Score
  - Share of Voice
  - Target Descriptor Adoption
  - Competitive Threat Analysis
  - Summary table
- Competitive Intelligence Analysis
- Recommendations Generation
- Limitations and Considerations

All content is brand-agnostic (uses "your brand" instead of specific brand names).

## How It Works

### User Flow:
1. User navigates to "How Tales Works" page from user menu dropdown
2. User clicks "Download as Word" button in upper right
3. Frontend makes GET request to `/api/export/how-tales-works/word`
4. Backend generates Word document from markdown content
5. Document is streamed back to the browser
6. Browser automatically downloads `How_Tales_Works.docx`

### Technical Details:
- Frontend uses axios with `responseType: 'blob'` to handle binary data
- Creates temporary URL using `window.URL.createObjectURL`
- Programmatically clicks hidden download link
- Cleans up temporary URL after download

## Testing

Both servers are running and ready to test:
- **Frontend:** http://localhost:5175/
- **Backend:** http://127.0.0.1:8000

To test:
1. Log into Tales
2. Click your initial icon (upper right)
3. Select "How Tales Works"
4. Click "Download as Word" button
5. Word document should download automatically

## File Structure

```
/Users/rachelkremen/Documents/Code/tales_project/
├── frontend/src/pages/
│   └── HowTalesWorks.tsx (updated with download button)
└── app/
    ├── main.py (new endpoint added)
    └── services/
        └── report_export.py (existing export_to_word function used)
```

## Dependencies

No new dependencies required - uses existing:
- `python-docx` (already in requirements.txt)
- `axios` (already in frontend)
- Material-UI components (already in frontend)

## Notes

- The download functionality reuses the existing Word export infrastructure used for reports
- Content is embedded directly in the endpoint (not pulled from database) to ensure consistency
- All markdown formatting (headers, tables, lists, bold text) is properly converted to Word format
- The endpoint requires authentication, so only logged-in users can download
