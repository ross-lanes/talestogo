#!/usr/bin/env python3
"""
Insert initial parameter thresholds for NSTXView outlier detection.

Thresholds based on published NSTX/NSTX-U machine specifications.
Sources: PPPL documentation, OSTI papers, NSTX-U Technical Design Report.
"""

import os
import sys
from sqlalchemy import create_engine, text

# Threshold data based on NSTX/NSTX-U specifications
THRESHOLDS = [
    # Operational Parameters
    {
        'parameter_name': 'Plasma Current',
        'parameter_pattern': '%plasma%current%',
        'min_value': 0.05,
        'max_value': 2.2,
        'expected_unit': 'MA',
        'category': 'operational',
        'reason_below': 'Below typical NSTX operating range',
        'reason_above': 'Exceeds NSTX-U maximum capability (2.0 MA) - likely reference to another machine or unit error (kA mislabeled as MA)',
        'source': 'NSTX-U Technical Design Report, PPPL',
        'notes': 'NSTX max: 1.5 MA, NSTX-U max: 2.0 MA'
    },
    {
        'parameter_name': 'Toroidal Field',
        'parameter_pattern': '%toroidal%field%',
        'min_value': -1.2,
        'max_value': 1.2,
        'expected_unit': 'T',
        'category': 'operational',
        'reason_below': 'Exceeds NSTX-U maximum capability (1.0 T in magnitude)',
        'reason_above': 'Exceeds NSTX-U maximum capability (1.0 T) - likely reference to another machine',
        'source': 'NSTX-U Technical Design Report, PPPL',
        'notes': 'NSTX max: 0.45 T, NSTX-U max: 1.0 T. Negative sign is just convention.'
    },
    {
        'parameter_name': 'NBI Power',
        'parameter_pattern': '%nbi%power%',
        'min_value': 0,
        'max_value': 18,
        'expected_unit': 'MW',
        'category': 'operational',
        'reason_below': None,
        'reason_above': 'Exceeds NSTX-U maximum NBI capability (15 MW) - likely reference to another machine',
        'source': 'NSTX-U Technical Design Report, PPPL',
        'notes': 'NSTX max: 7.5 MW, NSTX-U max: 15 MW'
    },
    {
        'parameter_name': 'RF Power',
        'parameter_pattern': '%rf%power%|%hhfw%power%',
        'min_value': 0,
        'max_value': 8,
        'expected_unit': 'MW',
        'category': 'operational',
        'reason_below': None,
        'reason_above': 'Exceeds NSTX-U maximum RF/HHFW capability (6 MW) - likely reference to another machine',
        'source': 'NSTX-U Technical Design Report, PPPL',
        'notes': 'Both NSTX and NSTX-U: 6 MW'
    },
    {
        'parameter_name': 'Total Heating Power',
        'parameter_pattern': '%total%heating%power%',
        'min_value': 0,
        'max_value': 25,
        'expected_unit': 'MW',
        'category': 'operational',
        'reason_below': None,
        'reason_above': 'Exceeds NSTX-U maximum total heating capability (~21 MW) - likely reference to another machine',
        'source': 'NSTX-U Technical Design Report, PPPL',
        'notes': 'NSTX max: ~13.5 MW, NSTX-U max: ~21 MW (15 NBI + 6 RF)'
    },
    {
        'parameter_name': 'Line Averaged Density',
        'parameter_pattern': '%line%avg%density%|%line%averaged%density%',
        'min_value': 1e18,
        'max_value': 1e20,
        'expected_unit': 'm^-3',
        'category': 'operational',
        'reason_below': 'Below typical NSTX operating range',
        'reason_above': 'Exceeds typical NSTX operating range',
        'source': 'NSTX operations data',
        'notes': 'Typical range for NSTX/NSTX-U operations'
    },

    # Plasma Parameters
    {
        'parameter_name': 'Electron Temperature',
        'parameter_pattern': '%electron%temp%',
        'min_value': 0.01,
        'max_value': 10,
        'expected_unit': 'keV',
        'category': 'plasma',
        'reason_below': 'Unrealistically low for NSTX plasmas',
        'reason_above': 'Unrealistic for NSTX plasmas (typical core: 1-5 keV) - likely extraction error or reference to reactor conditions',
        'source': 'NSTX published results',
        'notes': 'Core electron temperature typically 1-5 keV'
    },
    {
        'parameter_name': 'Ion Temperature',
        'parameter_pattern': '%ion%temp%',
        'min_value': 0.01,
        'max_value': 20,
        'expected_unit': 'keV',
        'category': 'plasma',
        'reason_below': 'Unrealistically low for NSTX plasmas',
        'reason_above': 'Unrealistic for NSTX plasmas (typical core: 1-15 keV) - likely extraction error or reference to reactor conditions',
        'source': 'NSTX published results',
        'notes': 'Core ion temperature typically 1-15 keV'
    },
    {
        'parameter_name': 'Electron Density',
        'parameter_pattern': '%electron%density%',
        'min_value': 1e17,
        'max_value': 5e20,
        'expected_unit': 'm^-3',
        'category': 'plasma',
        'reason_below': 'Below typical NSTX density range',
        'reason_above': 'Exceeds typical NSTX density range',
        'source': 'NSTX operations data',
        'notes': 'Typical range: 1e18 - 1e20 m^-3'
    },
    {
        'parameter_name': 'Beta',
        'parameter_pattern': '%beta%',
        'min_value': 0,
        'max_value': 45,
        'expected_unit': '%',
        'category': 'plasma',
        'reason_below': None,
        'reason_above': 'Exceeds maximum achieved beta (~40%) on NSTX - may be projection or error',
        'source': 'NSTX record beta publications',
        'notes': 'Exclude Beta_N. Max achieved ~40%'
    },
    {
        'parameter_name': 'Confinement Time',
        'parameter_pattern': '%confinement%time%',
        'min_value': 0.005,
        'max_value': 300,
        'expected_unit': 'ms',
        'category': 'plasma',
        'reason_below': 'Unrealistically short',
        'reason_above': 'Unrealistic confinement time for NSTX - likely error',
        'source': 'NSTX published results',
        'notes': 'Typical range: 10-200 ms for spherical tokamaks'
    },
    {
        'parameter_name': 'Stored Energy',
        'parameter_pattern': '%stored%energy%',
        'min_value': 0.01,
        'max_value': 1,
        'expected_unit': 'MJ',
        'category': 'plasma',
        'reason_below': 'Unrealistically low',
        'reason_above': 'Exceeds typical NSTX stored energy - likely reference to larger machine',
        'source': 'NSTX published results',
        'notes': 'Typical range in kJ, convert to MJ for comparison'
    },
    {
        'parameter_name': 'Pressure',
        'parameter_pattern': '%pressure%',
        'min_value': 1e-12,
        'max_value': 50,
        'expected_unit': 'kPa',
        'category': 'plasma',
        'reason_below': 'Unrealistically low',
        'reason_above': 'Exceeds typical NSTX plasma pressure',
        'source': 'NSTX published results',
        'notes': 'Plasma pressure varies widely'
    },

    # Performance Parameters
    {
        'parameter_name': 'Kappa',
        'parameter_pattern': '%kappa%|%elongation%',
        'min_value': 1.2,
        'max_value': 3.0,
        'expected_unit': 'dimensionless',
        'category': 'performance',
        'reason_below': 'Below typical spherical tokamak elongation',
        'reason_above': 'Exceeds achievable elongation for NSTX geometry',
        'source': 'NSTX design specifications',
        'notes': 'NSTX/NSTX-U: up to 2.6-2.7'
    },
    {
        'parameter_name': 'Triangularity',
        'parameter_pattern': '%triangularity%',
        'min_value': -0.5,
        'max_value': 1.0,
        'expected_unit': 'dimensionless',
        'category': 'performance',
        'reason_below': 'Outside physical range',
        'reason_above': 'Outside physical range',
        'source': 'Tokamak geometry constraints',
        'notes': 'Typical range: 0.08 - 0.8'
    },
    {
        'parameter_name': 'q95',
        'parameter_pattern': '%q95%|%q_95%',
        'min_value': 0.8,
        'max_value': 20,
        'expected_unit': 'dimensionless',
        'category': 'performance',
        'reason_below': 'q95 < 1 typically indicates unstable plasma',
        'reason_above': 'Unusually high q95',
        'source': 'MHD stability theory',
        'notes': 'Typical range: 2-15 for NSTX'
    },
    {
        'parameter_name': 'Beta_N',
        'parameter_pattern': '%beta%n%|%normalized%beta%',
        'min_value': 0,
        'max_value': 10,
        'expected_unit': 'dimensionless',
        'category': 'performance',
        'reason_below': None,
        'reason_above': 'Exceeds achievable normalized beta for NSTX',
        'source': 'NSTX published results',
        'notes': 'Record values ~7-9'
    },
    {
        'parameter_name': 'H Factor',
        'parameter_pattern': '%h%factor%|%h_factor%',
        'min_value': 0.4,
        'max_value': 3.5,
        'expected_unit': 'dimensionless',
        'category': 'performance',
        'reason_below': 'H-factor < 0.5 indicates very poor confinement',
        'reason_above': 'H-factor > 3 is unrealistic for NSTX',
        'source': 'NSTX published results',
        'notes': 'Typical range: 0.75 - 2.7'
    },
    {
        'parameter_name': 'Internal Inductance',
        'parameter_pattern': '%internal%inductance%|%li%',
        'min_value': 0.2,
        'max_value': 2.5,
        'expected_unit': 'dimensionless',
        'category': 'performance',
        'reason_below': 'Below typical range',
        'reason_above': 'Internal inductance is dimensionless (typical 0.5-1.5) - values >10 or with units like m^-3 indicate WRONG PARAMETER (likely density)',
        'source': 'Tokamak theory',
        'notes': 'SPECIAL: Flag if value > 10 or unit contains "m" - likely wrong parameter extracted',
        'special_case': 'check_wrong_units'
    },

    # Special Cases
    {
        'parameter_name': 'Fusion Power',
        'parameter_pattern': '%fusion%power%',
        'min_value': None,
        'max_value': 0.001,
        'expected_unit': 'MW',
        'category': 'performance',
        'reason_below': None,
        'reason_above': 'NSTX/NSTX-U does not produce measurable fusion power - ALL values are references to other machines or projections',
        'source': 'NSTX design specifications',
        'notes': 'SPECIAL: Flag ALL instances',
        'flag_all': True,
        'special_case': 'reference_only'
    }
]

def insert_thresholds(database_url: str, dry_run: bool = False):
    """Insert initial thresholds."""
    print(f"📊 Inserting initial parameter thresholds...")
    print(f"🗄️  Database: {database_url.split('@')[1].split('/')[0]}")
    print(f"🧪 Dry run: {dry_run}\n")

    engine = create_engine(database_url)

    with engine.connect() as conn:
        for threshold in THRESHOLDS:
            param_name = threshold['parameter_name']

            if dry_run:
                print(f"   [DRY RUN] Would insert: {param_name} ({threshold['min_value']} - {threshold['max_value']} {threshold['expected_unit']})")
            else:
                try:
                    # Check if threshold already exists
                    result = conn.execute(text("""
                        SELECT id FROM parameter_thresholds
                        WHERE parameter_name = :name AND active = TRUE
                    """), {'name': param_name})

                    if result.fetchone():
                        print(f"   ⏭️  Skipped (already exists): {param_name}")
                        continue

                    # Insert threshold
                    conn.execute(text("""
                        INSERT INTO parameter_thresholds (
                            parameter_name, parameter_pattern, min_value, max_value,
                            expected_unit, category, reason_below, reason_above,
                            flag_all, special_case, source, notes
                        ) VALUES (
                            :parameter_name, :parameter_pattern, :min_value, :max_value,
                            :expected_unit, :category, :reason_below, :reason_above,
                            :flag_all, :special_case, :source, :notes
                        )
                    """), {
                        'parameter_name': threshold['parameter_name'],
                        'parameter_pattern': threshold.get('parameter_pattern'),
                        'min_value': threshold.get('min_value'),
                        'max_value': threshold.get('max_value'),
                        'expected_unit': threshold['expected_unit'],
                        'category': threshold['category'],
                        'reason_below': threshold.get('reason_below'),
                        'reason_above': threshold.get('reason_above'),
                        'flag_all': threshold.get('flag_all', False),
                        'special_case': threshold.get('special_case'),
                        'source': threshold['source'],
                        'notes': threshold.get('notes')
                    })
                    conn.commit()
                    print(f"   ✅ Inserted: {param_name}")
                except Exception as e:
                    print(f"   ❌ Error inserting {param_name}: {e}")
                    conn.rollback()

        if not dry_run:
            # Verify
            result = conn.execute(text("SELECT COUNT(*) FROM parameter_thresholds"))
            count = result.fetchone()[0]
            print(f"\n✅ Total thresholds in database: {count}")

    print("\n✅ Threshold insertion complete!")
    return True

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Insert initial parameter thresholds')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--prod', action='store_true', help='Run on PRODUCTION database (use with caution!)')
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
        insert_thresholds(db_url, dry_run=args.dry_run)
        return 0
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
