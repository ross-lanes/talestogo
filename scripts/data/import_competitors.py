"""
Import competitors from JSON data.
This script will ONLY import competitors and will NOT affect existing queries or descriptors.
"""
import json
from app.database import SessionLocal
from app import models

# Competitor data
competitors_data = [
    {
        "Organization":"UKAEA (MAST-U, STEP)",
        "Type":"Public",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"spherical tokamak, UK flagship, Super-X divertor, STEP prototype",
        "Website":"ccfe.ukaea.uk",
        "Notes":"DIRECT COMPETITOR: MAST-U spherical tokamak at Culham, STEP future power plant"
    },
    {
        "Organization":"Tokamak Energy (ST40)",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"HTS magnets, spherical tokamak, 100M°C achieved, commercial 2030s",
        "Website":"tokamakenergy.co.uk",
        "Notes":"DIRECT COMPETITOR: ST40 spherical tokamak, achieved 100M°C in 2022"
    },
    {
        "Organization":"MIT Plasma Science and Fusion Center",
        "Type":"Public",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"academic leader, SPARC partnership, Alcator C-Mod legacy",
        "Website":"psfc.mit.edu",
        "Notes":"Major academic competitor, partnered with CFS"
    },
    {
        "Organization":"Commonwealth Fusion Systems",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"SPARC, ARC commercial plant, high-field, $2B+ funding",
        "Website":"cfs.energy",
        "Notes":"Well-funded private competitor, MIT spin-off"
    },
    {
        "Organization":"Lawrence Livermore National Laboratory",
        "Type":"Public",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"NIF, inertial confinement, ignition breakthrough 2022",
        "Website":"llnl.gov",
        "Notes":"Different approach (inertial vs magnetic), major 2022 milestone"
    },
    {
        "Organization":"Oak Ridge National Laboratory",
        "Type":"Public",
        "Focus Area":"Fusion/Quantum/Materials",
        "Track?":"Yes",
        "Key Descriptors":"multi-mission, materials science, quantum computing",
        "Website":"ornl.gov",
        "Notes":"Multi-domain competitor"
    },
    {
        "Organization":"General Atomics",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"DIII-D tokamak, conventional tokamak leader",
        "Website":"ga.com",
        "Notes":"Largest US tokamak, different design"
    },
    {
        "Organization":"TAE Technologies",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"field-reversed configuration, alternative approach",
        "Website":"tae.com",
        "Notes":"Different confinement approach"
    },
    {
        "Organization":"IBM Quantum",
        "Type":"Private",
        "Focus Area":"Quantum Computing",
        "Track?":"Yes",
        "Key Descriptors":"quantum computing leader, 1000+ qubit systems",
        "Website":"ibm.com/quantum",
        "Notes":"Quantum space competitor"
    },
    {
        "Organization":"Google Quantum AI",
        "Type":"Private",
        "Focus Area":"Quantum Computing",
        "Track?":"Yes",
        "Key Descriptors":"quantum computing, quantum supremacy claims",
        "Website":"quantumai.google",
        "Notes":"Quantum space competitor"
    },
    {
        "Organization":"Helion Energy",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"Magneto-inertial fusion, pulsed magnetic compression, aneutronic fusion, helium-3 production",
        "Website":"helionenergy.com",
        "Notes":"Developing a technology to produce fusion power and helium-3. Uses a linear fusion system with pulsed magnetic compression. Aims for 24/7 electricity production."
    },
    {
        "Organization":"Thea Energy",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"Stellarator, planar coil, spin-out from PPPL, Eos neutron source",
        "Website":"thea.energy",
        "Notes":"A spin-out from the Princeton Plasma Physics Laboratory (PPPL). Their approach is a variant of the stellarator with simplified planar electromagnetic coils. They are building a neutron source, Eos, as an intermediate step."
    },
    {
        "Organization":"Zap Energy",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"Sheared-flow-stabilized Z-pinch, no magnetic coils, compact, scalable",
        "Website":"zapenergy.com",
        "Notes":"Aims to commercialize fusion power using a sheared-flow-stabilized Z-pinch. This method confines and compresses plasma without expensive and complex magnetic coils."
    },
    {
        "Organization":"General Fusion",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"Magnetized target fusion (MTF), liquid metal compression, compact toroid",
        "Website":"generalfusion.com",
        "Notes":"Developing a fusion power technology based on magnetized target fusion. A magnetized target is injected into a cylinder of spinning liquid metal and compressed by steam-driven pistons."
    },
    {
        "Organization":"Realta Fusion",
        "Type":"Private",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":"Compact, scalable, modular, magnetic mirror, high-temperature superconducting magnets, spin-out from University of Wisconsin-Madison",
        "Website":"realtafusion.com",
        "Notes":"An early-stage spin-out from the University of Wisconsin-Madison. They are developing a lower-cost and less complex modular fusion reactor based on a tandem mirror configuration with high-temperature-superconducting magnets."
    },
    {
        "Organization":"ITER",
        "Type":"Public",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":None,
        "Website":None,
        "Notes":None
    },
    {
        "Organization":"JET",
        "Type":"Public",
        "Focus Area":"Fusion Energy",
        "Track?":"Yes",
        "Key Descriptors":None,
        "Website":None,
        "Notes":None
    }
]

def import_competitors():
    """Import competitors from JSON data."""
    db = SessionLocal()

    try:
        print("Starting competitor import...")
        print(f"Found {len(competitors_data)} competitors to import")

        imported_count = 0
        skipped_count = 0

        for comp_data in competitors_data:
            # Check if competitor already exists
            existing = db.query(models.Competitor).filter(
                models.Competitor.organization == comp_data['Organization']
            ).first()

            if existing:
                print(f"  ⊘ Skipping '{comp_data['Organization']}' (already exists)")
                skipped_count += 1
                continue

            # Parse track field (Yes/No to boolean)
            track = comp_data.get('Track?', 'Yes').lower() == 'yes'

            # Create new competitor
            competitor = models.Competitor(
                organization=comp_data['Organization'],
                type=comp_data['Type'],
                focus_area=comp_data.get('Focus Area'),
                track=track,
                key_descriptors=comp_data.get('Key Descriptors'),
                website=comp_data.get('Website'),
                notes=comp_data.get('Notes')
            )

            db.add(competitor)
            print(f"  ✓ Imported '{comp_data['Organization']}'")
            imported_count += 1

        db.commit()

        print("\n" + "="*60)
        print("Import Summary:")
        print(f"  • Imported: {imported_count} competitors")
        print(f"  • Skipped: {skipped_count} competitors (already exist)")
        print(f"  • Total in database: {db.query(models.Competitor).count()} competitors")
        print("="*60)

        # Verify queries and descriptors were not affected
        query_count = db.query(models.Query).count()
        descriptor_count = db.query(models.TargetDescriptor).count()
        print(f"\n✓ Queries remain safe: {query_count} queries in database")
        print(f"✓ Descriptors remain safe: {descriptor_count} descriptors in database")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error during import: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import_competitors()
