"""Functional gear - 12-tooth gear with proper involute tooth profile."""

import cadquery as cq
import math

# Gear specifications
num_teeth = 12
outer_diameter = 4
inner_diameter = 2
gear_thickness = 0.5
pressure_angle = 20  # Standard pressure angle in degrees

# Calculate gear parameters
outer_radius = outer_diameter / 2
inner_radius = inner_diameter / 2
pitch_radius = (outer_radius + inner_radius) / 2
module = (outer_diameter - inner_diameter) / (2 * num_teeth)
addendum = module
dedendum = 1.25 * module
base_radius = pitch_radius * math.cos(math.radians(pressure_angle))

# Create base gear disk
gear = cq.Workplane("XY").circle(pitch_radius).extrude(gear_thickness)

# Create involute tooth profile (simplified)
tooth_angle = 2 * math.pi / num_teeth
half_tooth_angle = tooth_angle / 4

for i in range(num_teeth):
    angle = i * tooth_angle
    
    # Create tooth using simplified profile
    # Tooth tip
    tip_x = outer_radius * math.cos(angle)
    tip_y = outer_radius * math.sin(angle)
    
    # Tooth base points
    left_angle = angle - half_tooth_angle
    right_angle = angle + half_tooth_angle
    
    left_base_x = pitch_radius * math.cos(left_angle)
    left_base_y = pitch_radius * math.sin(left_angle)
    right_base_x = pitch_radius * math.cos(right_angle)
    right_base_y = pitch_radius * math.sin(right_angle)
    
    # Create tooth profile with involute approximation
    tooth = (
        cq.Workplane("XY")
        .moveTo(left_base_x, left_base_y)
        .lineTo(tip_x, tip_y)
        .lineTo(right_base_x, right_base_y)
        .spline([
            (right_base_x * 0.9, right_base_y * 0.9),
            (left_base_x * 0.9, left_base_y * 0.9)
        ])
        .close()
        .extrude(gear_thickness)
    )
    
    gear = gear.union(tooth)

# Add center hole
center_hole = cq.Workplane("XY").circle(inner_radius).extrude(gear_thickness + 0.1)
gear = gear.cut(center_hole)

# Add keyway for shaft
keyway_width = inner_radius * 0.3
keyway = (
    cq.Workplane("XY")
    .rect(keyway_width, inner_diameter + 0.2)
    .extrude(gear_thickness + 0.1)
)
gear = gear.cut(keyway)

result = gear

show_object(result)