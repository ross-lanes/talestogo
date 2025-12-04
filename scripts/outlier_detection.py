#!/usr/bin/env python3
"""
NSTXView Outlier Detection Engine

Detects parameter measurements that fall outside realistic NSTX/NSTX-U operating ranges
and flags them in the database with detailed reasoning.

Usage:
    python3 scripts/outlier_detection.py --dry-run           # Test without changes
    python3 scripts/outlier_detection.py                     # Flag outliers on DEV
    python3 scripts/outlier_detection.py --prod              # Flag outliers on PROD
    python3 scripts/outlier_detection.py --reprocess-all     # Re-evaluate all measurements
    python3 scripts/outlier_detection.py --batch-id 5        # Process specific batch only
"""

import os
import sys
import re
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, text

class OutlierDetector:
    def __init__(self, database_url: str, dry_run: bool = False):
        self.database_url = database_url
        self.dry_run = dry_run
        self.engine = create_engine(database_url)
        self.thresholds = {}
        self.stats = {
            'total_checked': 0,
            'outliers_found': 0,
            'already_flagged': 0,
            'by_parameter': {}
        }

    def load_thresholds(self):
        """Load active thresholds from database."""
        print("📊 Loading parameter thresholds...")

        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT id, parameter_name, parameter_pattern, min_value, max_value,
                       expected_unit, reason_below, reason_above, flag_all, special_case
                FROM parameter_thresholds
                WHERE active = TRUE
            """))

            for row in result:
                threshold = {
                    'id': row[0],
                    'parameter_name': row[1],
                    'parameter_pattern': row[2],
                    'min_value': row[3],
                    'max_value': row[4],
                    'expected_unit': row[5],
                    'reason_below': row[6],
                    'reason_above': row[7],
                    'flag_all': row[8],
                    'special_case': row[9]
                }
                self.thresholds[row[1]] = threshold

        print(f"   ✅ Loaded {len(self.thresholds)} active thresholds\n")

    def match_parameter_to_threshold(self, param_name: str, unit: str) -> Optional[Dict]:
        """
        Match a parameter name to a threshold rule using pattern matching.
        Returns the matching threshold or None.
        """
        param_lower = param_name.lower()

        for threshold_name, threshold in self.thresholds.items():
            pattern = threshold['parameter_pattern']
            if not pattern:
                # Exact match only
                if param_name.lower() == threshold_name.lower():
                    return threshold
            else:
                # Pattern matching with | for OR
                patterns = pattern.split('|')
                for p in patterns:
                    # Convert SQL LIKE pattern to regex
                    regex_pattern = p.replace('%', '.*').strip()
                    if re.search(regex_pattern, param_lower, re.IGNORECASE):
                        return threshold

        return None

    def check_outlier(self, value: float, unit: str, param_name: str,
                     threshold: Dict) -> Tuple[bool, Optional[str]]:
        """
        Check if a measurement is an outlier.
        Returns (is_outlier, reason)
        """
        # Special case: Flag all instances (e.g., Fusion Power)
        if threshold.get('flag_all'):
            return True, threshold['reason_above']

        # Special case: Check for wrong units (e.g., Internal Inductance with m^-3)
        if threshold.get('special_case') == 'check_wrong_units':
            if unit and 'm' in unit.lower() and 'dimensionless' in threshold['expected_unit'].lower():
                return True, "Unit contains 'm' but should be dimensionless - likely wrong parameter extracted (possibly density)"
            if value and value > 10:  # li should be 0.5-1.5 typically
                return True, "Value > 10 suggests wrong parameter (internal inductance should be ~0.5-1.5)"

        # Check if value is below minimum
        if threshold['min_value'] is not None and value is not None:
            if value < threshold['min_value']:
                return True, threshold['reason_below'] or f"Value {value} below minimum threshold {threshold['min_value']}"

        # Check if value is above maximum
        if threshold['max_value'] is not None and value is not None:
            if value > threshold['max_value']:
                # Check for possible unit conversion error
                if value > threshold['max_value'] * 1000:
                    possible_correct = value / 1000
                    if possible_correct <= threshold['max_value']:
                        return True, f"{threshold['reason_above']}. Possible unit error: {value} {unit} might be {value/1000} (1000x factor)"
                return True, threshold['reason_above'] or f"Value {value} exceeds maximum threshold {threshold['max_value']}"

        return False, None

    def detect_outliers(self, batch_id: Optional[int] = None,
                       paper_ids: Optional[List[int]] = None,
                       reprocess_all: bool = False) -> Dict[str, Any]:
        """
        Main outlier detection function.

        Args:
            batch_id: Process only measurements from this batch
            paper_ids: Process only specific papers
            reprocess_all: Re-evaluate ALL measurements (use when thresholds change)

        Returns:
            Statistics and list of flagged measurements
        """
        print("🔍 Starting outlier detection...")
        print(f"   Mode: {'REPROCESS ALL' if reprocess_all else 'NEW ONLY'}")
        print(f"   Dry run: {self.dry_run}\n")

        # Build query conditions
        conditions = []
        params = {}

        if batch_id:
            conditions.append("batch_id = :batch_id")
            params['batch_id'] = batch_id
            print(f"   📦 Batch filter: {batch_id}")

        if paper_ids:
            conditions.append("paper_id = ANY(:paper_ids)")
            params['paper_ids'] = paper_ids
            print(f"   📄 Paper filter: {len(paper_ids)} papers")

        if not reprocess_all:
            # Only check measurements not already flagged
            conditions.append("(is_outlier IS NULL OR is_outlier = FALSE)")

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        # Get measurements to check
        with self.engine.connect() as conn:
            # Check if page_number column exists
            has_page_number = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'nstx_parameters'
                AND column_name = 'page_number'
            """)).fetchone() is not None

            if has_page_number:
                query = f"""
                    SELECT id, paper_id, parameter_name, parameter_category, value, unit, context, page_number
                    FROM nstx_parameters
                    WHERE {where_clause} AND value IS NOT NULL
                    ORDER BY parameter_name, value DESC
                """
            else:
                query = f"""
                    SELECT id, paper_id, parameter_name, parameter_category, value, unit, context, NULL as page_number
                    FROM nstx_parameters
                    WHERE {where_clause} AND value IS NOT NULL
                    ORDER BY parameter_name, value DESC
                """

            result = conn.execute(text(query), params)
            measurements = result.fetchall()

            print(f"📊 Checking {len(measurements)} measurements...\n")

            flagged_measurements = []

            for row in measurements:
                meas_id, paper_id, param_name, param_cat, value, unit, context, page_num = row
                self.stats['total_checked'] += 1

                # Match to threshold
                threshold = self.match_parameter_to_threshold(param_name, unit)

                if not threshold:
                    # No threshold defined for this parameter
                    continue

                # Check if outlier
                is_outlier, reason = self.check_outlier(value, unit, param_name, threshold)

                if is_outlier:
                    self.stats['outliers_found'] += 1

                    # Track by parameter
                    if param_name not in self.stats['by_parameter']:
                        self.stats['by_parameter'][param_name] = 0
                    self.stats['by_parameter'][param_name] += 1

                    flagged_measurements.append({
                        'id': meas_id,
                        'paper_id': paper_id,
                        'parameter_name': param_name,
                        'value': value,
                        'unit': unit,
                        'reason': reason,
                        'threshold_id': threshold['id'],
                        'context': context,
                        'page_number': page_num
                    })

                    # Flag in database
                    if not self.dry_run:
                        self.flag_measurement(conn, meas_id, reason, threshold['id'])

            if not self.dry_run:
                conn.commit()

        return {
            'total_checked': self.stats['total_checked'],
            'outliers_found': self.stats['outliers_found'],
            'by_parameter': self.stats['by_parameter'],
            'flagged_measurements': flagged_measurements
        }

    def flag_measurement(self, conn, measurement_id: int, reason: str, threshold_id: int):
        """Flag a measurement as an outlier in the database."""
        conn.execute(text("""
            UPDATE nstx_parameters
            SET is_outlier = TRUE,
                outlier_reason = :reason,
                flagged_at = NOW(),
                flagged_by_threshold_id = :threshold_id
            WHERE id = :measurement_id
        """), {
            'reason': reason,
            'threshold_id': threshold_id,
            'measurement_id': measurement_id
        })

    def print_summary(self, results: Dict[str, Any]):
        """Print summary of outlier detection."""
        print("\n" + "="*80)
        print("📊 OUTLIER DETECTION SUMMARY")
        print("="*80)
        print(f"Total measurements checked: {results['total_checked']}")
        print(f"Outliers found: {results['outliers_found']} ({results['outliers_found']/results['total_checked']*100:.1f}%)")
        print()
        print("Outliers by parameter:")
        for param, count in sorted(results['by_parameter'].items(), key=lambda x: x[1], reverse=True):
            print(f"   {param:40} {count:>5} outliers")
        print("="*80)

    def generate_report(self, results: Dict[str, Any], output_file: str = None):
        """Generate markdown report of outliers with DOI links."""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'outlier_report_{timestamp}.md'

        print(f"\n📝 Generating report: {output_file}")

        # Get paper info for flagged measurements
        with self.engine.connect() as conn:
            paper_info = {}
            for item in results['flagged_measurements']:
                if item['paper_id'] not in paper_info:
                    result = conn.execute(text("""
                        SELECT title, doi, authors
                        FROM nstx_papers
                        WHERE id = :paper_id
                    """), {'paper_id': item['paper_id']})
                    row = result.fetchone()
                    if row:
                        paper_info[item['paper_id']] = {
                            'title': row[0] or 'Unknown Title',
                            'doi': row[1],
                            'authors': row[2]
                        }

        # Generate markdown
        lines = []
        lines.append("# NSTXView Outlier Detection Report\n")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Total Measurements Checked**: {results['total_checked']}\n")
        lines.append(f"**Outliers Found**: {results['outliers_found']} ({results['outliers_found']/results['total_checked']*100:.1f}%)\n")
        lines.append("\n## Summary by Parameter\n")
        lines.append("| Parameter | Outliers | % of Total |")
        lines.append("|-----------|----------|------------|")

        for param, count in sorted(results['by_parameter'].items(), key=lambda x: x[1], reverse=True):
            pct = count / results['outliers_found'] * 100
            lines.append(f"| {param} | {count} | {pct:.1f}% |")

        lines.append("\n## Detailed Findings\n")

        # Group by parameter
        by_param = {}
        for item in results['flagged_measurements']:
            param = item['parameter_name']
            if param not in by_param:
                by_param[param] = []
            by_param[param].append(item)

        for param, items in sorted(by_param.items()):
            lines.append(f"\n### {param}\n")
            lines.append(f"**Total flagged**: {len(items)}\n")

            for item in items:
                paper = paper_info.get(item['paper_id'], {})
                title = paper.get('title', 'Unknown')
                doi = paper.get('doi')

                lines.append(f"\n#### {title}\n")
                if doi:
                    doi_url = doi if doi.startswith('http') else f"https://doi.org/{doi}"
                    lines.append(f"**DOI**: [{doi}]({doi_url})\n")
                else:
                    lines.append("**DOI**: Not available\n")

                lines.append(f"- **Value**: {item['value']} {item['unit'] or ''}\n")
                lines.append(f"- **Reason**: {item['reason']}\n")
                if item['page_number']:
                    lines.append(f"- **Page**: {item['page_number']}\n")
                if item['context']:
                    context_excerpt = item['context'][:300] + '...' if len(item['context']) > 300 else item['context']
                    lines.append(f"- **Context**: {context_excerpt}\n")

        # Write to file
        report_content = '\n'.join(lines)

        with open(output_file, 'w') as f:
            f.write(report_content)

        print(f"   ✅ Report saved: {output_file}")
        return output_file


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Detect outliers in NSTXView parameter data')
    parser.add_argument('--dry-run', action='store_true', help='Test without making changes')
    parser.add_argument('--prod', action='store_true', help='Run on PRODUCTION database')
    parser.add_argument('--reprocess-all', action='store_true', help='Re-evaluate ALL measurements')
    parser.add_argument('--batch-id', type=int, help='Process only specific batch')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    args = parser.parse_args()

    # Get database URL
    if args.prod:
        db_url = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway"
        if not args.dry_run:
            confirm = input("⚠️  WARNING: This will modify PRODUCTION database. Type 'yes' to continue: ")
            if confirm.lower() != 'yes':
                print("❌ Aborted")
                return 1
    else:
        db_url = "postgresql://postgres:REDACTED_RAILWAY_PASSWORD@hopper.proxy.rlwy.net:32217/railway"

    try:
        detector = OutlierDetector(db_url, dry_run=args.dry_run)
        detector.load_thresholds()

        results = detector.detect_outliers(
            batch_id=args.batch_id,
            reprocess_all=args.reprocess_all
        )

        detector.print_summary(results)

        if args.report and results['outliers_found'] > 0:
            detector.generate_report(results)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
