# -*- coding: utf-8 -*-
"""AccuRIG FBX -> 修正错位权重 -> T-pose 静态网格。

AccuRIG 把宽袖下方的袍子顶点错绑到 Hand（rest 手骨埋在袖/袍相交处），
抬臂时这些顶点被拉飞。修法：rest 空间里，臂链权重高但离臂骨段过远的顶点
（袍子/围巾），剥离臂组权重并归一化到剩余躯干组；不足时补 Waist/Hip。
只转两根上臂骨，前臂/手/twist 子骨刚性跟随。
"""
import os
import sys
from mathutils import Vector, Matrix
import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC = os.path.abspath(argv[0])
OUT = os.path.abspath(argv[1])
DIST_CM = float(argv[2]) if len(argv) > 2 else 15.0
os.makedirs(os.path.dirname(OUT), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
rig = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
if rig.animation_data:
    rig.animation_data.action = None

ARM_KEYS = ("clavicle", "upperarm", "forearm", "hand")
TORSO_FALLBACK = ["CC_Base_Waist", "CC_Base_Spine01", "CC_Base_Hip"]

# ---------- 权重清洗（rest, cm 空间） ----------
arm_groups = {g.index: g for g in obj.vertex_groups
              if any(k in g.name.lower() for k in ARM_KEYS)}
# 臂链骨段（cm）
segments = []
for g in arm_groups.values():
    b = rig.data.bones.get(g.name)
    if b:
        segments.append((np.array(b.head_local), np.array(b.tail_local)))

P = np.empty(len(obj.data.vertices) * 3)
obj.data.vertices.foreach_get("co", P)
P = P.reshape(-1, 3)

def min_seg_dist(pts):
    dmin = np.full(len(pts), 1e9)
    for a, b in segments:
        d = b - a
        ln2 = d @ d or 1e-9
        t = np.clip((pts - a) @ d / ln2, 0, 1)[:, None]
        dist = np.linalg.norm(pts - (a + t * d), axis=1)
        dmin = np.minimum(dmin, dist)
    return dmin

# 分批算距离
D = np.concatenate([min_seg_dist(P[i:i+8192]) for i in range(0, len(P), 8192)])

fixed = 0
for i, v in enumerate(obj.data.vertices):
    arm_w = sum(g.weight for g in v.groups if g.group in arm_groups)
    # 手骨最低约 z=54cm；再低的袍摆带任何臂权重都必是误绑
    bad = (arm_w > 0.30 and D[i] > DIST_CM) or (arm_w > 0.30 and P[i][2] < 56.0)
    if bad:
        keep = [(g.group, g.weight) for g in v.groups if g.group not in arm_groups]
        for grp in arm_groups.values():
            grp.remove([i])
        s = sum(w for _, w in keep)
        if s < 0.2:
            # 按高度选躯干兜底组
            z = P[i][2]
            fb = ("CC_Base_Spine01" if z > 85 else
                  "CC_Base_Waist" if z > 60 else "CC_Base_Hip")
            obj.vertex_groups[fb].add([i], 1.0, "REPLACE")
        else:
            for gi, w in keep:
                obj.vertex_groups[gi].add([i], w / s, "REPLACE")
        fixed += 1
print(f"[fix] 剥离错位臂权重顶点 {fixed}（阈值 {DIST_CM}cm）")

# ---------- 抬臂 ----------
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
Y = Vector((0, 1, 0)); I = Matrix.Identity(4)
for bname, sign in (("CC_Base_L_Upperarm", 1.0), ("CC_Base_R_Upperarm", -1.0)):
    pb = rig.pose.bones[bname]; mr = pb.bone.matrix_local
    qw = ((mr.to_3x3() @ Y).normalized()).rotation_difference(Vector((sign, 0, 0)))
    desired = Matrix.Translation(mr.translation) @ qw.to_matrix().to_4x4() @ mr.to_3x3().to_4x4()
    pt = pb.parent.bone.matrix_local @ pb.parent.matrix.inverted()
    pb.matrix_basis = mr.inverted() @ pt @ desired
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode="OBJECT")

# ---------- 烘焙 + 归一化 1.8m ----------
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for m in [x for x in obj.modifiers if x.type == "ARMATURE"]:
    bpy.ops.object.modifier_apply(modifier=m.name)
for g in list(obj.vertex_groups):
    obj.vertex_groups.remove(g)
bpy.data.objects.remove(rig, do_unlink=True)

bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
from mathutils import Vector as V
bbox = [obj.matrix_world @ V(c) for c in obj.bound_box]
mn = V((min(c.x for c in bbox), min(c.y for c in bbox), min(c.z for c in bbox)))
mx = V((max(c.x for c in bbox), max(c.y for c in bbox), max(c.z for c in bbox)))
obj.scale = (1.8 / (mx.z - mn.z),) * 3
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bbox = [obj.matrix_world @ V(c) for c in obj.bound_box]
mn = V((min(c.x for c in bbox), min(c.y for c in bbox), min(c.z for c in bbox)))
verts = np.fromiter((c for v in obj.data.vertices for c in v.co),
                    dtype=float, count=len(obj.data.vertices)*3).reshape(-1, 3)
legs = verts[(verts[:, 2] > mn.z+0.03) & (verts[:, 2] < mn.z+0.28)]
core = verts[(verts[:, 2] > mn.z+0.70) & (verts[:, 2] < mn.z+1.25)]
cx = float(np.median(legs[:, 0]))
cy = float(np.median(core[np.abs(core[:, 0]-cx) < 0.12, 1]))
obj.location = (-cx, -cy, -mn.z)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

fbx = OUT + ".fbx"
bpy.ops.export_scene.fbx(
    filepath=fbx, use_selection=True, object_types={"MESH"},
    mesh_smooth_type="EDGE", apply_unit_scale=True, global_scale=1.0,
    axis_forward="-Z", axis_up="Y", path_mode="COPY")
print(f"[fix] 导出 {fbx}（{os.path.getsize(fbx)/1e6:.1f} MB）")
