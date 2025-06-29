#!/usr/bin/env python3
"""
Pytest test suite for OpenAI verifier functionality

This module tests the OpenAI verification with o4-mini model.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ai_3d_print.openai_verifier import verify_cad_with_openai, encode_image_to_base64


def test_image_encoding(tmp_path):
    """Test base64 image encoding"""
    # Create a dummy PNG file for testing
    test_png = tmp_path / "test_image.png"
    dummy_png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
    
    test_png.write_bytes(dummy_png_data)
    
    # Test encoding
    encoded = encode_image_to_base64(test_png)
    assert encoded is not None
    assert len(encoded) > 0


def test_openai_api_call():
    """Test OpenAI API call with mocked response"""
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
                
                # Verify the API was called with correct model
                mock_client.beta.chat.completions.parse.assert_called_once()
                call_args = mock_client.beta.chat.completions.parse.call_args
                assert call_args[1]['model'] == 'o4-mini'


def test_openai_api_key_check(monkeypatch):
    """Test that API key is required"""
    # Remove API key from environment
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    
    png_files = {"test": "/path/to/test.png"}
    
    with pytest.raises(Exception) as exc_info:
        verify_cad_with_openai(png_files, "test criteria")
    
    # Check that the error is related to API key/authentication
    error_msg = str(exc_info.value).lower()
    assert "api_key" in error_msg or "authentication" in error_msg


def test_message_format():
    """Test that messages are formatted correctly for o4-mini"""
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


@pytest.mark.skipif(not os.environ.get('OPENAI_API_KEY'), reason="API key not available")
def test_real_api_call():
    """Test real API call if API key is available"""
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
        pytest.skip("No valid PNG files found for testing")
    
    png_files = {"test": str(test_png)}
    
    result = verify_cad_with_openai(png_files, "3D geometric shape or model")
    
    assert 'result' in result
    assert 'analysis' in result
    assert result['result'] in ['PASS', 'FAIL']


# This file can now be run with pytest
# Run with: pytest tests/test_openai_verifier.py -v

if __name__ == "__main__":
    # For backwards compatibility, run pytest when executed directly
    import pytest
    pytest.main([__file__, "-v"])