import cadquery as cq

# Chair dimensions
seat_width = 40  # 400mm
seat_depth = 40  # 400mm
seat_thickness = 3  # 30mm
leg_height = 45  # 450mm
leg_diameter = 4  # 40mm
backrest_height = 35  # 350mm
backrest_thickness = 2  # 20mm

# Create the seat
seat = cq.Workplane("XY").box(seat_width, seat_depth, seat_thickness)

# Create the legs (4 cylindrical legs)
leg_positions = [
    (seat_width/2 - leg_diameter/2, seat_depth/2 - leg_diameter/2),
    (-seat_width/2 + leg_diameter/2, seat_depth/2 - leg_diameter/2),
    (seat_width/2 - leg_diameter/2, -seat_depth/2 + leg_diameter/2),
    (-seat_width/2 + leg_diameter/2, -seat_depth/2 + leg_diameter/2)
]

# Start with the seat and add legs
result = seat

for x, y in leg_positions:
    leg = (cq.Workplane("XY")
           .center(x, y)
           .circle(leg_diameter/2)
           .extrude(-leg_height))
    result = result.union(leg)

# Create the backrest
backrest = (cq.Workplane("XY")
            .center(0, -seat_depth/2)
            .box(seat_width, backrest_thickness, backrest_height)
            .translate((0, 0, seat_thickness/2 + backrest_height/2)))

# Combine all parts
result = result.union(backrest)

show_object(result)