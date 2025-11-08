#!/usr/bin/env python3
"""Check reports in database for recommendations."""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/tales_db")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Get recent reports
    result = conn.execute(text("""
        SELECT id, brand_id, user_id, created_at,
               LENGTH(report_content) as content_length,
               CASE
                   WHEN report_content LIKE '%Strategic Recommendations%' THEN 'YES'
                   WHEN report_content LIKE '%Recommendations%' THEN 'YES (but not Strategic)'
                   ELSE 'NO'
               END as has_recommendations
        FROM reports
        ORDER BY created_at DESC
        LIMIT 10;
    """))

    print("\nRecent Reports:")
    print("-" * 100)
    for row in result:
        print(f"ID: {row.id} | Brand: {row.brand_id} | User: {row.user_id} | Created: {row.created_at}")
        print(f"  Content Length: {row.content_length} | Has Recommendations: {row.has_recommendations}")
        print()

    # Check the most recent report content
    result = conn.execute(text("""
        SELECT report_content
        FROM reports
        ORDER BY created_at DESC
        LIMIT 1;
    """))

    row = result.fetchone()
    if row:
        content = row.report_content
        print("\nSearching for recommendations sections in most recent report...")
        if "## 4. Strategic Recommendations" in content:
            print("✓ Found: '## 4. Strategic Recommendations'")
        elif "### 6. Recommendations" in content:
            print("✓ Found: '### 6. Recommendations'")
        elif "Recommendations" in content:
            print("⚠ Found 'Recommendations' but not in expected format")
            # Find where it appears
            idx = content.find("Recommendations")
            print(f"  Preview: ...{content[max(0, idx-50):idx+100]}...")
        else:
            print("✗ No recommendations section found")
