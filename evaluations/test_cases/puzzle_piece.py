"""Jigsaw puzzle piece - interlocking piece with knobs and blanks."""

import cadquery as cq
import math

# Puzzle piece specifications
base_size = 3
thickness = 0.5
knob_radius = 0.4
tolerance = 0.05  # For proper fit

# Create base square
base = cq.Workplane("XY").rect(base_size, base_size).extrude(thickness)

# Define knob/blank positions and types
# True = knob (protrusion), False = blank (indentation)
sides = {
    'top': True,     # Knob on top
    'right': False,  # Blank on right
    'bottom': True,  # Knob on bottom
    'left': False    # Blank on left
}

# Create knobs and blanks
for side, is_knob in sides.items():
    if side == 'top':
        center_x, center_y = 0, base_size/2
        direction = 1 if is_knob else -1
        knob_center = (center_x, center_y + direction * knob_radius)
    elif side == 'right':
        center_x, center_y = base_size/2, 0
        direction = 1 if is_knob else -1
        knob_center = (center_x + direction * knob_radius, center_y)
    elif side == 'bottom':
        center_x, center_y = 0, -base_size/2
        direction = 1 if is_knob else -1
        knob_center = (center_x, center_y - direction * knob_radius)
    else:  # left
        center_x, center_y = -base_size/2, 0
        direction = 1 if is_knob else -1
        knob_center = (center_x - direction * knob_radius, center_y)
    
    # Create knob/blank shape
    knob_shape = (
        cq.Workplane("XY")
        .moveTo(knob_center[0], knob_center[1])
        .circle(knob_radius + (tolerance if not is_knob else -tolerance))
        .extrude(thickness)
    )
    
    if is_knob:
        # Add knob (union)
        base = base.union(knob_shape)
    else:
        # Add blank (subtraction)
        base = base.cut(knob_shape)

# Add corner curves for more realistic puzzle piece shape
corner_radius = 0.2
corners = [
    (base_size/2 - corner_radius, base_size/2 - corner_radius),
    (-base_size/2 + corner_radius, base_size/2 - corner_radius),
    (-base_size/2 + corner_radius, -base_size/2 + corner_radius),
    (base_size/2 - corner_radius, -base_size/2 + corner_radius)
]

for corner_x, corner_y in corners:
    corner_cut = (
        cq.Workplane("XY")
        .moveTo(corner_x, corner_y)
        .rect(corner_radius * 2, corner_radius * 2)
        .extrude(thickness)
    )
    
    corner_round = (
        cq.Workplane("XY")
        .moveTo(corner_x, corner_y)
        .circle(corner_radius)
        .extrude(thickness)
    )
    
    base = base.cut(corner_cut).union(corner_round)

# Add small identification number "1" on the piece
number_elements = [
    # Vertical line for "1"
    cq.Workplane("XY").workplane(offset=thickness).moveTo(-0.3, 0).rect(0.1, 0.6).extrude(0.05),
    # Top diagonal for "1"  
    cq.Workplane("XY").workplane(offset=thickness).moveTo(-0.4, 0.2).rect(0.15, 0.08).extrude(0.05)
]

for element in number_elements:
    base = base.union(element)

result = base

show_object(result)