# NSTXView MCP Server

MCP (Model Context Protocol) server providing access to NSTX/NSTX-U plasma physics research data extracted from scholarly papers.

## Setup

```bash
cd nstxview-mcp
pip install -e .
```

## Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@host:port/database
```

## Running the Server

```bash
python server.py
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nstxview": {
      "command": "python3",
      "args": ["/path/to/nstxview-mcp/server.py"],
      "env": {
        "DATABASE_URL": "postgresql://..."
      }
    }
  }
}
```

## Available Tools

- **search_papers** - Search across paper content
- **get_paper_details** - Get full extracted information for a paper
- **query_shots** - Find shots matching specific criteria
- **get_shot_details** - Get all information about a specific shot
- **get_parameter_statistics** - Get aggregate statistics for a parameter
- **list_parameters** - Get all unique parameter names with counts
- **list_phenomena** - Get all unique phenomenon types with counts
- **get_database_stats** - Get overall database statistics
- **semantic_search** - Perform semantic search across paper chunks
- **find_related_collision_data** - Suggest CollisionDB queries based on species in a paper
