from pathlib import Path
import subprocess
import tempfile
import textwrap
import logging


from pydantic import BaseModel


class PNGPaths(BaseModel):
    front: Path
    right: Path
    top: Path
    iso: Path
    back_left: Path
    bottom_right: Path


class VerificationResult(BaseModel):
    status: str
    reasoning: str
    criteria: str



logger = logging.getLogger(__name__)


def generate_png_views_blender(
    stl_path: Path,
    output_dir: Path,
    base_name: str,
    blender_executable: str = "blender",
    image_size: int = 1024,
) -> PNGPaths:
    """Render multiple high‑quality PNG views of an STL using headless Blender.

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

        # Import STL (try newer operator first, fallback to older one)
        try:
            # Blender 4.x uses this operator
            bpy.ops.wm.stl_import(filepath=stl_path)
        except AttributeError:
            try:
                # Blender 3.x and older used this
                bpy.ops.import_mesh.stl(filepath=stl_path)
            except AttributeError:
                print("ERROR: Could not find STL import operator")
                raise
        
        # Get the imported object (should be the last one added)
        if not scene.objects:
            print("ERROR: No objects found after STL import")
            raise RuntimeError("STL import failed - no objects created")
        
        obj = scene.objects[-1]
        print(f"Successfully imported STL: {{obj.name}}")

        # Create dark purple material for the object
        material = bpy.data.materials.new(name="DarkPurpleMaterial")
        material.use_nodes = True
        
        # Clear existing nodes
        for node in material.node_tree.nodes:
            material.node_tree.nodes.remove(node)
        
        # Set up material nodes
        bsdf = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        output = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # Set dark purple color (RGB)
        bsdf.inputs['Base Color'].default_value = (0.3, 0.1, 0.6, 1.0)  # Dark purple
        bsdf.inputs['Metallic'].default_value = 0.0
        bsdf.inputs['Roughness'].default_value = 0.4
        
        # Assign material to object
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)

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

        # Set up white background
        world = scene.world
        if world is None:
            world = bpy.data.worlds.new("World")
            scene.world = world
        
        world.use_nodes = True
        
        # Clear existing world nodes
        for node in world.node_tree.nodes:
            world.node_tree.nodes.remove(node)
        
        # Create background shader with white color
        bg_node = world.node_tree.nodes.new(type='ShaderNodeBackground')
        output_node = world.node_tree.nodes.new(type='ShaderNodeOutputWorld')
        world.node_tree.links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])
        
        # Set white background color
        bg_node.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)  # Pure white
        bg_node.inputs['Strength'].default_value = 1.0

        # Configure render settings
        scene.render.engine = 'CYCLES'  # Use Cycles for better material rendering
        scene.cycles.samples = 32  # Lower samples for faster rendering
        
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
        scene.render.film_transparent = False  # Use white background instead of transparency

        for name, (theta, phi, radius) in views.items():
            print(f"Rendering view: {{name}}")
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

            output_path = os.path.join(out_dir, f"{{base_name}}_{{name}}.png")
            scene.render.filepath = output_path
            bpy.ops.render.render(write_still=True)
            print(f"Saved: {{output_path}}")
            
        print("All views rendered successfully!")
        """
    )

    # Write temp script and run Blender headless
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tf:
        tf.write(blender_script)
        temp_script_path = tf.name
    
    print(f"DEBUG: Blender script saved to: {temp_script_path}")
    print(f"DEBUG: Running Blender with STL: {stl_path}")
    print(f"DEBUG: Output directory: {output_dir}")
    
    try:
        result = subprocess.run([
            blender_executable,
            "-b",              # headless / background mode
            "-P", temp_script_path      # run this Python script inside Blender
        ], check=True, capture_output=True, text=True)
        
        print("DEBUG: Blender stdout:")
        print(result.stdout)
        if result.stderr:
            print("DEBUG: Blender stderr:")
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"DEBUG: Blender failed with return code {e.returncode}")
        print("DEBUG: Blender stdout:")
        print(e.stdout)
        print("DEBUG: Blender stderr:")
        print(e.stderr)
        print(f"DEBUG: You can manually inspect the script at: {temp_script_path}")
        raise
    
    # Check if files were actually created
    expected_files = [
        output_dir / f"{base_name}_front.png",
        output_dir / f"{base_name}_right.png", 
        output_dir / f"{base_name}_top.png",
        output_dir / f"{base_name}_iso.png",
        output_dir / f"{base_name}_back_left.png",
        output_dir / f"{base_name}_bottom_right.png",
    ]
    
    print("DEBUG: Checking for generated files:")
    for file_path in expected_files:
        exists = file_path.exists()
        logger.info(f"  {file_path}: {'EXISTS' if exists else 'MISSING'}")
        
    # Clean up temp script only if everything worked
    try:
        Path(temp_script_path).unlink()
    except:
        pass

    return PNGPaths(
        front=output_dir / f"{base_name}_front.png",
        right=output_dir / f"{base_name}_right.png",
        top=output_dir / f"{base_name}_top.png",
        iso=output_dir / f"{base_name}_iso.png",
        back_left=output_dir / f"{base_name}_back_left.png",
        bottom_right=output_dir / f"{base_name}_bottom_right.png",
    )


if __name__ == "__main__":
    generate_png_views_blender(
        stl_path=Path("/Users/rishigundakaram/Desktop/doodles/3d-print/cad-query-workspace/outputs/coffee_mug/coffee_mug.stl"),
        output_dir=Path("/Users/rishigundakaram/Desktop/doodles/3d-print/cad-query-workspace/outputs/coffee_mug/"),
        base_name="coffee_mug",
    )