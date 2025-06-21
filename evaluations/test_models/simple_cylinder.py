"""Simple cylinder for testing verification."""

import cadquery as cq

# Create a simple cylinder
result = cq.Workplane("XY").cylinder(height=10, radius=5)

show_object(result)