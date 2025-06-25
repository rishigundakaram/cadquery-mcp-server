"""Decorative bowl - organic shape with wave-pattern rim decoration."""

import cadquery as cq
import math

# Bowl specifications
base_diameter = 8
top_diameter = 12
bowl_height = 4
wall_thickness = 0.4
wave_amplitude = 0.5
wave_frequency = 8

# Create bowl using loft with multiple cross-sections
sections = []
heights = [0, bowl_height * 0.3, bowl_height * 0.7, bowl_height]
diameters = [base_diameter, base_diameter * 1.3, top_diameter * 0.8, top_diameter]

# Create outer bowl shape
for i, (height, diameter) in enumerate(zip(heights, diameters)):
    sections.append(
        cq.Workplane("XY").workplane(offset=height).circle(diameter / 2)
    )

bowl_outer = sections[0]
for i in range(1, len(sections)):
    bowl_outer = bowl_outer.loft(sections[i])

# Create inner cavity
inner_sections = []
for i, (height, diameter) in enumerate(zip(heights, diameters)):
    if i == 0:
        # Bottom has thickness
        inner_sections.append(
            cq.Workplane("XY").workplane(offset=height + wall_thickness).circle((diameter / 2) - wall_thickness)
        )
    else:
        inner_sections.append(
            cq.Workplane("XY").workplane(offset=height).circle((diameter / 2) - wall_thickness)
        )

bowl_inner = inner_sections[0]
for i in range(1, len(inner_sections)):
    bowl_inner = bowl_inner.loft(inner_sections[i])

# Create hollow bowl
bowl = bowl_outer.cut(bowl_inner)

# Add wave pattern to rim
wave_points = []
for i in range(wave_frequency * 4):  # 4 points per wave for smoothness
    angle = i * 2 * math.pi / (wave_frequency * 4)
    radius = (top_diameter / 2) + wave_amplitude * math.sin(wave_frequency * angle)
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    wave_points.append((x, y, bowl_height))

# Create wave rim using spline
wave_rim = (
    cq.Workplane("XY")
    .workplane(offset=bowl_height - 0.2)
    .spline(wave_points, includeCurrent=True)
    .close()
    .extrude(0.4)
)

# Add decorative ridges on the outside
for i in range(3):
    ridge_height = bowl_height * (0.3 + i * 0.2)
    ridge_diameter = base_diameter + (top_diameter - base_diameter) * (ridge_height / bowl_height)
    
    ridge = (
        cq.Workplane("XY")
        .workplane(offset=ridge_height)
        .circle((ridge_diameter / 2) + 0.1)
        .circle((ridge_diameter / 2) - 0.1)
        .extrude(0.1)
    )
    
    bowl = bowl.union(ridge)

# Combine bowl with wave rim
result = bowl.union(wave_rim)

show_object(result)