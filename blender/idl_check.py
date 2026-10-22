# -*- coding: utf-8 -*-
"""临时：识别 E:/download 下 hash 命名 GLB 的真实内容，逐张渲染到 blender/views/idl_<hash6>.png。"""
import os
import sys
import bpy
import math
from mathutils import Vector

VIEWS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'views')
FILES = [
    'c1e467c4c907df601c6520eee0334140',
    'b5e7335e538ef3901b1cb10fd3905558',
    'e0730ac81100a2bafe40afa31c977053',
    'bf69da721c671247214392affae1e48e',
    'f23163733bf5c1ed820f3c92f74c9010',
    '109bf201d81ce7305b5f07352f42a11b',
]
DL = 'E:/download'
RES = 420


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


for h in FILES:
    path = os.path.join(DL, h + '.glb')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.engine = 'BLENDER_EEVEE'
    w = bpy.data.worlds.new('w')
    scene.world = w
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.05, 0.05, 0.07, 1)

    bpy.ops.import_scene.gltf(filepath=path)
    meshes = [o for o in scene.objects if o.type == 'MESH']
    mins = Vector((1e9, 1e9, 1e9)); maxs = -mins
    for o in meshes:
        for c in o.bound_box:
            p = o.matrix_world @ Vector(c)
            for i in range(3):
                mins[i] = min(mins[i], p[i]); maxs[i] = max(maxs[i], p[i])
    center = (mins + maxs) * 0.5
    radius = (maxs - mins).length * 0.5
    for o in meshes:
        o.location = (o.location - center) / radius

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
    az = math.radians(25.0); d = 3.1
    cam.location = (math.sin(az) * d, -math.cos(az) * d, 0.28 * d + 0.15)
    scene.collection.objects.link(cam)
    scene.camera = cam
    look_at(cam, (0, 0, 0))

    out = os.path.join(VIEWS, f'idl_{h[:6]}.png')
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print(f'[IDL] {out}')
