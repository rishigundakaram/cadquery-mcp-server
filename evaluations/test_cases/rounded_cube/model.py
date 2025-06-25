import cadquery as cq

# Create a 5cm cube with 0.5cm edge fillets
# This demonstrates basic box creation and edge filleting operations

# Create the basic cube (5cm on each side)
cube = cq.Workplane("XY").box(5, 5, 5)

# Apply 0.5cm fillets to all edges
# This creates smooth, rounded edges while maintaining the cubic shape
result = cube.edges().fillet(0.5)

# Required for MCP server processing
show_object(result)