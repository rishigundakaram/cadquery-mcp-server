"""Main verification helper function for CAD models."""

import logging
from pathlib import Path
from typing import Any, Dict

from .render_cad import load_cadquery_model, generate_stl, generate_png_views
from .vision_analysis import analyze_cad_images_with_gpt4

logger = logging.getLogger(__name__)


def verify_model(file_path: str, verification_criteria: str = "") -> Dict[str, Any]:
    """
    Verify a CAD-Query model by generating outputs and analyzing with GPT-4 Vision.
    
    Args:
        file_path: Path to the CAD-Query Python file
        verification_criteria: Description of what to verify against
    
    Returns:
        Dictionary containing verification results and analysis
    """
    result = {
        "status": "PASS",
        "message": "CAD model verification completed successfully",
        "file_path": file_path,
        "details": [],
        "errors": []
    }
    
    try:
        # Validate input file
        script_path = Path(file_path)
        if not script_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {file_path}")
            
        if not script_path.suffix.lower() == '.py':
            raise ValueError(f"File must be a Python (.py) file: {file_path}")
        
        # Create output directory
        file_name = script_path.stem
        outputs_dir = script_path.parent.parent / "outputs" / file_name
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load the CAD-Query model (this will fail if code doesn't compile)
        model = load_cadquery_model(script_path)
        
        # Generate STL file
        stl_path = outputs_dir / f"{file_name}.stl"
        generate_stl(model, stl_path)
        
        # Generate PNG views
        png_results = generate_png_views(model, outputs_dir, file_name)
        
        # Perform vision-based verification if criteria provided and images generated
        if verification_criteria and png_results["status"] in ["success", "partial"] and png_results["files"]:
            logger.info(f"Starting vision analysis for {file_path}")
            
            # Analyze images with GPT-4 Vision
            vision_result = analyze_cad_images_with_gpt4(
                png_results["files"], 
                verification_criteria
            )
            
            # Update result based on vision analysis
            if vision_result["status"] == "SUCCESS":
                result["status"] = vision_result["verification_result"]
                result["message"] = f"Vision analysis completed: {vision_result['verification_result']}"
                result["vision_analysis"] = {
                    "confidence": vision_result.get("confidence", "UNKNOWN"),
                    "analysis": vision_result.get("analysis", {}),
                    "reasoning": vision_result.get("reasoning", ""),
                    "recommendations": vision_result.get("recommendations", "")
                }
                
                # Add details about the analysis
                if result["status"] == "PASS":
                    result["details"].append(f"Vision verification passed with {vision_result.get('confidence', 'UNKNOWN')} confidence")
                else:
                    result["details"].append(f"Vision verification failed: {vision_result.get('reasoning', 'No reason provided')}")
                    
            else:
                # Vision analysis failed, but model generation succeeded
                result["status"] = "PARTIAL"
                result["message"] = f"Model generated successfully, but vision analysis failed: {vision_result.get('message', 'Unknown error')}"
                result["vision_analysis"] = vision_result
                result["details"].append("Vision analysis could not be completed")
                result["errors"].append(f"Vision analysis error: {vision_result.get('message', 'Unknown error')}")
                
        elif verification_criteria:
            # Criteria provided but no images generated
            result["status"] = "PARTIAL" 
            result["message"] = "Model generated successfully, but verification images not available"
            result["details"].append("Vision verification skipped - no images available")
            result["errors"].extend(png_results.get("errors", []))
            
        else:
            # No verification criteria provided - just validate model generation
            result["status"] = "PASS"
            result["message"] = "CAD model generated successfully (no verification criteria provided)"
            result["details"].append("Model generation validated only")
        
        # Add PNG generation results
        result["png_generation"] = png_results
        result["output_files"] = {
            "stl_path": str(stl_path),
            "png_files": png_results["files"]
        }
        
        return result
        
    except Exception as e:
        result["status"] = "FAIL"
        result["message"] = f"Verification failed: {e}"
        result["errors"].append(str(e))
        logger.error(f"Verification failed for {file_path}: {e}")
        return result