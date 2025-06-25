"""Threaded bottle - bottle with neck threading for cap attachment."""

import cadquery as cq
import math

# Bottle specifications
bottle_height = 15
base_diameter = 6
neck_diameter = 3
neck_height = 2
wall_thickness = 0.3
thread_pitch = 0.5
thread_depth = 0.2

# Create bottle body using loft
base_circle = cq.Workplane("XY").circle(base_diameter / 2)
shoulder_circle = cq.Workplane("XY").workplane(offset=bottle_height - neck_height - 2).circle(neck_diameter / 2 + 0.5)
neck_circle = cq.Workplane("XY").workplane(offset=bottle_height - neck_height).circle(neck_diameter / 2)
top_circle = cq.Workplane("XY").workplane(offset=bottle_height).circle(neck_diameter / 2)

bottle_outer = base_circle.loft(shoulder_circle).union(
    shoulder_circle.loft(neck_circle)
).union(
    neck_circle.loft(top_circle)
)

# Create inner cavity
inner_base = cq.Workplane("XY").workplane(offset=wall_thickness).circle((base_diameter / 2) - wall_thickness)
inner_shoulder = cq.Workplane("XY").workplane(offset=bottle_height - neck_height - 2).circle((neck_diameter / 2) - wall_thickness + 0.3)
inner_neck = cq.Workplane("XY").workplane(offset=bottle_height - neck_height).circle((neck_diameter / 2) - wall_thickness)
inner_top = cq.Workplane("XY").workplane(offset=bottle_height - wall_thickness).circle((neck_diameter / 2) - wall_thickness)

bottle_inner = inner_base.loft(inner_shoulder).union(
    inner_shoulder.loft(inner_neck)
).union(
    inner_neck.loft(inner_top)
)

# Make bottle hollow
bottle = bottle_outer.cut(bottle_inner)

# Create threads on the neck
thread_turns = int(neck_height / thread_pitch)
neck_radius = neck_diameter / 2

for i in range(thread_turns * 8):  # 8 segments per turn for smoothness
    angle = i * 45  # degrees
    height = bottle_height - neck_height + (i * thread_pitch / 8)
    
    if height > bottle_height:
        break
    
    # Create thread segment
    thread_x = (neck_radius + thread_depth) * math.cos(math.radians(angle))
    thread_y = (neck_radius + thread_depth) * math.sin(math.radians(angle))
    
    # Create small thread element
    thread_element = (
        cq.Workplane("XY")
        .workplane(offset=height)
        .moveTo(thread_x, thread_y)
        .circle(thread_depth / 2)
        .extrude(thread_pitch / 8)
    )
    
    bottle = bottle.union(thread_element)

# Create bottle opening
opening = (
    cq.Workplane("XY")
    .workplane(offset=bottle_height)
    .circle((neck_diameter / 2) - wall_thickness)
    .extrude(0.1)
)

bottle = bottle.cut(opening)

result = bottle

show_object(result)