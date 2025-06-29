"""Main verification helper function for CAD models."""

import logging
from pathlib import Path
from typing import Any, Dict

from .render_cad import generate_stl
from .openai_verifier import verify_cad_with_vllm
from .generate_png_views import generate_png_views_blender, VerificationResult 

logger = logging.getLogger(__name__)


async def verify_model(
    file_path: str, criteria: str = None, output_path: str = None
) -> VerificationResult:
    """
    Verify a CAD-Query model by generating STL and PNG outputs, then analyze with OpenAI.

    Args:
        file_path: Path to the CAD-Query Python file
        criteria: Verification criteria for OpenAI analysis
        output_path: Optional custom output directory. If not provided, uses default location.

    Returns:
        Dictionary containing verification results and output file paths
    """
    # Validate input file
    script_path = Path(file_path)
    if not script_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {file_path}")

    if not script_path.suffix.lower() == ".py":
        raise ValueError(f"File must be a Python (.py) file: {file_path}")

    # Create output directory
    file_name = script_path.stem
    if output_path:
        outputs_dir = Path(output_path) / file_name
    else:
        outputs_dir = script_path.parent.parent / "outputs" / file_name
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Generate STL file directly from script
    try:
        stl_path = outputs_dir / f"{file_name}.stl"
        success, error_msg = generate_stl(script_path, stl_path)
        if not success:
            return VerificationResult(
                status="FAIL",
                reasoning=f"CadQuery compilation failed: {error_msg}" if error_msg else "Failed to generate STL file from CAD script",
                criteria=criteria,
            )
        logger.info(f"STL file generated: {stl_path}")
    except Exception as e:
        logger.error(f"Failed to verify CAD model: {e}", exc_info=True)
        return VerificationResult(
            status="FAIL",
            reasoning=f"Failed to generate STL file: {e}",
            criteria=criteria,
        )

    # Generate PNG views
    try:
        png_results = generate_png_views_blender(stl_path, outputs_dir, file_name)
        logger.info(f"PNG views generated: {png_results.model_dump()}")

    except Exception as e:
        logger.error(f"Failed to verify CAD model: {e}", exc_info=True)
        return VerificationResult(
            status="FAIL",
            reasoning=f"Failed to generate PNG views: {e}",
            criteria=criteria,
        )

    # Verify with OpenAI
    try:
        logger.info("Starting OpenAI verification...")
        openai_result = await verify_cad_with_vllm(png_results, criteria)
        logger.info(f"OpenAI verification completed with status: {openai_result.status}")
        return openai_result
    except Exception as e:
        logger.error(f"Failed to verify CAD model with OpenAI: {e}", exc_info=True)
        return VerificationResult(
            status="FAIL",
            reasoning=f"Failed to verify with OpenAI: {e}",
            criteria=criteria,
        )
