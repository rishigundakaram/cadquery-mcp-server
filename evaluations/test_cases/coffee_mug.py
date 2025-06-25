"""Coffee mug with handle - CAD-Query implementation."""

import cadquery as cq

# Coffee mug parameters
mug_height = 100  # 10cm
mug_diameter = 80  # 8cm diameter
wall_thickness = 3  # 3mm wall thickness
handle_width = 15  # Handle width
handle_thickness = 8  # Handle thickness

# Create the main mug body
mug_body = (
    cq.Workplane("XY")
    .circle(mug_diameter / 2)
    .extrude(mug_height)
    .faces(">Z")  # Select top face
    .shell(-wall_thickness)  # Create hollow interior
)

# Create handle using sweep along a path
handle_points = [
    (mug_diameter / 2 + 5, 0, mug_height - 20),  # Start point on mug
    (mug_diameter / 2 + 25, 0, mug_height - 15),  # Curve out
    (mug_diameter / 2 + 30, 0, mug_height - 35),  # Down
    (mug_diameter / 2 + 25, 0, mug_height - 55),  # Curve back
    (mug_diameter / 2 + 5, 0, mug_height - 50),   # End point on mug
]

# Create handle path
handle_path = cq.Workplane("XY").spline(handle_points)

# Create handle cross-section (oval)
handle_section = (
    cq.Workplane("YZ")
    .ellipse(handle_width, handle_thickness)
)

# Sweep the cross-section along the path to create handle
handle = handle_section.sweep(handle_path)

# Union the handle with the mug body
result = mug_body.union(handle)

# Required for MCP server processing
show_object(result)