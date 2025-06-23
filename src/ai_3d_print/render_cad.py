"""CAD rendering utilities for generating STL files and PNG views."""

import logging
import tempfile
from pathlib import Path
from typing import Any, Dict

import cadquery as cq

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
    Generate PNG views of the CAD model from different angles.
    
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
    
    # Define the views to generate
    views = {
        "right": {"dir": (1, 0, 0), "up": (0, 0, 1)},  # Looking from +X axis
        "top": {"dir": (0, 0, -1), "up": (0, 1, 0)},   # Looking from +Z axis (top down)
        "down": {"dir": (0, 0, 1), "up": (0, 1, 0)},   # Looking from -Z axis (bottom up)
        "iso": {"dir": (1, -1, 1), "up": (0, 0, 1)}    # Isometric view
    }
    
    try:
        # Import OCP for rendering (this is used by CadQuery for visualization)
        from OCP.Quantity import Quantity_Color
        from OCP.V3d import V3d_View
        
        # For each view, we'll try to use CadQuery's built-in export capabilities
        for view_name, view_config in views.items():
            try:
                output_file = output_dir / f"{base_name}_{view_name}.png"
                
                # Use CadQuery's export functionality to generate images
                # Note: This requires a display server or virtual display
                # For now, we'll create placeholder files and log the attempt
                
                # Create a simple visualization using matplotlib if available
                try:
                    import matplotlib.pyplot as plt
                    from mpl_toolkits.mplot3d import Axes3D
                    import numpy as np
                    
                    # Extract vertices from the model for basic visualization
                    vertices = []
                    for face in model.faces().vals():
                        for edge in face.edges():
                            for vertex in edge.vertices():
                                pt = vertex.val().Center()
                                vertices.append([pt.X(), pt.Y(), pt.Z()])
                    
                    if vertices:
                        vertices = np.array(vertices)
                        
                        fig = plt.figure(figsize=(8, 6))
                        ax = fig.add_subplot(111, projection='3d')
                        
                        # Plot vertices
                        ax.scatter(vertices[:, 0], vertices[:, 1], vertices[:, 2], alpha=0.6)
                        
                        # Set view angle based on the view configuration
                        if view_name == "right":
                            ax.view_init(elev=0, azim=0)
                        elif view_name == "top":
                            ax.view_init(elev=90, azim=0)
                        elif view_name == "down":
                            ax.view_init(elev=-90, azim=0)
                        elif view_name == "iso":
                            ax.view_init(elev=30, azim=45)
                        
                        ax.set_xlabel('X')
                        ax.set_ylabel('Y')
                        ax.set_zlabel('Z')
                        ax.set_title(f'{view_name.title()} View')
                        
                        plt.savefig(output_file, dpi=150, bbox_inches='tight')
                        plt.close()
                        
                        results["files"][view_name] = str(output_file)
                        logger.info(f"Generated {view_name} view: {output_file}")
                        
                    else:
                        # Create a placeholder file
                        output_file.write_text(f"Placeholder for {view_name} view")
                        results["files"][view_name] = str(output_file)
                        results["errors"].append(f"No vertices found for {view_name} view")
                        
                except ImportError:
                    # If matplotlib is not available, create placeholder files
                    output_file.write_text(f"Placeholder PNG for {view_name} view - matplotlib not available")
                    results["files"][view_name] = str(output_file)
                    results["errors"].append(f"matplotlib not available for {view_name} view")
                    
            except Exception as e:
                results["errors"].append(f"Failed to generate {view_name} view: {e}")
                logger.error(f"Error generating {view_name} view: {e}")
                
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"General rendering error: {e}")
        logger.error(f"Error in generate_png_views: {e}")
    
    return results


def execute_cadquery_script(script_path: Path) -> cq.Workplane:
    """
    Execute a CAD-Query Python script and return the model.
    
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
    
    # Create a namespace for script execution with CAD-Query and show_object
    namespace = {
        "cadquery": cq, 
        "cq": cq,
        "show_object": show_object,
        "__builtins__": __builtins__
    }
    
    # Execute the script
    try:
        exec(script_content, namespace)
    except Exception as e:
        raise Exception(f"Failed to execute CAD-Query script: {e}")
    
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