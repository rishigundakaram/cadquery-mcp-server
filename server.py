#!/usr/bin/env python3
"""
MCP Server for CAD Verification

This server provides a verification tool for CAD-Query generated models.
It integrates with Claude to validate 3D models before presenting results to users.
"""

import logging
import sys
from pathlib import Path
from typing import Any

import torch
from mcp.server.fastmcp import FastMCP
from transformers import AutoModelForCausalLM, AutoTokenizer
from src.ai_3d_print.verify_helper import verify_model

# Configure detailed logging for debugging
log_file = Path(__file__).parent / 'mcp_server.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(log_file, mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("CAD Verification Server")

# Initialize model and tokenizer globally
model = None
tokenizer = None

def load_model():
    """Load the HuggingFace model for code generation"""
    global model, tokenizer
    try:
        logger.info("Loading HuggingFace model: ricemonster/codegpt-small-sft")
        
        # Load tokenizer with original inference settings
        tokenizer = AutoTokenizer.from_pretrained(
            "ricemonster/codegpt-small-sft",
            trust_remote_code=True,
            use_fast=False,
            model_max_length=1024
        )
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        
        # Load model with original inference settings
        model = AutoModelForCausalLM.from_pretrained(
            "ricemonster/codegpt-small-sft",
            trust_remote_code=True
        )
        model.eval()

        logger.info("Model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False

# Model will be loaded lazily when first needed


@mcp.tool()
def verify_cad_query(file_path: str, verification_criteria: str) -> dict[str, Any]:
    """
    Verify a CAD-Query generated model against specified criteria.
    
    This tool generates STL files and PNG views (right, top, down, iso) of the model
    and validates it against the specified criteria.
    
    Args:
        file_path: Path to the CAD-Query Python file to verify
        verification_criteria: Description of what aspects to verify
                              (e.g., "coffee mug with handle, 10cm height, 8cm diameter")

    Returns:
        Dict containing verification status and details
    """
    logger.info("🔍 MCP Tool Called: verify_cad_query")
    logger.info(f"📁 File path: {file_path}")
    logger.info(f"📋 Verification criteria: {verification_criteria}")
    
    try:
        # Use the actual verification implementation with criteria
        result = verify_model(file_path, criteria=verification_criteria)
        
        # Add the verification criteria to the result
        result["criteria"] = verification_criteria
        
        logger.info(f"✅ Verification result: {result['status']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Verification failed with exception: {e}")
        return {
            "status": "FAIL",
            "message": f"Verification failed due to unexpected error: {e}",
            "file_path": file_path,
            "criteria": verification_criteria,
            "details": [],
            "errors": [f"Unexpected error: {e}"]
        }


@mcp.tool()
def generate_cad_query(description: str) -> dict[str, Any]:
    """
    Generate CAD-Query Python script from natural language description.

    Uses the ricemonster/codegpt-small-sft model to generate CAD-Query code
    from natural language descriptions. The generated code may not be valid
    but can be used to edit the original file.

    Example prompt formats (specify spatial units):
    - "The design features a cube with smooth edges and flat faces. It measures 0.5734 units in length, 0.6253 units in width, and 0.3000 units in height."
    - "The design consists of a rectangular block and a cylindrical object. The block has a length of about 0.75, a width of 0.375, and a height of 0.125. The cylinder, which is hollow, has a length and width of about 0.375 and a height of 0.21875. These parts are joined together to form the final shape."
    - "The design features a rectangular prism with a series of indented and protruding sections. The final part measures 0.75 units in length, 0.375 units in width, and 0.0625 units in height."
    - "This design features a small rectangular box with rounded edges and two circular holes on one face. The box measures roughly 0.75 units long, 0.234 units wide, and 0.0703 units tall."

    Args:
        description: Natural language description of the desired 3D model

    Returns:
        Dict containing generated script and status
    """
    logger.info("🔧 MCP Tool Called: generate_cad_query")
    logger.info(f"📝 Description: {description}")

    # Load model if not already loaded
    if model is None or tokenizer is None:
        logger.info("Loading model on first use...")
        if not load_model():
            logger.error("Failed to load model")
            return {
                "status": "ERROR",
                "message": "Failed to load model. Please check server logs.",
                "description": description,
                "generated_code": None
            }

    try:
        # Tokenize input directly from description
        inputs = tokenizer(description, return_tensors="pt", padding=True, truncation=True)
        
        # Calculate max_new_tokens dynamically like original inference
        input_lengths = inputs["input_ids"].shape[1]
        max_new_tokens = max(1, 1024 - input_lengths)

        # Generate code with original inference settings
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
                do_sample=False
            )

        # Decode generated text
        generated_code = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

        result = {
            "status": "SUCCESS",
            "message": "CAD code generated successfully",
            "description": description,
            "generated_code": generated_code
        }

        logger.info(f"✅ Generation result: {result['status']}")
        return result

    except Exception as e:
        logger.error(f"Error generating CAD code: {e}")
        return {
            "status": "ERROR",
            "message": f"Error generating CAD code: {str(e)}",
            "description": description,
            "generated_code": None
        }


if __name__ == "__main__":
    # Run the server
    mcp.run()
