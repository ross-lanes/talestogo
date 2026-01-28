#!/usr/bin/env python3
"""
Regenerate reports for DOE labs (Princeton Plasma Physics Laboratory and Oak Ridge National Laboratories)
with updated AI citation trends research and table format.
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set the DATABASE_URL to production
os.environ['DATABASE_URL'] = 'postgresql://postgres:REDACTED_RAILWAY_PASSWORD@tramway.proxy.rlwy.net:47287/railway'

from scripts.admin.generate_report import generate_report_main

def main():
    brands = [
        {"name": "Princeton Plasma Physics Laboratory", "user_id": 2, "brand_id": 1},
        {"name": "Oak Ridge National Laboratories", "user_id": 2, "brand_id": 18}
    ]

    for brand in brands:
        print("=" * 80)
        print(f"Regenerating report for: {brand['name']}")
        print(f"User ID: {brand['user_id']}, Brand ID: {brand['brand_id']}")
        print("=" * 80)
        print()

        try:
            generate_report_main(
                user_id=brand['user_id'],
                brand_id=brand['brand_id'],
                report_type='latest_batch'
            )
            print()
            print(f"✓ Successfully generated report for {brand['name']}")
            print()
        except Exception as e:
            print(f"✗ Error generating report for {brand['name']}: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 80)
    print("Report regeneration complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
