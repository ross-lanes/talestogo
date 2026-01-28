"""
One-off script to manually collect and analyze data for sl40@princeton.edu
Run this directly on Render shell: python manual_collect_sl40.py
"""
import os
import sys

# Make sure we're using production database
print("DATABASE_URL:", os.getenv('DATABASE_URL', 'NOT SET'))

sys.path.insert(0, '/app')

from app.database import SessionLocal
from app import models

# Run the collection
print("\n" + "="*80)
print("MANUAL COLLECTION FOR SL40@PRINCETON.EDU")
print("="*80 + "\n")

user_id = 15
brand_id = 5

# Just call the collection script directly with proper parameters
import subprocess

collection_cmd = [
    "python3", "/app/scripts/admin/collect_responses.py",
    str(user_id),
    "--brand-id", str(brand_id),
    "--task-id", "0"  # Dummy task ID for manual run
]

print(f"Running: {' '.join(collection_cmd)}\n")

result = subprocess.run(
    collection_cmd,
    capture_output=False,  # Let output go to console
    text=True
)

print(f"\n{'='*80}")
print(f"Collection completed with exit code: {result.returncode}")
print(f"{'='*80}\n")

if result.returncode == 0:
    print("✅ SUCCESS - Now run analysis")

    analysis_cmd = [
        "python3", "/app/analyze_responses.py",
        str(user_id),
        "--brand-id", str(brand_id),
        "--task-id", "0",
        "--auto-generate-report"
    ]

    print(f"Running: {' '.join(analysis_cmd)}\n")

    analysis_result = subprocess.run(
        analysis_cmd,
        capture_output=False,
        text=True
    )

    print(f"\n{'='*80}")
    print(f"Analysis completed with exit code: {analysis_result.returncode}")
    print(f"{'='*80}\n")

    if analysis_result.returncode == 0:
        print("✅ COMPLETE - Data collection and analysis finished!")
    else:
        print("❌ Analysis failed")
else:
    print("❌ Collection failed - check error messages above")
