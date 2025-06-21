"""3D donut (torus) example for CAD-Query workflow."""

import cadquery as cq

# Create a proper torus (donut) using the revolve method
# This method creates a true rounded donut by revolving a circle
major_radius = 15  # Distance from center to tube center
minor_radius = 3   # Tube radius

result = (cq.Workplane("YZ")
          .moveTo(major_radius, 0)  # Move to major radius distance from center
          .circle(minor_radius)     # Create circle with minor radius
          .revolve(360)             # Revolve 360 degrees around Y-axis to create torus
         )

# Export the result for cq-cli
# Note: show_object is provided by CQGI execution environment
show_object(result)  # noqa: F821
