"""Blender-side entry point for deterministic eight-direction sprite rendering."""

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


DIRECTIONS = (
    ("s", 0.0),
    ("sw", 45.0),
    ("w", 90.0),
    ("nw", 135.0),
    ("n", 180.0),
    ("ne", 225.0),
    ("e", 270.0),
    ("se", 315.0),
)


def parse_args():
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--resolution", type=int, default=512)
    return parser.parse_args(arguments)


def import_model(model_path: Path):
    extension = model_path.suffix.lower()
    if extension == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(model_path))
    else:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        if extension in (".glb", ".gltf"):
            bpy.ops.import_scene.gltf(filepath=str(model_path))
        elif extension == ".fbx":
            bpy.ops.import_scene.fbx(filepath=str(model_path))
        elif extension == ".obj":
            bpy.ops.wm.obj_import(filepath=str(model_path))
        elif extension == ".stl":
            bpy.ops.wm.stl_import(filepath=str(model_path))
        elif extension == ".ply":
            bpy.ops.wm.ply_import(filepath=str(model_path))
        elif extension in (".usd", ".usda", ".usdc"):
            bpy.ops.wm.usd_import(filepath=str(model_path))
        else:
            raise ValueError(f"Unsupported model extension: {extension}")

    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not mesh_objects:
        raise RuntimeError("The imported file contains no mesh objects.")
    return mesh_objects


def world_bounds(mesh_objects):
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in mesh_objects
        for corner in obj.bound_box
    ]
    minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
    maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
    return minimum, maximum


def center_model(mesh_objects):
    minimum, maximum = world_bounds(mesh_objects)
    center = Vector(((minimum.x + maximum.x) / 2, (minimum.y + maximum.y) / 2, minimum.z))
    roots = [obj for obj in bpy.context.scene.objects if obj.parent is None]
    pivot = bpy.data.objects.new("EightWayPivot", None)
    bpy.context.scene.collection.objects.link(pivot)
    for obj in roots:
        original_world = obj.matrix_world.copy()
        obj.parent = pivot
        obj.matrix_world = original_world
    pivot.matrix_world = Matrix.Translation(-center)
    bpy.context.view_layer.update()

    centered_minimum, centered_maximum = world_bounds(mesh_objects)
    dimensions = centered_maximum - centered_minimum
    return pivot, dimensions


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_area_light(name, location, energy, size, target):
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(light)
    light.location = location
    point_at(light, target)


def configure_scene(dimensions, resolution):
    scene = bpy.context.scene
    scene.frame_set(scene.frame_start)
    for obj in scene.objects:
        if obj.type in {"LIGHT", "CAMERA"}:
            obj.hide_render = True

    horizontal_diameter = math.hypot(dimensions.x, dimensions.y)
    height = max(dimensions.z, 0.001)
    subject_size = max(horizontal_diameter, height, 0.1)
    elevation = math.radians(35.0)
    target = Vector((0.0, 0.0, height * 0.46))
    distance = subject_size * 4.0

    camera_data = bpy.data.cameras.new("EightWayCamera")
    camera_data.type = "ORTHO"
    projected_height = height * math.cos(elevation) + horizontal_diameter * math.sin(elevation)
    camera_data.ortho_scale = max(horizontal_diameter, projected_height) * 1.25
    camera = bpy.data.objects.new("EightWayCamera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = (0.0, -distance * math.cos(elevation), target.z + distance * math.sin(elevation))
    point_at(camera, target)
    camera.hide_render = False
    scene.camera = camera

    add_area_light(
        "EightWayKey",
        Vector((-distance * 0.65, -distance * 0.7, distance * 0.9)),
        1100.0,
        subject_size * 2.0,
        target,
    )
    add_area_light(
        "EightWayFill",
        Vector((distance * 0.75, -distance * 0.15, distance * 0.35)),
        650.0,
        subject_size * 2.5,
        target,
    )

    world = scene.world or bpy.data.worlds.new("EightWayWorld")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.055, 0.065, 0.085, 1.0)
    background.inputs["Strength"].default_value = 0.8

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 15
    scene.view_settings.look = "AgX - Medium High Contrast"
    return scene


def main():
    args = parse_args()
    model_path = Path(args.model).resolve()
    output_directory = Path(args.output).resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    mesh_objects = import_model(model_path)
    pivot, dimensions = center_model(mesh_objects)
    scene = configure_scene(dimensions, args.resolution)

    for index, (name, angle) in enumerate(DIRECTIONS):
        pivot.rotation_euler[2] = math.radians(angle)
        bpy.context.view_layer.update()
        scene.render.filepath = str(output_directory / f"{index:02d}_{name}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
