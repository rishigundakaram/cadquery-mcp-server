"""CAD rendering utilities for generating STL files and PNG views."""

import logging
from pathlib import Path
from typing import Any, Dict
import numpy as np

import cadquery as cq
import trimesh
import pyrender
from PIL import Image
from .types import PNGPaths

logger = logging.getLogger(__name__)


def generate_stl(script_path: Path, output_path: Path) -> bool:
    """
    Generate STL file from CAD-Query script.

    Args:
        script_path: Path to the CAD-Query Python script
        output_path: Path where STL file should be saved

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use cq-cli to convert CAD-Query script to STL
        import subprocess
        result = subprocess.run([
            "cq-cli", 
            "--codec", "stl",
            "--infile", str(script_path),
            "--outfile", str(output_path),
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info(f"STL generated successfully: {output_path}")
            return True
        else:
            logger.error(f"cq-cli execution failed: {result.stderr}")
            logger.error(f"cq-cli stdout: {result.stdout}")
            return False

    except Exception as e:
        logger.error(f"Failed to generate STL: {e}. If the error is a timeout, most likely the \
        geometry is invalid. ")
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


def make_scene(
    mesh: trimesh.Trimesh, camera_pose: np.ndarray, light_intensity: float = 3.0
) -> pyrender.Scene:
    """
    Create a pyrender scene with mesh, camera, and lighting optimized for LLM vision analysis.

    Args:
        mesh: Trimesh object to render
        camera_pose: 4x4 camera transformation matrix
        light_intensity: Brightness of the directional light

    Returns:
        Configured pyrender scene
    """
    # White background for high contrast
    scene = pyrender.Scene(bg_color=[1.0, 1.0, 1.0, 1.0], ambient_light=[0.3, 0.3, 0.3])

    # Create bright yellow material with good contrast properties
    material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[1.0, 0.8, 0.0, 1.0],  # Bright yellow
        metallicFactor=0.0,  # Not metallic (matte finish)
        roughnessFactor=0.8,  # Rough surface (less shiny)
        emissiveFactor=[0.0, 0.0, 0.0],  # No emission
    )

    # Add mesh with custom yellow material
    mesh_node = pyrender.Mesh.from_trimesh(mesh, material=material, smooth=True)
    scene.add(mesh_node)

    # Add wireframe overlay for geometric edges only (not triangulation)
    wireframe_material = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=[0.0, 0.0, 0.0, 1.0],  # Black wireframe
        metallicFactor=0.0,
        roughnessFactor=1.0,
    )

    # Add distinct edge highlighting using face normals to detect sharp edges
    try:
        # Find sharp edges (where face normals change significantly)
        face_adjacency = mesh.face_adjacency
        face_normals = mesh.face_normals

        # Calculate angle between adjacent faces
        adjacent_face_normals = face_normals[face_adjacency]
        face_angles = np.arccos(
            np.clip(
                np.sum(
                    adjacent_face_normals[:, 0] * adjacent_face_normals[:, 1], axis=1
                ),
                -1,
                1,
            )
        )

        # Find edges where faces meet at sharp angles (> 30 degrees)
        sharp_edge_mask = face_angles > np.deg2rad(30)

        if np.any(sharp_edge_mask):
            # Create wireframe highlighting only sharp geometric edges
            wireframe_mesh = mesh.copy()
            wireframe_mesh.visual.face_colors = [0, 0, 0, 255]  # Black
            wireframe_node = pyrender.Mesh.from_trimesh(
                wireframe_mesh, material=wireframe_material, wireframe=True
            )
            scene.add(wireframe_node)
    except:
        # Fallback to simple wireframe if edge detection fails
        wireframe_mesh = mesh.copy()
        wireframe_mesh.visual.face_colors = [0, 0, 0, 255]  # Black
        wireframe_node = pyrender.Mesh.from_trimesh(
            wireframe_mesh, material=wireframe_material, wireframe=True
        )
        scene.add(wireframe_node)

    # Add perspective camera
    cam = pyrender.PerspectiveCamera(yfov=np.deg2rad(45), znear=0.05, zfar=50)
    scene.add(cam, pose=camera_pose)

    # Add main directional light (key light)
    main_light = pyrender.DirectionalLight(
        color=[1.0, 1.0, 1.0], intensity=light_intensity
    )
    scene.add(main_light, pose=camera_pose)

    # Add fill light from opposite side for better contrast
    fill_light_pose = camera_pose.copy()
    fill_light_pose[0:3, 3] = -fill_light_pose[0:3, 3] * 0.5  # Opposite side, closer
    fill_light = pyrender.DirectionalLight(
        color=[1.0, 1.0, 1.0],
        intensity=light_intensity * 0.3,  # Dimmer fill light
    )
    scene.add(fill_light, pose=fill_light_pose)

    return scene

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
        "__builtins__": __builtins__,
    }

    # Execute the script - if it fails, the model is invalid
    logger.info(f"Executing script: {script_content}")
    exec(script_content, namespace)
    logger.info(f"Script executed: {namespace.keys()}")
    # First, check if show_object was called
    if shown_objects:
        for obj in shown_objects:
            if isinstance(obj, cq.Workplane):
                return obj
    logger.info(f"Shown objects: {shown_objects}")
    # Look for the result in common variable names
    result_candidates = ["result", "model", "part", "shape"]
    logger.info(f"Result candidates: {result_candidates}")
    for candidate in result_candidates:
        if candidate in namespace and isinstance(namespace[candidate], cq.Workplane):
            logger.info(f"Found result: {candidate}")
            return namespace[candidate]

    # If no obvious result variable, look for any Workplane object
    for name, value in namespace.items():
        if isinstance(value, cq.Workplane) and not name.startswith("_"):
            logger.info(f"Found result in namespace: {name}")
            return value

    raise Exception("No CAD-Query Workplane object found in script")
