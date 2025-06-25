import cadquery as cq

# Create a square pyramid with 6x6 base and 8 unit height
# Using loft operation to connect square base to a point at the top

# Create the square base as a face on XY plane
base_face = cq.Workplane("XY").rect(6, 6).faces()

# Create a point at the apex (8 units above the base)
# Move to the center and create a workplane 8 units up, then create a tiny circle
apex_point = cq.Workplane("XY").center(0, 0).workplane(offset=8).circle(0.001).faces()

# Loft between the square base face and the point to create the pyramid
result = base_face.loft(apex_point)

# Required for MCP server processing
show_object(result)