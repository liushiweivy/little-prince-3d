# -*- coding: utf-8 -*-
"""AccuRIG 绑好的 FBX -> 借它的专业权重烤出 T-pose 静态网格，供 Mixamo 重绑。

用法：
  blender --background --python blender/bake_accurig_tpose.py -- \
    assets/for-accurig/prince_accurig.fbx <out_no_ext> [t|a]
  t = 双臂抬平（Mixamo 用），a = 仅转正导出（默认）
"""
import os
import sys
from mathutils import Vector, Matrix
import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
SRC = os.path.abspath(argv[0])
OUT = os.path.abspath(argv[1])
MODE = argv[2] if len(argv) > 2 else "a"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
rig = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]

if MODE == "t":
    # 只转两根上臂骨：前臂/手/twist 全是它的子骨，会自动刚直跟随（diag_chain 验证）。
    # 切勿逐根 pinned rest-head 旋转——子骨头会脱离已移动的父骨被拽回原位，蒙皮撕碎。
    # FBX 自带 rest-pose Action（710 条单关键帧）会在评估时覆盖 pose，先摘掉。
    if rig.animation_data:
        rig.animation_data.action = None

    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    Y_AXIS = Vector((0, 1, 0))
    IDENTITY = Matrix.Identity(4)
    # AccuRIG FBX 约定：角色 L 在 +X、R 在 -X
    for bname, sign in (("CC_Base_L_Upperarm", 1.0), ("CC_Base_R_Upperarm", -1.0)):
        target = Vector((sign, 0, 0))
        pb = rig.pose.bones[bname]
        m_rest = pb.bone.matrix_local
        rest_y = (m_rest.to_3x3() @ Y_AXIS).normalized()
        qw = rest_y.rotation_difference(target)
        r0 = m_rest.to_3x3().to_4x4()
        desired = Matrix.Translation(m_rest.translation) @ qw.to_matrix().to_4x4() @ r0
        parent_term = (pb.parent.bone.matrix_local @ pb.parent.matrix.inverted()
                       if pb.parent else IDENTITY)
        pb.matrix_basis = m_rest.inverted() @ parent_term @ desired
        bpy.context.view_layer.update()
    for bn in ("CC_Base_L_Upperarm", "CC_Base_L_Forearm", "CC_Base_L_Hand",
               "CC_Base_R_Upperarm", "CC_Base_R_Forearm", "CC_Base_R_Hand"):
        pb = rig.pose.bones[bn]
        y = (pb.matrix.to_3x3() @ Y_AXIS).normalized()
        print(f"[bake] {bn:28s} head={tuple(round(c,1) for c in pb.head)} "
              f"y={tuple(round(c,2) for c in y)}")
    bpy.ops.object.mode_set(mode="OBJECT")

    # 烘焙进网格：应用 armature 修饰器，删骨架与顶点组
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for m in [x for x in obj.modifiers if x.type == "ARMATURE"]:
        bpy.ops.object.modifier_apply(modifier=m.name)
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    bpy.data.objects.remove(rig, do_unlink=True)

# FBX 导入时网格带 cm 级父级缩放，删骨架后还原为原始尺寸：统一归一到 1.8m、
# 脚底 z=0、腿/躯干中位 XY 居中（与 prep_tpose.py 同一套）。
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
from mathutils import Vector as V
import numpy as np
bbox = [obj.matrix_world @ V(c) for c in obj.bound_box]
mn = V((min(c.x for c in bbox), min(c.y for c in bbox), min(c.z for c in bbox)))
mx = V((max(c.x for c in bbox), max(c.y for c in bbox), max(c.z for c in bbox)))
obj.scale = (1.8 / (mx.z - mn.z),) * 3
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bbox = [obj.matrix_world @ V(c) for c in obj.bound_box]
mn = V((min(c.x for c in bbox), min(c.y for c in bbox), min(c.z for c in bbox)))
verts = np.fromiter((c for v in obj.data.vertices for c in v.co),
                    dtype=float, count=len(obj.data.vertices) * 3).reshape(-1, 3)
legs = verts[(verts[:, 2] > mn.z + 0.03) & (verts[:, 2] < mn.z + 0.28)]
core = verts[(verts[:, 2] > mn.z + 0.70) & (verts[:, 2] < mn.z + 1.25)]
cx = float(np.median(legs[:, 0]))
cy = float(np.median(core[np.abs(core[:, 0] - cx) < 0.12, 1]))
obj.location = (-cx, -cy, -mn.z)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
print(f"[bake] 归一化完成 1.80m 居中=({cx:.3f},{cy:.3f})")

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
fbx = OUT + ".fbx"
bpy.ops.export_scene.fbx(
    filepath=fbx, use_selection=True, object_types={"MESH"},
    mesh_smooth_type="EDGE", apply_unit_scale=True, global_scale=1.0,
    axis_forward="-Z", axis_up="Y", path_mode="COPY",
)
print(f"[bake] 导出 {fbx}（{os.path.getsize(fbx)/1e6:.1f} MB）")
