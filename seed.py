import json
from app.database import SessionLocal
from app import crud, schemas


def seed_queries():
    """
    Reads queries from a JSON file and posts them to the API one by one.
    This version connects directly to the database.
    """
    db = SessionLocal()
    try:
        print("--- Seeding query data ---")
        json_file = "queries.json"

        try:
            with open(json_file, 'r') as f:
                queries_to_add = json.load(f)
            print(f"Found {len(queries_to_add)} queries to load from {json_file}.")
        except FileNotFoundError:
            print(f"ERROR: The file '{json_file}' was not found. Skipping query seeding.")
            return
        except json.JSONDecodeError:
            print(f"ERROR: Could not decode JSON from '{json_file}'. Please check for syntax errors.")
            return

        added_count = 0
        for query_data in queries_to_add:
            # Check if a query with the same query_id already exists
            existing_query = crud.get_query_by_query_id(db, query_id=query_data["query_id"])
            if existing_query:
                print(f"Skipping existing query: '{query_data['query_id']}'")
                continue

            # Create a schema object and add to the database
            query_schema = schemas.QueryCreate(**query_data)
            crud.create_query(db=db, query=query_schema)
            print(f"Added query: '{query_data['query_id']}'")
            added_count += 1

        print(f"--- Query seeding complete. Added {added_count} new queries. ---")

    finally:
        db.close()

def seed_descriptors():
    """
    Populates the database with initial descriptor data.
    Checks for existing descriptors to prevent duplicates.
    """
    db = SessionLocal()
    try:
        print("\n--- Seeding descriptor data ---")

        descriptors_to_add = [
            {"descriptor": "global leader", "category": "Leadership", "target_for_pppl": True, "current_ownership": "Contested", "priority": "High", "notes": "Core positioning term"},
            {"descriptor": "pioneering", "category": "Leadership", "target_for_pppl": True, "current_ownership": "PPPL/historical", "priority": "High", "notes": "Spherical tokamak + stellarator heritage"},
            {"descriptor": "innovative", "category": "Innovation", "target_for_pppl": True, "current_ownership": "Multiple", "priority": "High", "notes": "Technology advancement"},
            {"descriptor": "cutting-edge", "category": "Innovation", "target_for_pppl": True, "current_ownership": "Multiple", "priority": "High", "notes": "Latest technology"},
            {"descriptor": "spherical tokamak", "category": "Technology", "target_for_pppl": True, "current_ownership": "PPPL/UKAEA/Tokamak Energy", "priority": "High", "notes": "PPPL differentiator"},
            {"descriptor": "liquid lithium", "category": "Technology", "target_for_pppl": True, "current_ownership": "PPPL", "priority": "High", "notes": "Unique PPPL expertise"},
            {"descriptor": "most powerful", "category": "Scale", "target_for_pppl": True, "current_ownership": "Target for NSTX-U", "priority": "High", "notes": "Power positioning"},
            {"descriptor": "sustainable", "category": "Mission", "target_for_pppl": True, "current_ownership": "Industry-wide", "priority": "Medium", "notes": "Environmental narrative"},
            {"descriptor": "energy independence", "category": "Mission", "target_for_pppl": True, "current_ownership": "PPPL messaging", "priority": "Medium", "notes": "Strategic importance"},
            {"descriptor": "premier", "category": "Leadership", "target_for_pppl": False, "current_ownership": "Multiple labs", "priority": "Medium", "notes": "Prestige positioning"},
            {"descriptor": "world-class", "category": "Leadership", "target_for_pppl": False, "current_ownership": "Multiple labs", "priority": "Medium", "notes": "Quality indicator"},
            {"descriptor": "breakthrough", "category": "Innovation", "target_for_pppl": False, "current_ownership": "LLNL (ignition)", "priority": "High", "notes": "Major achievement term"},
            {"descriptor": "compact", "category": "Technology", "target_for_pppl": False, "current_ownership": "Spherical tokamak labs", "priority": "Medium", "notes": "Design advantage"},
            {"descriptor": "largest", "category": "Scale", "target_for_pppl": False, "current_ownership": "GA (DIII-D)", "priority": "Low", "notes": "NSTX-U largest spherical, but not largest overall"},
        ]

        added_count = 0
        for desc_data in descriptors_to_add:
            # Check if a descriptor with the same name already exists
            existing_desc = crud.get_descriptor_by_name(db, name=desc_data["descriptor"])
            if existing_desc:
                print(f"Skipping existing descriptor: '{desc_data['descriptor']}'")
                continue

            # Create a schema object and add to the database
            descriptor_schema = schemas.TargetDescriptorCreate(**desc_data)
            crud.create_descriptor(db=db, descriptor=descriptor_schema)
            print(f"Added descriptor: '{desc_data['descriptor']}'")
            added_count += 1

        print(f"--- Descriptor seeding complete. Added {added_count} new descriptors. ---")

    finally:
        db.close()

def seed_competitors():
    """
    Populates the database with initial competitor data.
    Checks for existing competitors to prevent duplicates.
    """
    db = SessionLocal()
    try:
        print("\n--- Seeding competitor data ---")

        competitors_to_add = [
            {"organization": "UKAEA (MAST-U, STEP)", "type": "Public", "focus_area": "Spherical Tokamaks, Fusion Power Plant Design", "track": True, "key_descriptors": "Super-X divertor, STEP prototype", "website": "ccfe.ukaea.uk", "notes": "Direct competitor in spherical tokamak design."},
            {"organization": "Tokamak Energy (ST40)", "type": "Private", "focus_area": "High-Field Spherical Tokamaks, HTS Magnets", "track": True, "key_descriptors": "HTS magnets, spherical tokamak, commercial 2030s", "website": "tokamakenergy.co.uk", "notes": "Direct private sector spherical tokamak competitor."},
            {"organization": "Commonwealth Fusion Systems (CFS)", "type": "Private", "focus_area": "SPARC, ARC commercial plant, High-Field Magnets", "track": True, "key_descriptors": "high-field, $2B+ funding, MIT spin-off", "website": "cfs.energy", "notes": "Major well-funded private competitor."},
            {"organization": "MIT Plasma Science and Fusion Center", "type": "Public", "focus_area": "Academic Research, SPARC partnership", "track": True, "key_descriptors": "academic leader, Alcator C-Mod legacy", "website": "psfc.mit.edu", "notes": "Major academic partner and competitor (via CFS link)."},
            {"organization": "Lawrence Livermore National Laboratory (LLNL)", "type": "Public", "focus_area": "Inertial Confinement Fusion (NIF)", "track": True, "key_descriptors": "NIF, ignition breakthrough 2022, inertial confinement", "website": "llnl.gov", "notes": "Competitor in a different fusion approach (magnetic vs inertial)."},
            {"organization": "General Atomics (GA)", "type": "Private", "focus_area": "Conventional Tokamaks (DIII-D)", "track": True, "key_descriptors": "DIII-D tokamak, conventional tokamak leader", "website": "ga.com", "notes": "Manages the largest US tokamak."}
        ]

        added_count = 0
        for comp_data in competitors_to_add:
            # Check if a competitor with the same name already exists
            existing_comp = crud.get_competitor_by_organization(db, organization=comp_data["organization"])
            if existing_comp:
                print(f"Skipping existing competitor: '{comp_data['organization']}'")
                continue

            # Create a schema object and add to the database
            competitor_schema = schemas.CompetitorCreate(**comp_data)
            crud.create_competitor(db=db, competitor=competitor_schema)
            print(f"Added competitor: '{comp_data['organization']}'")
            added_count += 1

        print(f"--- Competitor seeding complete. Added {added_count} new competitors. ---")

    finally:
        db.close()

if __name__ == "__main__":
    # Run all seeding functions
    seed_queries()
    seed_descriptors()
    seed_competitors()

    
