import cadquery as cq

# Create three spheres for the snowman body
bottom_ball = cq.Workplane("XY").sphere(5)
middle_ball = cq.Workplane("XY").workplane(offset=8).sphere(3.5)
top_ball = cq.Workplane("XY").workplane(offset=14).sphere(2.5)

# Combine all three balls
result = bottom_ball.union(middle_ball).union(top_ball)

show_object(result)  # noqa: F821
