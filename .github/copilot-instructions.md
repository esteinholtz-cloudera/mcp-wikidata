# Wikidata MCP Server - AI Agent Instructions

## Project Overview
This is a Model Context Protocol (MCP) server implementation for interacting with Wikidata. The server provides tools for searching entities/properties, extracting metadata, and executing SPARQL queries against Wikidata.

## Key Components

### Server (`src/server.py`)
- Core MCP server implementation using FastMCP
- Exposes tools for Wikidata interaction:
  - `search_entity`: Searches for Wikidata entity IDs
  - `search_property`: Finds property IDs
  - `get_properties`: Retrieves available properties for an entity
  - Executes SPARQL queries against Wikidata's endpoint

### Client (`src/client.py`) 
- Example implementation using langchain-mcp-adapters
- Demonstrates how to:
  - Initialize MCP client session
  - Load and use MCP tools
  - Create and run LangChain agents with the tools

## Development Workflow

### Environment Setup
1. Use `uv` for dependency management:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv
uv sync  # Install base dependencies
uv sync --extra example  # Install client example dependencies
```

### Running the Server
1. Start the server: `uv run src/server.py`
2. For testing with example client: `uv run src/client.py` (in another shell)

### Integration Patterns
- Server communicates via MCP (Model Context Protocol)
- Uses `httpx` for async HTTP requests to Wikidata API
- Follows Wikidata API conventions for entity/property searches
- Entity IDs start with Q (e.g., Q495980 for Bong Joon-ho)
- Property IDs start with P (e.g., P57 for director)

## Best Practices
1. Handle API rate limits and errors gracefully
2. Keep queries focused and specific due to Wikidata's vast scope
3. Use async/await patterns consistently for API interactions
4. Validate entity and property IDs before SPARQL queries

## Common Workflows
1. Entity/Property Search → Get Properties → SPARQL Query
2. Use unambiguous search terms for better results
3. Check response formats in the example outputs for proper handling

## Key Files
- `src/server.py`: Core MCP server implementation
- `src/client.py`: Example client usage
- `pyproject.toml`: Project dependencies and metadata
- `smithery.yaml`: Smithery configuration for deployment