# NSTXView Outlier Detection & Management System - Implementation Plan

**Status**: Ready for Discovery Phase
**Created**: 2024-12-04
**Last Updated**: 2024-12-04

## Executive Summary

Build a comprehensive outlier detection and management system for NSTXView that:
1. Identifies measurements outside realistic NSTX/NSTX-U operating ranges
2. Flags (not deletes) outliers with detailed reasoning and source context
3. Provides admin web interface for threshold management and outlier review
4. Automatically processes new papers as they're ingested
5. Allows reprocessing all papers when thresholds change
6. Generates detailed reports with DOI links to source material

## Critical Design Principles

### ⚠️ Threshold Source of Truth
**DO NOT use current database values to set thresholds** - the database contains extraction errors that would be codified.

**Source of truth**: Published NSTX/NSTX-U machine specifications from PPPL documentation and OSTI papers.

**Margin strategy**: Minimal margins above documented capabilities (e.g., NSTX-U max current = 2.0 MA, threshold = 2.2 MA)

### Data Preservation
- Flag, never delete measurements
- All changes must be reversible
- Track all threshold changes in history
- Preserve source context for human review

### Admin Control
- Web interface for threshold management
- Manual review and correction capability
- Ability to override automatic flagging
- Audit trail of all changes

## Phase 1: Database Discovery

### Objectives
Understand the actual database structure without making any assumptions about table or column names.

### Discovery Tasks

#### 1.1 Connect to DEV Database
```bash
# Use DEV database connection string
DATABASE_URL="postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway"
```

#### 1.2 Table Discovery
```sql
-- List all tables
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Look for tables related to:
-- - Measurements/parameters/extracted_data
-- - Papers/documents/publications
-- - Users (for admin check)
-- - Any existing quality control tables
```

#### 1.3 Schema Inspection
For each relevant table, document:
```sql
-- Get column details
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = '[table_name]'
ORDER BY ordinal_position;

-- Get foreign key relationships
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

#### 1.4 Critical Fields to Locate
- **Measurements table**:
  - Parameter name field
  - Value field (numeric)
  - Unit field
  - Source context fields (paragraph text, page number)
  - Link to paper (foreign key)
  - Timestamp fields (created_at, updated_at)
  - Batch/collection ID (if exists)

- **Papers table**:
  - DOI field (format?)
  - Title field
  - Metadata fields

- **Users table**:
  - Role/permission fields (for admin check)
  - OAuth fields

#### 1.5 Sample Data Analysis
```sql
-- Look at actual measurements
SELECT * FROM [measurements_table] LIMIT 20;

-- Get all unique parameter names
SELECT DISTINCT parameter_name, COUNT(*) as count
FROM [measurements_table]
GROUP BY parameter_name
ORDER BY parameter_name;

-- Check for parameter name variations
SELECT parameter_name, unit, COUNT(*) as count
FROM [measurements_table]
WHERE parameter_name ILIKE '%plasma%current%'
GROUP BY parameter_name, unit;

-- Check source context availability
SELECT
    COUNT(*) as total,
    COUNT(source_paragraph) as has_paragraph,
    COUNT(page_number) as has_page,
    COUNT(*) - COUNT(source_paragraph) as missing_context
FROM [measurements_table];

-- Check timestamp/batch fields
SELECT
    COUNT(*) as total,
    COUNT(created_at) as has_timestamp,
    COUNT(batch_id) as has_batch_id
FROM [measurements_table];
```

#### 1.6 Current Data Ranges
```sql
-- Get ranges for all parameters
SELECT
    parameter_name,
    unit,
    COUNT(*) as measurement_count,
    MIN(value) as min_value,
    MAX(value) as max_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median_value,
    AVG(value) as avg_value,
    STDDEV(value) as stddev_value
FROM [measurements_table]
GROUP BY parameter_name, unit
ORDER BY parameter_name;
```

#### 1.7 Paper Ingestion Pipeline Investigation
- Locate the code that processes new papers
- Identify where measurements are inserted into database
- Find the appropriate hook point for automatic outlier detection

#### 1.8 Existing API Endpoints
```bash
# Check backend router files
ls -la app/routers/

# Search for measurement/parameter endpoints
grep -r "measurement" app/routers/
grep -r "parameter" app/routers/
```

### Discovery Outputs

**Document to create**: `discovery-findings.md`

Contents:
1. **Schema diagram** with all relevant tables and relationships
2. **Field mapping** - exact column names for all critical fields
3. **Parameter inventory** - complete list with current ranges
4. **Data quality assessment**:
   - How many measurements have source context?
   - How many have timestamps?
   - How many papers have DOIs?
5. **Example outliers** - 10-15 specific examples to show stakeholder
6. **API endpoint inventory** - existing routes we can leverage
7. **Ingestion pipeline diagram** - where to hook outlier detection
8. **Missing infrastructure** - what needs to be added

---

## Phase 2: Database Schema Extensions

### 2.1 Add Outlier Tracking to Measurements

**Schema changes**:
```sql
-- Add outlier tracking columns to measurements table
ALTER TABLE [measurements_table]
ADD COLUMN IF NOT EXISTS is_outlier BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS outlier_reason TEXT,
ADD COLUMN IF NOT EXISTS flagged_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS flagged_by_threshold_id INTEGER, -- links to threshold version
ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS reviewed_by INTEGER, -- user_id
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS review_action VARCHAR(20), -- 'confirmed', 'corrected', 'dismissed'
ADD COLUMN IF NOT EXISTS review_notes TEXT,
ADD COLUMN IF NOT EXISTS corrected_value NUMERIC,
ADD COLUMN IF NOT EXISTS corrected_unit VARCHAR(50);

-- Add timestamp if missing
ALTER TABLE [measurements_table]
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- Backfill existing measurements to Dec 2, 2024 1pm ET
UPDATE [measurements_table]
SET created_at = '2024-12-02 13:00:00-05:00'
WHERE created_at IS NULL;

-- Add batch tracking if missing
ALTER TABLE [measurements_table]
ADD COLUMN IF NOT EXISTS batch_id INTEGER DEFAULT 1;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_measurements_outlier
ON [measurements_table](is_outlier) WHERE is_outlier = TRUE;

CREATE INDEX IF NOT EXISTS idx_measurements_batch
ON [measurements_table](batch_id);

CREATE INDEX IF NOT EXISTS idx_measurements_created
ON [measurements_table](created_at DESC);
```

### 2.2 Create Parameter Thresholds Table

**Purpose**: Store and version control threshold rules for all parameters.

```sql
CREATE TABLE IF NOT EXISTS parameter_thresholds (
    id SERIAL PRIMARY KEY,
    parameter_name VARCHAR(100) NOT NULL,
    parameter_pattern VARCHAR(200), -- regex/ILIKE pattern for matching variations
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    expected_unit VARCHAR(50),
    category VARCHAR(50), -- 'operational', 'plasma', 'performance'
    reason_below TEXT, -- why values below min are outliers
    reason_above TEXT, -- why values above max are outliers
    flag_all BOOLEAN DEFAULT FALSE, -- flag all instances (e.g., Fusion Power)
    special_case VARCHAR(50), -- 'wrong_units', 'reference_only', etc.
    source VARCHAR(200), -- citation for threshold (PPPL doc, paper, etc.)
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER, -- user_id
    notes TEXT
);

-- Create unique constraint
CREATE UNIQUE INDEX idx_param_threshold_active
ON parameter_thresholds(parameter_name)
WHERE active = TRUE;

-- Threshold change history
CREATE TABLE IF NOT EXISTS threshold_history (
    id SERIAL PRIMARY KEY,
    parameter_name VARCHAR(100) NOT NULL,
    old_min DOUBLE PRECISION,
    old_max DOUBLE PRECISION,
    new_min DOUBLE PRECISION,
    new_max DOUBLE PRECISION,
    changed_by INTEGER NOT NULL, -- user_id
    changed_at TIMESTAMP DEFAULT NOW(),
    reason TEXT,
    reprocessing_triggered BOOLEAN DEFAULT FALSE
);
```

### 2.3 Insert Initial Thresholds

**Based on NSTX/NSTX-U specifications** (minimal margins):

```sql
INSERT INTO parameter_thresholds
(parameter_name, parameter_pattern, min_value, max_value, expected_unit, category, reason_below, reason_above, source, notes)
VALUES
-- Operational Parameters
('Plasma Current', '%plasma%current%', 0.05, 2.2, 'MA', 'operational',
    'Below typical NSTX operating range',
    'Exceeds NSTX-U maximum capability (2.0 MA) - likely reference to another machine or unit error (kA mislabeled as MA)',
    'NSTX-U Technical Design Report, PPPL',
    'NSTX max: 1.5 MA, NSTX-U max: 2.0 MA'),

('Toroidal Field', '%toroidal%field%', -1.2, 1.2, 'T', 'operational',
    'Exceeds NSTX-U maximum capability (1.0 T in magnitude)',
    'Exceeds NSTX-U maximum capability (1.0 T) - likely reference to another machine',
    'NSTX-U Technical Design Report, PPPL',
    'NSTX max: 0.45 T, NSTX-U max: 1.0 T. Negative sign is just convention.'),

('NBI Power', '%nbi%power%', 0, 18, 'MW', 'operational',
    NULL,
    'Exceeds NSTX-U maximum NBI capability (15 MW) - likely reference to another machine',
    'NSTX-U Technical Design Report, PPPL',
    'NSTX max: 7.5 MW, NSTX-U max: 15 MW'),

('RF Power', '%rf%power%|%hhfw%power%', 0, 8, 'MW', 'operational',
    NULL,
    'Exceeds NSTX-U maximum RF/HHFW capability (6 MW) - likely reference to another machine',
    'NSTX-U Technical Design Report, PPPL',
    'Both NSTX and NSTX-U: 6 MW'),

('Total Heating Power', '%total%heating%power%', 0, 25, 'MW', 'operational',
    NULL,
    'Exceeds NSTX-U maximum total heating capability (~21 MW) - likely reference to another machine',
    'NSTX-U Technical Design Report, PPPL',
    'NSTX max: ~13.5 MW, NSTX-U max: ~21 MW (15 NBI + 6 RF)'),

('Line Averaged Density', '%line%avg%density%|%line%averaged%density%', 1e18, 1e20, 'm^-3', 'operational',
    'Below typical NSTX operating range',
    'Exceeds typical NSTX operating range',
    'NSTX operations data',
    'Typical range for NSTX/NSTX-U operations'),

-- Plasma Parameters
('Electron Temperature', '%electron%temp%', 0.01, 10, 'keV', 'plasma',
    'Unrealistically low for NSTX plasmas',
    'Unrealistic for NSTX plasmas (typical core: 1-5 keV) - likely extraction error or reference to reactor conditions',
    'NSTX published results',
    'Core electron temperature typically 1-5 keV'),

('Ion Temperature', '%ion%temp%', 0.01, 20, 'keV', 'plasma',
    'Unrealistically low for NSTX plasmas',
    'Unrealistic for NSTX plasmas (typical core: 1-15 keV) - likely extraction error or reference to reactor conditions',
    'NSTX published results',
    'Core ion temperature typically 1-15 keV'),

('Electron Density', '%electron%density%', 1e17, 5e20, 'm^-3', 'plasma',
    'Below typical NSTX density range',
    'Exceeds typical NSTX density range',
    'NSTX operations data',
    'Typical range: 1e18 - 1e20 m^-3'),

('Beta (total)', '%beta%', 0, 45, '%', 'plasma',
    NULL,
    'Exceeds maximum achieved beta (~40%) on NSTX - may be projection or error',
    'NSTX record beta publications',
    'Exclude Beta_N. Max achieved ~40%'),

('Confinement Time', '%confinement%time%', 0.005, 300, 'ms', 'plasma',
    'Unrealistically short',
    'Unrealistic confinement time for NSTX - likely error',
    'NSTX published results',
    'Typical range: 10-200 ms for spherical tokamaks'),

('Stored Energy', '%stored%energy%', 0.01, 500, 'kJ', 'plasma',
    'Unrealistically low',
    'Exceeds typical NSTX stored energy - likely reference to larger machine',
    'NSTX published results',
    'Typical range depends on plasma conditions'),

('Pressure', '%pressure%', 1e-12, 50, 'kPa', 'plasma',
    'Unrealistically low',
    'Exceeds typical NSTX plasma pressure',
    'NSTX published results',
    'Plasma pressure varies widely'),

-- Performance Parameters
('Kappa', '%kappa%|%elongation%', 1.2, 3.0, 'dimensionless', 'performance',
    'Below typical spherical tokamak elongation',
    'Exceeds achievable elongation for NSTX geometry',
    'NSTX design specifications',
    'NSTX/NSTX-U: up to 2.6-2.7'),

('Triangularity', '%triangularity%', -0.5, 1.0, 'dimensionless', 'performance',
    'Outside physical range',
    'Outside physical range',
    'Tokamak geometry constraints',
    'Typical range: 0.08 - 0.8'),

('q95', '%q95%|%q_95%', 0.8, 20, 'dimensionless', 'performance',
    'q95 < 1 typically indicates unstable plasma',
    'Unusually high q95',
    'MHD stability theory',
    'Typical range: 2-15 for NSTX'),

('Beta_N', '%beta%n%|%normalized%beta%', 0, 10, 'dimensionless', 'performance',
    NULL,
    'Exceeds achievable normalized beta for NSTX',
    'NSTX published results',
    'Record values ~7-9'),

('H Factor', '%h%factor%|%h_factor%', 0.4, 3.5, 'dimensionless', 'performance',
    'H-factor < 0.5 indicates very poor confinement',
    'H-factor > 3 is unrealistic for NSTX',
    'NSTX published results',
    'Typical range: 0.75 - 2.7'),

('Internal Inductance', '%internal%inductance%|%li%', 0.2, 2.5, 'dimensionless', 'performance',
    'Below typical range',
    'Internal inductance is dimensionless (typical 0.5-1.5) - values >10 or with units like m^-3 indicate WRONG PARAMETER (likely density)',
    'Tokamak theory',
    'SPECIAL: Flag if value > 10 or unit contains "m" - likely wrong parameter extracted'),

-- Special Cases
('Fusion Power', '%fusion%power%', NULL, 0.001, 'MW', 'plasma',
    NULL,
    'NSTX/NSTX-U does not produce measurable fusion power - ALL values are references to other machines or projections',
    'NSTX design specifications',
    'SPECIAL: Flag ALL instances');

-- Mark Fusion Power to flag all
UPDATE parameter_thresholds
SET flag_all = TRUE, special_case = 'reference_only'
WHERE parameter_name = 'Fusion Power';

-- Mark Internal Inductance for special unit checking
UPDATE parameter_thresholds
SET special_case = 'check_wrong_units'
WHERE parameter_name = 'Internal Inductance';
```

### 2.4 Create Batch Tracking Table

```sql
CREATE TABLE IF NOT EXISTS ingestion_batches (
    id SERIAL PRIMARY KEY,
    batch_name VARCHAR(100),
    papers_processed INTEGER DEFAULT 0,
    measurements_extracted INTEGER DEFAULT 0,
    outliers_flagged INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    error_message TEXT,
    triggered_by INTEGER, -- user_id, null if automatic
    notes TEXT
);

-- Insert initial batch for existing data
INSERT INTO ingestion_batches
(id, batch_name, papers_processed, started_at, completed_at, status, notes)
VALUES
(1, 'Initial Historical Data',
 (SELECT COUNT(DISTINCT paper_id) FROM [measurements_table]),
 '2024-12-02 13:00:00-05:00',
 '2024-12-02 13:00:00-05:00',
 'completed',
 'All papers processed before outlier detection system was implemented');
```

---

## Phase 3: Outlier Detection Engine

### 3.1 Detection Script Architecture

**File**: `scripts/outlier_detection.py`

**Functions**:
```python
def detect_outliers(
    batch_id: Optional[int] = None,
    paper_ids: Optional[List[int]] = None,
    reprocess_all: bool = False,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Main outlier detection function.

    Args:
        batch_id: Process only measurements from this batch
        paper_ids: Process only specific papers
        reprocess_all: Re-evaluate ALL measurements (use when thresholds change)
        dry_run: Report what would be flagged without committing

    Returns:
        Statistics and list of flagged measurements
    """
    pass

def match_parameter_to_threshold(
    parameter_name: str,
    unit: str
) -> Optional[ThresholdRule]:
    """
    Match a parameter name to threshold rules using pattern matching.
    Handles variations like "Plasma Current" vs "plasma_current" vs "Ip"
    """
    pass

def check_outlier(
    value: float,
    unit: str,
    parameter_name: str,
    threshold: ThresholdRule
) -> Tuple[bool, Optional[str]]:
    """
    Check if a single measurement is an outlier.

    Returns:
        (is_outlier, reason)
    """
    pass

def flag_measurement(
    measurement_id: int,
    reason: str,
    threshold_id: int,
    dry_run: bool = False
) -> None:
    """
    Flag a measurement as an outlier in the database.
    """
    pass

def generate_outlier_report(
    flagged_measurements: List[Dict],
    output_format: str = 'markdown'
) -> str:
    """
    Generate report of outliers with DOI links and source context.

    Args:
        output_format: 'markdown', 'json', 'csv', or 'html'
    """
    pass
```

### 3.2 Pattern Matching Strategy

Handle parameter name variations:
```python
PARAMETER_ALIASES = {
    'Plasma Current': ['plasma current', 'plasma_current', 'Ip', 'I_p', 'I_plasma'],
    'Toroidal Field': ['toroidal field', 'toroidal_field', 'Bt', 'B_t', 'B_toroidal'],
    'Electron Temperature': ['electron temperature', 'electron_temperature', 'Te', 'T_e'],
    # ... etc
}

def normalize_parameter_name(param_name: str) -> str:
    """Convert variations to canonical name."""
    pass

def match_parameter_pattern(param_name: str, pattern: str) -> bool:
    """
    Check if param_name matches ILIKE pattern or regex.
    Example: '%plasma%current%' matches 'Plasma Current (MA)'
    """
    pass
```

### 3.3 Special Case Handlers

```python
def check_internal_inductance_units(value: float, unit: str) -> Tuple[bool, str]:
    """
    Internal inductance should be dimensionless (0.5-1.5).
    If value > 10 or unit contains 'm', it's likely density mislabeled.
    """
    if value > 10:
        return True, "Value suggests this is density (m^-3), not internal inductance"
    if unit and 'm' in unit.lower():
        return True, f"Unit '{unit}' suggests wrong parameter - li is dimensionless"
    return False, None

def check_fusion_power(value: float) -> Tuple[bool, str]:
    """
    NSTX doesn't produce fusion power - ALL instances are references.
    """
    return True, "NSTX/NSTX-U does not produce measurable fusion power - reference to another machine"

def check_unit_conversion_error(
    value: float,
    unit: str,
    threshold_max: float
) -> Optional[str]:
    """
    Detect likely unit conversion errors.
    Example: Plasma current of 20000 MA is probably 20000 A = 20 kA = 0.02 MA
    """
    if value > threshold_max * 1000:  # More than 1000x over threshold
        possible_correct = value / 1000  # Try kA -> MA
        if possible_correct <= threshold_max:
            return f"Possible unit error: {value} MA might actually be {value} kA = {possible_correct} MA"
    return None
```

### 3.4 Execution Modes

**Mode 1: Initial Full Scan**
```bash
python scripts/outlier_detection.py --initial --dry-run
python scripts/outlier_detection.py --initial  # After review
```

**Mode 2: Process Specific Batch**
```bash
python scripts/outlier_detection.py --batch-id 5
```

**Mode 3: Reprocess All (after threshold changes)**
```bash
python scripts/outlier_detection.py --reprocess-all --threshold-version 3
```

**Mode 4: Process Specific Papers**
```bash
python scripts/outlier_detection.py --paper-ids 123,456,789
```

---

## Phase 4: Admin Web Interface

### 4.1 New React Pages

**Location**: `frontend/src/pages/admin/`

**Pages to create**:

1. **`OutlierReviewDashboard.tsx`**
   - List all flagged measurements with filters
   - Columns: Parameter, Value, Paper (with DOI link), Reason, Source Context
   - Actions: Review, Correct Value, Dismiss, View Paper
   - Filters: Parameter type, Date range, Reviewed status, Batch
   - Export to CSV/PDF

2. **`ThresholdManagement.tsx`**
   - Table of all parameter thresholds
   - Edit min/max values with validation
   - View threshold history
   - Add new parameter thresholds
   - Trigger reprocessing when thresholds change

3. **`ReprocessingControl.tsx`**
   - View batch history
   - Trigger full reprocessing
   - Monitor progress
   - View statistics (before/after ranges)

4. **`OutlierReport.tsx`**
   - Auto-generated report for latest batch
   - Grouped by parameter
   - Clickable DOI links
   - Source paragraph display
   - Export options

### 4.2 Navigation Integration

**Modify**: `frontend/src/components/Navigation.tsx` or `AppBar.tsx`

Add admin menu under user icon (upper right):
```tsx
// In user menu dropdown (currently shows first letter of name)
<MenuItem onClick={() => navigate('/admin/outlier-review')}>
  <ListItemIcon><FlagIcon /></ListItemIcon>
  <ListItemText>Review Outliers</ListItemText>
</MenuItem>
<MenuItem onClick={() => navigate('/admin/thresholds')}>
  <ListItemIcon><SettingsIcon /></ListItemIcon>
  <ListItemText>Manage Thresholds</ListItemText>
</MenuItem>
<MenuItem onClick={() => navigate('/admin/reprocessing')}>
  <ListItemIcon><RefreshIcon /></ListItemIcon>
  <ListItemText>Reprocessing</ListItemText>
</MenuItem>

// Only show if user.is_admin === true
{user?.is_admin && (
  <>
    <Divider />
    {/* Admin menu items */}
  </>
)}
```

### 4.3 API Endpoints

**New routes in**: `app/routers/outliers.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_admin_user

router = APIRouter(prefix="/api/outliers", tags=["outliers"])

@router.get("/")
async def get_outliers(
    parameter: Optional[str] = None,
    reviewed: Optional[bool] = None,
    batch_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_admin_user)
):
    """Get list of flagged outliers with filters."""
    pass

@router.get("/{measurement_id}")
async def get_outlier_detail(
    measurement_id: int,
    current_user = Depends(get_current_admin_user)
):
    """Get detailed info about a specific flagged measurement."""
    pass

@router.post("/{measurement_id}/review")
async def review_outlier(
    measurement_id: int,
    action: str,  # 'confirmed', 'corrected', 'dismissed'
    corrected_value: Optional[float] = None,
    corrected_unit: Optional[str] = None,
    notes: Optional[str] = None,
    current_user = Depends(get_current_admin_user)
):
    """Mark outlier as reviewed with action."""
    pass

@router.post("/batch/review")
async def batch_review(
    measurement_ids: List[int],
    action: str,
    notes: Optional[str] = None,
    current_user = Depends(get_current_admin_user)
):
    """Review multiple outliers at once."""
    pass

@router.get("/statistics")
async def get_outlier_statistics(
    batch_id: Optional[int] = None,
    current_user = Depends(get_current_admin_user)
):
    """Get statistics on outliers by parameter."""
    pass
```

**New routes in**: `app/routers/thresholds.py`

```python
@router.get("/thresholds")
async def get_thresholds(
    current_user = Depends(get_current_admin_user)
):
    """Get all active parameter thresholds."""
    pass

@router.put("/thresholds/{threshold_id}")
async def update_threshold(
    threshold_id: int,
    min_value: Optional[float],
    max_value: Optional[float],
    reason: str,
    trigger_reprocess: bool = False,
    current_user = Depends(get_current_admin_user)
):
    """
    Update threshold values.
    Logs change to threshold_history.
    Optionally triggers reprocessing.
    """
    pass

@router.get("/thresholds/{threshold_id}/history")
async def get_threshold_history(
    threshold_id: int,
    current_user = Depends(get_current_admin_user)
):
    """Get change history for a threshold."""
    pass

@router.post("/reprocess")
async def trigger_reprocessing(
    reprocess_all: bool = False,
    batch_id: Optional[int] = None,
    current_user = Depends(get_current_admin_user)
):
    """
    Trigger outlier reprocessing with current thresholds.
    Can reprocess all data or specific batch.
    """
    pass
```

### 4.4 Authorization

**Add admin check**:
```python
# In app/auth.py or app/dependencies.py

async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that ensures current user is an admin.
    Raises 403 if not admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user

# Add is_admin field to User model if not exists
# In app/models.py:
class User(Base):
    # ... existing fields ...
    is_admin = Column(Boolean, default=False)
```

---

## Phase 5: Automatic Pipeline Integration

### 5.1 Hook into Paper Ingestion

**Locate ingestion code** (discovered in Phase 1):
```bash
# Likely in app/services/data_pipeline.py or similar
grep -r "insert.*measurement" app/services/
```

**Add outlier detection step**:
```python
# In data_pipeline.py or similar

from scripts.outlier_detection import detect_outliers

async def process_paper(paper_id: int):
    """Process a single paper: extract data, analyze, flag outliers."""

    # 1. Extract measurements (existing code)
    measurements = await extract_measurements(paper_id)

    # 2. Insert into database (existing code)
    await insert_measurements(measurements, batch_id=current_batch_id)

    # 3. NEW: Run outlier detection on this paper's measurements
    outlier_results = detect_outliers(paper_ids=[paper_id])

    # 4. NEW: Generate outlier report if any found
    if outlier_results['outliers_count'] > 0:
        report_path = generate_outlier_report(
            outlier_results['flagged_measurements'],
            output_format='html'
        )
        # Store report path in database or send notification
        await store_outlier_report(paper_id, report_path)

    return {
        'measurements_extracted': len(measurements),
        'outliers_flagged': outlier_results['outliers_count']
    }
```

### 5.2 Batch Processing

**Update batch workflow**:
```python
async def process_batch(paper_ids: List[int], batch_name: str):
    """Process multiple papers in a batch."""

    # Create batch record
    batch = await create_batch(batch_name, paper_count=len(paper_ids))

    try:
        # Process each paper
        for paper_id in paper_ids:
            await process_paper(paper_id)

        # Run batch-level outlier detection (catches any missed)
        outlier_results = detect_outliers(batch_id=batch.id)

        # Generate consolidated report
        report = generate_outlier_report(
            outlier_results['flagged_measurements'],
            output_format='html'
        )

        # Mark batch complete
        await complete_batch(
            batch.id,
            outliers_flagged=outlier_results['outliers_count'],
            report_path=report
        )

    except Exception as e:
        await fail_batch(batch.id, error=str(e))
        raise
```

### 5.3 Notification System

**Send alerts when outliers are found**:
```python
async def notify_outliers_found(
    batch_id: int,
    outlier_count: int,
    report_path: str
):
    """
    Notify admins when outliers are detected.
    Could be email, in-app notification, etc.
    """
    admin_users = await get_admin_users()

    for admin in admin_users:
        # In-app notification
        await create_notification(
            user_id=admin.id,
            type='outliers_detected',
            title=f'{outlier_count} outliers flagged in latest batch',
            message=f'Review outliers at /admin/outlier-review?batch={batch_id}',
            link=f'/admin/outlier-review?batch={batch_id}'
        )

        # Optional: Email notification
        # await send_email(admin.email, subject, body)
```

---

## Phase 6: Report Generation

### 6.1 Report Formats

**Markdown Report** (for GitHub, documentation):
```python
def generate_markdown_report(outliers: List[Dict]) -> str:
    """
    Generate markdown report with:
    - Executive summary
    - Statistics table
    - Detailed listings by parameter
    - DOI links
    - Source context
    """
    pass
```

**HTML Report** (for web viewing):
```python
def generate_html_report(outliers: List[Dict]) -> str:
    """
    Generate interactive HTML report with:
    - Sortable/filterable table
    - Clickable DOI links (open in new tab)
    - Collapsible source context
    - Charts showing parameter distributions
    """
    pass
```

**CSV Export** (for spreadsheet analysis):
```python
def generate_csv_report(outliers: List[Dict]) -> str:
    """
    Generate CSV with columns:
    - Paper Title, DOI, Parameter, Value, Unit, Reason, Source Text, Page
    """
    pass
```

**JSON Export** (for programmatic access):
```python
def generate_json_report(outliers: List[Dict]) -> str:
    """
    Generate structured JSON with all outlier data.
    """
    pass
```

### 6.2 Report Storage

```sql
CREATE TABLE IF NOT EXISTS outlier_reports (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER REFERENCES ingestion_batches(id),
    report_type VARCHAR(20), -- 'markdown', 'html', 'csv', 'json'
    file_path TEXT,
    outlier_count INTEGER,
    generated_at TIMESTAMP DEFAULT NOW(),
    generated_by INTEGER -- user_id, null if automatic
);
```

### 6.3 Report Template

**Example HTML report structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>NSTXView Outlier Report - Batch {batch_id}</title>
    <style>
        /* Professional styling */
        .outlier-card { border-left: 4px solid #ff5722; }
        .doi-link { color: #1976d2; }
        .source-context { background: #f5f5f5; font-family: monospace; }
    </style>
</head>
<body>
    <h1>NSTXView Outlier Detection Report</h1>
    <p><strong>Generated:</strong> {timestamp}</p>
    <p><strong>Batch:</strong> {batch_name}</p>
    <p><strong>Total Outliers:</strong> {outlier_count}</p>

    <h2>Summary Statistics</h2>
    <table>
        <tr><th>Parameter</th><th>Outliers</th><th>% of Total</th></tr>
        {statistics_rows}
    </table>

    <h2>Detailed Findings</h2>
    {for each parameter}
        <h3>{parameter_name}</h3>
        <p>Total flagged: {count}</p>

        {for each outlier}
            <div class="outlier-card">
                <h4>
                    <a href="https://doi.org/{doi}" class="doi-link" target="_blank">
                        {paper_title}
                    </a>
                </h4>
                <ul>
                    <li><strong>Value:</strong> {value} {unit}</li>
                    <li><strong>Expected range:</strong> {min} - {max} {unit}</li>
                    <li><strong>Reason:</strong> {reason}</li>
                    <li><strong>Page:</strong> {page_number}</li>
                </ul>
                <details>
                    <summary>Source Context</summary>
                    <pre class="source-context">{source_paragraph}</pre>
                </details>
            </div>
        {/for}
    {/for}
</body>
</html>
```

---

## Phase 7: Testing & Validation

### 7.1 Test Cases

**Unit tests** (`tests/test_outlier_detection.py`):
```python
def test_plasma_current_outlier():
    """Test that 20000 MA plasma current is flagged."""
    assert is_outlier(value=20000, parameter='Plasma Current', unit='MA') == True

def test_plasma_current_valid():
    """Test that 1.5 MA plasma current is NOT flagged."""
    assert is_outlier(value=1.5, parameter='Plasma Current', unit='MA') == False

def test_fusion_power_always_flagged():
    """Test that ALL fusion power values are flagged."""
    assert is_outlier(value=0.0001, parameter='Fusion Power', unit='MW') == True

def test_internal_inductance_wrong_units():
    """Test that li with density units is flagged."""
    assert is_outlier(value=6e19, parameter='Internal Inductance', unit='m^-3') == True

def test_parameter_name_variations():
    """Test that 'Plasma Current', 'plasma_current', 'Ip' all match."""
    assert match_parameter('Plasma Current') == match_parameter('Ip')
```

**Integration tests**:
```python
def test_full_detection_pipeline():
    """Test end-to-end outlier detection on sample data."""
    # Insert test measurements
    # Run detection
    # Verify correct outliers flagged
    # Check report generation
    pass

def test_reprocessing():
    """Test that reprocessing updates outlier flags correctly."""
    # Flag outliers with old thresholds
    # Update thresholds
    # Reprocess
    # Verify flags updated
    pass

def test_batch_processing():
    """Test processing a batch of papers."""
    # Create batch
    # Process papers
    # Verify outliers detected
    # Check report generated
    pass
```

### 7.2 Validation Queries

**After initial flagging**:
```sql
-- Count outliers by parameter
SELECT
    parameter_name,
    COUNT(*) as outlier_count,
    MIN(value) as min_outlier,
    MAX(value) as max_outlier
FROM [measurements_table]
WHERE is_outlier = TRUE
GROUP BY parameter_name
ORDER BY outlier_count DESC;

-- Verify clean data ranges are reasonable
SELECT
    parameter_name,
    unit,
    COUNT(*) as valid_count,
    MIN(value) as clean_min,
    MAX(value) as clean_max
FROM [measurements_table]
WHERE is_outlier = FALSE OR is_outlier IS NULL
GROUP BY parameter_name, unit
ORDER BY parameter_name;

-- Check that all Fusion Power is flagged
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE is_outlier = TRUE) as flagged,
    COUNT(*) FILTER (WHERE is_outlier = FALSE) as not_flagged
FROM [measurements_table]
WHERE parameter_name ILIKE '%fusion%power%';
-- Expected: not_flagged = 0

-- Spot check: Plasma Current should be < 2.2 MA in clean data
SELECT value, unit, is_outlier
FROM [measurements_table]
WHERE parameter_name ILIKE '%plasma%current%'
ORDER BY value DESC
LIMIT 20;
```

### 7.3 Manual Review Sample

**Process**:
1. Generate list of 20 random outliers (stratified by parameter)
2. For each outlier:
   - Look up DOI
   - Find source paragraph in actual paper
   - Verify extraction accuracy
   - Check if value refers to NSTX or another machine
   - Document findings
3. Calculate false positive rate
4. Adjust thresholds if needed

**Sample review form**:
```
Outlier ID: 12345
Parameter: Plasma Current
Extracted Value: 20000 MA
Paper: [Title] (DOI: xxx)
Source Page: 5

Manual Review:
☐ Extraction accurate - value is in paper as stated
☐ Refers to NSTX/NSTX-U
☐ Refers to other machine (which: ______)
☐ Unit conversion error (correct value: ______)
☐ Wrong parameter extracted
☐ Other issue: ______

Action:
☐ Confirm outlier flag
☐ Correct value to: ______
☐ Dismiss flag (false positive)

Notes: _______________________
```

---

## Phase 8: Deployment

### 8.1 Deployment Checklist

**DEV Environment**:
- [ ] Connect to DEV database
- [ ] Run schema migrations
- [ ] Insert threshold data
- [ ] Backfill created_at and batch_id fields
- [ ] Run initial outlier detection (dry-run)
- [ ] Review dry-run results
- [ ] Run actual flagging
- [ ] Generate reports
- [ ] Deploy admin UI
- [ ] Test all admin endpoints
- [ ] Verify MCP tools still work
- [ ] Manual review sample

**PROD Environment** (after DEV approval):
- [ ] Create database backup
- [ ] Run schema migrations
- [ ] Insert threshold data
- [ ] Backfill created_at and batch_id fields
- [ ] Run initial outlier detection
- [ ] Generate reports
- [ ] Deploy admin UI
- [ ] Deploy API endpoints
- [ ] Update MCP server to use clean_measurements view
- [ ] Verify all systems operational
- [ ] Send report to stakeholders

### 8.2 Rollback Plan

If something goes wrong:

```sql
-- Rollback schema changes
BEGIN;
ALTER TABLE [measurements_table]
DROP COLUMN IF EXISTS is_outlier,
DROP COLUMN IF EXISTS outlier_reason,
DROP COLUMN IF EXISTS flagged_at,
DROP COLUMN IF EXISTS flagged_by_threshold_id,
DROP COLUMN IF EXISTS reviewed,
DROP COLUMN IF EXISTS reviewed_by,
DROP COLUMN IF EXISTS reviewed_at,
DROP COLUMN IF EXISTS review_action,
DROP COLUMN IF EXISTS review_notes,
DROP COLUMN IF EXISTS corrected_value,
DROP COLUMN IF EXISTS corrected_unit;

DROP TABLE IF EXISTS parameter_thresholds CASCADE;
DROP TABLE IF EXISTS threshold_history CASCADE;
DROP TABLE IF EXISTS ingestion_batches CASCADE;
DROP TABLE IF EXISTS outlier_reports CASCADE;

COMMIT; -- or ROLLBACK if you change your mind
```

### 8.3 Documentation Updates

**Update these files**:

1. **`CLAUDE.md`** - Add section:
```markdown
## Data Quality & Outlier Detection

NSTXView automatically detects and flags measurements that fall outside realistic NSTX/NSTX-U operating ranges. This prevents extraction errors, unit conversion mistakes, and references to other machines from contaminating query results.

- Thresholds based on published NSTX/NSTX-U specifications
- Admin interface at `/admin/outlier-review`
- Automatic detection on new paper ingestion
- Full reprocessing capability when thresholds change
- See `DATA_QUALITY.md` for details
```

2. **Create `DATA_QUALITY.md`**:
```markdown
# NSTXView Data Quality & Outlier Detection

## Overview
[Explain system]

## Parameter Thresholds
[Table of all parameters with min/max values and sources]

## Outlier Detection Process
[How it works]

## Admin Interface Guide
[How to use the admin UI]

## Reprocessing
[How to reprocess data]

## Maintenance
[Ongoing maintenance procedures]
```

3. **Update `HowNSTXViewWorks.tsx`**:
```tsx
<Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 3 }}>
  Data Quality Control
</Typography>
<Typography variant="body1" paragraph>
  NSTXView includes automatic outlier detection to ensure query accuracy.
  Measurements outside realistic NSTX/NSTX-U operating ranges are automatically
  flagged and excluded from queries. Thresholds are based on published machine
  specifications from PPPL documentation.
</Typography>
```

4. **MCP Server README** - Document filtering behavior

---

## Expected Outcomes

### Before Cleanup

| Parameter | Count | Min | Max | Issues |
|-----------|-------|-----|-----|--------|
| Plasma Current | 436 | 0.15 MA | 20000 MA | 20000 MA = 10000x over spec |
| Toroidal Field | 403 | -2.5 T | 6.0 T | 6 T = 6x over spec |
| NBI Power | 252 | 0.32 MW | 90 MW | 90 MW = 6x over spec |
| RF Power | 173 | 0.2 MW | 550 MW | 550 MW = 90x over spec |
| Electron Temp | 271 | 0.179 keV | 4000 keV | 4000 keV = 800x typical |
| Ion Temp | 128 | 0.1 keV | 1900 keV | 1900 keV = 125x typical |
| Internal Inductance | 65 | 0.21 | 6E19 | 6E19 = wrong units (density) |
| Fusion Power | 14 | 3.0 MW | 60 MW | NSTX doesn't produce fusion |

### After Cleanup (Expected)

| Parameter | Clean Count | Clean Min | Clean Max | Outliers Flagged |
|-----------|-------------|-----------|-----------|------------------|
| Plasma Current | ~410 | 0.15 MA | 2.1 MA | ~26 |
| Toroidal Field | ~390 | -1.1 T | 1.1 T | ~13 |
| NBI Power | ~235 | 0.32 MW | 17 MW | ~17 |
| RF Power | ~165 | 0.2 MW | 7 MW | ~8 |
| Electron Temp | ~250 | 0.179 keV | 9 keV | ~21 |
| Ion Temp | ~115 | 0.1 keV | 18 keV | ~13 |
| Internal Inductance | ~30 | 0.21 | 2.3 | ~35 (wrong units) |
| Fusion Power | 0 | NULL | NULL | 14 (all) |

**Total estimated outliers**: 150-200 out of ~2000 measurements (7-10%)

---

## Success Metrics

The implementation is successful when:

1. ✅ **Accuracy**: All measurements outside NSTX/NSTX-U specifications are flagged
2. ✅ **Low false positives**: <5% false positive rate in manual review sample
3. ✅ **Complete reporting**: Every outlier has DOI link and source context
4. ✅ **Realistic ranges**: Clean data shows realistic parameter ranges
5. ✅ **MCP integration**: MCP tools return accurate results using clean data
6. ✅ **Reversibility**: All flagging can be undone/corrected
7. ✅ **Automation**: New papers automatically processed for outliers
8. ✅ **Admin control**: Web interface allows threshold management and review
9. ✅ **Reprocessing**: Full reprocessing works when thresholds change
10. ✅ **Documentation**: All systems documented for maintenance

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 1. Discovery | Database exploration, schema documentation | 3-4 hours |
| 2. Schema | Migrations, threshold table, batch tracking | 2 hours |
| 3. Detection Engine | Python scripts, pattern matching, special cases | 6-8 hours |
| 4. Web Interface | React pages, API endpoints, authorization | 10-12 hours |
| 5. Pipeline Integration | Hook into ingestion, batch processing | 3-4 hours |
| 6. Reports | Multiple formats, templates, storage | 3-4 hours |
| 7. Testing | Unit tests, integration tests, validation | 4-5 hours |
| 8. Deployment | DEV deploy, review, PROD deploy, docs | 4-5 hours |

**Total**: 35-44 hours (5-6 working days)

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| False positives | High | Medium | Conservative thresholds; manual review sample |
| Missing outliers | Medium | Low | Document edge cases; iterative refinement |
| Breaking MCP tools | High | Low | Comprehensive testing; rollback plan |
| Performance issues | Medium | Low | Indexes on key columns; query optimization |
| Threshold disputes | Medium | Medium | Document sources; peer review; history tracking |
| User confusion | Low | Medium | Clear UI; good documentation; training |
| Database corruption | High | Very Low | Backups before changes; transaction safety |

---

## Open Questions

1. Should outlier detection be synchronous (blocks paper processing) or asynchronous (background job)?
2. What should happen to existing query results that included outliers? Regenerate?
3. Should we version/timestamp clean_measurements view snapshots?
4. How long should outlier reports be retained?
5. Should there be different admin permission levels (reviewer vs threshold editor)?
6. Should outliers be completely hidden from non-admin users, or visible with warnings?

---

## Next Steps

**Immediate**:
1. ✅ Plan reviewed and approved by stakeholder
2. ➡️ **Begin Phase 1: Discovery** on DEV database
3. Document findings and refine plan

**After Discovery**:
1. Review findings with stakeholder
2. Proceed through phases 2-8 sequentially
3. Generate reports after each major phase
4. Deploy to DEV, test thoroughly
5. Deploy to PROD after sign-off

---

**Plan Status**: Ready for Implementation
**Approved By**: [Stakeholder name]
**Approval Date**: [Date]
**Next Review**: After Phase 1 Discovery
