"""Keychain name tag - flat tag with extruded text and keyring hole."""

import cadquery as cq

# Tag specifications
tag_length = 4
tag_width = 2
tag_thickness = 0.3
hole_diameter = 0.4
text_depth = 0.1

# Create base tag
tag_base = cq.Workplane("XY").rect(tag_length, tag_width).extrude(tag_thickness)

# Create keyring hole
hole = (
    cq.Workplane("XY")
    .moveTo(tag_length/2 - 0.4, 0)  # Position hole near edge
    .circle(hole_diameter / 2)
    .extrude(tag_thickness + 0.1)  # Through hole
)

# Cut hole from base
tag_with_hole = tag_base.cut(hole)

# Add extruded text "TAG"
# Note: CAD-Query text requires specific positioning
text_workplane = (
    cq.Workplane("XY")
    .workplane(offset=tag_thickness)
    .moveTo(-0.8, 0)  # Position text on tag
)

# Create simple text using geometric shapes instead of text() function
# Letter "T"
t_vertical = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(-1.2, 0).rect(0.15, 0.8).extrude(text_depth)
t_horizontal = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(-1.2, 0.32).rect(0.6, 0.15).extrude(text_depth)

# Letter "A" 
a_left = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(-0.5, -0.2).rect(0.15, 0.6).extrude(text_depth)
a_right = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(-0.2, -0.2).rect(0.15, 0.6).extrude(text_depth)
a_top = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(-0.35, 0.32).rect(0.3, 0.15).extrude(text_depth)
a_middle = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(-0.35, 0.05).rect(0.3, 0.1).extrude(text_depth)

# Letter "G"
g_vertical = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(0.2, 0).rect(0.15, 0.8).extrude(text_depth)
g_top = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(0.42, 0.32).rect(0.45, 0.15).extrude(text_depth)
g_bottom = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(0.42, -0.32).rect(0.45, 0.15).extrude(text_depth)
g_middle = cq.Workplane("XY").workplane(offset=tag_thickness).moveTo(0.5, -0.05).rect(0.3, 0.1).extrude(text_depth)

# Combine all elements
result = (tag_with_hole
         .union(t_vertical).union(t_horizontal)
         .union(a_left).union(a_right).union(a_top).union(a_middle)
         .union(g_vertical).union(g_top).union(g_bottom).union(g_middle))

show_object(result)