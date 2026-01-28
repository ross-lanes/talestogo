# How Tales Works Page - Implementation Summary

## What Was Created

A new page called "How Tales Works" has been added to the Tales platform that explains the methodology behind the AI reputation analysis. This page is accessible from the user menu dropdown (click on your initial icon in the upper right corner).

## Changes Made

### 1. Created New Component
**File:** `frontend/src/pages/HowTalesWorks.tsx`
- Comprehensive methodology page with all sections from the Analysis Methodology document
- Content updated to be brand-agnostic (uses "your brand" instead of "Physics of Plasmas")
- Nicely formatted with Material-UI components including:
  - Typography with proper hierarchy
  - Paper components for section containers
  - Tables for calculation details
  - Color-coded sections with primary/secondary colors
  - Formula boxes with monospace fonts
  - Examples and explanatory text

### 2. Added Route
**File:** `frontend/src/App.tsx`
- Imported the HowTalesWorks component
- Added route: `/how-tales-works`
- Route is protected (requires authentication)
- Wrapped in Layout component for consistent navigation

### 3. Added Menu Item
**File:** `frontend/src/components/Layout.tsx`
- Imported InfoIcon from Material-UI icons
- Added `handleHowTalesWorks()` function to navigate to the page
- Added "How Tales Works" menu item to the user dropdown menu
- Positioned above "Settings" in the menu
- Uses Info icon for visual clarity

## Content Sections

The "How Tales Works" page includes:

1. **Data Collection Methods**
   - Explains multi-platform AI querying
   - Describes visibility tests
   - Notes about priority levels not affecting calculations

2. **Analytical Framework**
   - Two-stage analysis process
   - Structured data extraction
   - AI-powered insight generation

3. **Key Performance Metrics**
   - List of all metrics with descriptions
   - Platform segmentation explanation

4. **Mathematical Formulas for Metric Calculations**
   - Brand Mentions (Mention Rate) - with formula and table
   - Positioning Score - with scoring system table
   - Share of Voice - with calculation details
   - Target Descriptor Adoption - with matching logic
   - Competitive Threat Analysis - explains qualitative approach
   - Summary table comparing all metrics

5. **Competitive Intelligence Analysis**
   - Competitor tracking methodology
   - Co-occurrence analysis
   - Competitive gap identification

6. **Recommendations Generation**
   - AI-driven synthesis process
   - Gap analysis approach
   - Actionable recommendations structure

7. **Limitations and Considerations**
   - Important caveats about the analysis
   - Temporal nature of findings
   - Correlation vs. causation notes

## How to Access

1. Log into the Tales platform
2. Click on your initial icon in the upper right corner (the avatar with your first letter)
3. Select "How Tales Works" from the dropdown menu
4. The page will open showing the complete methodology

## Technical Details

- **Component Type:** React functional component using TypeScript
- **Styling:** Material-UI (MUI) v5 components with custom sx props
- **Layout:** Responsive with max-width container
- **Tables:** Properly formatted with TableContainer, Table, TableHead, TableBody
- **Typography:** Hierarchical headings (h4, h5, h6) with body text
- **Colors:** Uses theme colors (primary.main, secondary.main, text.secondary)
- **Accessibility:** Proper semantic HTML and ARIA-compliant MUI components

## Testing

The implementation has been tested by:
- Running the development server (confirmed no compilation errors)
- Verifying TypeScript type checking passes
- Confirming the route is properly configured
- Ensuring the menu item appears in the user dropdown

## Development Server

The frontend is currently running at: http://localhost:5175/
