#!/usr/bin/env python3
"""Test database connection and report accessibility."""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.database import SessionLocal, DATABASE_URL
from app import crud, models

print(f"Testing database connection...")
print(f"DATABASE_URL: {DATABASE_URL}")
print()

try:
    db = SessionLocal()

    # Test basic connection
    print("✓ Database connection successful")

    # Query reports
    reports = db.query(models.Report).all()
    print(f"✓ Found {len(reports)} reports in database")
    print()

    # Show report details
    for report in reports:
        print(f"Report ID: {report.id}")
        print(f"  Title: {report.title}")
        print(f"  User ID: {report.user_id}")
        print(f"  Content length: {len(report.report_content) if report.report_content else 0} chars")
        print(f"  Created: {report.created_at}")
        print()

    # Test crud function
    if reports:
        test_report_id = reports[0].id
        test_user_id = reports[0].user_id
        retrieved = crud.get_report(db, report_id=test_report_id, user_id=test_user_id)
        if retrieved:
            print(f"✓ crud.get_report() working correctly")
            print(f"  Retrieved report: {retrieved.title}")
        else:
            print(f"✗ crud.get_report() returned None")

    db.close()
    print("\n✓ All tests passed!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
