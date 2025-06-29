from pathlib import Path
from typing import NamedTuple
import subprocess
import tempfile
import textwrap

class PNGPaths(NamedTuple):
    front: Path
    right: Path
    top: Path
    iso: Path
    back_left: Path
    bottom_right: Path


def generate_png_views_blender(
    stl_path: Path,
    output_dir: Path,
    base_name: str,
    blender_executable: str = "blender",
    image_size: int = 1024,
) -> PNGPaths:
    """Render multiple high‑quality PNG views of an STL using headless Blender.

    Args:
        stl_path: The STL file to render.
        output_dir: Folder in which to save PNG files (will be created).
        base_name: Prefix for each PNG (e.g. "widget" → widget_front.png …).
        blender_executable: Path to the Blender binary (defaults to whatever is
            on $PATH).  On macOS Homebrew installs it at /Applications/Blender.app/Contents/MacOS/Blender.
        image_size: Square resolution (NxN) for the output images.

    Returns:
        PNGPaths with absolute paths to the rendered images.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Mini‑script executed *inside* Blender
    blender_script = textwrap.dedent(
        f"""
        import bpy, math, os
        from mathutils import Vector

        stl_path = r"{stl_path}"
        out_dir = r"{output_dir}"
        base_name = "{base_name}"
        img_res = {image_size}

        # Fresh, empty scene (removes default cube/light/camera)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene

        # Import STL
        bpy.ops.import_mesh.stl(filepath=stl_path)
        obj = scene.objects[-1]

        # Normalise: fit longest dimension to 1.0 and centre at origin
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        scale_factor = 1.0 / max(obj.dimensions)
        obj.scale = (scale_factor,) * 3
        obj.location = (0, 0, 0)

        # Create camera once; we will move/rotate it per‑view
        cam_data = bpy.data.cameras.new(name="RenderCam")
        cam = bpy.data.objects.new("RenderCam", cam_data)
        scene.collection.objects.link(cam)
        scene.camera = cam

        # Simple three‑point lighting (key, fill, back)
        def add_light(name, location, energy=1000):
            light_data = bpy.data.lights.new(name=name, type='AREA')
            light_data.energy = energy
            light = bpy.data.objects.new(name, light_data)
            light.location = location
            scene.collection.objects.link(light)

        add_light("key", (3, 3, 4))
        add_light("fill", (-3, -1, 2), energy=600)
        add_light("back", (-2, 4, 4), energy=400)

        # Views defined in (theta°, phi°, radius)
        views = {{
            "front": (0, 20, 3.0),
            "right": (90, 20, 3.0),
            "top": (0, 85, 3.0),
            "iso": (45, 35, 3.5),
            "back_left": (135, 25, 3.2),
            "bottom_right": (315, -45, 3.0),
        }}

        scene.render.resolution_x = img_res
        scene.render.resolution_y = img_res
        scene.render.image_settings.file_format = 'PNG'
        scene.render.film_transparent = True  # nice to have

        for name, (theta, phi, radius) in views.items():
            # Spherical → Cartesian
            theta_r = math.radians(theta)
            phi_r = math.radians(90 - phi)
            x = radius * math.sin(phi_r) * math.cos(theta_r)
            y = radius * math.sin(phi_r) * math.sin(theta_r)
            z = radius * math.cos(phi_r)
            cam.location = (x, y, z)
            # Aim camera at origin
            direction = Vector((0, 0, 0)) - cam.location
            cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

            scene.render.filepath = os.path.join(out_dir, f"{base_name}_{name}.png")
            bpy.ops.render.render(write_still=True)
        """
    )

    # Write temp script and run Blender headless
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tf:
        tf.write(blender_script)
    subprocess.run([
        blender_executable,
        "-b",              # headless / background mode
        "-P", tf.name      # run this Python script inside Blender
    ], check=True)

    return PNGPaths(
        front=output_dir / f"{base_name}_front.png",
        right=output_dir / f"{base_name}_right.png",
        top=output_dir / f"{base_name}_top.png",
        iso=output_dir / f"{base_name}_iso.png",
        back_left=output_dir / f"{base_name}_back_left.png",
        bottom_right=output_dir / f"{base_name}_bottom_right.png",
    )
