# -*- coding: utf-8 -*-
"""临时诊断：摆 T-pose 后直接渲染实时蒙皮（不烘焙），并检查顶点组与 twist 骨权重。"""
import math
import os
import sys
from mathutils import Vector, Matrix
import bpy

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
VIEW_DIR = os.path.abspath(sys.argv[sys.argv.index("--") + 2])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
rig = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]

print("[live] 顶点组：", sorted(g.name for g in obj.vertex_groups))

# 关键：FBX 导给 armature 对象挂了 0.01 缩放，先把缩放烘焙进骨架/网格数据
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
print(f"[live] apply 后 armature scale={tuple(round(s,4) for s in rig.scale)}")

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
Y_AXIS = Vector((0, 1, 0))
IDENTITY = Matrix.Identity(4)
for side, sign in (("L", 1.0), ("R", -1.0)):
    target = Vector((sign, 0, 0))
    for key in (f"CC_Base_{side}_Upperarm", f"CC_Base_{side}_Forearm",
                f"CC_Base_{side}_Hand"):
        pb = rig.pose.bones[key]
        m_rest = pb.bone.matrix_local
        rest_y = (m_rest.to_3x3() @ Y_AXIS).normalized()
        qw = rest_y.rotation_difference(target)
        r0 = m_rest.to_3x3().to_4x4()
        desired = Matrix.Translation(m_rest.translation) @ qw.to_matrix().to_4x4() @ r0
        parent_term = (pb.parent.bone.matrix_local @ pb.parent.matrix.inverted()
                       if pb.parent else IDENTITY)
        pb.matrix_basis = m_rest.inverted() @ parent_term @ desired
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode="OBJECT")

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
for name, az in (("live_front", 0), ("live_side", 90)):
    a = math.radians(az)
    cam.location = Vector((math.sin(a) * 3.0, -math.cos(a) * 3.0, 0.9))
    cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(VIEW_DIR, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("[live] done")
