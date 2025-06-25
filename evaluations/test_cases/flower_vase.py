"""Flower vase - tapered with decorative ridges."""

import cadquery as cq

# Vase specifications
base_diameter = 6
top_diameter = 4
height = 12
wall_thickness = 0.4
ridge_count = 8

# Create main vase body using loft
base_circle = cq.Workplane("XY").circle(base_diameter / 2)
top_circle = cq.Workplane("XY").workplane(offset=height).circle(top_diameter / 2)
vase_outer = base_circle.loft(top_circle)

# Create inner cavity
inner_base = cq.Workplane("XY").workplane(offset=wall_thickness).circle((base_diameter / 2) - wall_thickness)
inner_top = cq.Workplane("XY").workplane(offset=height).circle((top_diameter / 2) - wall_thickness)
vase_inner = inner_base.loft(inner_top)

# Make vase hollow
vase = vase_outer.cut(vase_inner)

# Add decorative ridges using array pattern
for i in range(ridge_count):
    ridge_height = (height / ridge_count) * i + 1
    # Calculate diameter at this height (linear interpolation)
    diameter_at_height = base_diameter - (base_diameter - top_diameter) * (ridge_height / height)
    
    # Create ridge as a thin torus
    ridge = (
        cq.Workplane("XY")
        .workplane(offset=ridge_height)
        .circle((diameter_at_height / 2) + 0.1)
        .circle((diameter_at_height / 2) - 0.1)
        .extrude(0.2)
    )
    
    vase = vase.union(ridge)

result = vase

show_object(result)