#!/usr/bin/env python3
"""
Test script for OpenAI verifier functionality

This script tests the OpenAI verification with o4-mini model.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ai_3d_print.openai_verifier import verify_cad_with_openai, encode_image_to_base64


def test_image_encoding():
    """Test base64 image encoding"""
    print("🧪 Testing image encoding...")
    
    # Create a dummy PNG file for testing
    test_png = Path("test_image.png")
    dummy_png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    try:
        test_png.write_bytes(dummy_png_data)
        
        # Test encoding
        encoded = encode_image_to_base64(test_png)
        assert encoded is not None
        assert len(encoded) > 0
        print("✅ Image encoding works")
        
        # Cleanup
        test_png.unlink()
        return True
        
    except Exception as e:
        print(f"❌ Image encoding test failed: {e}")
        if test_png.exists():
            test_png.unlink()
        return False


def test_openai_api_call():
    """Test OpenAI API call with mocked response"""
    print("\n🧪 Testing OpenAI API call (mocked)...")
    
    try:
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.parsed = Mock()
        mock_response.choices[0].message.parsed.result = "PASS"
        mock_response.choices[0].message.parsed.analysis = "The model meets all specified criteria."
        
        # Mock PNG files
        png_files = {
            "isometric": "/path/to/isometric.png",
            "front": "/path/to/front.png",
            "top": "/path/to/top.png"
        }
        
        with patch('src.ai_3d_print.openai_verifier.openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.beta.chat.completions.parse.return_value = mock_response
            mock_openai.return_value = mock_client
            
            with patch('src.ai_3d_print.openai_verifier.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                
                with patch('src.ai_3d_print.openai_verifier.encode_image_to_base64') as mock_encode:
                    mock_encode.return_value = "base64_encoded_image_data"
                    
                    result = verify_cad_with_openai(png_files, "simple 10x10x10 box")
                    
                    assert result["result"] == "PASS"
                    assert "criteria" in result["analysis"]
                    print("✅ Mocked OpenAI API call works")
                    print(f"   Result: {result['result']}")
                    print(f"   Analysis: {result['analysis'][:50]}...")
                    
                    # Verify the API was called with correct model
                    mock_client.beta.chat.completions.parse.assert_called_once()
                    call_args = mock_client.beta.chat.completions.parse.call_args
                    assert call_args[1]['model'] == 'o4-mini'
                    print("✅ Confirmed o4-mini model is used")
                    
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False


def test_openai_api_key_check():
    """Test that API key is required"""
    print("\n🧪 Testing API key requirement...")
    
    try:
        # Temporarily remove API key
        original_key = os.environ.get('OPENAI_API_KEY')
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        png_files = {"test": "/path/to/test.png"}
        
        try:
            result = verify_cad_with_openai(png_files, "test criteria")
            print("⚠️  API call succeeded without key (unexpected)")
            return False
        except Exception as e:
            if "api_key" in str(e).lower() or "authentication" in str(e).lower():
                print("✅ API key requirement enforced")
                return True
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        finally:
            # Restore API key
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key
                
    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False


def test_message_format():
    """Test that messages are formatted correctly for o4-mini"""
    print("\n🧪 Testing message format...")
    
    try:
        png_files = {
            "isometric": "/path/to/isometric.png",
            "front": "/path/to/front.png"
        }
        
        with patch('src.ai_3d_print.openai_verifier.openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message = Mock()
            mock_response.choices[0].message.parsed = Mock()
            mock_response.choices[0].message.parsed.result = "PASS"
            mock_response.choices[0].message.parsed.analysis = "Test analysis"
            mock_client.beta.chat.completions.parse.return_value = mock_response
            mock_openai.return_value = mock_client
            
            with patch('src.ai_3d_print.openai_verifier.Path') as mock_path:
                mock_path.return_value.exists.return_value = True
                
                with patch('src.ai_3d_print.openai_verifier.encode_image_to_base64') as mock_encode:
                    mock_encode.return_value = "base64_data"
                    
                    verify_cad_with_openai(png_files, "test criteria")
                    
                    # Check the message format
                    call_args = mock_client.beta.chat.completions.parse.call_args
                    messages = call_args[1]['messages']
                    
                    assert len(messages) == 1
                    assert messages[0]['role'] == 'user'
                    assert 'content' in messages[0]
                    
                    content = messages[0]['content']
                    assert len(content) >= 3  # text + 2 images
                    assert content[0]['type'] == 'text'
                    assert content[1]['type'] == 'image_url'
                    assert content[2]['type'] == 'image_url'
                    
                    # Check image URL format
                    assert content[1]['image_url']['url'].startswith('data:image/png;base64,')
                    assert content[2]['image_url']['url'].startswith('data:image/png;base64,')
                    
                    print("✅ Message format is correct for o4-mini")
                    print(f"   Messages: {len(messages)}")
                    print(f"   Content items: {len(content)}")
                    print(f"   Image URLs: {sum(1 for c in content if c['type'] == 'image_url')}")
                    
        return True
        
    except Exception as e:
        print(f"❌ Message format test failed: {e}")
        return False


def test_real_api_call():
    """Test real API call if API key is available"""
    print("\n🧪 Testing real OpenAI API call...")
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  Skipping real API test - no API key found")
        return True
    
    try:
        # Look for existing PNG files in the project to use for testing
        test_png = None
        
        # Check for PNG files in evaluations/outputs directory
        outputs_dir = Path("evaluations/outputs")
        if outputs_dir.exists():
            for png_file in outputs_dir.rglob("*.png"):
                if png_file.exists() and png_file.stat().st_size > 100:  # Valid file size
                    test_png = png_file
                    break
        
        if not test_png:
            print("⚠️  Skipping real API test - no valid PNG files found for testing")
            return True
        
        print(f"   Using test image: {test_png}")
        
        png_files = {"test": str(test_png)}
        
        result = verify_cad_with_openai(png_files, "3D geometric shape or model")
        
        assert 'result' in result
        assert 'analysis' in result
        assert result['result'] in ['PASS', 'FAIL']
        
        print("✅ Real API call successful")
        print(f"   Result: {result['result']}")
        print(f"   Analysis: {result['analysis'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Real API call failed: {e}")
        return False


def main():
    """Run all OpenAI verifier tests"""
    print("🚀 OpenAI Verifier Tests (o4-mini model)\n")
    
    tests = [
        test_image_encoding,
        test_openai_api_call,
        test_openai_api_key_check,
        test_message_format,
        test_real_api_call
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All OpenAI verifier tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    main()