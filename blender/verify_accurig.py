# -*- coding: utf-8 -*-
"""验证 AccuRIG 导出的 FBX：骨架/权重/姿势，渲染 front/side 叠图。"""
import math
import os
import sys
from mathutils import Vector
import bpy

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
VIEW_DIR = os.path.abspath(sys.argv[sys.argv.index("--") + 2])
os.makedirs(VIEW_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
rigs = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
print(f"[verify] mesh={len(meshes)} armature={len(rigs)}")
for r in rigs:
    bones = list(r.data.bones)
    print(f"[verify] 骨架 {r.name} 骨数 {len(bones)}")
    print("[verify] 骨名:", [b.name for b in bones][:40])
for m in meshes:
    vg = len(m.vertex_groups)
    entries = sum(len(v.groups) for v in m.data.vertices)
    mod = [x.type for x in m.modifiers]
    bb = [m.matrix_world @ Vector(c) for c in m.bound_box]
    zs = [c.z for c in bb]
    xs = [c.x for c in bb]
    print(f"[verify] mesh {m.name} 顶点 {len(m.data.vertices)} 顶点组 {vg} "
          f"权重条目 {entries} modifiers={mod} 高={max(zs)-min(zs):.3f} "
          f"宽={max(xs)-min(xs):.3f}")

# 渲染：骨架前置显示
if rigs:
    rig = rigs[0]
    rig.show_in_front = True
    rig.data.display_type = "OCTAHEDRAL"
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "OBJECT"
scene.render.resolution_x = 700
scene.render.resolution_y = 900
cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 2.2
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for name, az in (("rig_front", 0), ("rig_side", 90)):
    a = math.radians(az)
    cam.location = Vector((math.sin(a) * 3.0, -math.cos(a) * 3.0, 0.9))
    cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(VIEW_DIR, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print(f"[verify] 渲染完成 -> {VIEW_DIR}/rig_front.png rig_side.png")
