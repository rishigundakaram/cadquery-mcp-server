"""Vision-based CAD verification using GPT-4 Vision API."""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def create_verification_prompt(verification_criteria: str) -> str:
    """
    Create a detailed prompt for GPT-4 Vision to analyze CAD images.
    
    Args:
        verification_criteria: The criteria to verify against
        
    Returns:
        Formatted prompt string
    """
    return f"""You are a CAD verification expert analyzing 3D model images. You will be shown 4 views of the same 3D model:
1. Right view (from +X axis)
2. Top view (from +Z axis, looking down)
3. Bottom view (from -Z axis, looking up)
4. Isometric view (3D perspective)

VERIFICATION CRITERIA: {verification_criteria}

Please analyze these 4 views and determine if the 3D model meets the specified criteria. Consider:

1. **Geometric accuracy**: Does the shape match what was requested?
2. **Proportions**: Are the dimensions and proportions reasonable for the described object?
3. **Features**: Are all required features present (handles, holes, etc.)?
4. **Overall design**: Does it look like a functional version of the requested object?

Provide your analysis in this exact JSON format:
{{
    "verification_result": "PASS" or "FAIL",
    "confidence": "HIGH", "MEDIUM", or "LOW",
    "analysis": {{
        "geometric_accuracy": "your assessment of shape accuracy",
        "proportions": "your assessment of proportions and dimensions", 
        "features": "your assessment of required features",
        "overall_design": "your overall assessment"
    }},
    "reasoning": "detailed explanation of your decision",
    "recommendations": "any suggestions for improvement (if FAIL)"
}}

Be thorough but concise. Focus on whether this model would actually serve the intended purpose."""


def analyze_cad_images_with_gpt4(
    image_paths: Dict[str, str], 
    verification_criteria: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze CAD images using GPT-4 Vision API.
    
    Args:
        image_paths: Dictionary mapping view names to image file paths
        verification_criteria: The criteria to verify against
        api_key: OpenAI API key (if None, will try to get from environment)
        
    Returns:
        Dictionary containing verification results
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.getenv("OPENAI_API_KEY")
        
    if not api_key:
        return {
            "status": "ERROR",
            "message": "OpenAI API key not provided. Set OPENAI_API_KEY environment variable.",
            "verification_result": "FAIL",
            "confidence": "LOW",
            "analysis": {},
            "reasoning": "Cannot perform verification without API access",
            "recommendations": "Configure OpenAI API key to enable verification"
        }
    
    try:
        # Prepare image data for API
        image_data = []
        for view_name, path in image_paths.items():
            if not Path(path).exists():
                logger.warning(f"Image not found: {path}")
                continue
                
            base64_image = encode_image_to_base64(path)
            image_data.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"
                }
            })
        
        if not image_data:
            return {
                "status": "ERROR", 
                "message": "No valid images found for analysis",
                "verification_result": "FAIL",
                "confidence": "LOW",
                "analysis": {},
                "reasoning": "No images available for verification",
                "recommendations": "Ensure image generation is working properly"
            }
        
        # Create the prompt
        prompt = create_verification_prompt(verification_criteria)
        
        # Prepare API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # Construct message content with text prompt and images
        content = [{"type": "text", "text": prompt}] + image_data
        
        payload = {
            "model": "gpt-4o",  # Using GPT-4o which has vision capabilities
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1  # Low temperature for consistent analysis
        }
        
        # Make API request
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return {
                "status": "ERROR",
                "message": error_msg,
                "verification_result": "FAIL", 
                "confidence": "LOW",
                "analysis": {},  
                "reasoning": "API request failed",
                "recommendations": "Check API key and network connectivity"
            }
        
        # Parse response
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Try to parse JSON response
        try:
            # Look for JSON in the response (GPT might add extra text around it)
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_content = content[start_idx:end_idx]
                parsed_result = json.loads(json_content)
                
                # Add status and raw response
                parsed_result["status"] = "SUCCESS"
                parsed_result["raw_response"] = content
                
                logger.info(f"GPT-4 Vision analysis completed: {parsed_result['verification_result']}")
                return parsed_result
            else:
                # If no JSON found, return raw response
                return {
                    "status": "SUCCESS",
                    "verification_result": "FAIL",  # Default to FAIL if we can't parse
                    "confidence": "LOW",
                    "analysis": {},
                    "reasoning": f"Could not parse structured response: {content}",
                    "recommendations": "Check prompt formatting",
                    "raw_response": content
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            return {
                "status": "SUCCESS",
                "verification_result": "FAIL",  # Default to FAIL if we can't parse
                "confidence": "LOW", 
                "analysis": {},
                "reasoning": f"Response parsing error: {str(e)}",
                "recommendations": "Check response format",
                "raw_response": content
            }
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error during API request: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "ERROR",
            "message": error_msg,
            "verification_result": "FAIL",
            "confidence": "LOW",
            "analysis": {},
            "reasoning": "Network connectivity issue",
            "recommendations": "Check internet connection and API endpoint"
        }
        
    except Exception as e:
        error_msg = f"Unexpected error during vision analysis: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "ERROR", 
            "message": error_msg,
            "verification_result": "FAIL",
            "confidence": "LOW",
            "analysis": {},
            "reasoning": "Unexpected error during analysis",
            "recommendations": "Check logs for detailed error information"
        }