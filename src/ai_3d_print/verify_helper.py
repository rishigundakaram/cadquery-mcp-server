"""Main verification helper function for CAD models."""

import logging
from pathlib import Path

from .models import VerificationResponse, VerificationResult
from .services import RenderService, VisionService
from .render_cad import load_cadquery_model

logger = logging.getLogger(__name__)


def verify_model(file_path: str, verification_criteria: str = "") -> VerificationResponse:
    """
    Verify a CAD-Query model by generating outputs and analyzing with GPT-4.1 Vision.
    
    Args:
        file_path: Path to the CAD-Query Python file
        verification_criteria: Description of what to verify against
    
    Returns:
        VerificationResponse with the verification result
    """
    try:
        # Validate input file
        script_path = Path(file_path)
        if not script_path.exists():
            return VerificationResponse.error(f"Input file does not exist: {file_path}")
            
        if not script_path.suffix.lower() == '.py':
            return VerificationResponse.error(f"File must be a Python (.py) file: {file_path}")
        
        # Create output directory
        file_name = script_path.stem
        outputs_dir = script_path.parent.parent / "outputs" / file_name
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load the CAD-Query model (this will fail if code doesn't compile)
        try:
            model = load_cadquery_model(script_path)
        except Exception as e:
            return VerificationResponse.error(f"Failed to load CAD model: {e}")
        
        # Initialize services
        render_service = RenderService()
        vision_service = VisionService()
        
        # Render the model to STL and PNG files
        render_result = render_service.render_model(model, outputs_dir, file_name)
        
        if not render_result.success:
            return VerificationResponse.error(f"Failed to render model: {render_result.get_error_summary()}")
        
        # If no verification criteria provided, just validate model generation
        if not verification_criteria:
            return VerificationResponse.success("CAD model generated successfully")
        
        # Perform vision-based verification
        if not render_result.has_images():
            return VerificationResponse.error("Images not available for verification")
        
        logger.info(f"Starting vision analysis for {file_path}")
        vision_result = vision_service.analyze_cad_model(render_result.image_views, verification_criteria)
        
        # Return the vision analysis result directly
        return vision_result
        
    except Exception as e:
        logger.error(f"Verification failed for {file_path}: {e}")
        return VerificationResponse.error(f"Unexpected verification error: {e}")