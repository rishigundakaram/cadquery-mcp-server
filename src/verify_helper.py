"""Main verification helper function for CAD models."""

import logging
from pathlib import Path
from typing import Any, Dict

from .render_cad import load_cadquery_model, generate_stl, generate_png_views
from .openai_verifier import verify_cad_with_vllm
from .types import VerificationResult
from .generate_png_views import generate_png_views_blender

logger = logging.getLogger(__name__)


def verify_model(
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
        if not generate_stl(script_path, stl_path):
            return VerificationResult(
                status="FAIL",
                reasoning="Failed to generate STL file from CAD script",
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

    # Add PNG file paths to result
    try:
        openai_result = verify_cad_with_vllm(png_results, criteria)
    except Exception as e:
        logger.error(f"Failed to verify CAD model: {e}", exc_info=True)
        return VerificationResult(
            status="FAIL",
            reasoning=f"Failed to add PNG file paths to result: {e}",
            criteria=criteria,
        )
    return openai_result
