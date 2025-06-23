"""CAD rendering utilities for generating STL files and PNG views."""

import logging
from pathlib import Path
from typing import Any, Dict

import cadquery as cq
from cadquery.vis import show

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
    Generate PNG views of the CAD model from different angles using CadQuery's native visualization.
    
    Args:
        model: CAD-Query Workplane object
        output_dir: Directory to save PNG files
        base_name: Base name for the PNG files (without extension)
    
    Returns:
        Dict containing the status and generated file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "status": "success",
        "files": {},
        "errors": []
    }
    
    # Define the views to generate with their camera parameters
    views = {
        "right": {"elevation": 0, "roll": 90, "zoom": 1.5},     # Looking from +X axis
        "top": {"elevation": 90, "roll": 0, "zoom": 1.5},       # Looking from +Z axis (top down)
        "down": {"elevation": -90, "roll": 0, "zoom": 1.5},     # Looking from -Z axis (bottom up)
        "iso": {"elevation": 30, "roll": 45, "zoom": 1.2}       # Isometric view
    }
    
    # Generate each view using CadQuery's native show() function
    for view_name, view_params in views.items():
        try:
            output_file = output_dir / f"{base_name}_{view_name}.png"
            
            # Use CadQuery's native show() function with screenshot capability
            show(
                model,
                width=800,
                height=600,
                screenshot=str(output_file),
                zoom=view_params["zoom"],
                roll=view_params["roll"],
                elevation=view_params["elevation"],
                interact=False  # Don't open interactive window
            )
            
            results["files"][view_name] = str(output_file)
            logger.info(f"Generated {view_name} view: {output_file}")
            
        except Exception as e:
            results["errors"].append(f"Failed to generate {view_name} view: {e}")
            logger.error(f"Error generating {view_name} view: {e}")
    
    # Update status based on results
    if results["errors"] and not results["files"]:
        results["status"] = "error"
    elif results["errors"]:
        results["status"] = "partial"
    
    return results


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