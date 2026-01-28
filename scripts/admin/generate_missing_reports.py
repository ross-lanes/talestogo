#!/usr/bin/env python3
"""
Generate reports for all brands that have data collections but are missing reports.

This script:
1. Finds all brands with completed collection batches
2. Checks if each brand has a report for their latest batch
3. Generates reports for brands that need them

Usage:
    python3 scripts/admin/generate_missing_reports.py [--dry-run] [--yes]

Options:
    --dry-run    Show which reports would be generated without actually generating them
    --yes        Skip confirmation prompt and generate reports immediately
"""

import os
import sys
import time
import argparse

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app.database import SessionLocal
from app.models import BrandInfo, CollectionBatch, Report


def get_brands_needing_reports():
    """Find all brands that need reports generated."""
    db = SessionLocal()

    try:
        brands = db.query(BrandInfo).all()
        brands_needing_reports = []

        for brand in brands:
            # Get latest completed batch
            latest_batch = db.query(CollectionBatch).filter(
                CollectionBatch.brand_id == brand.id,
                CollectionBatch.user_id == brand.user_id,
                CollectionBatch.status == 'completed'
            ).order_by(CollectionBatch.started_at.desc()).first()

            if not latest_batch:
                continue  # No data collected for this brand

            # Get latest report
            latest_report = db.query(Report).filter(
                Report.brand_id == brand.id,
                Report.user_id == brand.user_id
            ).order_by(Report.created_at.desc()).first()

            # Check if report is needed
            needs_report = False
            reason = ""

            if not latest_report:
                needs_report = True
                reason = "No reports exist"
            elif latest_batch.started_at > latest_report.created_at:
                needs_report = True
                reason = f"Batch ({latest_batch.started_at.strftime('%Y-%m-%d')}) is newer than report ({latest_report.created_at.strftime('%Y-%m-%d')})"

            if needs_report:
                brands_needing_reports.append({
                    'brand_id': brand.id,
                    'user_id': brand.user_id,
                    'brand_name': brand.brand_name,
                    'batch_id': latest_batch.id,
                    'batch_date': latest_batch.started_at.strftime('%B %d, %Y'),
                    'reason': reason
                })

        return brands_needing_reports

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Generate missing reports for all brands')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without doing it')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("=" * 70)
    print("GENERATE MISSING REPORTS")
    print("=" * 70)
    print()

    brands_needing_reports = get_brands_needing_reports()

    if not brands_needing_reports:
        print("All brands have up-to-date reports. Nothing to do.")
        return

    print(f"Found {len(brands_needing_reports)} brand(s) needing reports:")
    print()
    for b in brands_needing_reports:
        print(f"  - {b['brand_name']}")
        print(f"    User ID: {b['user_id']}, Brand ID: {b['brand_id']}")
        print(f"    Latest batch: {b['batch_date']} (ID: {b['batch_id']})")
        print(f"    Reason: {b['reason']}")
        print()

    if args.dry_run:
        print("DRY RUN - No reports generated.")
        return

    # Confirm before proceeding (unless --yes flag is passed)
    if not args.yes:
        response = input(f"Generate reports for {len(brands_needing_reports)} brand(s)? [y/N]: ")
        if response.lower() != 'y':
            print("Cancelled.")
            return

    # Import report generator
    from scripts.admin.generate_report import generate_report_main

    print()
    print("=" * 70)
    print("GENERATING REPORTS")
    print("=" * 70)

    success = 0
    failed = []

    for i, brand in enumerate(brands_needing_reports, 1):
        print(f"\n[{i}/{len(brands_needing_reports)}] Generating report for: {brand['brand_name']}")
        print(f"    user_id={brand['user_id']}, brand_id={brand['brand_id']}")
        print("-" * 70)

        try:
            generate_report_main(
                user_id=brand['user_id'],
                brand_id=brand['brand_id'],
                report_type='latest_batch'
            )
            success += 1
            print(f"\nSUCCESS: {brand['brand_name']} report generated")
        except Exception as e:
            failed.append({'brand': brand['brand_name'], 'error': str(e)})
            print(f"\nFAILED: {brand['brand_name']} - {e}")

        # Wait between reports to avoid rate limits
        if i < len(brands_needing_reports):
            print("\nWaiting 30 seconds before next report...")
            time.sleep(30)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total brands: {len(brands_needing_reports)}")
    print(f"Successful: {success}")
    print(f"Failed: {len(failed)}")

    if failed:
        print("\nFailed reports:")
        for f in failed:
            print(f"  - {f['brand']}: {f['error'][:100]}")

    print()
    print("Done!")


if __name__ == "__main__":
    main()
