#!/usr/bin/env python3
"""
Test script for the CAD Verification MCP Server

This script tests the cad_verify tool functionality and helps debug MCP integration.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_server_basic():
    """Test basic server functionality"""
    print("🧪 Testing MCP server basic functionality...")
    
    try:
        # Test server import
        import server
        print("✅ Server imports successfully")
        
        # Test tool function directly
        result = server.cad_verify("test_file.py", "test criteria")
        print(f"✅ cad_verify function works: {result}")
        
        return True
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False


def test_with_real_file():
    """Test with an actual CAD file"""
    print("\n🧪 Testing with real CAD file...")
    
    # Create a simple test file
    test_file = Path("test_box.py")
    test_content = '''import cadquery as cq
result = cq.Workplane("XY").box(10, 10, 10)
show_object(result)
'''
    
    try:
        test_file.write_text(test_content)
        print(f"✅ Created test file: {test_file}")
        
        # Test verification
        import server
        result = server.cad_verify(str(test_file), "simple 10x10x10 box")
        print(f"✅ Verification result: {json.dumps(result, indent=2)}")
        
        # Cleanup
        test_file.unlink()
        print("✅ Cleaned up test file")
        
        return True
    except Exception as e:
        print(f"❌ Real file test failed: {e}")
        if test_file.exists():
            test_file.unlink()
        return False


def test_mcp_inspector():
    """Test using MCP Inspector"""
    print("\n🧪 Testing with MCP Inspector...")
    print("Note: This requires mcp to be installed and will open interactive mode")
    
    try:
        # Check if mcp is available
        result = subprocess.run(["mcp", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ MCP CLI not found. Install with: pip install mcp")
            return False
        
        print(f"✅ MCP CLI found: {result.stdout.strip()}")
        print("\n📋 To test interactively, run:")
        print("   mcp dev server.py")
        print("\nThen test the cad_verify tool with:")
        print('   {"file_path": "examples/box.py", "verification_criteria": "simple box"}')
        
        return True
    except Exception as e:
        print(f"❌ MCP Inspector test failed: {e}")
        return False


def test_claude_desktop_config():
    """Generate Claude Desktop configuration"""
    print("\n🧪 Generating Claude Desktop configuration...")
    
    try:
        server_path = Path(__file__).parent / "server.py"
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
        
        config_file = Path("claude_desktop_config.json")
        config_file.write_text(json.dumps(config, indent=2))
        
        print(f"✅ Generated config file: {config_file}")
        print(f"📋 Copy this to your Claude Desktop config location:")
        print(f"   macOS: ~/Library/Application Support/Claude/claude_desktop_config.json")
        print(f"   Windows: %APPDATA%/Claude/claude_desktop_config.json")
        
        return True
    except Exception as e:
        print(f"❌ Config generation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 CAD Verification MCP Server Tests\n")
    
    # Change to mcp directory
    mcp_dir = Path(__file__).parent
    original_dir = Path.cwd()
    
    try:
        import os
        os.chdir(mcp_dir)
        print(f"📁 Working directory: {mcp_dir}")
        
        tests = [
            test_server_basic,
            test_with_real_file,
            test_mcp_inspector,
            test_claude_desktop_config
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        print(f"\n📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed! MCP server is ready to use.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
            
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    main()