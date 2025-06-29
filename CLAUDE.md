# MCP Server for CAD Verification

This directory contains the MCP (Model Context Protocol) server that provides CAD verification capabilities for Claude.

## Setup Instructions

### Install MCP Dependencies
```bash
uv sync --extra cad
```

### Test MCP Server Functionality
```bash
# Run tests with pytest (recommended)
uv run pytest tests/ -v

# Run specific test files
uv run pytest tests/test_server.py -v
uv run pytest tests/test_openai_verifier.py -v

# Legacy test runner (for backwards compatibility)
uv run python tests/test_server.py
uv run python tests/test_openai_verifier.py
```

### Test with MCP Inspector (Interactive)
```bash
uv run mcp dev server.py
```

### Run Evaluations
```bash
uv run python evaluations/evaluate_verify.py
```

### Configure Claude Desktop
See `README.md` for complete Claude Desktop integration instructions.

## MCP Server Features

The current implementation includes:
- **Comprehensive logging**: All verification requests logged to `mcp/mcp_server.log`
- **File validation**: Checks file existence and Python file type
- **Detailed error handling**: Descriptive error messages for debugging  
- **Test suite**: `tests/test_server.py` for automated testing
- **Evaluation harness**: `evaluations/` directory with test models and verification scripts

## MCP Server Status

### Verification Tool
Current verification logic is a **dummy implementation** that always returns `PASS`. This provides the framework for future enhancements:
- Parse CAD-Query code syntax
- Execute model generation
- Analyze resulting geometry dimensions
- Validate specific design criteria
- Advanced geometric analysis

### Code Generation Tool
The `generate_cad_query` tool is **fully implemented** using the HuggingFace model `ricemonster/codegpt-small-sft`:
- Loads GPT-2 based model for code generation
- Generates CAD-Query Python scripts from natural language descriptions
- Handles parameters and constraints
- Returns complete executable CAD scripts
- Includes comprehensive error handling and logging

## Tool Usage

### Verification Tool
The server provides a `verify_cad_query` tool with two parameters:
- **`file_path`**: Path to the CAD-Query Python file to verify
- **`verification_criteria`**: Description of what to verify (e.g., "coffee mug with handle, 10cm height, 8cm diameter")

**Example usage:**
```
verify_cad_query(
    file_path="evaluations/test_models/coffee_mug.py",
    verification_criteria="coffee mug with handle, 10cm height, 8cm diameter"
)
```

### Code Generation Tool
The server provides a `generate_cad_query` tool with two parameters:
- **`description`**: Natural language description of the desired 3D model
- **`parameters`**: Optional specific dimensions or constraints

**Example usage:**
```
generate_cad_query(
    description="simple box",
    parameters="10x10x10 mm"
)
```

**Returns:**
- `status`: SUCCESS/ERROR
- `message`: Status description
- `generated_code`: Complete CAD-Query Python script
- `description`: Original description
- `parameters`: Original parameters