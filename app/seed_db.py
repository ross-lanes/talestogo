from app.database import SessionLocal
from app import crud, schemas

def seed_data():
    db = SessionLocal()
    try:
        print("Seeding initial data...")
        print("--- Seeding query data ---")

        # Create some sample queries
        queries_to_create = [
            schemas.QueryCreate(
                query_id="Q001",
                query_text="What is PPPL?",
                category="General",
                priority="High",
                target_outcome="Understand basic definition",
                active=True,
                notes="Initial test query"
            ),
            schemas.QueryCreate(
                query_id="Q002",
                query_text="Who are the main competitors of PPPL?",
                category="Competitor Analysis",
                priority="Medium",
                target_outcome="Identify key competitors",
                active=True,
                notes="Competitor research"
            ),
            schemas.QueryCreate(
                query_id="Q003",
                query_text="What are the latest news about PPPL?",
                category="News",
                priority="High",
                target_outcome="Stay updated on recent developments",
                active=True,
                notes="Daily news check"
            ),
            schemas.QueryCreate(query_id="Q004", query_text="What is the mission of PPPL?", category="General", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q005", query_text="What are the key research areas at PPPL?", category="Research", priority="High", active=True),
            schemas.QueryCreate(query_id="Q006", query_text="Describe the NSTX-U experiment.", category="Projects", priority="High", active=True),
            schemas.QueryCreate(query_id="Q007", query_text="How is PPPL contributing to fusion energy development?", category="Impact", priority="High", active=True),
            schemas.QueryCreate(query_id="Q008", query_text="Who funds PPPL?", category="General", priority="Low", active=True),
            schemas.QueryCreate(query_id="Q009", query_text="What educational programs does PPPL offer?", category="Education", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q010", query_text="What is a tokamak?", category="General", priority="Low", active=True),
            schemas.QueryCreate(query_id="Q011", query_text="How does a spherical tokamak differ from a conventional one?", category="Research", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q012", query_text="What is plasma?", category="General", priority="Low", active=True),
            schemas.QueryCreate(query_id="Q013", query_text="What are some recent breakthroughs from PPPL?", category="News", priority="High", active=True),
            schemas.QueryCreate(query_id="Q014", query_text="How does PPPL collaborate with other institutions?", category="Collaboration", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q015", query_text="What is the role of liquid metals in fusion research at PPPL?", category="Research", priority="High", active=True),
            schemas.QueryCreate(query_id="Q016", query_text="Is fusion energy safe?", category="General", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q017", query_text="When can we expect fusion power plants?", category="Future", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q018", query_text="Compare PPPL's approach to fusion with that of ITER.", category="Competitor Analysis", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q019", query_text="What is the significance of the LTX-β experiment?", category="Projects", priority="High", active=True),
            schemas.QueryCreate(query_id="Q020", query_text="How is AI being used in fusion research at PPPL?", category="Research", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q021", query_text="What are the environmental benefits of fusion energy?", category="Impact", priority="Medium", active=True),
            schemas.QueryCreate(query_id="Q022", query_text="Who is the director of PPPL?", category="General", priority="Low", active=True),
        ]

        new_queries_count = 0
        for query_data in queries_to_create:
            existing_query = crud.get_query_by_query_id(db, query_id=query_data.query_id)
            if not existing_query:
                crud.create_query(db, query=query_data)
                print(f"  - Created query: '{query_data.query_id}'")
                new_queries_count += 1
            else:
                print(f"  - Skipping existing query: '{query_data.query_id}'")
        print(f"--- Query seeding complete. Added {new_queries_count} new queries. ---\n")

        # --- Seed Target Descriptors ---
        print("--- Seeding descriptor data ---")
        descriptors_to_create = [
            schemas.TargetDescriptorCreate(descriptor="global leader", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="pioneering", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="innovative", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="cutting-edge", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="spherical tokamak", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="liquid lithium", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="most powerful", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="sustainable", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="energy independence", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="premier", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="world-class", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="breakthrough", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="compact", is_target=True),
            schemas.TargetDescriptorCreate(descriptor="largest", is_target=True),
        ]
        new_descriptors_count = 0
        for desc_data in descriptors_to_create:
            existing_desc = crud.get_descriptor_by_text(db, descriptor=desc_data.descriptor)
            if not existing_desc:
                crud.create_descriptor(db, descriptor=desc_data)
                print(f"  - Created descriptor: '{desc_data.descriptor}'")
                new_descriptors_count += 1
            else:
                print(f"  - Skipping existing descriptor: '{desc_data.descriptor}'")
        print(f"--- Descriptor seeding complete. Added {new_descriptors_count} new descriptors. ---\n")

        # --- Seed Competitors ---
        print("--- Seeding competitor data ---")
        competitors_to_create = [
            schemas.CompetitorCreate(organization="UKAEA (MAST-U, STEP)"),
            schemas.CompetitorCreate(organization="Tokamak Energy (ST40)"),
            schemas.CompetitorCreate(organization="Commonwealth Fusion Systems (CFS)"),
            schemas.CompetitorCreate(organization="MIT Plasma Science and Fusion Center"),
            schemas.CompetitorCreate(organization="Lawrence Livermore National Laboratory (LLNL)"),
            schemas.CompetitorCreate(organization="General Atomics (GA)"),
        ]
        new_competitors_count = 0
        for comp_data in competitors_to_create:
            existing_comp = crud.get_competitor_by_organization(db, organization=comp_data.organization)
            if not existing_comp:
                crud.create_competitor(db, competitor=comp_data)
                print(f"  - Created competitor: '{comp_data.organization}'")
                new_competitors_count += 1
            else:
                print(f"  - Skipping existing competitor: '{comp_data.organization}'")
        print(f"--- Competitor seeding complete. Added {new_competitors_count} new competitors. ---\n")

        print("--- Seeding complete. ---")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()