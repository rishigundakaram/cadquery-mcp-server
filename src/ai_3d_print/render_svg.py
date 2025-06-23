"""SVG rendering utilities for CAD models."""

import logging
from pathlib import Path
from typing import Any, Dict

import cadquery as cq

logger = logging.getLogger(__name__)


def generate_svg_views(model: cq.Workplane, output_dir: Path, base_name: str) -> Dict[str, Any]:
    """
    Generate SVG views of the CAD model from different angles.
    
    Args:
        model: CAD-Query Workplane object
        output_dir: Directory to save SVG files
        base_name: Base name for the SVG files (without extension)
    
    Returns:
        Dict containing the status and generated file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "status": "success",
        "files": {},
        "errors": []
    }
    
    # Define the views to generate with their parameters
    views = {
        "right": {"direction": (1, 0, 0), "up": (0, 0, 1)},     # Looking from +X axis
        "top": {"direction": (0, 0, -1), "up": (0, 1, 0)},      # Looking from +Z axis (top down)
        "down": {"direction": (0, 0, 1), "up": (0, 1, 0)},      # Looking from -Z axis (bottom up)
        "iso": {"direction": (1, 1, 1), "up": (0, 0, 1)}        # Isometric view
    }
    
    # Generate each view
    for view_name, view_params in views.items():
        try:
            output_file = output_dir / f"{base_name}_{view_name}.svg"
            
            # Create SVG using CadQuery's exporters
            # Need to convert Workplane to Shape for SVG export
            if hasattr(model, 'val') and model.val():
                # Get the first shape from the workplane  
                shape = model.val()
            elif hasattr(model, 'objects') and model.objects:
                # Get the first object from the workplane
                shape = model.objects[0]
            else:
                # Try to get any solid/compound from the workplane
                shape = model
            
            svg_content = cq.exporters.getSVG(
                shape,
                opts={
                    "width": 800,
                    "height": 600,
                    "marginLeft": 10,
                    "marginTop": 10,
                    "projectionDir": view_params["direction"],
                    "strokeWidth": 0.25,
                    "strokeColor": (0, 0, 0),
                    "hiddenColor": (160, 160, 160),
                    "showHidden": True
                }
            )
            
            # Write SVG to file
            with open(output_file, 'w') as f:
                f.write(svg_content)
            
            results["files"][view_name] = str(output_file)
            logger.info(f"Generated {view_name} SVG view: {output_file}")
            
        except Exception as e:
            results["errors"].append(f"Failed to generate {view_name} SVG view: {e}")
            logger.error(f"Error generating {view_name} SVG view: {e}")
    
    # Update status based on results
    if results["errors"] and not results["files"]:
        results["status"] = "error"
    elif results["errors"]:
        results["status"] = "partial"
    
    return results