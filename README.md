# CAD-Query MCP Server

A Model Context Protocol (MCP) server that provides CAD generation and verification tools for Claude Code. This server enables conversational 3D modeling by exposing CAD-Query functionality through MCP tools.

## Features

- **`verify_cad_query`** - Validates CAD-Query generated models against criteria
- **`generate_cad_query`** - *(Stub implementation)* Generates CAD-Query Python scripts from descriptions
- **CAD-Query Integration** - Full CAD-Query support for parametric 3D modeling
- **STL/STEP Export** - Direct export to 3D printing and CAD formats
- **Visual Feedback** - SVG generation for model inspection

## Installation

```bash
# Install dependencies
uv sync

# For development with CAD verification capabilities
uv sync --extra cad

# Test the server
uv run pytest tests/ -v

# Run with MCP Inspector (interactive testing)
uv run mcp dev server.py
```

## Claude Desktop Configuration

Add this to your Claude Desktop configuration file:

### macOS
Location: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Location: `%APPDATA%/Claude/claude_desktop_config.json`

### Configuration
```json
{
  "mcpServers": {
    "cadquery-server": {
      "command": "python",
      "args": ["/path/to/cadquery-mcp-server/server.py"],
      "env": {}
    }
  }
}
```

## MCP Tools

### `verify_cad_query`

Validates a CAD-Query generated model against specified criteria.

**Parameters:**
- `file_path` (string): Path to the CAD-Query Python file
- `verification_criteria` (string): Description of what to verify

**Example:**
```json
{
  "file_path": "models/coffee_mug.py",
  "verification_criteria": "coffee mug with handle, 10cm height, 8cm diameter"
}
```

**Returns:**
```json
{
  "status": "PASS" | "FAIL",
  "message": "Description of result", 
  "file_path": "Path to verified file",
  "criteria": "Verification criteria used",
  "details": "Additional verification details"
}
```

### `generate_cad_query` *(Stub Implementation)*

Generates CAD-Query Python scripts from natural language descriptions.

**NOTE**: Currently returns a stub response indicating the feature is not yet implemented.

**Parameters:**
- `description` (string): Natural language description of the desired 3D model
- `parameters` (string, optional): Specific dimensions or constraints

**Example:**
```json
{
  "description": "Create a coffee mug with a handle, 10cm tall and 8cm diameter",
  "parameters": "height=100mm, diameter=80mm, handle_width=15mm"
}
```

**Returns:**
```json
{
  "status": "NOT_IMPLEMENTED",
  "message": "CAD code generation is not yet implemented",
  "description": "Input description",
  "parameters": "Input parameters",
  "details": "Additional information"
}
```

## CAD-Query Script Requirements

All CAD-Query scripts must end with `show_object(result)`:

```python
import cadquery as cq
result = cq.Workplane("XY").box(10, 10, 10)
show_object(result)  # Required for processing
```

## Development

### Testing
```bash
# Run tests with pytest
uv run pytest tests/ -v

# Run specific test files
uv run pytest tests/test_server.py -v
uv run pytest tests/test_openai_verifier.py -v

# Interactive testing with MCP Inspector
uv run mcp dev server.py

# Run evaluations
uv run python evaluations/evaluate_verify.py

# Legacy test runner (for backwards compatibility)
uv run python tests/test_server.py
uv run python tests/test_openai_verifier.py
```

### Extending the Server

The current `verify_cad_query` implementation is a basic validator. You can enhance it to:

- Parse and validate CAD-Query syntax
- Execute model generation and catch errors
- Analyze resulting geometry dimensions
- Check for specific features and constraints
- Generate detailed validation reports