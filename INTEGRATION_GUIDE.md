# MCP Server Integration Guide for Claude Code

This guide provides step-by-step instructions to integrate the CAD Verification MCP server with your Claude Code session.

## Quick Setup for This Session

### Step 1: Install MCP Dependencies

```bash
cd /Users/rishigundakaram/Desktop/doodles/ai-3d-print/mcp
pip install -r requirements.txt
```

### Step 2: Test the Server

```bash
# Test basic functionality
python test_server.py

# Test with MCP Inspector (interactive)
mcp dev server.py
```

### Step 3: Configure Claude Desktop

1. **Find your Claude Desktop config file:**
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

2. **Add this configuration:**
```json
{
  "mcpServers": {
    "cad-verification": {
      "command": "python",
      "args": ["/Users/rishigundakaram/Desktop/doodles/ai-3d-print/mcp/server.py"],
      "env": {}
    }
  }
}
```

3. **Restart Claude Desktop** completely (quit and reopen)

### Step 4: Verify Integration

1. **Check for MCP tools**: In Claude, you should see the `cad_verify` tool available
2. **Test the tool**: Try calling it with a sample file
3. **Check logs**: Look for `mcp_server.log` in the mcp directory

## Viewing MCP Logs

The server creates detailed logs in multiple places:

### 1. Real-time Console Logs
```bash
# Watch server logs in real-time
cd /Users/rishigundakaram/Desktop/doodles/ai-3d-print/mcp
mcp dev server.py
```

### 2. Log File
```bash
# View the log file
tail -f /Users/rishigundakaram/Desktop/doodles/ai-3d-print/mcp/mcp_server.log

# View recent logs
cat /Users/rishigundakaram/Desktop/doodles/ai-3d-print/mcp/mcp_server.log
```

### 3. Test with Detailed Logging
```bash
cd /Users/rishigundakaram/Desktop/doodles/ai-3d-print/mcp
python test_server.py
```

## Expected Log Output

When the `cad_verify` tool is called, you should see logs like:

```
2024-06-19 10:30:45,123 - __main__ - INFO - 🔍 MCP Tool Called: cad_verify
2024-06-19 10:30:45,124 - __main__ - INFO - 📁 File path: examples/box.py
2024-06-19 10:30:45,125 - __main__ - INFO - 📋 Verification criteria: simple 10x10x10 box
2024-06-19 10:30:45,126 - __main__ - DEBUG - 📄 File content preview: import cadquery as cq...
2024-06-19 10:30:45,127 - __main__ - INFO - ✅ Verification result: PASS
```

## Testing the Integration

### Manual Test
You can manually test if Claude can call the tool:

1. **Create a test file:**
```bash
cd /Users/rishigundakaram/Desktop/doodles/ai-3d-print
echo 'import cadquery as cq
result = cq.Workplane("XY").box(1, 1, 1)
show_object(result)' > test.py
```

2. **Ask Claude to verify it:**
"Please verify the file test.py using the cad_verify tool with criteria 'simple 1x1x1 cube'"

3. **Check the logs** for verification activity

### Automated Test
```bash
cd /Users/rishigundakaram/Desktop/doodles/ai-3d-print/mcp
python test_server.py
```

## Troubleshooting

### Tool Not Available
- Ensure Claude Desktop is completely restarted
- Check config file syntax (valid JSON)
- Verify file paths are absolute and correct

### Server Errors
- Check Python environment has MCP installed
- Look at `mcp_server.log` for error details
- Test server with `mcp dev server.py`

### No Logs
- Check if log file is being created in mcp directory
- Ensure server.py has write permissions
- Try running test_server.py to see if basic logging works

## Next Steps

Once integrated, Claude will:
1. **Always call `cad_verify`** before presenting CAD outputs
2. **Log all verification requests** with detailed information
3. **Provide verification status** for quality control

The logs will help you monitor and debug the verification process as you develop more sophisticated verification logic.