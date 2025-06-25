import cadquery as cq

# Simple ring (torus) with revolve operation
# Major radius: 3 units (distance from center to tube center)
# Minor radius: 0.8 units (tube thickness)

# Create the ring by revolving a circular cross-section
result = (
    cq.Workplane("XZ")        # Work in XZ plane for profile
    .moveTo(3, 0)             # Move to major radius distance from center
    .circle(0.8)              # Create circular cross-section with minor radius
    .revolve(360)             # Revolve 360 degrees around Y-axis to create torus
)

show_object(result)