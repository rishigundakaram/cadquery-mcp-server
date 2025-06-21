import cadquery as cq

# Create the main mug body (cylinder with thick walls)
mug_body = (cq.Workplane("XY")
            .cylinder(height=10, radius=4)
            .faces(">Z")
            .shell(-0.3))

# Create handle attachment points first
attachment_top = (cq.Workplane("XY")
                  .center(4, 0)
                  .cylinder(height=1, radius=0.4)
                  .translate((0, 0, 7)))

attachment_bottom = (cq.Workplane("XY")
                     .center(4, 0)
                     .cylinder(height=1, radius=0.4)
                     .translate((0, 0, 2)))

# Create the curved handle body
handle_body = (cq.Workplane("XY")
               .center(5.5, 0)
               .box(1, 0.8, 5)
               .translate((0, 0, 4.5)))

# Create the full handle by combining attachment points and body
handle = attachment_top.union(attachment_bottom).union(handle_body)

# Combine everything
result = mug_body.union(handle)

show_object(result)