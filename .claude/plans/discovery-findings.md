# NSTXView Outlier Detection - Phase 1 Discovery Findings

**Date**: 2024-12-04
**Database**: DEV (postgresql://...hopper.proxy.rlwy.net:32217/railway)
**Status**: Discovery Complete ✅

## Executive Summary

Discovery phase successfully completed on DEV database. Found **2,136 parameter measurements** across ~90 papers with several clear outliers that exceed NSTX/NSTX-U machine capabilities by orders of magnitude.

**Critical Finding**: Database already has `created_at` timestamp field (defaults to `now()`) but NO batch tracking system yet.

## Database Schema

### Key Tables Identified

1. **`nstx_parameters`** - Contains all extracted parameter measurements
2. **`nstx_papers`** - Contains paper metadata including DOI
3. **`nstx_shots`** - Links parameters to specific shots
4. **`nstx_phenomena`** - Extracted phenomena data

### nstx_parameters Schema

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | integer | NO | Primary key |
| paper_id | integer | NO | FK to nstx_papers |
| shot_id | integer | YES | FK to nstx_shots (optional) |
| **parameter_name** | varchar | NO | ✅ Parameter identifier |
| **parameter_category** | varchar | YES | ✅ Category (operational/plasma/performance) |
| **value** | double precision | YES | ✅ Numeric value |
| value_min | double precision | YES | Range minimum |
| value_max | double precision | YES | Range maximum |
| **unit** | varchar | YES | ✅ Unit of measurement |
| normalized_value | double precision | YES | Normalized version |
| normalized_unit | varchar | YES | Normalized unit |
| uncertainty | double precision | YES | Measurement uncertainty |
| **context** | text | YES | ✅ Source paragraph text |
| **page_number** | integer | YES | ✅ Page in paper |
| **created_at** | timestamp | YES | ✅ Extraction timestamp |

✅ **All required fields for outlier detection are present!**

### nstx_papers Schema

| Column | Type | Notes |
|--------|------|-------|
| id | integer | Primary key |
| **title** | varchar | ✅ Paper title |
| **doi** | varchar | ✅ DOI for linking |
| authors | text | Author list |
| abstract | text | Abstract |
| journal | varchar | Publication venue |
| publication_date | date | Publication date |
| status | varchar | Processing status |
| created_at | timestamp | When added |
| updated_at | timestamp | Last modified |

✅ **Has DOI field for report links!**

## Current Data Ranges

### ⚠️ MAJOR OUTLIERS IDENTIFIED

| Parameter | Current Max | NSTX-U Max | Outlier Factor | Issue |
|-----------|-------------|------------|----------------|-------|
| **Plasma Current** | 35.3 MA | 2.0 MA | **17.6x** | Likely 35,300 A mislabeled as MA |
| **Toroidal Field** | 5.6 T | 1.0 T | **5.6x** | Reference to other machine |
| **NBI Power** | 42 MW | 15 MW | **2.8x** | Reference to other machine |
| **RF Power** | 100 MW | 6 MW | **16.7x** | Reference to other machine |
| **Total Heating** | 100 MW | 21 MW | **4.8x** | Reference to other machine |
| **Electron Temp** | 4000 eV | ~5000 eV | **0.8x** | Just under reactor temps |
| **Ion Temp** | 1900 eV | ~5000 eV | **0.38x** | Possibly valid but high |
| **Electron Temp (keV)** | 20 keV | ~5 keV | **4x** | Likely reactor reference |
| **Ion Temp (keV)** | 50 keV | ~15 keV | **3.3x** | Likely reactor reference |
| **Stored Energy** | 350 MJ | ~0.5 MJ | **700x** | Definitely wrong scale |
| **Fusion Power** | 60 MW | 0 MW | **∞** | NSTX doesn't produce fusion! |

### Unit Inconsistencies Detected

1. **Electron Density**:
   - Has values in: m^-3, cm^-3, 10^19 m^-3, 10^20 m^-3, 10^13 cm^-3, 10^12 cm^-3
   - One outlier: m^-4 (wrong dimension!)

2. **Beta_N**:
   - Mix of dimensionless, %, and weird units like "% m T/MA" and "% m T MA^-1"

3. **Internal Inductance (li)**:
   - Should be dimensionless
   - No wrong-unit instances found (good!)

## Measurements by Category

| Category | Count | Avg per Paper |
|----------|-------|---------------|
| Operational | 976 | ~11 |
| Plasma | 892 | ~10 |
| Performance | 268 | ~3 |
| **Total** | **2,136** | **~24** |

## Missing Infrastructure

### ❌ No Batch Tracking System
- No `batch_id` column in nstx_parameters
- No `ingestion_batches` table
- Cannot identify when parameters were added
- **Need to add**: Batch tracking for reprocessing capability

### ❌ No Outlier Tracking Columns
- No `is_outlier` column
- No `outlier_reason` column
- No `flagged_at` timestamp
- No `reviewed` status
- **Need to add**: Full outlier tracking system

### ❌ No Threshold Management
- No `parameter_thresholds` table
- No `threshold_history` table
- **Need to add**: Threshold configuration and history

## Specific Outlier Examples

### Plasma Current Outliers
```
Value: 35.3 MA (vs. NSTX-U max: 2.0 MA)
Likely cause: 35,300 A = 35.3 kA = 0.0353 MA (decimal point error)
Count: Need to query individual records
```

### Toroidal Field Outliers
```
Value: 5.6 T (vs. NSTX-U max: 1.0 T)
Likely cause: Reference to ITER or other machine
```

### Fusion Power - ALL Invalid
```
All fusion power values are invalid for NSTX
NSTX/NSTX-U does not produce measurable fusion power
These are projections or references to other machines
Count: 6 total (all should be flagged)
```

### Stored Energy Scale Error
```
Value: 350 MJ (vs. NSTX typical: ~200 kJ = 0.2 MJ)
Likely cause: Wrong unit or reference to reactor
Factor: 1750x over realistic value
```

## Recommended Thresholds (Minimal Margins)

Based on published NSTX/NSTX-U specifications:

| Parameter | Min | Max | Unit | Source |
|-----------|-----|-----|------|--------|
| Plasma Current | 0.05 | 2.2 | MA | NSTX-U max 2.0 MA |
| Toroidal Field | -1.2 | 1.2 | T | NSTX-U max 1.0 T |
| NBI Power | 0 | 18 | MW | NSTX-U max 15 MW |
| RF Power | 0 | 8 | MW | NSTX-U max 6 MW |
| Total Heating | 0 | 25 | MW | NSTX-U max ~21 MW |
| Electron Temp | 0.01 | 10 | keV | Typical core 1-5 keV |
| Ion Temp | 0.01 | 20 | keV | Typical core 1-15 keV |
| Electron Density | 1e17 | 5e20 | m^-3 | Operating range |
| Beta (total) | 0 | 45 | % | Max achieved ~40% |
| Beta_N | 0 | 10 | dimensionless | Max achieved ~9 |
| Confinement Time | 0.005 | 300 | ms | Typical 10-200 ms |
| Stored Energy | 0.01 | 1 | MJ | Convert from kJ |
| Kappa | 1.2 | 3.0 | dimensionless | NSTX-U max 2.7 |
| q95 | 0.8 | 20 | dimensionless | Typical 2-15 |
| H Factor | 0.4 | 3.5 | dimensionless | Typical 0.75-2.7 |
| Internal Inductance | 0.2 | 2.5 | dimensionless | Typical 0.5-1.5 |
| **Fusion Power** | NULL | 0.001 | MW | **FLAG ALL** |

## Estimated Outlier Count

Based on data ranges:

| Parameter | Estimated Outliers |
|-----------|-------------------|
| Plasma Current | ~15-20 (values > 2.2 MA) |
| Toroidal Field | ~10-15 (abs > 1.2 T) |
| NBI Power | ~10 (values > 18 MW) |
| RF Power | ~5 (values > 8 MW) |
| Total Heating | ~5 (values > 25 MW) |
| Electron Temp | ~20 (values > 10 keV) |
| Ion Temp | ~10 (values > 20 keV) |
| Stored Energy | ~5 (MJ values > 1) |
| Fusion Power | **6** (ALL instances) |
| **TOTAL ESTIMATE** | **~85-100 outliers** |

## Next Steps

### Immediate (Phase 2):
1. Add outlier tracking columns to `nstx_parameters`
2. Add batch tracking system
3. Create `parameter_thresholds` table
4. Create `threshold_history` table
5. Backfill `created_at` if any NULL values exist

### Phase 3:
1. Implement outlier detection script
2. Run dry-run on DEV
3. Generate detailed outlier report with DOIs

### Phase 4:
1. Build admin web interface
2. Implement threshold management UI
3. Add review workflow

## Questions Resolved

✅ **What are table/column names?**
   - `nstx_parameters` with fields: `parameter_name`, `value`, `unit`, `context`, `page_number`

✅ **Is there source context?**
   - Yes! `context` field has paragraph text, `page_number` has page

✅ **How is DOI stored?**
   - `nstx_papers.doi` field, appears to be just the identifier (no URL prefix)

✅ **Are there timestamps?**
   - Yes! `created_at` defaults to `now()`, but no batch tracking

✅ **How many total measurements?**
   - 2,136 parameter measurements across ~90 papers

## Database Connection Info

**DEV Database:**
```
postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway
```

**PROD Database:**
```
postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway
```

---

**Discovery Status**: ✅ COMPLETE
**Ready for Phase 2**: Schema Modifications
