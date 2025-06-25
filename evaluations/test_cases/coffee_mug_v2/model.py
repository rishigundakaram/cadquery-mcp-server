"""Coffee mug - 9cm tall, 7cm diameter with curved handle."""

import cadquery as cq

# Mug specifications
mug_height = 9
mug_diameter = 7
wall_thickness = 0.5

# Create main mug body
mug_body = (
    cq.Workplane("XY")
    .circle(mug_diameter / 2)
    .extrude(mug_height)
    .faces(">Z")
    .shell(-wall_thickness)
)

# Create handle using sweep operation
# Define handle path points
handle_points = [
    (mug_diameter / 2 + 0.3, 0, mug_height - 1.5),  # Start on mug
    (mug_diameter / 2 + 2, 0, mug_height - 1),       # Curve out
    (mug_diameter / 2 + 2.5, 0, mug_height - 3),     # Down
    (mug_diameter / 2 + 2.5, 0, mug_height - 5),     # Continue down
    (mug_diameter / 2 + 2, 0, mug_height - 7),       # Curve back in
    (mug_diameter / 2 + 0.3, 0, mug_height - 6.5),   # End on mug
]

# Create spline path for handle
handle_path = cq.Workplane("XY").spline(handle_points)

# Create handle cross-section (circular)
handle_section = cq.Workplane("YZ").circle(0.4)

# Sweep to create handle
handle = handle_section.sweep(handle_path)

# Union handle with mug body
result = mug_body.union(handle)

show_object(result)