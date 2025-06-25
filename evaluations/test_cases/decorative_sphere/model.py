"""
Decorative Sphere with Dimpled Texture
======================================

This script creates a decorative sphere with a dimpled texture by subtracting
smaller spheres from the surface of a main sphere.

Specifications:
- Main sphere: 4cm radius
- Dimples: 0.5cm radius spheres subtracted from surface
- Multiple dimples positioned around the sphere for texture
"""

import cadquery as cq
import math

# Main sphere parameters
main_radius = 4.0  # 4cm radius
dimple_radius = 0.5  # 0.5cm radius for dimples

# Create the main sphere
main_sphere = cq.Workplane("XY").sphere(main_radius)

# Define dimple positions (positioned slightly outside the main sphere surface)
# Using spherical coordinates to distribute dimples around the sphere
dimple_positions = [
    # Top hemisphere dimples
    (3.7, 0, 2.5),      # Top front
    (2.6, 2.6, 2.0),    # Top front-right
    (-2.6, 2.6, 2.0),   # Top front-left
    (0, -3.7, 1.5),     # Top back
    
    # Equatorial dimples
    (3.8, 0, 0),        # Front center
    (0, 3.8, 0),        # Right center
    (-3.8, 0, 0),       # Back center
    (0, -3.8, 0),       # Left center
    
    # Bottom hemisphere dimples
    (2.6, 2.6, -2.0),   # Bottom front-right
    (-2.6, 2.6, -2.0),  # Bottom front-left
    (3.7, 0, -2.5),     # Bottom front
    (0, -3.7, -1.5),    # Bottom back
]

# Start with the main sphere
result = main_sphere

# Create and subtract each dimple
for i, (x, y, z) in enumerate(dimple_positions):
    # Create a small sphere for the dimple
    dimple = (cq.Workplane("XY")
              .sphere(dimple_radius)
              .translate((x, y, z)))
    
    # Subtract the dimple from the main sphere
    result = result.cut(dimple)

# Required for MCP server processing
show_object(result)