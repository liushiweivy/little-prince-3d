# -*- coding: utf-8 -*-
"""渲染与 prep_tpose.py 同一归一化下的 front/right 正交图，供 PIL 叠加米制网格读数。

用法：blender --background --python blender/render_grid.py -- <in.glb> <view_dir>
相机：700x900、ortho_scale=2.05、目标 z=0.9，ppm=900/2.05。
front: u=350+x*ppm, v=450-(z-0.9)*ppm；right: u=350+y*ppm, v 同。
"""
import math
import os
import sys
from mathutils import Vector
import bpy
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
VIEW_DIR = os.path.abspath(sys.argv[sys.argv.index("--") + 2])
os.makedirs(VIEW_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
mx = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
obj.scale = (1.8 / (mx.z - mn.z),) * 3
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
verts = np.fromiter((c for v in obj.data.vertices for c in v.co),
                    dtype=float, count=len(obj.data.vertices) * 3).reshape(-1, 3)
legs = verts[(verts[:, 2] > mn.z + 0.03) & (verts[:, 2] < mn.z + 0.28)]
core = verts[(verts[:, 2] > mn.z + 0.70) & (verts[:, 2] < mn.z + 1.25)]
cx = float(np.median(legs[:, 0]))
cy = float(np.median(core[np.abs(core[:, 0] - cx) < 0.12, 1]))
obj.location = (-cx, -cy, -mn.z)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.8, 0.82, 0.88)
scene.render.resolution_x = 700
scene.render.resolution_y = 900
cam_data = bpy.data.cameras.new("ortho_cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.05
cam = bpy.data.objects.new("ortho_cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for name, az in (("grid_front", 0), ("grid_right", 90)):
    a = math.radians(az)
    cam.location = Vector((math.sin(a) * 3.0, -math.cos(a) * 3.0, 0.9))
    cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(VIEW_DIR, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print(f"[grid] 已渲染到 {VIEW_DIR}/grid_front.png, grid_right.png")
