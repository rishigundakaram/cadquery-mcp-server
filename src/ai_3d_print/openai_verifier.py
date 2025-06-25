"""OpenAI-based CAD verification using o3-mini model with structured outputs."""

import base64
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

import openai
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class VerificationResult(BaseModel):
    """Simple structured output for CAD verification."""
    result: str  # "PASS" or "FAIL"
    analysis: str  # Detailed reasoning


def encode_image_to_base64(image_path: Path) -> str:
    """Convert PNG image to base64 string for OpenAI API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def verify_cad_with_openai(png_files: Dict[str, str], criteria: str) -> Dict[str, Any]:
    """
    Verify CAD model using OpenAI o3-mini with structured outputs.
    
    Args:
        png_files: Dictionary mapping view names to file paths
        criteria: Verification criteria string
    
    Returns:
        Dictionary containing verification result and analysis
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Prepare image content for the API
    image_content = []
    for view_name, file_path in png_files.items():
        if Path(file_path).exists():
            base64_image = encode_image_to_base64(Path(file_path))
            image_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            })
    
    # Create the prompt
    prompt = f"""
    Analyze these 3D CAD model images and verify if they meet the following criteria:
    
    Criteria: {criteria}
    
    The images show different views of the same 3D model. Please:
    1. Examine each view carefully
    2. Check if the model matches the specified criteria
    3. Provide detailed analysis of what is correct and what is incorrect
    4. Give a final PASS or FAIL result
    
    Be thorough in explaining your reasoning, including specific measurements, shapes, features, and any discrepancies you notice.
    """
    
    # Prepare messages
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                *image_content
            ]
        }
    ]
    
    # Call OpenAI API with structured output
    response = client.beta.chat.completions.parse(
        model="o3-mini",
        messages=messages,
        response_format=VerificationResult
    )
    
    # Extract the structured result
    verification_result = response.choices[0].message.parsed
    
    return {
        "result": verification_result.result,
        "analysis": verification_result.analysis
    }