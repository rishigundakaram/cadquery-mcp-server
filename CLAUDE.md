# MCP Server for CAD Verification

This directory contains the MCP (Model Context Protocol) server that provides CAD verification capabilities for Claude.

## Setup Instructions

### Install MCP Dependencies
```bash
cd mcp && pip install -r requirements.txt
```

### Test MCP Server Functionality
```bash
python test_server.py
```

### Test with MCP Inspector (Interactive)
```bash
mcp dev server.py
```

### Configure Claude Desktop
See `README.md` and `INTEGRATION_GUIDE.md` for complete Claude Desktop integration instructions.

## MCP Server Features

The current implementation includes:
- **Comprehensive logging**: All verification requests logged to `mcp/mcp_server.log`
- **File validation**: Checks file existence and Python file type
- **Detailed error handling**: Descriptive error messages for debugging  
- **Test suite**: `mcp/test_server.py` for automated testing
- **Integration guides**: Complete setup documentation in `mcp/` directory

## MCP Server Status

Current verification logic is a **dummy implementation** that always returns `PASS`. This provides the framework for future enhancements:
- Parse CAD-Query code syntax
- Execute model generation
- Analyze resulting geometry dimensions
- Validate specific design criteria
- Advanced geometric analysis

## Tool Usage

The server provides a `cad_verify` tool with two parameters:
- **`file_path`**: Path to the CAD-Query Python file to verify
- **`verification_criteria`**: Description of what to verify (e.g., "coffee mug with handle, 10cm height, 8cm diameter")

**Example usage:**
```
cad_verify(
    file_path="examples/coffee_mug.py",
    verification_criteria="coffee mug with handle, 10cm height, 8cm diameter"
)
```

The tool returns verification status and details.