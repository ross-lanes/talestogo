"""
Import descriptors from JSON data.
This script will ONLY import descriptors and will NOT affect existing queries or competitors.
"""
import json
from app.database import SessionLocal
from app import models

# Descriptor data
descriptors_data = [
  {
    "descriptor": "global leader",
    "category": "Leadership",
    "target_for_pppl": True,
    "current_ownership": "Contested",
    "priority": "High",
    "notes": "Core positioning term"
  },
  {
    "descriptor": "pioneering",
    "category": "Leadership",
    "target_for_pppl": True,
    "current_ownership": "PPPL/historical",
    "priority": "High",
    "notes": "Spherical tokamak + stellarator heritage"
  },
  {
    "descriptor": "innovative",
    "category": "Innovation",
    "target_for_pppl": True,
    "current_ownership": "Multiple",
    "priority": "High",
    "notes": "Technology advancement"
  },
  {
    "descriptor": "cutting-edge",
    "category": "Innovation",
    "target_for_pppl": True,
    "current_ownership": "Multiple",
    "priority": "High",
    "notes": "Latest technology"
  },
  {
    "descriptor": "spherical tokamak",
    "category": "Technology",
    "target_for_pppl": True,
    "current_ownership": "PPPL/UKAEA/Tokamak Energy",
    "priority": "High",
    "notes": "PPPL differentiator"
  },
  {
    "descriptor": "liquid lithium",
    "category": "Technology",
    "target_for_pppl": True,
    "current_ownership": "PPPL",
    "priority": "High",
    "notes": "Unique PPPL expertise"
  },
  {
    "descriptor": "most powerful",
    "category": "Scale",
    "target_for_pppl": True,
    "current_ownership": "Target for NSTX-U",
    "priority": "High",
    "notes": "Power positioning"
  },
  {
    "descriptor": "sustainable",
    "category": "Mission",
    "target_for_pppl": True,
    "current_ownership": "Industry-wide",
    "priority": "Medium",
    "notes": "Environmental narrative"
  },
  {
    "descriptor": "energy independence",
    "category": "Mission",
    "target_for_pppl": True,
    "current_ownership": "PPPL messaging",
    "priority": "Medium",
    "notes": "Strategic importance"
  }
]

def import_descriptors():
    """Import descriptors from JSON data."""
    db = SessionLocal()

    try:
        print("Starting descriptor import...")
        print(f"Found {len(descriptors_data)} descriptors to import")

        imported_count = 0
        skipped_count = 0

        for desc_data in descriptors_data:
            # Check if descriptor already exists
            existing = db.query(models.TargetDescriptor).filter(
                models.TargetDescriptor.descriptor == desc_data['descriptor']
            ).first()

            if existing:
                print(f"  ⊘ Skipping '{desc_data['descriptor']}' (already exists)")
                skipped_count += 1
                continue

            # Create new descriptor
            descriptor = models.TargetDescriptor(
                descriptor=desc_data['descriptor'],
                category=desc_data['category'],
                target_for_pppl=desc_data['target_for_pppl'],
                current_ownership=desc_data.get('current_ownership'),
                priority=desc_data['priority'],
                notes=desc_data.get('notes')
            )

            db.add(descriptor)
            print(f"  ✓ Imported '{desc_data['descriptor']}'")
            imported_count += 1

        db.commit()

        print("\n" + "="*60)
        print("Import Summary:")
        print(f"  • Imported: {imported_count} descriptors")
        print(f"  • Skipped: {skipped_count} descriptors (already exist)")
        print(f"  • Total in database: {db.query(models.TargetDescriptor).count()} descriptors")
        print("="*60)

        # Verify queries were not affected
        query_count = db.query(models.Query).count()
        print(f"\n✓ Queries remain safe: {query_count} queries in database")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error during import: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import_descriptors()
