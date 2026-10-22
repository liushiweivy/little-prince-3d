# -*- coding: utf-8 -*-
"""临时质检：同一模型原档 vs lite 并排透视渲染，输出一张对比 PNG。

用法：
  blender --background --python blender/render_check.py -- hunyuan-king hunyuan-throne
输出：blender/views/lite_check_<name>.png（左原档 / 右 lite），完成后可删。
"""
import os
import sys
import bpy
import math
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = os.path.join(ROOT, 'blender', 'views')
RES = 560


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def render_view(glb_path, az_deg=28.0, elev=0.28):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.film_transparent = False
    world = bpy.data.worlds.new('w')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (0.05, 0.05, 0.07, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = 1.0

    bpy.ops.import_scene.gltf(filepath=glb_path)
    meshes = [o for o in scene.objects if o.type == 'MESH']
    # 居中并归一到包围球半径 1
    mins = Vector((1e9, 1e9, 1e9)); maxs = -mins
    for o in meshes:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            mins.x = min(mins.x, p.x); mins.y = min(mins.y, p.y); mins.z = min(mins.z, p.z)
            maxs.x = max(maxs.x, p.x); maxs.y = max(maxs.y, p.y); maxs.z = max(maxs.z, p.z)
    center = (mins + maxs) * 0.5
    radius = (maxs - mins).length * 0.5
    for o in meshes:
        o.location = (o.location - center) / radius

    # 灯光：key + fill
    key_data = bpy.data.lights.new('key', 'SUN'); key_data.energy = 3.0
    key = bpy.data.objects.new('key', key_data)
    key.rotation_euler = (math.radians(55), math.radians(10), math.radians(-35))
    scene.collection.objects.link(key)
    fill_data = bpy.data.lights.new('fill', 'SUN'); fill_data.energy = 1.2
    fill = bpy.data.objects.new('fill', fill_data)
    fill.rotation_euler = (math.radians(40), math.radians(-20), math.radians(120))
    scene.collection.objects.link(fill)

    cam_data = bpy.data.cameras.new('cam')
    cam_data.angle = math.radians(38)
    cam = bpy.data.objects.new('cam', cam_data)
    d = 3.1
    az = math.radians(az_deg)
    cam.location = (math.sin(az) * d, -math.cos(az) * d, elev * d + 0.15)
    scene.collection.objects.link(cam)
    scene.camera = cam
    look_at(cam, (0, 0, 0))

    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = os.path.join(VIEWS, '_tmp_view.png')
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(scene.render.filepath)
    arr = np.array(img.pixels[:], dtype=np.float32).reshape(RES, RES, 4)
    arr = np.flipud(arr)
    arr_8 = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
    return arr_8


def main():
    os.makedirs(VIEWS, exist_ok=True)
    names = sys.argv[sys.argv.index('--') + 1:]
    for name in names:
        orig = os.path.join(ROOT, 'web/models', name + '.glb')
        lite = os.path.join(ROOT, 'web/models/lite', name + '.glb')
        az = 25.0
        a = render_view(orig, az)
        b = render_view(lite, az)
        sep = np.full((RES, 3, 3), 90, dtype=np.uint8)
        sep = np.concatenate([sep, np.full((RES, 3, 1), 255, dtype=np.uint8)], axis=2)
        combo = np.concatenate([a, sep, b], axis=1)
        out = os.path.join(VIEWS, f'lite_check_{name}.png')
        h, w = combo.shape[:2]
        img = bpy.data.images.new('out', w, h, alpha=True)
        rgba = np.flipud(combo).reshape(-1, 4).astype(np.float32) / 255.0
        img.pixels.foreach_set(rgba.reshape(-1))
        img.filepath_raw = out
        img.file_format = 'PNG'
        img.save()
        print(f'[CHECK] {out}')


if __name__ == '__main__':
    main()
