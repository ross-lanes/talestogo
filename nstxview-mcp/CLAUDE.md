# NSTXView MCP Server

MCP (Model Context Protocol) server providing access to NSTX/NSTX-U plasma physics research data extracted from ~90 scholarly papers.

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL database with NSTXView tables
- Environment variables configured

### Installation

```bash
cd nstxview-mcp
pip install -e .
```

### Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:port/database
CHROMADB_HOST=localhost  # Optional, for semantic search
CHROMADB_PORT=8000       # Optional, for semantic search
```

## Running the Server

```bash
# Direct execution
python server.py

# Or via installed script
nstxview-mcp
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nstxview": {
      "command": "python",
      "args": ["/path/to/nstxview-mcp/server.py"],
      "env": {
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

## Available Tools

### search_papers
Search across paper content using semantic or text search.
- **query**: Natural language search query
- **limit**: Maximum results (default 10)
- **use_semantic**: Use semantic search via ChromaDB if available (default True)

### semantic_search
Perform dedicated semantic search across paper chunks using vector embeddings.
- **query**: Natural language search query
- **limit**: Maximum results (default 10)
- **section**: Filter by section (abstract, introduction, results, etc.)

### get_paper_details
Get full extracted information for a specific paper including shots, parameters, and phenomena.
- **paper_id**: Database ID of the paper

### query_shots
Find shots matching specific criteria.
- **shot_numbers**: Comma-separated shot numbers (e.g., "141234,141235")
- **min_shot/max_shot**: Shot number range
- **role**: Filter by role (primary, comparison, reference)
- **limit**: Maximum results (default 20)

### get_shot_details
Get all information about a specific shot across all papers.
- **shot_number**: 6-digit shot number (100000-199999)

### get_parameter_statistics
Get aggregate statistics for a parameter across all papers.
- **parameter_name**: Parameter name (e.g., "ion_temperature")

### list_parameters
Get all unique parameter names with counts and categories.

### list_phenomena
Get all unique phenomenon types with counts and categories.

### get_database_stats
Get overall statistics about the NSTXView database including paper counts, processing status, and vector store info.

### find_related_collision_data
Suggest CollisionDB queries based on species mentioned in a paper.
- **paper_id**: Database ID of the paper

## Resources

### nstxview://parameter-reference
Reference guide for plasma parameters with typical ranges and units.

### nstxview://phenomenon-types
Categorized list of plasma phenomena (instabilities, confinement modes, etc.)

### nstxview://about
Information about NSTXView and NSTX/NSTX-U experiments.

## Integration with CollisionDB

This server is designed to work alongside the CollisionDB MCP server. Use `find_related_collision_data` to get species suggestions that can be queried via CollisionDB for collision cross sections and rate coefficients.

Example workflow:
1. Search for papers about a topic: `search_papers("lithium wall conditioning")`
2. Get paper details: `get_paper_details(paper_id)`
3. Find related collision data: `find_related_collision_data(paper_id)`
4. Use CollisionDB to query: `search_by_species(species="Li")`

## Shot Number Format

NSTX/NSTX-U shot numbers are 6-digit integers starting with 1:
- Valid range: 100000 - 199999
- Example: 141234, 138576, 142000

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check .
```
