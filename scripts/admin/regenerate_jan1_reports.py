#!/usr/bin/env python3
"""
Script to delete January 1, 2025 reports and regenerate them with the new monthly format.

This script:
1. Finds all reports created on January 1, 2025
2. Deletes them
3. Regenerates them using the new monthly report format

Usage:
    DATABASE_URL="your_db_url" python3 scripts/admin/regenerate_jan1_reports.py
"""

import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import SessionLocal
from app.models import Report, BrandInfo


def get_jan1_reports():
    """Find all reports created on January 1, 2025."""
    db = SessionLocal()
    try:
        # Find reports created on January 1, 2025
        reports = db.query(Report).filter(
            Report.created_at >= datetime(2025, 1, 1, 0, 0, 0),
            Report.created_at < datetime(2025, 1, 2, 0, 0, 0)
        ).all()

        return reports
    finally:
        db.close()


def delete_jan1_reports():
    """Delete all January 1, 2025 reports."""
    db = SessionLocal()
    try:
        # Find and delete reports
        deleted_count = db.query(Report).filter(
            Report.created_at >= datetime(2025, 1, 1, 0, 0, 0),
            Report.created_at < datetime(2025, 1, 2, 0, 0, 0)
        ).delete()

        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def get_brand_user_pairs():
    """Get unique (user_id, brand_id) pairs from the deleted reports."""
    db = SessionLocal()
    try:
        # Get all active brands
        brands = db.query(BrandInfo).filter(BrandInfo.is_active == True).all()
        return [(brand.user_id, brand.id, brand.brand_name) for brand in brands]
    finally:
        db.close()


def main():
    print("="*70)
    print("REGENERATE JANUARY 1, 2025 REPORTS")
    print("="*70)
    print()

    # Check for existing January 1 reports
    reports = get_jan1_reports()

    if not reports:
        print("No reports found for January 1, 2025.")
        print("\nTo generate new monthly reports, use the web interface or run:")
        print("  python3 scripts/admin/generate_report.py --user-id <id> --brand-id <id> --report-type monthly")
        return

    print(f"Found {len(reports)} reports from January 1, 2025:")
    for report in reports:
        print(f"  - ID {report.id}: {report.title} (Brand ID: {report.brand_id})")

    print()
    response = input("Delete these reports and regenerate with monthly format? [y/N]: ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    # Collect brand info before deleting
    brand_info = []
    for report in reports:
        brand_info.append({
            'user_id': report.user_id,
            'brand_id': report.brand_id,
            'title': report.title
        })

    # Delete the reports
    print("\nDeleting old reports...")
    deleted_count = delete_jan1_reports()
    print(f"Deleted {deleted_count} reports.")

    # Regenerate reports
    print("\nRegenerating reports with monthly format...")
    print("="*70)

    # Import here to avoid circular imports
    from scripts.admin.generate_report import generate_report_main

    unique_pairs = list(set((b['user_id'], b['brand_id']) for b in brand_info))

    for user_id, brand_id in unique_pairs:
        print(f"\nGenerating monthly report for user_id={user_id}, brand_id={brand_id}...")
        try:
            generate_report_main(user_id, brand_id, report_type='monthly')
            print(f"Successfully generated monthly report for brand_id={brand_id}")
        except Exception as e:
            print(f"ERROR generating report for brand_id={brand_id}: {e}")

    print()
    print("="*70)
    print("REGENERATION COMPLETE")
    print("="*70)


if __name__ == '__main__':
    main()
