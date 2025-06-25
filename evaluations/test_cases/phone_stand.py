"""Phone stand - angled support with 60-degree viewing angle and cable management."""

import cadquery as cq
import math

# Stand specifications
base_length = 8
base_width = 6
base_thickness = 1
back_height = 6
angle_degrees = 60
slot_width = 1
slot_depth = 0.8
cable_hole_diameter = 1.2

# Convert angle to radians
angle_rad = math.radians(angle_degrees)

# Create base
base = cq.Workplane("XY").rect(base_length, base_width).extrude(base_thickness)

# Calculate back support dimensions and position
back_length = back_height / math.sin(angle_rad)
back_x_offset = back_length * math.cos(angle_rad) / 2

# Create angled back support
back_support = (
    cq.Workplane("XY")
    .moveTo(base_length/2 - back_x_offset, 0)
    .rect(back_length, base_width - 1)
    .extrude(0.8)
    .rotate((0, 0, 0), (0, 1, 0), angle_degrees)
    .translate((0, 0, base_thickness))
)

# Create phone slot in the back support
phone_slot = (
    cq.Workplane("XY")
    .moveTo(base_length/2 - 1.5, 0)
    .rect(slot_width, base_width + 1)
    .extrude(3)
    .rotate((0, 0, 0), (0, 1, 0), angle_degrees)
    .translate((0, 0, base_thickness + 1))
)

# Create cable management hole in base
cable_hole = (
    cq.Workplane("XY")
    .moveTo(-base_length/2 + 1.5, 0)
    .circle(cable_hole_diameter / 2)
    .extrude(base_thickness + 0.1)
)

# Combine all parts
result = base.union(back_support).cut(phone_slot).cut(cable_hole)

show_object(result)