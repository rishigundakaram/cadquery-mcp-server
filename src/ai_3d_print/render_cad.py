"""CAD rendering utilities for generating STL files and PNG views."""

import logging
from pathlib import Path
from typing import Any, Dict
import tempfile
import math

import cadquery as cq
import cairosvg
from PIL import Image

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


def svg_to_png(svg_content: str, output_path: Path, width: int = 800, height: int = 600) -> bool:
    """
    Convert SVG content to PNG file.
    
    Args:
        svg_content: SVG content as string
        output_path: Path where PNG file should be saved
        width: Output image width
        height: Output image height
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Convert SVG to PNG using cairosvg
        png_data = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=width,
            output_height=height
        )
        
        # Save PNG data to file
        with open(output_path, 'wb') as f:
            f.write(png_data)
        
        logger.info(f"Successfully converted SVG to PNG: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert SVG to PNG: {e}")
        return False


def generate_png_views(model: cq.Workplane, output_dir: Path, base_name: str) -> Dict[str, Any]:
    """
    Generate PNG views of the CAD model from different angles using SVG export and conversion.
    
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
    
    # Define the views to generate with their projection parameters
    views = {
        "front": {"direction": (0, -1, 0), "up": (0, 0, 1)},    # Front view (XZ plane)
        "right": {"direction": (1, 0, 0), "up": (0, 0, 1)},     # Right view (YZ plane)
        "top": {"direction": (0, 0, -1), "up": (0, 1, 0)},      # Top view (XY plane)
        "iso": {"direction": (1, -1, 1), "up": (0, 0, 1)}       # Isometric view
    }
    
    # Generate each view using SVG export and conversion
    for view_name, view_params in views.items():
        try:
            output_file = output_dir / f"{base_name}_{view_name}.png"
            
            # Generate SVG using CadQuery's export functionality
            with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as temp_svg:
                try:
                    # Export model to SVG
                    cq.exporters.export(
                        model,
                        temp_svg.name,
                        exportType=cq.exporters.ExportTypes.SVG,
                        opt={
                            "width": 800,
                            "height": 600,
                            "marginLeft": 50,
                            "marginTop": 50,
                            "showAxes": False,
                            "projectionDir": view_params["direction"],
                            "strokeWidth": 0.25,
                            "strokeColor": (0, 0, 0),
                            "hiddenColor": (160, 160, 160),
                            "showHidden": True
                        }
                    )
                    
                    # Read the generated SVG content
                    svg_content = Path(temp_svg.name).read_text()
                    
                    # Convert SVG to PNG
                    if svg_to_png(svg_content, output_file):
                        results["files"][view_name] = str(output_file)
                        logger.info(f"Generated {view_name} view: {output_file}")
                    else:
                        results["errors"].append(f"Failed to convert {view_name} view SVG to PNG")
                        
                except Exception as e:
                    results["errors"].append(f"Failed to generate {view_name} view: {e}")
                    logger.error(f"Error generating {view_name} view: {e}")
                finally:
                    # Clean up temporary SVG file
                    try:
                        Path(temp_svg.name).unlink()
                    except:
                        pass
            
        except Exception as e:
            results["errors"].append(f"Failed to create temporary file for {view_name} view: {e}")
            logger.error(f"Error creating temporary file for {view_name} view: {e}")
    
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