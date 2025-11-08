#!/usr/bin/env python3
"""Test the recommendations API endpoint."""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/tales_db")
engine = create_engine(DATABASE_URL)

# Simulate what the API does
with engine.connect() as conn:
    # Get most recent report for user 2 (assuming that's the current user)
    result = conn.execute(text("""
        SELECT id, brand_id, report_content, created_at, total_responses
        FROM reports
        WHERE user_id = 2
        ORDER BY created_at DESC
        LIMIT 1;
    """))

    latest_report = result.fetchone()

    if latest_report:
        print(f"Latest Report ID: {latest_report.id}")
        print(f"Brand ID: {latest_report.brand_id}")
        print(f"Created: {latest_report.created_at}")
        print(f"Total Responses: {latest_report.total_responses}")
        print()

        report_content = latest_report.report_content
        recommendations_text = ""

        # Current logic from the API
        if "## 4. Strategic Recommendations" in report_content:
            print("✓ Found '## 4. Strategic Recommendations' section")
            sections = report_content.split("\n## ")
            for section in sections:
                if section.startswith("4. Strategic Recommendations"):
                    recommendations_text = section
                    next_section_pos = recommendations_text.find("\n## ", 3)
                    if next_section_pos > 0:
                        recommendations_text = recommendations_text[:next_section_pos]
                    break
        else:
            print("✗ Did NOT find '## 4. Strategic Recommendations'")
            print("\nLooking for other recommendation formats...")

            if "### 6. Recommendations" in report_content:
                print("✓ Found '### 6. Recommendations' instead!")

            # Show all section headers
            print("\nAll section headers in report:")
            for line in report_content.split('\n'):
                if line.startswith('##'):
                    print(f"  {line[:80]}")

        print(f"\nRecommendations text length: {len(recommendations_text)}")
        print(f"Has recommendations: {bool(recommendations_text)}")
