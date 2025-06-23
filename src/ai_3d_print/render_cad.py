"""CAD rendering utilities for generating STL files and PNG views."""

import logging
from pathlib import Path
from typing import Any, Dict

import cadquery as cq
from .render_svg import generate_svg_views
from .svg_to_png import convert_svg_views_to_png

logger = logging.getLogger(__name__)


def generate_stl(model: cq.Workplane, output_path: Path) -> bool:
    """
    Generate STL file from CAD-Query model.
    
    Args:
        model: CAD-Query Workplane object
        output_path: Path where STL file should be saved
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export to STL
        cq.exporters.export(model, str(output_path))
        logger.info(f"STL generated successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate STL: {e}")
        return False


def generate_png_views(model: cq.Workplane, output_dir: Path, base_name: str) -> Dict[str, Any]:
    """
    Generate PNG views of the CAD model from different angles using SVG conversion.
    
    This method generates SVG views first (which works in headless environments)
    and then converts them to PNG format for compatibility with vision analysis.
    
    Args:  
        model: CAD-Query Workplane object
        output_dir: Directory to save PNG files
        base_name: Base name for the PNG files (without extension)
    
    Returns:
        Dict containing the status and generated file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating PNG views for {base_name} using SVG conversion method")
    
    # First, generate SVG views
    svg_results = generate_svg_views(model, output_dir, base_name)
    
    if svg_results["status"] == "error":
        logger.error("Failed to generate SVG views")
        return {
            "status": "error",
            "files": {},
            "errors": svg_results["errors"]
        }
    
    # Convert SVG views to PNG
    png_results = convert_svg_views_to_png(svg_results["files"], output_dir, base_name)
    
    # Combine results
    combined_results = {
        "status": "success",
        "files": png_results["files"],
        "errors": svg_results["errors"] + png_results["errors"]
    }
    
    # Update status based on overall results
    if combined_results["errors"] and not combined_results["files"]:
        combined_results["status"] = "error"
    elif combined_results["errors"]:
        combined_results["status"] = "partial"
    
    # Log results
    if combined_results["files"]:
        logger.info(f"Successfully generated {len(combined_results['files'])} PNG views")
        for view_name, path in combined_results["files"].items():
            logger.info(f"  {view_name}: {path}")
    
    if combined_results["errors"]:
        logger.warning(f"Encountered {len(combined_results['errors'])} errors during PNG generation")
        for error in combined_results["errors"]:
            logger.warning(f"  {error}")
    
    return combined_results


def load_cadquery_model(script_path: Path) -> cq.Workplane:
    """
    Load a CAD-Query model from a Python script.
    
    Args:
        script_path: Path to the Python script containing CAD-Query code
    
    Returns:
        cq.Workplane: The resulting CAD model
    
    Raises:
        Exception: If script execution fails or no model is found
    """
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    # Read the script content
    script_content = script_path.read_text()
    
    # Storage for models passed to show_object
    shown_objects = []
    
    def show_object(obj):
        """Mock show_object function to capture CAD models."""
        shown_objects.append(obj)
        return obj
    
    # Create a namespace for script execution
    namespace = {
        "cadquery": cq, 
        "cq": cq,
        "show_object": show_object,
        "__builtins__": __builtins__
    }
    
    # Execute the script - if it fails, the model is invalid
    exec(script_content, namespace)
    
    # First, check if show_object was called
    if shown_objects:
        for obj in shown_objects:
            if isinstance(obj, cq.Workplane):
                return obj
    
    # Look for the result in common variable names
    result_candidates = ["result", "model", "part", "shape"]
    
    for candidate in result_candidates:
        if candidate in namespace and isinstance(namespace[candidate], cq.Workplane):
            return namespace[candidate]
    
    # If no obvious result variable, look for any Workplane object
    for name, value in namespace.items():
        if isinstance(value, cq.Workplane) and not name.startswith("_"):
            return value
    
    raise Exception("No CAD-Query Workplane object found in script")