"""CAD rendering utilities for generating STL files and PNG views."""

import logging
from pathlib import Path
from typing import Any, Dict
import numpy as np

import cadquery as cq
import trimesh
import pyrender
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


def look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    """
    Generate a 4x4 look-at transformation matrix.
    
    Args:
        eye: Camera position
        target: Point to look at
        up: Up vector
        
    Returns:
        4x4 transformation matrix
    """
    # Calculate camera coordinate system
    forward = target - eye
    forward = forward / np.linalg.norm(forward)
    
    right = np.cross(forward, up)
    right = right / np.linalg.norm(right)
    
    up_corrected = np.cross(right, forward)
    up_corrected = up_corrected / np.linalg.norm(up_corrected)
    
    # Create transformation matrix
    transform = np.eye(4)
    transform[0:3, 0] = right
    transform[0:3, 1] = up_corrected  
    transform[0:3, 2] = -forward
    transform[0:3, 3] = eye
    
    return transform


def spherical_pose(theta_deg: float, phi_deg: float, radius: float) -> np.ndarray:
    """
    Generate a 4x4 camera-to-world transform matrix for spherical coordinates.
    
    Args:
        theta_deg: Azimuth angle in degrees
        phi_deg: Elevation angle in degrees  
        radius: Distance from origin
    
    Returns:
        4x4 transformation matrix
    """
    theta, phi = np.deg2rad(theta_deg), np.deg2rad(phi_deg)
    
    # Cartesian coordinates on a sphere
    x = radius * np.cos(phi) * np.sin(theta)
    y = radius * np.sin(phi)
    z = radius * np.cos(phi) * np.cos(theta)
    
    # Look-at origin
    eye = np.array([x, y, z])
    target = np.zeros(3)
    up = np.array([0, 1, 0])
    
    return look_at(eye, target, up)


def make_scene(mesh: trimesh.Trimesh, camera_pose: np.ndarray, 
               light_intensity: float = 3.0) -> pyrender.Scene:
    """
    Create a pyrender scene with mesh, camera, and lighting.
    
    Args:
        mesh: Trimesh object to render
        camera_pose: 4x4 camera transformation matrix
        light_intensity: Brightness of the directional light
    
    Returns:
        Configured pyrender scene
    """
    scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0], ambient_light=[0.1, 0.1, 0.1])
    
    # Add mesh with smooth shading
    mesh_node = pyrender.Mesh.from_trimesh(mesh, smooth=True)
    scene.add(mesh_node)
    
    # Add perspective camera
    cam = pyrender.PerspectiveCamera(yfov=np.deg2rad(45), znear=0.05, zfar=50)
    scene.add(cam, pose=camera_pose)
    
    # Add directional light co-located with camera
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=light_intensity)
    scene.add(light, pose=camera_pose)
    
    return scene


def generate_png_views(model: cq.Workplane, output_dir: Path, base_name: str) -> Dict[str, Any]:
    """
    Generate high-quality 3D rendered PNG views using trimesh + pyrender.
    
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
    
    try:
        # First generate STL file to load with trimesh
        temp_stl = output_dir / f"{base_name}_temp.stl"
        cq.exporters.export(model, str(temp_stl))
        
        # Load mesh with trimesh
        mesh = trimesh.load(str(temp_stl))
        
        # Normalize mesh - fit to unit cube and center
        mesh.apply_scale(1.0 / mesh.scale)
        mesh.apply_translation(-mesh.center_mass)
        
        # Clean up temp STL
        try:
            temp_stl.unlink()
        except:
            pass
        
        # Define camera positions for different views
        views = {
            "front": (0, 20, 3.0),      # Front view
            "right": (90, 20, 3.0),     # Right side view  
            "top": (0, 85, 3.0),        # Top down view
            "iso": (45, 35, 3.5),       # Isometric view
        }
        
        # Set up off-screen renderer
        renderer = pyrender.OffscreenRenderer(1024, 1024)
        
        try:
            for view_name, (theta, phi, radius) in views.items():
                try:
                    output_file = output_dir / f"{base_name}_{view_name}.png"
                    
                    # Generate camera pose
                    camera_pose = spherical_pose(theta, phi, radius)
                    
                    # Create scene
                    scene = make_scene(mesh, camera_pose)
                    
                    # Render with shadows
                    color, depth = renderer.render(scene, flags=pyrender.RenderFlags.SHADOWS_DIRECTIONAL)
                    
                    # Convert to PIL Image and save
                    img = Image.fromarray(color)
                    img.save(output_file, 'PNG')
                    
                    results["files"][view_name] = str(output_file)
                    logger.info(f"Generated {view_name} view: {output_file}")
                    
                except Exception as e:
                    results["errors"].append(f"Failed to generate {view_name} view: {e}")
                    logger.error(f"Error generating {view_name} view: {e}")
        
        finally:
            renderer.delete()
            
    except Exception as e:
        results["errors"].append(f"Failed to load mesh for 3D rendering: {e}")
        logger.error(f"Error in 3D rendering pipeline: {e}")
    
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