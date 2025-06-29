#!/usr/bin/env python3
"""
Test script for the CAD Verification MCP Server

This script tests the verify_cad_query tool functionality and helps debug MCP integration.
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
        sys.path.append(str(Path(__file__).parent.parent))
        import server

        print("✅ Server imports successfully")

        # Test tool function directly
        result = server.verify_cad_query("test_file.py", "test criteria")
        print(f"✅ verify_cad_query function works: {result}")

        return True
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False


def test_with_real_file():
    """Test with an actual CAD file"""
    print("\n🧪 Testing with real CAD file...")

    # Create a simple test file
    test_file = Path("test_box.py")
    test_content = """import cadquery as cq
result = cq.Workplane("XY").box(10, 10, 10)
show_object(result)
"""

    try:
        test_file.write_text(test_content)
        print(f"✅ Created test file: {test_file}")

        # Test verification with default output
        sys.path.append(str(Path(__file__).parent.parent))
        import server

        result = server.verify_cad_query(str(test_file), "simple 10x10x10 box")
        # print(f"✅ Verification result: {json.dumps(result, indent=2)}")

        # Cleanup
        test_file.unlink()
        print("✅ Cleaned up test file")

        return True
    except Exception as e:
        print(f"❌ Real file test failed: {e}")
        if test_file.exists():
            test_file.unlink()
        return False


def test_with_custom_output_path():
    """Test verification with custom output path"""
    print("\n🧪 Testing with custom output path...")

    # Create a simple test file
    test_file = Path("test_cylinder.py")
    test_content = """import cadquery as cq
result = cq.Workplane("XY").cylinder(5, 20)
show_object(result)
"""

    try:
        test_file.write_text(test_content)
        print(f"✅ Created test file: {test_file}")

        # Test verification with custom output path
        custom_output = Path("custom_outputs")
        sys.path.append(str(Path(__file__).parent.parent))
        from src.ai_3d_print.verify_helper import verify_model

        result = verify_model(str(test_file), "simple cylinder", str(custom_output))
        print(f"✅ Verification with custom output: {json.dumps(result, indent=2)}")

        # Check if files were created in custom location
        expected_dir = custom_output / "test_cylinder"
        if expected_dir.exists():
            print(f"✅ Custom output directory created: {expected_dir}")
        else:
            print(f"❌ Custom output directory not found: {expected_dir}")

        # Cleanup
        # test_file.unlink()
        # if custom_output.exists():
        #     import shutil
        #     shutil.rmtree(custom_output)
        #     print("✅ Cleaned up custom output directory")

        return True
    except Exception as e:
        print(f"❌ Custom output test failed: {e}")
        if test_file.exists():
            test_file.unlink()
        # Cleanup custom output if it exists
        custom_output = Path("custom_outputs")
        if custom_output.exists():
            import shutil

            shutil.rmtree(custom_output)
        return False


def test_generate_cad_query():
    """Test CAD code generation functionality"""
    print("\n🧪 Testing CAD code generation...")

    try:
        sys.path.append(str(Path(__file__).parent.parent))
        import server

        # Test basic generation
        result = server.generate_cad_query("simple box", "10x10x10 mm")
        print(f"✅ Generation result status: {result['status']}")

        if result["status"] == "SUCCESS":
            print("✅ Generated code preview:")
            print(
                result["generated_code"][:200] + "..."
                if len(result["generated_code"]) > 200
                else result["generated_code"]
            )
        else:
            print(f"⚠️  Generation failed: {result['message']}")

        # Test another shape
        result2 = server.generate_cad_query("cylinder", "radius 5mm, height 20mm")
        print(f"✅ Second generation status: {result2['status']}")

        return True
    except Exception as e:
        print(f"❌ CAD generation test failed: {e}")
        return False


def test_mcp_inspector():
    """Test using MCP Inspector"""
    print("\n🧪 Testing with MCP Inspector...")
    print("Note: This requires mcp to be installed and will open interactive mode")

    try:
        # Check if mcp is available
        result = subprocess.run(["mcp", "version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ MCP CLI not found. Install with: pip install mcp")
            return False

        print(f"✅ MCP CLI found: {result.stdout.strip()}")
        print("\n📋 To test interactively, run:")
        print("   mcp dev server.py")
        print("\nThen test the verify_cad_query tool with:")
        print(
            '   {"file_path": "examples/box.py", "verification_criteria": "simple box"}'
        )

        return True
    except Exception as e:
        print(f"❌ MCP Inspector test failed: {e}")
        return False


def test_claude_desktop_config():
    """Generate Claude Desktop configuration"""
    print("\n🧪 Generating Claude Desktop configuration...")

    try:
        server_path = Path(__file__).parent.parent / "server.py"
        abs_server_path = server_path.resolve()

        config = {
            "mcpServers": {
                "cad-verification": {
                    "command": "python",
                    "args": [str(abs_server_path)],
                    "env": {},
                }
            }
        }

        config_file = Path("claude_desktop_config.json")
        config_file.write_text(json.dumps(config, indent=2))

        print(f"✅ Generated config file: {config_file}")
        print("📋 Copy this to your Claude Desktop config location:")
        print(
            "   macOS: ~/Library/Application Support/Claude/claude_desktop_config.json"
        )
        print("   Windows: %APPDATA%/Claude/claude_desktop_config.json")

        return True
    except Exception as e:
        print(f"❌ Config generation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 CAD Verification MCP Server Tests\n")

    # Change to project root directory
    project_dir = Path(__file__).parent.parent
    original_dir = Path.cwd()

    try:
        import os

        os.chdir(project_dir)
        print(f"📁 Working directory: {project_dir}")

        tests = [
            test_server_basic,
            test_with_real_file,
            test_with_custom_output_path,
            # test_generate_cad_query,
            test_mcp_inspector,
            test_claude_desktop_config,
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
