# PPPL Data Migration Plan

## Overview

This plan describes how to export existing PPPL data from the production Tales instance and import it into PPPL's self-hosted deployment.

## What Data Would Be Migrated

| Data Type | Description | Estimated Volume |
|-----------|-------------|------------------|
| Brand | PPPL brand configuration (name, aliases, description) | 1 record |
| Queries | Questions asked about PPPL to AI platforms | ~20-50 records |
| Competitors | Other labs/organizations tracked | ~5-10 records |
| Descriptors | Key terms tracked in responses | ~10-20 records |
| Responses | Raw AI responses collected | Hundreds to thousands |
| Analysis Results | Sentiment, mentions, positioning data | Same as responses |
| Reports | Generated report content (if any) | 0-10 records |

## Migration Approach

### Option A: JSON Export/Import (Recommended)

**Pros:**
- Human-readable, can be reviewed before import
- Portable across database types (SQLite, PostgreSQL)
- Can be version controlled
- Easy to edit if needed

**Cons:**
- Requires custom export/import scripts

**Process:**
1. Create `scripts/admin/export_brand_data.py` that:
   - Takes a brand name as input
   - Exports all related data to a JSON file
   - Preserves relationships but uses portable references (not database IDs)

2. Create `scripts/admin/import_brand_data.py` that:
   - Reads the JSON export file
   - Creates records in the new database
   - Assigns data to the admin user who runs the import
   - Handles ID remapping automatically

### Option B: PostgreSQL Dump (Alternative)

**Pros:**
- Uses native PostgreSQL tools
- Faster for large datasets
- Exact data preservation

**Cons:**
- Only works if both systems use PostgreSQL
- Requires careful handling of foreign keys and user associations
- Less portable

---

## Recommended Implementation: JSON Export/Import

### Export Script (`scripts/admin/export_brand_data.py`)

```
Usage: python scripts/admin/export_brand_data.py --brand "Princeton Plasma Physics Laboratory" --output pppl_data.json
```

The script would:
1. Connect to production database
2. Find the brand by name
3. Export in this structure:

```json
{
  "export_info": {
    "exported_at": "2026-01-25T12:00:00Z",
    "source_system": "Tales Production",
    "tales_version": "1.0.0"
  },
  "brand": {
    "name": "Princeton Plasma Physics Laboratory",
    "description": "...",
    "aliases": ["PPPL", "Princeton Plasma Lab"]
  },
  "queries": [
    {
      "text": "What is PPPL known for?",
      "category": "General",
      "priority": "high",
      "is_active": true
    }
  ],
  "competitors": [
    {"name": "Oak Ridge National Laboratory"},
    {"name": "Lawrence Livermore National Laboratory"}
  ],
  "descriptors": [
    {"term": "fusion research", "category": "positive"},
    {"term": "plasma physics", "category": "neutral"}
  ],
  "responses": [
    {
      "query_text": "What is PPPL known for?",
      "platform": "gemini",
      "response_text": "Princeton Plasma Physics Laboratory is...",
      "collected_at": "2026-01-15T10:30:00Z",
      "analysis": {
        "mentioned": "yes",
        "mention_type": "direct",
        "sentiment": "positive",
        "position": "leader",
        "competitors_mentioned": ["Oak Ridge"],
        "descriptors_found": ["fusion research"]
      }
    }
  ],
  "reports": [
    {
      "title": "PPPL Monthly Report - January 2026",
      "content": "...",
      "generated_at": "2026-01-20T14:00:00Z"
    }
  ]
}
```

### Import Script (`scripts/admin/import_brand_data.py`)

```
Usage: docker compose exec app python scripts/admin/import_brand_data.py --file pppl_data.json
```

The script would:
1. Verify the admin user is logged in (or prompt for admin email)
2. Validate the JSON structure
3. Create records in order (brand first, then queries, etc.)
4. Remap all relationships to new IDs
5. Assign the brand to the importing admin user
6. Report success/failure counts

---

## Migration Steps for PPPL

### On Production (before handoff):

1. Run export script:
   ```bash
   python scripts/admin/export_brand_data.py \
     --brand "Princeton Plasma Physics Laboratory" \
     --output pppl_data.json
   ```

2. Include `pppl_data.json` in the deployment kit

### At PPPL (after deployment):

1. Deploy Tales using the deployment kit
2. Create initial admin account
3. Run import script:
   ```bash
   docker compose exec app python scripts/admin/import_brand_data.py --file pppl_data.json
   ```
4. Verify data in the UI
5. Configure LLM providers to continue collecting new data

---

## Data Ownership Considerations

| Issue | Solution |
|-------|----------|
| Original user IDs don't exist | Assign all data to the importing admin |
| Brand sharing settings | Reset to private (PPPL-only) |
| Scheduled tasks | Not migrated (PPPL sets up their own) |
| User accounts | Not migrated (PPPL creates their own users) |

---

## Estimated Development Effort

| Task | Effort |
|------|--------|
| Export script | 2-3 hours |
| Import script | 3-4 hours |
| Testing with real data | 1-2 hours |
| Documentation | 1 hour |
| **Total** | **7-10 hours** |

---

## Alternative: Manual Recreation

If the data volume is small enough, PPPL could manually recreate:
- Brand configuration (5 minutes)
- Queries (10-30 minutes depending on count)
- Competitors and descriptors (5-10 minutes)

However, **historical responses cannot be manually recreated** since they represent actual AI outputs at specific points in time. If preserving this historical data is important, the export/import scripts are necessary.

---

## Recommendation

**Implement Option A (JSON Export/Import)** because:
1. PPPL has significant historical response data worth preserving
2. The scripts are reusable for other lab deployments
3. JSON format is transparent and auditable
4. Works regardless of database configuration (SQLite or PostgreSQL)

The export file becomes part of the deployment kit specifically for PPPL (or any lab with existing data).
