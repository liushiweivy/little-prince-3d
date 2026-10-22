# -*- coding: utf-8 -*-
"""诊断 AccuRIG FBX：打印四肢骨 rest 坐标、armature 对象缩放，并渲染 rest 骨架叠图。"""
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
rig = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
print(f"[diag] armature scale={tuple(rig.scale)} parent={rig.parent}")
for b in rig.data.bones:
    n = b.name.lower()
    if any(k in n for k in ("upperarm", "forearm", "hand", "clavicle", "shoulder",
                            "thigh", "calf", "foot", "hip", "spine02", "head")):
        print(f"[diag] {b.name:32s} head={tuple(round(c,2) for c in b.head_local)} "
              f"tail={tuple(round(c,2) for c in b.tail_local)} parent={b.parent.name if b.parent else '-'}")

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
cam_data.ortho_scale = 220.0
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
for name, az in (("diag_front", 0), ("diag_side", 90)):
    a = math.radians(az)
    cam.location = Vector((math.sin(a) * 300, -math.cos(a) * 300, 90))
    cam.rotation_euler = (Vector((0, 0, 90)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(VIEW_DIR, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("[diag] done")
