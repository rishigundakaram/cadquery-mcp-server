import cadquery as cq

# Pen holder specifications:
# - Height: 8 units
# - Outer diameter: 4 units (radius: 2 units)
# - Inner diameter: 3.5 units (radius: 1.75 units)
# - Base thickness: 0.25 units

# Create the outer cylinder
outer_cylinder = cq.Workplane("XY").circle(2).extrude(8)

# Create the inner cavity (hollow part)
# Start from the top of the base (offset by base thickness)
inner_cavity = (
    cq.Workplane("XY")
    .workplane(offset=0.25)  # Start from base thickness
    .circle(1.75)            # Inner radius
    .extrude(7.75)           # Height minus base thickness
)

# Subtract the inner cavity from the outer cylinder to create the hollow pen holder
result = outer_cylinder.cut(inner_cavity)

# Required for MCP server processing
show_object(result)