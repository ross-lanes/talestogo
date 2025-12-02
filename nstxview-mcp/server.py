"""
NSTXView MCP Server

Model Context Protocol server for accessing NSTX/NSTX-U plasma physics
research data. Can be used alongside CollisionDB MCP for comprehensive
plasma physics research.
"""

import os
import json
from typing import Optional
from datetime import datetime

from fastmcp import FastMCP

# Database connection
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "")
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))


# Initialize MCP server
mcp = FastMCP(
    name="NSTXView Server",
    instructions="""
    NSTXView provides access to extracted information from ~90 scholarly
    papers about NSTX and NSTX-U plasma physics experiments at Princeton
    Plasma Physics Laboratory.

    ## Key Concepts

    ### Shots
    Individual plasma experiments, identified by 6-digit numbers starting with 1
    (e.g., 141234, 138576). Each shot represents a specific plasma discharge
    with unique parameters and phenomena.

    ### Parameters
    Quantitative plasma measurements including:
    - **Plasma**: Ion/electron temperature (keV), density (m^-3), pressure, beta
    - **Operational**: Plasma current (MA), magnetic field (T), heating power (MW)
    - **Performance**: H-factor, confinement time, stored energy

    ### Phenomena
    Observed physics categorized as:
    - **Instabilities**: ELMs, kink modes, tearing modes, Alfvén eigenmodes
    - **Confinement**: H-mode, L-mode, transport barriers
    - **Disruptions**: VDEs, runaway electrons, thermal quench

    ## Integration with CollisionDB
    This server can be used alongside the CollisionDB MCP to cross-reference
    plasma parameters with atomic collision data. For example:
    - Find collision cross sections for species mentioned in papers
    - Look up rate coefficients for impurity species
    - Cross-reference plasma temperatures with collision energy ranges

    ## Common Queries
    - "What papers discuss H-mode transitions?"
    - "Show parameters for shot 141234"
    - "What phenomena are associated with high beta?"
    - "Find papers about lithium wall conditioning"
    """
)


# Database helper
def get_db_session():
    """Get a database session"""
    if not DATABASE_URL:
        return None
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()


# === Tools ===

@mcp.tool()
def search_papers(
    query: str,
    limit: int = 10
) -> str:
    """
    Search across paper content using semantic search.

    Args:
        query: Natural language search query
        limit: Maximum number of results (default 10)

    Returns:
        JSON with matching papers and relevant excerpts
    """
    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database not configured"})

    try:
        # Simple text search fallback (ChromaDB integration would be better)
        search_term = f"%{query}%"
        result = db.execute(text("""
            SELECT id, title, authors, abstract, doi, journal
            FROM nstx_papers
            WHERE title ILIKE :search
               OR abstract ILIKE :search
               OR extracted_text ILIKE :search
            LIMIT :limit
        """), {"search": search_term, "limit": limit})

        papers = []
        for row in result:
            papers.append({
                "id": row.id,
                "title": row.title,
                "authors": json.loads(row.authors) if row.authors else None,
                "abstract": row.abstract[:500] + "..." if row.abstract and len(row.abstract) > 500 else row.abstract,
                "doi": row.doi,
                "journal": row.journal
            })

        return json.dumps({
            "query": query,
            "count": len(papers),
            "papers": papers
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@mcp.tool()
def get_paper_details(paper_id: int) -> str:
    """
    Get full extracted information for a specific paper.

    Args:
        paper_id: Database ID of the paper

    Returns:
        JSON with complete paper metadata, shots, parameters, and phenomena
    """
    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database not configured"})

    try:
        # Get paper
        paper_result = db.execute(text("""
            SELECT id, title, authors, abstract, doi, journal, publication_date,
                   experiment_type, key_findings, status
            FROM nstx_papers WHERE id = :id
        """), {"id": paper_id})
        paper_row = paper_result.fetchone()

        if not paper_row:
            return json.dumps({"error": f"Paper {paper_id} not found"})

        # Get shots
        shots_result = db.execute(text("""
            SELECT shot_number, role, context, characteristics
            FROM nstx_shots WHERE paper_id = :id
        """), {"id": paper_id})
        shots = [
            {
                "shot_number": row.shot_number,
                "role": row.role,
                "context": row.context,
                "characteristics": json.loads(row.characteristics) if row.characteristics else None
            }
            for row in shots_result
        ]

        # Get parameters
        params_result = db.execute(text("""
            SELECT p.parameter_name, p.parameter_category, p.value, p.unit,
                   p.uncertainty, s.shot_number, p.context
            FROM nstx_parameters p
            LEFT JOIN nstx_shots s ON p.shot_id = s.id
            WHERE p.paper_id = :id
        """), {"id": paper_id})
        parameters = [
            {
                "name": row.parameter_name,
                "category": row.parameter_category,
                "value": row.value,
                "unit": row.unit,
                "uncertainty": row.uncertainty,
                "shot_number": row.shot_number,
                "context": row.context
            }
            for row in params_result
        ]

        # Get phenomena
        phenom_result = db.execute(text("""
            SELECT ph.phenomenon_type, ph.phenomenon_category, ph.description,
                   ph.is_primary_focus, s.shot_number
            FROM nstx_phenomena ph
            LEFT JOIN nstx_shots s ON ph.shot_id = s.id
            WHERE ph.paper_id = :id
        """), {"id": paper_id})
        phenomena = [
            {
                "type": row.phenomenon_type,
                "category": row.phenomenon_category,
                "description": row.description,
                "is_primary_focus": row.is_primary_focus,
                "shot_number": row.shot_number
            }
            for row in phenom_result
        ]

        return json.dumps({
            "paper": {
                "id": paper_row.id,
                "title": paper_row.title,
                "authors": json.loads(paper_row.authors) if paper_row.authors else None,
                "abstract": paper_row.abstract,
                "doi": paper_row.doi,
                "journal": paper_row.journal,
                "publication_date": str(paper_row.publication_date) if paper_row.publication_date else None,
                "experiment_type": paper_row.experiment_type,
                "key_findings": json.loads(paper_row.key_findings) if paper_row.key_findings else None
            },
            "shots": shots,
            "parameters": parameters,
            "phenomena": phenomena
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@mcp.tool()
def query_shots(
    shot_numbers: Optional[str] = None,
    min_shot: Optional[int] = None,
    max_shot: Optional[int] = None,
    role: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Find shots matching specific criteria.

    Args:
        shot_numbers: Comma-separated shot numbers (e.g., "141234,141235")
        min_shot: Minimum shot number
        max_shot: Maximum shot number
        role: Filter by role ("primary", "comparison", "reference")
        limit: Maximum results (default 20)

    Returns:
        JSON with matching shots and their associated papers
    """
    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database not configured"})

    try:
        conditions = []
        params = {"limit": limit}

        if shot_numbers:
            nums = [int(n.strip()) for n in shot_numbers.split(",")]
            conditions.append("s.shot_number IN :shot_nums")
            params["shot_nums"] = tuple(nums)

        if min_shot:
            conditions.append("s.shot_number >= :min_shot")
            params["min_shot"] = min_shot

        if max_shot:
            conditions.append("s.shot_number <= :max_shot")
            params["max_shot"] = max_shot

        if role:
            conditions.append("s.role = :role")
            params["role"] = role

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        result = db.execute(text(f"""
            SELECT s.shot_number, s.role, s.context, p.id as paper_id, p.title
            FROM nstx_shots s
            JOIN nstx_papers p ON s.paper_id = p.id
            WHERE {where_clause}
            ORDER BY s.shot_number
            LIMIT :limit
        """), params)

        shots = []
        for row in result:
            shots.append({
                "shot_number": row.shot_number,
                "role": row.role,
                "context": row.context,
                "paper_id": row.paper_id,
                "paper_title": row.title
            })

        return json.dumps({
            "count": len(shots),
            "shots": shots
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@mcp.tool()
def get_shot_details(shot_number: int) -> str:
    """
    Get all information about a specific shot across all papers.

    Shot numbers are 6-digit integers starting with 1 (e.g., 141234).

    Args:
        shot_number: The 6-digit shot number

    Returns:
        JSON with all data from all papers mentioning this shot
    """
    if not (100000 <= shot_number <= 199999):
        return json.dumps({"error": "Shot number must be 6 digits starting with 1 (100000-199999)"})

    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database not configured"})

    try:
        # Get all occurrences of this shot
        result = db.execute(text("""
            SELECT s.id, s.role, s.context, s.characteristics,
                   p.id as paper_id, p.title, p.publication_date
            FROM nstx_shots s
            JOIN nstx_papers p ON s.paper_id = p.id
            WHERE s.shot_number = :shot_number
        """), {"shot_number": shot_number})

        occurrences = []
        for row in result:
            shot_id = row.id

            # Get parameters for this shot occurrence
            params_result = db.execute(text("""
                SELECT parameter_name, parameter_category, value, unit, uncertainty, context
                FROM nstx_parameters
                WHERE shot_id = :shot_id
            """), {"shot_id": shot_id})
            parameters = [
                {
                    "name": p.parameter_name,
                    "category": p.parameter_category,
                    "value": p.value,
                    "unit": p.unit,
                    "uncertainty": p.uncertainty
                }
                for p in params_result
            ]

            # Get phenomena for this shot occurrence
            phenom_result = db.execute(text("""
                SELECT phenomenon_type, phenomenon_category, description, is_primary_focus
                FROM nstx_phenomena
                WHERE shot_id = :shot_id
            """), {"shot_id": shot_id})
            phenomena = [
                {
                    "type": ph.phenomenon_type,
                    "category": ph.phenomenon_category,
                    "description": ph.description,
                    "is_primary_focus": ph.is_primary_focus
                }
                for ph in phenom_result
            ]

            occurrences.append({
                "paper_id": row.paper_id,
                "paper_title": row.title,
                "publication_date": str(row.publication_date) if row.publication_date else None,
                "role": row.role,
                "context": row.context,
                "characteristics": json.loads(row.characteristics) if row.characteristics else None,
                "parameters": parameters,
                "phenomena": phenomena
            })

        if not occurrences:
            return json.dumps({"error": f"No data found for shot {shot_number}"})

        return json.dumps({
            "shot_number": shot_number,
            "paper_count": len(occurrences),
            "occurrences": occurrences
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@mcp.tool()
def get_parameter_statistics(parameter_name: str) -> str:
    """
    Get aggregate statistics for a specific parameter across all papers.

    Args:
        parameter_name: Name of the parameter (e.g., "ion_temperature", "plasma_current")

    Returns:
        JSON with statistics (min, max, avg, count) and list of values by paper
    """
    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database not configured"})

    try:
        # Get aggregate stats
        stats_result = db.execute(text("""
            SELECT
                COUNT(*) as count,
                MIN(value) as min_value,
                MAX(value) as max_value,
                AVG(value) as avg_value
            FROM nstx_parameters
            WHERE parameter_name = :name AND value IS NOT NULL
        """), {"name": parameter_name})
        stats_row = stats_result.fetchone()

        # Get all values with context
        values_result = db.execute(text("""
            SELECT p.value, p.unit, p.uncertainty, p.context,
                   s.shot_number, paper.title, paper.id as paper_id
            FROM nstx_parameters p
            JOIN nstx_papers paper ON p.paper_id = paper.id
            LEFT JOIN nstx_shots s ON p.shot_id = s.id
            WHERE p.parameter_name = :name
            ORDER BY p.value
        """), {"name": parameter_name})

        values = [
            {
                "value": row.value,
                "unit": row.unit,
                "uncertainty": row.uncertainty,
                "shot_number": row.shot_number,
                "paper_id": row.paper_id,
                "paper_title": row.title
            }
            for row in values_result
        ]

        if stats_row.count == 0:
            return json.dumps({"error": f"No data found for parameter: {parameter_name}"})

        return json.dumps({
            "parameter_name": parameter_name,
            "statistics": {
                "count": stats_row.count,
                "min": stats_row.min_value,
                "max": stats_row.max_value,
                "average": round(stats_row.avg_value, 4) if stats_row.avg_value else None
            },
            "values": values
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@mcp.tool()
def list_parameters() -> str:
    """
    Get a list of all unique parameter names with counts.

    Returns:
        JSON with list of parameters, their categories, and occurrence counts
    """
    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database not configured"})

    try:
        result = db.execute(text("""
            SELECT parameter_name, parameter_category, COUNT(*) as count
            FROM nstx_parameters
            GROUP BY parameter_name, parameter_category
            ORDER BY count DESC
        """))

        parameters = [
            {
                "name": row.parameter_name,
                "category": row.parameter_category,
                "count": row.count
            }
            for row in result
        ]

        return json.dumps({
            "total_unique": len(parameters),
            "parameters": parameters
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@mcp.tool()
def list_phenomena() -> str:
    """
    Get a list of all unique phenomenon types with counts.

    Returns:
        JSON with list of phenomena, their categories, and occurrence counts
    """
    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database not configured"})

    try:
        result = db.execute(text("""
            SELECT phenomenon_type, phenomenon_category, COUNT(*) as count
            FROM nstx_phenomena
            GROUP BY phenomenon_type, phenomenon_category
            ORDER BY count DESC
        """))

        phenomena = [
            {
                "type": row.phenomenon_type,
                "category": row.phenomenon_category,
                "count": row.count
            }
            for row in result
        ]

        return json.dumps({
            "total_unique": len(phenomena),
            "phenomena": phenomena
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


@mcp.tool()
def find_related_collision_data(paper_id: int) -> str:
    """
    Suggest CollisionDB queries based on species mentioned in a paper.

    Use this to cross-reference paper findings with atomic collision data.
    The suggestions can be used with the CollisionDB MCP server.

    Args:
        paper_id: Database ID of the paper

    Returns:
        JSON with suggested species and CollisionDB query suggestions
    """
    db = get_db_session()
    if not db:
        return json.dumps({"error": "Database not configured"})

    try:
        # Get paper text
        result = db.execute(text("""
            SELECT title, abstract, extracted_text
            FROM nstx_papers WHERE id = :id
        """), {"id": paper_id})
        row = result.fetchone()

        if not row:
            return json.dumps({"error": f"Paper {paper_id} not found"})

        text_content = f"{row.title or ''} {row.abstract or ''}"

        # Common species in fusion experiments
        species_patterns = {
            "deuterium": ["D", "D2", "D+"],
            "hydrogen": ["H", "H2", "H+"],
            "helium": ["He", "He+", "He+2"],
            "carbon": ["C", "C+", "C+2", "C+3", "C+4"],
            "lithium": ["Li", "Li+"],
            "tungsten": ["W", "W+"],
            "boron": ["B", "B+"],
            "nitrogen": ["N", "N2", "N+"],
            "oxygen": ["O", "O+"]
        }

        found_species = []
        text_lower = text_content.lower()

        for species_name, notations in species_patterns.items():
            if species_name in text_lower:
                found_species.append({
                    "species": species_name,
                    "pyvalem_notations": notations,
                    "suggested_queries": [
                        f"search_by_species(species='{notations[0]}')",
                        f"search_collision_data(reactants='e- + {notations[0]}')"
                    ]
                })

        # Check for impurity mentions
        impurity_keywords = ["impurity", "impurities", "radiation", "spectroscopy"]
        has_impurity_content = any(kw in text_lower for kw in impurity_keywords)

        return json.dumps({
            "paper_id": paper_id,
            "paper_title": row.title,
            "found_species": found_species,
            "has_impurity_content": has_impurity_content,
            "collisiondb_note": "Use these species with the CollisionDB MCP server to find relevant collision cross sections and rate coefficients."
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        db.close()


# === Resources ===

@mcp.resource("nstxview://parameter-reference")
def parameter_reference() -> str:
    """Reference guide for plasma parameters in NSTX/NSTX-U experiments."""
    return """
# NSTX/NSTX-U Plasma Parameter Reference

## Plasma Parameters

| Parameter | Symbol | Typical Range | Unit | Description |
|-----------|--------|---------------|------|-------------|
| Ion Temperature | Ti | 0.5 - 5 | keV | Central ion temperature |
| Electron Temperature | Te | 0.5 - 3 | keV | Central electron temperature |
| Electron Density | ne | 1-10 × 10^19 | m^-3 | Line-averaged electron density |
| Plasma Pressure | p | 5 - 50 | kPa | Total plasma pressure |
| Beta | β | 5 - 40 | % | Ratio of plasma to magnetic pressure |
| Normalized Beta | βN | 3 - 6 | - | Beta normalized to I/aB |
| Stored Energy | W | 100 - 500 | kJ | Total plasma stored energy |
| Energy Confinement Time | τE | 20 - 100 | ms | Energy confinement time |

## Operational Parameters

| Parameter | Symbol | Typical Range | Unit | Description |
|-----------|--------|---------------|------|-------------|
| Plasma Current | Ip | 0.3 - 1.5 | MA | Total plasma current |
| Toroidal Field | Bt | 0.3 - 0.55 | T | Toroidal magnetic field on axis |
| NBI Power | PNBI | 2 - 7 | MW | Neutral beam injection power |
| RF Power | PRF | 0 - 6 | MW | HHFW/ICRF heating power |
| Safety Factor | q95 | 4 - 15 | - | Safety factor at 95% flux |
| Internal Inductance | li | 0.4 - 1.2 | - | Internal inductance |
| Elongation | κ | 2.0 - 2.8 | - | Plasma elongation |
| Triangularity | δ | 0.4 - 0.8 | - | Plasma triangularity |

## Performance Metrics

| Metric | Symbol | Description |
|--------|--------|-------------|
| H-factor | H98 | Confinement quality vs ITER98(y,2) scaling |
| H-mode | - | High confinement mode operation |
| Fusion Power | Pfus | D-D fusion power (for D plasmas) |
| Neutron Rate | - | Neutron production rate |
"""


@mcp.resource("nstxview://phenomenon-types")
def phenomenon_types() -> str:
    """Categorized list of plasma phenomena observed in NSTX/NSTX-U."""
    return """
# NSTX/NSTX-U Plasma Phenomena Reference

## Instabilities

### Edge Localized Modes (ELMs)
- **Type I ELMs**: Large amplitude, low frequency (~10-50 Hz)
- **Type III ELMs**: Small amplitude, high frequency (>100 Hz)
- **Grassy ELMs**: Very small, frequent ELMs
- **ELM-free**: H-mode without ELMs (often with other edge control)

### MHD Modes
- **Kink modes**: Current-driven external kink instabilities
- **Tearing modes**: Resistive instabilities creating magnetic islands
- **Neoclassical tearing modes (NTM)**: Bootstrap current-driven
- **Resistive wall modes (RWM)**: Stabilized by conducting wall

### Fast Particle Modes
- **Toroidal Alfvén Eigenmodes (TAE)**: Driven by energetic particles
- **Energetic particle modes (EPM)**: Fast ion driven
- **Fishbones**: n=1 internal kink with fast ions

## Confinement Regimes

### H-mode Variants
- **Standard H-mode**: High confinement with ELMs
- **QH-mode**: Quiescent H-mode (ELM-free)
- **EDA H-mode**: Enhanced D-alpha H-mode
- **I-mode**: Improved confinement, L-mode edge

### Transport Barriers
- **Edge Transport Barrier (ETB)**: H-mode pedestal
- **Internal Transport Barrier (ITB)**: Core transport reduction

## Divertor Physics

- **Detachment**: Radiative divertor detachment
- **Snowflake divertor**: Advanced divertor geometry
- **Super-X**: Extended leg divertor concept
- **Lithium conditioning**: Wall conditioning with lithium

## Disruptions

- **Thermal quench**: Rapid loss of thermal energy
- **Current quench**: Plasma current decay
- **Vertical Displacement Events (VDE)**: Vertical instability
- **Runaway electrons**: High-energy electron generation
"""


@mcp.resource("nstxview://about")
def about() -> str:
    """Information about NSTXView and NSTX/NSTX-U."""
    return """
# About NSTXView

NSTXView is a research analysis system for papers about plasma physics
experiments on the NSTX (National Spherical Torus Experiment) and NSTX-U
(Upgrade) at Princeton Plasma Physics Laboratory.

## About NSTX/NSTX-U

NSTX and NSTX-U are spherical tokamaks - fusion devices with a compact,
spherical shape (aspect ratio ~1.3) compared to conventional tokamaks.
This geometry offers potential advantages for future fusion power plants:

- Higher plasma pressure (beta) limits
- Better confinement at high beta
- More compact design
- Natural divertor solutions

### Key NSTX-U Parameters
- Major radius: 0.93 m
- Minor radius: 0.6 m
- Aspect ratio: 1.55
- Toroidal field: up to 1 T
- Plasma current: up to 2 MA
- NBI power: up to 10 MW
- RF power: up to 6 MW

## Data Source

This system contains extracted data from ~90 peer-reviewed journal
articles about NSTX and NSTX-U experiments. Each paper has been
processed to extract:

- Paper metadata (title, authors, journal, DOI)
- Shot numbers (6-digit identifiers for specific plasma discharges)
- Plasma parameters (temperatures, densities, currents, etc.)
- Phenomena discussed (instabilities, confinement modes, etc.)

## Integration with CollisionDB

NSTXView can be used alongside the CollisionDB MCP server to:
- Find collision cross sections for species mentioned in papers
- Look up rate coefficients for impurity transport modeling
- Cross-reference plasma conditions with collision physics data
"""


# Main entry point
if __name__ == "__main__":
    mcp.run()
