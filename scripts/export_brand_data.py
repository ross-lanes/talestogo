"""
Export brand data (brand info, queries, descriptors, competitors) to JSON files.

This script exports all data for a specific brand from the database to JSON files
that can be imported into another database (e.g., from localhost to production).

Usage:
    python export_brand_data.py --brand-id 2 --output-dir ./brand_export
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models
from dotenv import load_dotenv
import argparse

load_dotenv()


def export_brand_data(brand_id: int, output_dir: str, database_url: str = None):
    """
    Export all data for a specific brand to JSON files.

    Args:
        brand_id: The brand ID to export
        output_dir: Directory to save the JSON files
        database_url: Optional database URL (defaults to DATABASE_URL env var)
    """
    # Get database URL
    db_url = database_url or os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL not found in environment")

    # Create database session
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Get brand info
        print(f"Exporting brand {brand_id}...")
        brand = db.query(models.BrandInfo).filter(models.BrandInfo.id == brand_id).first()
        if not brand:
            print(f"ERROR: Brand with ID {brand_id} not found")
            return False

        print(f"Found brand: {brand.brand_name}")

        # Export brand info
        brand_data = {
            "brand_name": brand.brand_name,
            "website_url": brand.website_url,
            "industry": brand.industry,
            "description": brand.description,
            "strategic_messages": brand.strategic_messages,
        }

        with open(os.path.join(output_dir, "brand_info.json"), "w") as f:
            json.dump(brand_data, f, indent=2)
        print(f"✓ Exported brand info")

        # Export queries
        queries = db.query(models.Query).filter(models.Query.brand_id == brand_id).all()
        queries_data = [
            {
                "query_id": q.query_id,
                "query_text": q.query_text,
                "category": q.category,
                "priority": q.priority,
                "target_outcome": q.target_outcome,
                "brand_in_query": q.brand_in_query,
                "active": q.active,
                "notes": q.notes,
            }
            for q in queries
        ]

        with open(os.path.join(output_dir, "queries.json"), "w") as f:
            json.dump(queries_data, f, indent=2)
        print(f"✓ Exported {len(queries_data)} queries")

        # Export descriptors
        descriptors = db.query(models.TargetDescriptor).filter(
            models.TargetDescriptor.brand_id == brand_id
        ).all()
        descriptors_data = [
            {
                "descriptor": d.descriptor,
                "is_target": d.is_target,
                "current_ownership": d.current_ownership,
                "priority": d.priority,
                "notes": d.notes,
            }
            for d in descriptors
        ]

        with open(os.path.join(output_dir, "descriptors.json"), "w") as f:
            json.dump(descriptors_data, f, indent=2)
        print(f"✓ Exported {len(descriptors_data)} descriptors")

        # Export competitors
        competitors = db.query(models.Competitor).filter(
            models.Competitor.brand_id == brand_id
        ).all()
        competitors_data = [
            {
                "organization": c.organization,
                "type": c.type,
                "focus_area": c.focus_area,
                "track": c.track,
                "key_descriptors": c.key_descriptors,
                "website": c.website,
                "notes": c.notes,
            }
            for c in competitors
        ]

        with open(os.path.join(output_dir, "competitors.json"), "w") as f:
            json.dump(competitors_data, f, indent=2)
        print(f"✓ Exported {len(competitors_data)} competitors")

        # Create summary
        summary = {
            "brand_name": brand.brand_name,
            "brand_id": brand_id,
            "exported_at": str(brand.created_at),
            "counts": {
                "queries": len(queries_data),
                "descriptors": len(descriptors_data),
                "competitors": len(competitors_data),
            }
        }

        with open(os.path.join(output_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)

        print(f"\n✓ Export completed successfully!")
        print(f"Files saved to: {output_dir}")
        print(f"  - brand_info.json")
        print(f"  - queries.json ({len(queries_data)} items)")
        print(f"  - descriptors.json ({len(descriptors_data)} items)")
        print(f"  - competitors.json ({len(competitors_data)} items)")
        print(f"  - summary.json")

        return True

    except Exception as e:
        print(f"ERROR: Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export brand data to JSON files")
    parser.add_argument("--brand-id", type=int, required=True, help="Brand ID to export")
    parser.add_argument("--output-dir", type=str, default="./brand_export",
                        help="Output directory for JSON files")
    parser.add_argument("--database-url", type=str, help="Database URL (optional, uses .env if not provided)")

    args = parser.parse_args()

    print("=" * 60)
    print("BRAND DATA EXPORT")
    print("=" * 60)

    success = export_brand_data(args.brand_id, args.output_dir, args.database_url)

    if success:
        print("\n" + "=" * 60)
        print("Next step: Import to production using:")
        print(f"python scripts/import_brand_data.py --input-dir {args.output_dir} --user-email YOUR_EMAIL")
        print("=" * 60)
        sys.exit(0)
    else:
        sys.exit(1)
