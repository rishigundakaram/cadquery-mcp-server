"""Multi-compartment organizer - rectangular base with circular compartments."""

import cadquery as cq

# Organizer specifications
base_length = 12
base_width = 8
base_height = 2
compartment_depths = 1.5

# Compartment specifications (diameter in cm)
compartment_diameters = [3, 2.5, 2]
compartment_positions = [
    (-3, 0),    # Large compartment (left)
    (1.5, 1.5), # Medium compartment (top right)
    (1.5, -1.5) # Small compartment (bottom right)
]

# Create base
base = cq.Workplane("XY").rect(base_length, base_width).extrude(base_height)

# Create compartments by cutting holes
result = base
for i, (diameter, (x, y)) in enumerate(zip(compartment_diameters, compartment_positions)):
    compartment = (
        cq.Workplane("XY")
        .workplane(offset=base_height - compartment_depths)
        .moveTo(x, y)
        .circle(diameter / 2)
        .extrude(compartment_depths + 0.1)  # Extra height to ensure clean cut
    )
    result = result.cut(compartment)

show_object(result)