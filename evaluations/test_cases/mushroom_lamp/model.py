import cadquery as cq

# Create mushroom cap using simple dome shape
mushroom_cap = (
    cq.Workplane("XY")
    .circle(6)
    .extrude(2)
    .faces(">Z")
    .shell(-0.5)
)

# Add curved top to cap
cap_top = (
    cq.Workplane("XY")
    .circle(6)
    .extrude(0.1)
    .translate((0, 0, 2))
)

# Create dome shape using loft
cap_dome = (
    cq.Workplane("XY").workplane(offset=2)
    .circle(6)
    .workplane(offset=1)
    .circle(4)
    .workplane(offset=1)
    .circle(2)
    .workplane(offset=1)
    .circle(0.5)
    .loft()
)

# Hollow out the dome
cap_dome_hollow = (
    cq.Workplane("XY").workplane(offset=2.5)
    .circle(5.5)
    .workplane(offset=1)
    .circle(3.5)
    .workplane(offset=1)
    .circle(1.5)
    .loft()
)

cap_dome = cap_dome.cut(cap_dome_hollow)

# Combine cap parts
mushroom_cap = mushroom_cap.union(cap_dome)

# Create mushroom stem - hollow cylinder
stem_outer = (
    cq.Workplane("XY")
    .circle(1.5)
    .extrude(8)
)

stem_inner = (
    cq.Workplane("XY")
    .circle(1)
    .extrude(8.5)
)

mushroom_stem = stem_outer.cut(stem_inner)

# Create cord hole at the bottom
cord_hole = (
    cq.Workplane("XY")
    .rect(1, 0.6)
    .extrude(1)
    .translate((1, 0, 0))
)

mushroom_stem = mushroom_stem.cut(cord_hole)

# Combine cap and stem
result = mushroom_cap.union(mushroom_stem)

show_object(result)