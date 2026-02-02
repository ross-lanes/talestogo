#!/usr/bin/env python3
"""
Convert SQLite database export to brand import format.

This script converts the tales_export JSON format (full database dump)
to the brand-specific import format expected by import_brand_data.py.

Usage:
    python scripts/admin/convert_sqlite_export.py \
        --input tales_export_20251106_202307.json \
        --brand "Princeton Plasma Physics Laboratory" \
        --output pppl_brand.json
"""

import argparse
import json
import sys
from datetime import datetime


def convert_export(input_file: str, brand_name: str, output_file: str):
    """Convert database export to brand import format."""

    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Find the brand
    brand = None
    for b in data.get('brands', []):
        if brand_name.lower() in b['brand_name'].lower():
            brand = b
            break

    if not brand:
        print(f"ERROR: Brand '{brand_name}' not found")
        print("\nAvailable brands:")
        for b in data.get('brands', []):
            print(f"  - {b['brand_name']} (ID: {b['id']})")
        sys.exit(1)

    brand_id = brand['id']
    print(f"Found brand: {brand['brand_name']} (ID: {brand_id})")

    # Get owner email if available
    owner_email = "unknown"
    for u in data.get('users', []):
        if u['id'] == brand.get('user_id'):
            owner_email = u['email']
            break

    # Build export data in import format
    export_data = {
        "export_info": {
            "exported_at": datetime.utcnow().isoformat(),
            "source_system": f"Converted from {data.get('source', 'SQLite export')}",
            "tales_version": "1.0.0",
            "brand_id": brand_id,
            "original_owner_email": owner_email
        },
        "brand": {
            "name": brand['brand_name'],
            "website_url": brand.get('website_url'),
            "industry": brand.get('industry'),
            "description": brand.get('description'),
            "strategic_messages": brand.get('strategic_messages')
        },
        "queries": [],
        "competitors": [],
        "descriptors": [],
        "collection_batches": [],
        "responses": [],
        "reports": []
    }

    # Filter queries for this brand
    for q in data.get('queries', []):
        if q.get('brand_id') == brand_id:
            export_data["queries"].append({
                "query_id": q.get('query_id'),
                "query_text": q.get('query_text'),
                "category": q.get('category'),
                "priority": q.get('priority'),
                "target_outcome": q.get('target_outcome'),
                "brand_in_query": q.get('brand_in_query'),
                "active": q.get('active', True),
                "notes": q.get('notes'),
                "created_at": q.get('created_at')
            })
    print(f"Queries: {len(export_data['queries'])}")

    # Filter competitors for this brand
    for c in data.get('competitors', []):
        if c.get('brand_id') == brand_id:
            export_data["competitors"].append({
                "organization": c.get('organization'),
                "type": c.get('type'),
                "focus_area": c.get('focus_area'),
                "track": c.get('track', True),
                "key_descriptors": c.get('key_descriptors'),
                "website": c.get('website'),
                "notes": c.get('notes')
            })
    print(f"Competitors: {len(export_data['competitors'])}")

    # Filter descriptors for this brand
    for d in data.get('target_descriptors', []):
        if d.get('brand_id') == brand_id:
            export_data["descriptors"].append({
                "descriptor": d.get('descriptor'),
                "is_target": d.get('is_target', True),
                "current_ownership": d.get('current_ownership'),
                "priority": d.get('priority'),
                "notes": d.get('notes')
            })
    print(f"Descriptors: {len(export_data['descriptors'])}")

    # Filter responses for this brand
    for r in data.get('responses', []):
        if r.get('brand_id') == brand_id:
            export_data["responses"].append({
                "query_id": r.get('query_id'),
                "query_text": r.get('query_text'),
                "platform": r.get('platform'),
                "response_text": r.get('response_text'),
                "timestamp": r.get('timestamp'),
                "batch_name": None,  # Not available in old format
                "brand_mentioned": r.get('brand_mentioned'),
                "brand_position": r.get('brand_position'),
                "sentiment": r.get('sentiment'),
                "descriptors": r.get('descriptors'),
                "competitors": r.get('competitors'),
                "sources": r.get('sources'),
                "campaign_period": r.get('campaign_period'),
                "notes": r.get('notes'),
                "analyzed_at": r.get('analyzed_at')
            })
    print(f"Responses: {len(export_data['responses'])}")

    # Filter reports for this brand
    for r in data.get('reports', []):
        if r.get('brand_id') == brand_id:
            export_data["reports"].append({
                "title": r.get('title'),
                "report_content": r.get('report_content'),
                "report_type": r.get('report_type'),
                "period_label": r.get('period_label'),
                "start_date": r.get('start_date'),
                "end_date": r.get('end_date'),
                "total_responses": r.get('total_responses'),
                "mention_rate": r.get('mention_rate'),
                "google_doc_url": r.get('google_doc_url'),
                "created_at": r.get('created_at')
            })
    print(f"Reports: {len(export_data['reports'])}")

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    import os
    print(f"\n{'='*60}")
    print("CONVERSION COMPLETE")
    print(f"{'='*60}")
    print(f"Brand: {brand['brand_name']}")
    print(f"Output: {output_file}")
    print(f"File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    print("\nNote: This is converted from an older export.")
    print("For latest data, export directly from production database.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert SQLite database export to brand import format"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input JSON file (SQLite export format)"
    )
    parser.add_argument(
        "--brand", "-b",
        required=True,
        help="Brand name to extract (partial match supported)"
    )
    parser.add_argument(
        "--output", "-o",
        default="brand_export.json",
        help="Output JSON file path (default: brand_export.json)"
    )

    args = parser.parse_args()
    convert_export(args.input, args.brand, args.output)


if __name__ == "__main__":
    main()
