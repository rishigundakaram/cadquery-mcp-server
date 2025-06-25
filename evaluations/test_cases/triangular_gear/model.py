import cadquery as cq
import math

# Parameters
num_teeth = 32
gear_radius = 0.5  # 1 unit diameter = 0.5 unit radius
tooth_depth = 0.05
thickness = 0.1
center_hole_radius = 0.05

# Calculate tooth parameters
tooth_angle = 2 * math.pi / num_teeth
base_radius = gear_radius - tooth_depth

# Create the base gear circle and extrude it
gear = cq.Workplane("XY").circle(base_radius).extrude(thickness)

# Create triangular teeth
for i in range(num_teeth):
    angle = i * tooth_angle
    
    # Calculate tooth tip position (outward from center)
    tooth_tip_x = gear_radius * math.cos(angle)
    tooth_tip_y = gear_radius * math.sin(angle)
    
    # Calculate tooth base corners
    half_tooth_angle = tooth_angle / 2
    left_angle = angle - half_tooth_angle
    right_angle = angle + half_tooth_angle
    
    left_base_x = base_radius * math.cos(left_angle)
    left_base_y = base_radius * math.sin(left_angle)
    right_base_x = base_radius * math.cos(right_angle)
    right_base_y = base_radius * math.sin(right_angle)
    
    # Create triangular tooth and extrude it
    tooth = (cq.Workplane("XY")
             .moveTo(left_base_x, left_base_y)
             .lineTo(tooth_tip_x, tooth_tip_y)
             .lineTo(right_base_x, right_base_y)
             .close()
             .extrude(thickness))
    
    # Add tooth to gear
    gear = gear.union(tooth)

# Add center hole
gear = gear.faces(">Z").circle(center_hole_radius).cutThruAll()

result = gear
show_object(result)