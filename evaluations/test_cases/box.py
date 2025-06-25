"""Simple box example for testing CAD-Query workflow."""

import cadquery as cq

# Create a simple box with a hole through the center
result = cq.Workplane("XY").box(20, 20, 10).faces(">Z").hole(5)

# Export the result for cq-cli
# Note: show_object is provided by CQGI execution environment
show_object(result)  # noqa: F821
