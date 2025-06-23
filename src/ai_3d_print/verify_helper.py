"""Main verification helper function for CAD models."""

import logging
from pathlib import Path
from typing import Any, Dict

from .render_cad import execute_cadquery_script, generate_stl, generate_png_views

logger = logging.getLogger(__name__)


def verify_model(file_path: str) -> Dict[str, Any]:
    """
    Verify a CAD-Query model by generating STL and PNG outputs.
    
    Args:
        file_path: Path to the CAD-Query Python file
    
    Returns:
        Dictionary containing verification results and output file paths
    """
    result = {
        "status": "PASS",
        "message": "CAD model verification completed successfully",
        "file_path": file_path,
        "outputs": {
            "stl": None,
            "pngs": {}
        },
        "details": [],
        "errors": []
    }
    
    try:
        # Validate input file
        script_path = Path(file_path)
        if not script_path.exists():
            result["status"] = "FAIL"
            result["message"] = f"File not found: {file_path}"
            result["errors"].append(f"Input file does not exist: {file_path}")
            return result
            
        if not script_path.suffix.lower() == '.py':
            result["status"] = "FAIL"
            result["message"] = f"Invalid file type: {file_path}"
            result["errors"].append(f"File must be a Python (.py) file: {file_path}")
            return result
        
        # Create output directory
        file_name = script_path.stem
        outputs_dir = script_path.parent.parent / "outputs" / file_name
        
        try:
            outputs_dir.mkdir(parents=True, exist_ok=True)
            result["details"].append(f"Created output directory: {outputs_dir}")
        except Exception as e:
            result["status"] = "FAIL"
            result["message"] = f"Failed to create output directory: {e}"
            result["errors"].append(f"Could not create output directory: {e}")
            return result
        
        # Execute the CAD-Query script
        try:
            model = execute_cadquery_script(script_path)
            result["details"].append("Successfully executed CAD-Query script")
        except Exception as e:
            result["status"] = "FAIL"
            result["message"] = f"Failed to execute CAD script: {e}"
            result["errors"].append(f"Script execution error: {e}")
            return result
        
        # Generate STL file
        stl_path = outputs_dir / f"{file_name}.stl"
        try:
            if generate_stl(model, stl_path):
                result["outputs"]["stl"] = str(stl_path)
                result["details"].append(f"Generated STL file: {stl_path}")
            else:
                result["errors"].append("Failed to generate STL file")
        except Exception as e:
            result["errors"].append(f"STL generation error: {e}")
        
        # Generate PNG views
        try:
            png_results = generate_png_views(model, outputs_dir, file_name)
            result["outputs"]["pngs"] = png_results["files"]
            
            if png_results["status"] == "success":
                result["details"].append(f"Generated {len(png_results['files'])} PNG views")
            else:
                result["errors"].extend(png_results.get("errors", []))
                
            # Add details about each generated PNG
            for view_name, png_path in png_results["files"].items():
                result["details"].append(f"Generated {view_name} view: {png_path}")
                
        except Exception as e:
            result["errors"].append(f"PNG generation error: {e}")
        
        # Determine final status
        if result["errors"]:
            if result["outputs"]["stl"] or result["outputs"]["pngs"]:
                result["status"] = "PARTIAL"
                result["message"] = "Verification completed with some errors"
            else:
                result["status"] = "FAIL"
                result["message"] = "Verification failed - no outputs generated"
        else:
            result["status"] = "PASS"
            result["message"] = "CAD model verification completed successfully"
        
        # Add summary information
        stl_count = 1 if result["outputs"]["stl"] else 0
        png_count = len(result["outputs"]["pngs"])
        result["details"].append(f"Generated {stl_count} STL file and {png_count} PNG views")
        
    except Exception as e:
        result["status"] = "FAIL"
        result["message"] = f"Unexpected error during verification: {e}"
        result["errors"].append(f"Unexpected error: {e}")
        logger.error(f"Unexpected error in verify_model: {e}")
    
    return result