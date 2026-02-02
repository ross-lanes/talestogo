# Brand Data Files

This directory contains exported brand data for PPPL deployment.

## Current Files

- `pppl_brand.json` - Princeton Plasma Physics Laboratory brand data
  - Converted from November 2025 export
  - Contains 22 queries, 17 competitors, 88 responses, 4 reports
  - **For latest data, re-export from production** (see below)

## Updating Brand Data

To get the latest brand data from production:

1. Set the production DATABASE_URL:
   ```bash
   export DATABASE_URL="postgresql://tales_3bh3_user:PASSWORD@dpg-d418u6be5dus738o7d0g-a.oregon-postgres.render.com/tales_3bh3"
   ```

2. Export PPPL brand:
   ```bash
   python scripts/admin/export_brand_data.py \
     --brand "Princeton Plasma Physics Laboratory" \
     --output deployment-kit-pppl/data/pppl_brand.json
   ```

3. Export Princeton Engineering brand (if needed):
   ```bash
   python scripts/admin/export_brand_data.py \
     --brand "Princeton Engineering" \
     --output deployment-kit-pppl/data/princeton_engineering_brand.json
   ```

## Data Structure

Each JSON file contains:
- `export_info` - Export metadata (timestamp, source, version)
- `brand` - Brand configuration (name, description, strategic messages)
- `queries` - Monitoring queries with categories and priorities
- `competitors` - Tracked competitor organizations
- `descriptors` - Target descriptors/positioning terms
- `responses` - LLM responses with analysis data
- `reports` - Generated analysis reports
