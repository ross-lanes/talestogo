# NSTXView Outlier Detection and Cleanup Plan

## Goal
Identify, flag, and report parameter measurements in the NSTXView database that fall outside realistic NSTX/NSTX-U operating ranges, providing a detailed report with DOI links and source context for manual review.

## Key Principles
- **Flag, don't delete**: Preserve all data for review
- **Maintain traceability**: Link every outlier to its source paper and context
- **Evidence-based thresholds**: Use documented NSTX/NSTX-U specifications
- **Reversible operations**: All changes can be rolled back

## Phase 1: Discovery & Schema Analysis

### 1.1 Database Connection & Schema Inspection
**Objective**: Understand the current database structure and identify all relevant tables and columns.

**Tasks**:
- [ ] Connect to DEV database (not production initially)
- [ ] List all tables related to papers, measurements, and parameters
- [ ] Document table schema for:
  - Main measurements/parameters table (column names, data types)
  - Papers/documents table (DOI, title, source fields)
  - Join relationships between tables
- [ ] Examine sample data to understand:
  - Parameter naming conventions (exact strings used)
  - How units are stored
  - How source context is stored (paragraph text, page numbers)
  - Current data quality issues

**Key Questions**:
- What is the measurements table actually named?
- Are there separate tables for different parameter categories?
- Is source paragraph text stored? If so, what column name?
- How is DOI stored (full URL vs identifier)?
- Are there any existing data quality flags?

### 1.2 Current Data Range Analysis
**Objective**: Get baseline statistics on all parameter ranges before cleanup.

**Tasks**:
- [ ] Query min/max/count for ALL parameters in database
- [ ] Export current data ranges to CSV for comparison
- [ ] Identify parameters with obviously problematic values
- [ ] Document specific examples of outliers found

## Phase 2: Schema Modifications

### 2.1 Add Outlier Tracking Columns
**Objective**: Add columns to flag and track outliers without data loss.

**Implementation**:
```sql
ALTER TABLE [measurements_table_name]
ADD COLUMN IF NOT EXISTS is_outlier BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS outlier_reason TEXT,
ADD COLUMN IF NOT EXISTS flagged_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS reviewed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS review_notes TEXT;

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_measurements_outlier
ON [measurements_table_name](is_outlier) WHERE is_outlier = TRUE;
```

**Rollback Plan**:
```sql
-- If needed to undo
ALTER TABLE [measurements_table_name]
DROP COLUMN IF EXISTS is_outlier,
DROP COLUMN IF EXISTS outlier_reason,
DROP COLUMN IF EXISTS flagged_at,
DROP COLUMN IF EXISTS reviewed,
DROP COLUMN IF EXISTS review_notes;
```

### 2.2 Create Parameter Thresholds Configuration
**Objective**: Store threshold rules in database for transparency and maintainability.

**Implementation**:
Create `parameter_thresholds` table with columns:
- parameter_name (with pattern matching for variations)
- min_value, max_value
- expected_unit
- reason_high, reason_low (explanation text)
- flag_all (boolean for parameters like "Fusion Power")
- special_case (enum: WRONG_UNITS, REFERENCE_ONLY, etc.)

**Thresholds** (based on NSTX/NSTX-U specifications):

| Parameter | Min | Max | Unit | Special Cases |
|-----------|-----|-----|------|---------------|
| Plasma Current | 0.05 | 3.0 | MA | Values in kA may have been mislabeled as MA |
| Toroidal Field | -1.5 | 1.5 | T | Negative is convention, absolute value matters |
| NBI Power | 0 | 20 | MW | NSTX-U max is 15 MW |
| RF/HHFW Power | 0 | 10 | MW | NSTX-U max is 6 MW |
| Total Heating Power | 0 | 30 | MW | NSTX-U max ~21 MW |
| Electron Temperature | 0.001 | 30 | keV | Typical core: 1-5 keV |
| Ion Temperature | 0.001 | 50 | keV | Typical core: 1-15 keV |
| Electron Density | 1e17 | 5e20 | m^-3 | |
| Beta (total) | 0 | 60 | % | Max achieved ~40% |
| Beta_N (normalized) | 0 | 12 | dimensionless | |
| Confinement Time | 0.001 | 500 | ms | Typical 10-200 ms |
| Stored Energy | 0.001 | 1000 | kJ | |
| Kappa (elongation) | 1.0 | 3.5 | dimensionless | |
| Triangularity | -0.5 | 1.0 | dimensionless | |
| q95 | 0.5 | 20 | dimensionless | <1 typically unstable |
| H Factor | 0.3 | 4.0 | dimensionless | |
| Internal Inductance (li) | 0.1 | 3.0 | dimensionless | **FLAG IF UNIT IS m^-3 (wrong parameter)** |
| Fusion Power | NULL | 0.001 | MW | **FLAG ALL - NSTX doesn't produce fusion** |

## Phase 3: Outlier Detection & Flagging

### 3.1 Develop Detection Algorithm
**Objective**: Create robust SQL queries or Python script to identify outliers.

**Approaches**:

**Option A: SQL-based (faster, runs in database)**
- Write UPDATE statements for each parameter type
- Use ILIKE pattern matching for parameter name variations
- Apply thresholds from configuration table
- Log all flagging operations

**Option B: Python script (more flexible, easier testing)**
- Query all measurements
- Apply thresholds with configurable rules
- Handle special cases (unit mismatches, pattern recognition)
- Batch update with transaction safety
- Generate detailed logs

**Recommendation**: Python script for initial implementation (easier to test and refine), then optimize to SQL if needed for performance.

### 3.2 Parameter Name Matching Strategy
**Challenge**: Parameter names may have variations in extraction.

**Solution**:
- Use fuzzy matching (e.g., "Plasma Current", "plasma current", "Ip", "I_p")
- Create parameter_name_aliases table
- Implement normalization function

### 3.3 Special Case Handling

**Case 1: Wrong Units (Internal Inductance)**
- Internal inductance is dimensionless (typical: 0.5-1.5)
- Database shows values like 6E19 m^-3 (density units!)
- **Action**: Flag as "WRONG_PARAMETER - appears to be density, not li"

**Case 2: Fusion Power**
- NSTX/NSTX-U doesn't produce measurable fusion power
- ALL fusion power values are references to other machines or projections
- **Action**: Flag ALL entries with reason "Reference to other machine - NSTX doesn't produce fusion"

**Case 3: Unit Conversion Errors**
- Plasma current of 20,000 MA likely means 20,000 A = 20 kA = 0.02 MA
- **Action**: Flag with "Possible unit error - may be kA mislabeled as MA"

### 3.4 Flagging Implementation
**Execution**:
1. **Backup**: Create database snapshot/backup
2. **Transaction wrapper**: All UPDATEs in single transaction
3. **Dry run**: Log what would be flagged without committing
4. **Review dry run results**: Manually check sample of flagged items
5. **Execute**: Run with COMMIT
6. **Verification**: Query to confirm expected number of flags

**Safety checks**:
- Don't flag more than 30% of data for any parameter (might indicate bad threshold)
- Don't flag if threshold source is uncertain
- Log all flagging operations with timestamp

## Phase 4: Report Generation

### 4.1 Outlier Report Requirements
**Format**: Markdown document with:
- Executive summary (total outliers, by parameter)
- Detailed listings grouped by parameter
- Each outlier includes:
  - Paper title with DOI link
  - Extracted value with units
  - Expected range
  - Reason flagged
  - Source paragraph excerpt (first 300 chars)
  - Page number (if available)

### 4.2 Report Generation Script
**Implementation**: Python script that:
1. Queries all flagged measurements with JOIN to papers
2. Groups by parameter_name
3. Generates markdown with proper formatting
4. Creates DOI hyperlinks: `[Paper Title](https://doi.org/{doi})`
5. Includes statistics summary
6. Exports to `/scripts/reports/outlier_report_YYYYMMDD.md`

**Additional outputs**:
- CSV export for spreadsheet analysis
- JSON export for programmatic access
- Summary statistics JSON

### 4.3 Report Template Structure
```markdown
# NSTXView Outlier Detection Report
**Generated**: [timestamp]
**Database**: [dev/prod]
**Total measurements**: X
**Outliers flagged**: Y (Z%)

## Summary by Parameter
| Parameter | Total | Outliers | % Flagged | Previous Range | Clean Range |
|-----------|-------|----------|-----------|----------------|-------------|
| ... | ... | ... | ... | ... | ... |

## Detailed Findings

### Parameter: Plasma Current
**Total flagged**: X
**Reason**: Exceeds NSTX-U maximum capability (2 MA)

#### [Paper Title](https://doi.org/XX.XXXX/xxxxx)
- **Extracted value**: 20000 MA
- **Expected range**: 0.05 - 3.0 MA
- **Likely cause**: Unit conversion error (kA vs MA)
- **Source (page X)**: "The plasma current reached 20000 kA during..."
- **Action needed**: Review paper, correct extraction or flag as reference

[Repeat for each outlier...]
```

## Phase 5: Data View Creation

### 5.1 Create Clean Data View
**Objective**: Provide a filtered view excluding outliers for use in queries and MCP tools.

**Implementation**:
```sql
CREATE OR REPLACE VIEW clean_measurements AS
SELECT *
FROM [measurements_table]
WHERE is_outlier = FALSE OR is_outlier IS NULL;

-- Summary view for quick statistics
CREATE OR REPLACE VIEW parameter_statistics AS
SELECT
    parameter_name,
    unit,
    COUNT(*) as total_measurements,
    COUNT(*) FILTER (WHERE is_outlier = TRUE) as outliers,
    COUNT(*) FILTER (WHERE is_outlier = FALSE OR is_outlier IS NULL) as valid,
    MIN(value) FILTER (WHERE NOT is_outlier) as valid_min,
    MAX(value) FILTER (WHERE NOT is_outlier) as valid_max,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value)
        FILTER (WHERE NOT is_outlier) as valid_median,
    AVG(value) FILTER (WHERE NOT is_outlier) as valid_avg,
    STDDEV(value) FILTER (WHERE NOT is_outlier) as valid_stddev
FROM [measurements_table]
GROUP BY parameter_name, unit
ORDER BY parameter_name;
```

### 5.2 Update MCP Server Queries
**Objective**: Ensure MCP tools use clean data by default, with option to include outliers.

**Changes needed**:
1. Modify `query_shots`, `get_parameter_statistics` to use `clean_measurements` view
2. Add optional `include_outliers` parameter to tools
3. Update tool descriptions to mention outlier filtering
4. Test all MCP tools after changes

## Phase 6: Validation & Testing

### 6.1 Validation Queries
**Objective**: Verify the cleanup worked as expected.

**Queries**:
```sql
-- Count outliers by parameter
SELECT parameter_name, COUNT(*) as outlier_count
FROM [measurements_table]
WHERE is_outlier = TRUE
GROUP BY parameter_name
ORDER BY outlier_count DESC;

-- Verify new ranges are reasonable
SELECT
    parameter_name,
    MIN(value) as clean_min,
    MAX(value) as clean_max,
    COUNT(*) as clean_count
FROM clean_measurements
GROUP BY parameter_name
ORDER BY parameter_name;

-- Spot check: Plasma Current should now be < 3 MA
SELECT parameter_name, value, unit, is_outlier
FROM [measurements_table]
WHERE parameter_name ILIKE '%plasma current%'
ORDER BY value DESC
LIMIT 20;

-- Verify all Fusion Power is flagged
SELECT COUNT(*) as total,
       COUNT(*) FILTER (WHERE is_outlier = TRUE) as flagged
FROM [measurements_table]
WHERE parameter_name ILIKE '%fusion%power%';
```

### 6.2 Manual Review Sample
**Process**:
1. Select 10 random outliers from report
2. Look up DOI and find source paragraph in paper
3. Verify:
   - Value was correctly extracted
   - Value does refer to NSTX (not ITER/JET/reactor)
   - Flagging reason is accurate
4. Document any false positives
5. Adjust thresholds if needed

### 6.3 Before/After Comparison
**Generate comparison report**:
- Document ranges before and after cleanup
- Show reduction in unrealistic values
- Highlight parameters most affected

## Phase 7: Deployment & Documentation

### 7.1 Deployment Sequence
1. **DEV environment**:
   - Run full process on dev database
   - Generate report
   - Review with stakeholders
   - Refine thresholds if needed

2. **PROD environment** (after dev approval):
   - Create database backup
   - Run schema changes
   - Run outlier detection
   - Generate report
   - Update MCP server
   - Verify MCP tools work correctly

### 7.2 Documentation Updates
**Update these files**:
- `CLAUDE.md`: Add section on data quality and outlier handling
- `HowNSTXViewWorks.tsx`: Add note about data quality filtering
- Create `DATA_QUALITY.md`: Document thresholds, process, and maintenance
- MCP server README: Document outlier filtering behavior

### 7.3 Ongoing Maintenance
**Create maintenance procedures**:
- Re-run outlier detection after new papers are added
- Quarterly review of thresholds
- Track false positive rate
- Script to flag new measurements as they're added

## Success Criteria

**The implementation is successful when**:
1. ✅ All measurements outside realistic NSTX/NSTX-U ranges are flagged
2. ✅ No false positives in manual review sample (or <5% rate)
3. ✅ Complete report generated with DOI links and source context
4. ✅ Clean data views show realistic parameter ranges
5. ✅ MCP tools return accurate results using clean data
6. ✅ All changes are reversible (unflagging possible)
7. ✅ Process is documented for future maintenance

## Expected Outcomes

| Parameter | Before (max) | After (max clean) | Outliers Flagged |
|-----------|-------------|-------------------|------------------|
| Plasma Current | 20000 MA | ~2.5 MA | ~20-30 entries |
| Toroidal Field | 6.0 T | ~1.2 T | ~10-15 entries |
| NBI Power | 90 MW | ~18 MW | ~15-20 entries |
| RF Power | 550 MW | ~8 MW | ~5-10 entries |
| Total Heating | 840 MW | ~25 MW | ~10-15 entries |
| Electron Temp | 4000 keV | ~10 keV | ~20-30 entries |
| Ion Temp | 1900 keV | ~20 keV | ~10-15 entries |
| Internal Inductance | 6E19 | ~2.0 | ~30-40 (wrong units) |
| Fusion Power | 60 MW | 0 | ALL (~14 entries) |

**Estimated total outliers**: 150-250 measurements out of ~2,000 total (7-12%)

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| False positives (flagging valid data) | High | Manual review sample; conservative thresholds |
| Missing actual outliers | Medium | Document known edge cases; iterative refinement |
| Breaking MCP tools | High | Test all tools after view changes; rollback plan |
| Performance degradation | Low | Index on is_outlier column; views are efficient |
| Threshold disputes | Medium | Document sources for all thresholds; peer review |

## Timeline Estimate

- **Phase 1 (Discovery)**: 2-3 hours
- **Phase 2 (Schema)**: 1 hour
- **Phase 3 (Detection)**: 3-4 hours (incl testing)
- **Phase 4 (Report)**: 2-3 hours
- **Phase 5 (Views)**: 1-2 hours
- **Phase 6 (Validation)**: 2-3 hours
- **Phase 7 (Deploy)**: 2 hours

**Total**: ~13-18 hours of work

## Questions for Stakeholder Review

1. Are the thresholds appropriate? Any parameters missing?
2. Should we create a UI for reviewing flagged outliers?
3. Who should review the outlier report before production deployment?
4. Should outlier detection run automatically on new paper ingestion?
5. Are there any parameters that should be excluded from outlier detection?
6. Should we add a "confidence" score to outlier flags?

## Next Steps

After plan approval:
1. Execute Phase 1 (Discovery) on dev database
2. Share schema findings and refine plan if needed
3. Proceed through phases sequentially
4. Generate interim report after Phase 3 for review
5. Deploy to production only after stakeholder sign-off

---

**Plan Status**: Draft - Awaiting Review
**Created**: 2025-12-04
**Author**: Claude Code
