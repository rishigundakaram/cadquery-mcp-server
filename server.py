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
        model = AutoModelForCausalLM.from_pretrained("ricemonster/codegpt-small-sft")
        tokenizer = AutoTokenizer.from_pretrained("ricemonster/codegpt-small-sft")

        # Add padding token if it doesn't exist
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        logger.info("Model loaded successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False

# Load model at startup
load_model()


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
        result = verify_model(file_path, verification_criteria)
        
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
def generate_cad_query(description: str, parameters: str = "") -> dict[str, Any]:
    """
    Generate CAD-Query Python script from natural language description.

    Uses the ricemonster/codegpt-small-sft model to generate CAD-Query code
    from natural language descriptions.

    Args:
        description: Natural language description of the desired 3D model
        parameters: Optional specific dimensions or constraints

    Returns:
        Dict containing generated script and status
    """
    logger.info("🔧 MCP Tool Called: generate_cad_query")
    logger.info(f"📝 Description: {description}")
    logger.info(f"📏 Parameters: {parameters}")

    # Check if model is loaded
    if model is None or tokenizer is None:
        logger.error("Model not loaded")
        return {
            "status": "ERROR",
            "message": "Model not loaded. Please check server logs.",
            "description": description,
            "parameters": parameters,
            "generated_code": None
        }

    try:
        # Create prompt for CAD-Query code generation
        full_description = f"{description}"
        if parameters:
            full_description += f" with parameters: {parameters}"

        prompt = f"""# Generate CAD-Query Python code for: {full_description}
# Import cadquery and create the 3D model
import cadquery as cq

# Create the model
result = """

        # Tokenize input
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)

        # Generate code
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract the generated code part (after the prompt)
        generated_code = generated_text[len(prompt):].strip()

        result = {
            "status": "SUCCESS",
            "message": "CAD code generated successfully",
            "description": description,
            "parameters": parameters,
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
            "parameters": parameters,
            "generated_code": None
        }


if __name__ == "__main__":
    # Run the server
    mcp.run()
