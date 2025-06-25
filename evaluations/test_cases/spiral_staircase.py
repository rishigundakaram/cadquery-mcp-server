"""Spiral staircase - helical staircase with 8 steps using sweep operations."""

import cadquery as cq
import math

# Staircase specifications
num_steps = 8
total_height = 6
radius = 4
step_width = 1
step_thickness = 0.3
center_post_radius = 0.5

# Calculate step parameters
height_per_step = total_height / num_steps
angle_per_step = 2 * math.pi / num_steps

# Create center post
center_post = cq.Workplane("XY").circle(center_post_radius).extrude(total_height)

# Create helical path for the staircase
def create_helical_path():
    points = []
    for i in range(num_steps + 1):
        angle = i * angle_per_step
        height = i * height_per_step
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        points.append((x, y, height))
    return points

# Create individual steps
staircase = center_post

for i in range(num_steps):
    angle = i * angle_per_step
    height = i * height_per_step
    
    # Create step shape
    step = (
        cq.Workplane("XY")
        .workplane(offset=height)
        .moveTo(center_post_radius, 0)
        .lineTo(radius, 0)
        .lineTo(radius, step_width)
        .lineTo(center_post_radius, step_width)
        .close()
        .extrude(step_thickness)
        .rotate((0, 0, 0), (0, 0, 1), math.degrees(angle))
    )
    
    staircase = staircase.union(step)

# Create handrail using helical sweep
handrail_points = []
for i in range(num_steps * 4):  # More points for smoother curve
    angle = i * angle_per_step / 4
    height = i * height_per_step / 4
    x = (radius + 0.5) * math.cos(angle)
    y = (radius + 0.5) * math.sin(angle)
    handrail_points.append((x, y, height + step_thickness))

# Create handrail path
handrail_path = cq.Workplane("XY").spline(handrail_points)

# Create handrail cross-section
handrail_section = cq.Workplane("YZ").circle(0.1)

# Sweep to create handrail
handrail = handrail_section.sweep(handrail_path)

# Combine all parts
result = staircase.union(handrail)

show_object(result)