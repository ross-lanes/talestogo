# Brand Data Files

This directory contains exported brand data for PPPL deployment.

## Current Files

- `pppl_brand.json` - Princeton Plasma Physics Laboratory brand data
  - Exported February 2026 from Railway production database
  - Contains 22 queries, 17 competitors, 352 responses, 8 reports
  - **For latest data, re-export from production** (see below)

## Updating Brand Data

To get the latest brand data from production:

1. Set the production DATABASE_URL (get from Railway dashboard):
   ```bash
   export DATABASE_URL="postgresql://..."
   ```

2. Export PPPL brand:
   ```bash
   python scripts/admin/export_brand_data.py \
     --brand "Princeton Plasma Physics Laboratory" \
     --output deployment-kit-pppl/data/pppl_brand.json
   ```

## Data Structure

The JSON file contains:
- `export_info` - Export metadata (timestamp, source, version)
- `brand` - Brand configuration (name, description, strategic messages)
- `queries` - Monitoring queries with categories and priorities
- `competitors` - Tracked competitor organizations
- `descriptors` - Target descriptors/positioning terms
- `responses` - LLM responses with analysis data
- `reports` - Generated analysis reports
