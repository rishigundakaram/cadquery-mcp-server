"""Main verification helper function for CAD models."""

import logging
from pathlib import Path
from typing import Any, Dict

from .render_cad import load_cadquery_model, generate_stl, generate_png_views

logger = logging.getLogger(__name__)


def verify_model(file_path: str, output_path: str = None) -> Dict[str, Any]:
    """
    Verify a CAD-Query model by generating STL and PNG outputs.
    
    Args:
        file_path: Path to the CAD-Query Python file
        output_path: Optional custom output directory. If not provided, uses default location.
    
    Returns:
        Dictionary containing verification results and output file paths
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
        if output_path:
            outputs_dir = Path(output_path) / file_name
        else:
            outputs_dir = script_path.parent.parent / "outputs" / file_name
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Load the CAD-Query model (this will fail if code doesn't compile)
        model = load_cadquery_model(script_path)
        
        # Generate STL file
        stl_path = outputs_dir / f"{file_name}.stl"
        generate_stl(model, stl_path)
        
        # Generate PNG views
        png_results = generate_png_views(model, outputs_dir, file_name)
        
        return result
        
    except Exception as e:
        result["status"] = "FAIL"
        result["message"] = f"Verification failed: {e}"
        result["errors"].append(str(e))
        logger.error(f"Verification failed for {file_path}: {e}")
        return result