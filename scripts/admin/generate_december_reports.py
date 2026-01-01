#!/usr/bin/env python3
"""
Generate December 2025 monthly reports for all brands with December data.
Run this on Railway where the GEMINI_API_KEY has higher quota limits.

Usage:
    python3 scripts/admin/generate_december_reports.py
"""

import time
from generate_report import generate_report_main

# Brands with December 2025 data
BRANDS_TO_GENERATE = [
    {"user_id": 2, "brand_id": 1, "name": "Princeton Plasma Physics Laboratory"},
    {"user_id": 2, "brand_id": 3, "name": "Physics of Plasmas"},
    {"user_id": 10, "brand_id": 6, "name": "Salonpas"},
    {"user_id": 15, "brand_id": 14, "name": "Princeton Engineering"},
    {"user_id": 10, "brand_id": 15, "name": "RLS Radiopharmacies"},
    {"user_id": 10, "brand_id": 16, "name": "Gozellix"},
]

def main():
    print("=" * 70)
    print("GENERATING DECEMBER 2025 MONTHLY REPORTS")
    print("=" * 70)
    print()

    total = len(BRANDS_TO_GENERATE)
    success = 0
    failed = []

    for i, brand in enumerate(BRANDS_TO_GENERATE, 1):
        print(f"\n[{i}/{total}] Generating report for: {brand['name']}")
        print(f"        user_id={brand['user_id']}, brand_id={brand['brand_id']}")
        print("-" * 70)

        try:
            generate_report_main(
                user_id=brand['user_id'],
                brand_id=brand['brand_id'],
                report_type='monthly'
            )
            success += 1
            print(f"\nSUCCESS: {brand['name']} report generated")
        except Exception as e:
            failed.append({"brand": brand['name'], "error": str(e)})
            print(f"\nFAILED: {brand['name']} - {e}")

        # Wait between reports to avoid rate limits
        if i < total:
            print("\nWaiting 30 seconds before next report...")
            time.sleep(30)

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total brands: {total}")
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
