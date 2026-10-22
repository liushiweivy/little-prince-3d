# -*- coding: utf-8 -*-
"""比较两种摆姿法对蒙皮的实际驱动：matrix_basis vs 直接 quaternion（twist 骨也摆）。"""
import os, sys
from mathutils import Vector, Matrix
import bpy
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
METHOD = sys.argv[sys.argv.index("--") + 2]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
rig = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]

# 关掉 FBX 自带 rest-pose Action，避免单关键帧在评估时覆盖姿势
rig.animation_data.action = None

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")

PAIRS = []
for side, sign in (("L", 1.0), ("R", -1.0)):
    keys = [f"CC_Base_{side}_Upperarm", f"CC_Base_{side}_UpperarmTwist01",
            f"CC_Base_{side}_UpperarmTwist02", f"CC_Base_{side}_Forearm",
            f"CC_Base_{side}_ForearmTwist01", f"CC_Base_{side}_ForearmTwist02",
            f"CC_Base_{side}_Hand"]
    PAIRS.append((sign, keys))

Y_AXIS = Vector((0, 1, 0))
IDENTITY = Matrix.Identity(4)

def moved_count():
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    eo = obj.evaluated_get(deps)
    me = eo.to_mesh()
    A = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", A)
    # rest：用修饰前网格
    b0 = obj.data
    B = np.empty(len(b0.vertices) * 3); b0.vertices.foreach_get("co", B)
    diff = np.linalg.norm(A.reshape(-1, 3) - B.reshape(-1, 3), axis=1)
    eo.to_mesh_clear()
    return int((diff > 0.5).sum()), float(diff.max())

if METHOD == "basis":
    for sign, keys in PAIRS:
        target = Vector((sign, 0, 0))
        for key in keys:
            pb = rig.pose.bones[key]
            m_rest = pb.bone.matrix_local
            rest_y = (m_rest.to_3x3() @ Y_AXIS).normalized()
            qw = rest_y.rotation_difference(target)
            r0 = m_rest.to_3x3().to_4x4()
            desired = Matrix.Translation(m_rest.translation) @ qw.to_matrix().to_4x4() @ r0
            parent_term = (pb.parent.bone.matrix_local @ pb.parent.matrix.inverted()
                           if pb.parent else IDENTITY)
            pb.matrix_basis = m_rest.inverted() @ parent_term @ desired
elif METHOD == "quat":
    # 每根骨独立在世界系绕自己骨头转；用父级当前矩阵换算
    for sign, keys in PAIRS:
        target = Vector((sign, 0, 0))
        for key in keys:
            pb = rig.pose.bones[key]
            m_rest = pb.bone.matrix_local
            rest_y = (m_rest.to_3x3() @ Y_AXIS).normalized()
            qw = rest_y.rotation_difference(target)
            # 世界系旋转 -> bone local 旋转四元数
            if pb.parent:
                p_rot = pb.parent.matrix.to_3x3()
                pr_rot = pb.parent.bone.matrix_local.to_3x3()
                local_q = (p_rot.inverted() @ qw.to_matrix() @ pr_rot).to_quaternion()
            else:
                local_q = qw
            pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = local_q

n, mx = moved_count()
print(f"[m={METHOD}] 移动顶点(>0.5cm)={n} 最大位移={mx:.2f}cm")
for sign, keys in PAIRS:
    for key in keys[:1] + keys[3:5] + keys[6:]:
        pb = rig.pose.bones[key]
        y = (pb.matrix.to_3x3() @ Y_AXIS).normalized()
        print(f"  {key:32s} y={tuple(round(c,2) for c in y)}")
