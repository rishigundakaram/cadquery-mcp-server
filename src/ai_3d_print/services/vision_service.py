"""Vision service for CAD verification using GPT-4.1."""

import base64
import json
import logging
import os
from typing import Optional

import requests

from ..models import VerificationResponse, VerificationResult, ImageViews

logger = logging.getLogger(__name__)


class VisionService:
    """Service for analyzing CAD models using GPT-4.1 Vision API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the vision service.
        
        Args:
            api_key: OpenAI API key (if None, will try to get from environment)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided")
    
    def _encode_image_to_base64(self, image_path) -> str:
        """Encode an image file to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _create_structured_schema(self) -> dict:
        """Create the JSON schema for structured output."""
        return {
            "name": "cad_verification_result",
            "schema": {
                "type": "object",
                "properties": {
                    "verification_result": {
                        "type": "string",
                        "enum": ["PASS", "FAIL"],
                        "description": "Whether the CAD model meets the verification criteria"
                    },
                    "reasoning": {
                        "type": "string",
                        "maxLength": 200,
                        "description": "Brief explanation of the verification decision"
                    }
                },
                "required": ["verification_result", "reasoning"],
                "additionalProperties": False
            }
        }
    
    def _create_verification_prompt(self, verification_criteria: str) -> str:
        """Create the system prompt for CAD verification."""
        return f"""You are a CAD verification expert analyzing 3D model images. You will be shown 4 views of the same 3D model:
1. Right view (from +X axis)
2. Top view (from +Z axis, looking down)
3. Bottom view (from -Z axis, looking up)  
4. Isometric view (3D perspective)

VERIFICATION CRITERIA: {verification_criteria}

Analyze these views and determine if the 3D model meets the specified criteria. Consider:
- Does the shape match what was requested?
- Are the proportions reasonable for the described object?
- Are all required features present (handles, holes, etc.)?
- Would this model serve its intended purpose?

Respond with PASS if the model meets the criteria, or FAIL if it does not."""
    
    def analyze_cad_model(self, image_views: ImageViews, verification_criteria: str) -> VerificationResponse:
        """
        Analyze CAD model images using GPT-4.1 Vision API.
        
        Args:
            image_views: ImageViews object containing paths to the 4 CAD views
            verification_criteria: Description of what to verify against
        
        Returns:
            VerificationResponse with the analysis result
        """
        if not self.api_key:
            return VerificationResponse.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        try:
            # Prepare image data for API
            image_data = []
            for view_name, path in image_views.get_view_paths().items():
                try:
                    base64_image = self._encode_image_to_base64(path)
                    image_data.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    })
                except Exception as e:
                    logger.warning(f"Failed to encode {view_name} image: {e}")
            
            if not image_data:
                return VerificationResponse.error("No valid images found for analysis")
            
            # Create the prompt and schema
            prompt = self._create_verification_prompt(verification_criteria)
            schema = self._create_structured_schema()
            
            # Prepare API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Construct message content with text prompt and images
            content = [{"type": "text", "text": prompt}] + image_data
            
            payload = {
                "model": "gpt-4o-2024-08-06",  # GPT-4o with structured outputs support
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": schema
                },
                "max_tokens": 500,
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
                return VerificationResponse.error(error_msg)
            
            # Parse structured response
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            try:
                parsed_result = json.loads(content)
                
                # Extract result and reasoning
                result_str = parsed_result["verification_result"]
                reasoning = parsed_result["reasoning"]
                
                # Convert to enum and create response
                if result_str == "PASS":
                    logger.info(f"GPT-4.1 Vision analysis: PASS - {reasoning}")
                    return VerificationResponse.success(reasoning)
                else:
                    logger.info(f"GPT-4.1 Vision analysis: FAIL - {reasoning}")
                    return VerificationResponse.failure(reasoning)
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Failed to parse structured response: {e}")
                return VerificationResponse.error(f"Invalid API response format: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during API request: {str(e)}"
            logger.error(error_msg)
            return VerificationResponse.error(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error during vision analysis: {str(e)}"
            logger.error(error_msg)
            return VerificationResponse.error(error_msg)