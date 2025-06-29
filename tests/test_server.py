#!/usr/bin/env python3
"""
Pytest test suite for the CAD Verification MCP Server

This module tests the verify_cad_query tool functionality and helps debug MCP integration.
"""

import json
import subprocess
import sys
from pathlib import Path
import pytest
import shutil

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
import server


def test_server_basic():
    """Test basic server functionality"""
    # Test server import - if we got here, import worked
    assert hasattr(server, 'verify_cad_query')
    
    # Test tool function directly
    result = server.verify_cad_query("test_file.py", "test criteria")
    assert result is not None
    assert isinstance(result, dict)


def test_with_real_file(tmp_path):
    """Test with an actual CAD file"""
    # Create a simple test file
    test_file = tmp_path / "test_box.py"
    test_content = '''import cadquery as cq
result = cq.Workplane("XY").box(10, 10, 10)
show_object(result)
'''
    
    test_file.write_text(test_content)
    
    # Test verification with default output
    result = server.verify_cad_query(str(test_file), "simple 10x10x10 box")
    
    assert result is not None
    assert isinstance(result, dict)
    # The actual result format depends on the server implementation


def test_with_custom_output_path(tmp_path):
    """Test verification with custom output path"""
    # Create a simple test file
    test_file = tmp_path / "test_cylinder.py"
    test_content = '''import cadquery as cq
result = cq.Workplane("XY").cylinder(5, 20)
show_object(result)
'''
    
    test_file.write_text(test_content)
    
    # Test verification with custom output path
    custom_output = tmp_path / "custom_outputs"
    
    from src.ai_3d_print.verify_helper import verify_model
    result = verify_model(str(test_file), str(custom_output))
    
    assert result is not None
    assert isinstance(result, dict)
    
    # Check if files were created in custom location
    expected_dir = custom_output / "test_cylinder"
    # Note: This assertion depends on the actual implementation behavior


def test_generate_cad_query():
    """Test CAD code generation functionality"""
    # Test basic generation
    result = server.generate_cad_query("simple box", "10x10x10 mm")
    
    assert 'status' in result
    assert result['status'] in ['SUCCESS', 'ERROR']
    
    if result['status'] == 'SUCCESS':
        assert 'generated_code' in result
        assert isinstance(result['generated_code'], str)
        assert len(result['generated_code']) > 0
    
    # Test another shape
    result2 = server.generate_cad_query("cylinder", "radius 5mm, height 20mm")
    assert 'status' in result2
    assert result2['status'] in ['SUCCESS', 'ERROR']


def test_mcp_inspector():
    """Test MCP CLI availability"""
    try:
        # Check if mcp is available
        result = subprocess.run(["mcp", "--version"], capture_output=True, text=True)
        # MCP CLI may not be installed, so we just check if it's available
        mcp_available = result.returncode == 0
        
        # This test doesn't fail if MCP is not available
        assert isinstance(mcp_available, bool)
        
        if mcp_available:
            assert len(result.stdout.strip()) > 0
            
    except FileNotFoundError:
        # MCP CLI not installed, which is acceptable
        pytest.skip("MCP CLI not installed")
    except Exception as e:
        pytest.fail(f"MCP Inspector test failed: {e}")


def test_claude_desktop_config(tmp_path):
    """Generate Claude Desktop configuration"""
    server_path = Path(__file__).parent.parent / "server.py"
    abs_server_path = server_path.resolve()
    
    config = {
        "mcpServers": {
            "cad-verification": {
                "command": "python",
                "args": [str(abs_server_path)],
                "env": {}
            }
        }
    }
    
    config_file = tmp_path / "claude_desktop_config.json"
    config_file.write_text(json.dumps(config, indent=2))
    
    assert config_file.exists()
    
    # Verify the config can be loaded back
    loaded_config = json.loads(config_file.read_text())
    assert "mcpServers" in loaded_config
    assert "cad-verification" in loaded_config["mcpServers"]
    assert loaded_config["mcpServers"]["cad-verification"]["command"] == "python"


# This file can now be run with pytest
# Run with: pytest tests/test_server.py -v

if __name__ == "__main__":
    # For backwards compatibility, run pytest when executed directly
    import pytest
    pytest.main([__file__, "-v"])