# -*- coding: utf-8 -*-
"""混元小王子 GLB -> T-pose（双臂抬平）FBX/OBJ，供 AccuRig 本地绑骨。

阶段 1（默认）：导入 -> 立正归一 1.8m -> 体素切片估关节 -> 建临时骨架，
  渲染 front/side 叠图并写出 joints.json，不做自动权重。
阶段 2（末尾加 bake）：自动权重 -> 双臂旋到水平 -> 渲染 T-pose 图 ->
  armature_apply 烘焙进网格 -> 删骨架 -> 导出 FBX + OBJ。

关节坐标可用 <view_dir>/joints_overrides.json 人工覆盖（与 joints.json 同结构，
只写要改的键，例如 {"sho_L": [0.16, 0.0, 1.32]}）。

用法：
  blender --background --python blender/prep_tpose.py -- <in.glb> <out_no_ext> <view_dir>
  blender --background --python blender/prep_tpose.py -- <in.glb> <out_no_ext> <view_dir> bake
"""
import json
import math
import os
import sys
from mathutils import Vector

import bpy

BAKE = "bake" in sys.argv
REST = "rest" in sys.argv
argv = sys.argv[sys.argv.index("--") + 1:]
SRC = os.path.abspath(argv[0])
OUT_NOEXT = os.path.abspath(argv[1])
VIEW_DIR = os.path.abspath(argv[2])
os.makedirs(VIEW_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT_NOEXT), exist_ok=True)
OVERRIDE_PATH = os.path.join(VIEW_DIR, "joints_overrides.json")


# ---------- 场景清理 / 导入 / 归一化（与 prep_mixamo.py 一致） ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes, "GLB 里没有网格"
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = "prince"
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
mx = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
obj.scale = (1.8 / (mx.z - mn.z),) * 3
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
# XY 居中按腿部/躯干中位，避免飘带把中心拉偏
import numpy as np

verts = np.fromiter((c for v in obj.data.vertices for c in v.co), dtype=float,
                    count=len(obj.data.vertices) * 3).reshape(-1, 3)
legs = verts[(verts[:, 2] > mn.z + 0.03) & (verts[:, 2] < mn.z + 0.28)]
core = verts[(verts[:, 2] > mn.z + 0.70) & (verts[:, 2] < mn.z + 1.25)]
cx = float(np.median(legs[:, 0]))
cy = float(np.median(core[np.abs(core[:, 0] - cx) < 0.12, 1]))
obj.location = (-cx, -cy, -mn.z)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
zmin, zmax = 0.0, 1.8
print(f"[tpose] 归一化完成 身高 1.80m 顶点 {len(obj.data.vertices)} 居中=({cx:.3f},{cy:.3f})")

# ---------- 关节默认值（按比例初值，精确坐标用 joints_overrides.json 覆盖） ----------
# 王子是宽袖长袍 Q 版：袖子正面轮廓与躯干贴合，x 聚类分不开，
# 统一从 render_grid.py 的米制网格图上读数，再渲染 marker 叠图迭代校正。
joints = {
    "hips": [0.0, 0.0, 0.88],
    "chest": [0.0, 0.0, 1.26],
    "neck": [0.0, 0.0, 1.38],
    "head": [0.0, 0.0, 1.55],
    "sho_L": [-0.12, 0.0, 1.30],
    "elb_L": [-0.15, 0.01, 0.98],
    "wri_L": [-0.14, 0.02, 0.66],
    "sho_R": [0.12, 0.0, 1.30],
    "elb_R": [0.15, 0.01, 0.98],
    "wri_R": [0.14, 0.02, 0.66],
    "kne_L": [-0.08, 0.0, 0.42],
    "ank_L": [-0.08, 0.0, 0.08],
    "kne_R": [0.08, 0.0, 0.42],
    "ank_R": [0.08, 0.0, 0.08],
}
if os.path.exists(OVERRIDE_PATH):
    with open(OVERRIDE_PATH, encoding="utf-8") as f:
        joints.update(json.load(f))
    print(f"[tpose] 已应用覆盖：{OVERRIDE_PATH}")
with open(os.path.join(VIEW_DIR, "joints.json"), "w", encoding="utf-8") as f:
    json.dump(joints, f, ensure_ascii=False, indent=2)
print("[tpose] 关节估计：", json.dumps(joints, ensure_ascii=False))


# ---------- 建临时骨架 ----------
def v(key):
    return Vector(joints[key])


rig_data = bpy.data.armatures.new("temprig")
rig = bpy.data.objects.new("temprig", rig_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="EDIT")


def bone(name, head, tail, parent=None):
    b = rig_data.edit_bones.new(name)
    b.head, b.tail, b.use_deform = Vector(head), Vector(tail), True
    if parent:
        b.parent = rig_data.edit_bones[parent]
    return b


hip = v("hips")
bone("hips", hip - Vector((0, 0, 0.02)), hip + Vector((0, 0, 0.14)))
bone("spine", hip + Vector((0, 0, 0.12)), v("chest"), "hips")
bone("chest", v("chest"), v("neck"), "spine")
bone("neck", v("neck"), v("head"), "chest")
bone("head", v("head"), v("head") + Vector((0, 0, 0.14)), "neck")
for side in ("L", "R"):
    s = -1 if side == "L" else 1
    sho, elb, wri = v(f"sho_{side}"), v(f"elb_{side}"), v(f"wri_{side}")
    # 手指不单独建骨（细指体素重网格会丢，heat 必失败）：前臂直接延到指节，
    # T-pose 阶段手整体跟臂刚直运动即可；脚同理并进小腿。
    knuckle = wri + (wri - elb).normalized() * 0.10
    bone(f"upper_arm.{side}", sho, elb, "chest")
    bone(f"forearm.{side}", elb, knuckle, f"upper_arm.{side}")
    ank, kne = v(f"ank_{side}"), v(f"kne_{side}")
    bone(f"thigh.{side}", hip + Vector((s * 0.03, 0, -0.01)), kne, "hips")
    bone(f"shin.{side}", kne, ank, f"thigh.{side}")

# envelope 半径：决定各骨"胶囊"影响范围。躯干骨要粗（宽袖贴着身体，
# 靠胶囊半径让躯干顶点归躯干而不是被胳膊带走），臂骨刚好罩住袖子。
RADII = {
    "hips": 0.17, "spine": 0.16, "chest": 0.18, "neck": 0.08, "head": 0.22,
    "clav_L": 0.07, "clav_R": 0.07,
    # 臂骨半径要罩住整个宽袖（袖口外摆到 ~0.20）；配合 envelope_distance=0.035
    # 的硬衰减，袖子整体跟胳膊走，躯干归躯干，避免半权重撕裂。
    "upper_arm.L": (0.10, 0.12), "upper_arm.R": (0.10, 0.12),
    "forearm.L": (0.13, 0.17), "forearm.R": (0.13, 0.17),
    "hand.L": 0.06, "hand.R": 0.06,
    "thigh.L": 0.13, "thigh.R": 0.13, "shin.L": 0.07, "shin.R": 0.07,
    "foot.L": 0.07, "foot.R": 0.07,
}
for eb in rig_data.edit_bones:
    r = RADII.get(eb.name)
    if r:
        rh, rt = r if isinstance(r, tuple) else (r, r)
        eb.head_radius, eb.tail_radius = rh, rt
        eb.envelope_distance = max(rh, rt) + 0.035  # 半径外衰减带很窄：近似硬分区
bpy.ops.object.mode_set(mode="OBJECT")
rig_data.display_type = "OCTAHEDRAL"
rig.show_in_front = True


# ---------- 叠图渲染 ----------
marker_objs = []
colors = {"L": (0.95, 0.15, 0.12, 1), "R": (0.12, 0.35, 0.95, 1),
          "S": (0.95, 0.8, 0.1, 1), "LEG": (0.2, 0.8, 0.25, 1)}
for key, jv in joints.items():
    tag = "L" if key.endswith("_L") else "R" if key.endswith("_R") else \
          "LEG" if "kne" in key or "ank" in key else "S"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=jv)
    m = bpy.context.object
    m.color = colors[tag]
    marker_objs.append(m)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "OBJECT"
scene.render.resolution_x = 700
scene.render.resolution_y = 900
cam_data = bpy.data.cameras.new("ortho_cam")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("ortho_cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam


def shoot(name, az):
    a = math.radians(az)
    cam.location = Vector((math.sin(a) * 3.0, -math.cos(a) * 3.0, 0.9))
    cam.rotation_euler = (Vector((0, 0, 0.9)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_data.ortho_scale = 2.05
    scene.render.filepath = os.path.join(VIEW_DIR, f"{name}.png")
    bpy.ops.render.render(write_still=True)


shoot("rest_front", 0)
shoot("rest_side", 90)
print(f"[tpose] rest 叠图已写入 {VIEW_DIR}（rest_front/rest_side）")

if REST:
    # AccuRIG 直接收立正/A-pose：只导归一化后的纯网格，不做 T-pose 变形
    bpy.ops.object.mode_set(mode="OBJECT")
    for m in marker_objs:
        bpy.data.objects.remove(m, do_unlink=True)
    bpy.data.objects.remove(rig, do_unlink=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    fbx_path = OUT_NOEXT + ".fbx"
    bpy.ops.export_scene.fbx(
        filepath=fbx_path, use_selection=True, object_types={"MESH"},
        mesh_smooth_type="EDGE", apply_unit_scale=True, global_scale=1.0,
        axis_forward="-Z", axis_up="Y", path_mode="COPY",
    )
    obj_path = OUT_NOEXT + ".obj"
    bpy.ops.wm.obj_export(filepath=obj_path, export_selected_objects=True,
                          forward_axis="NEGATIVE_Z", up_axis="Y")
    print(f"[tpose] rest 导出完成：{fbx_path}（{os.path.getsize(fbx_path)/1e6:.1f} MB）")
    print(f"[tpose] rest 导出完成：{obj_path}（{os.path.getsize(obj_path)/1e6:.1f} MB）")
    sys.exit(0)

if not BAKE:
    print("[tpose] 未加 bake/rest 参数：只做检测与叠图，确认 joints 后加 bake 重跑")
    sys.exit(0)


# ---------- 绑定权重：体素重网格笼子 + 热扩散 + Data Transfer ----------
# 王子网格袖子/上衣相交、非流形：直接 heat 全失败，envelope 又把袖子撕成两半。
# 正路：复制一份做 voxel remesh 成封闭流形笼子 -> 在笼子上 heat 绑定
# （袖子与上衣相交处在笼子里熔接，热扩散给出平滑过渡）-> 最近面插值把权重
# 传回原网格，原网格只加 armature 修饰器，几何细节不动。
def weight_count(target=obj):
    return sum(len(v.groups) for v in target.data.vertices)


bind_mode = None
cage_mesh = obj.data.copy()
cage = obj.copy()
cage.data = cage_mesh
cage.name = "cage"
bpy.context.scene.collection.objects.link(cage)
bpy.ops.object.select_all(action="DESELECT")
cage.select_set(True)
bpy.context.view_layer.objects.active = cage
rem = cage.modifiers.new("remesh", "REMESH")
rem.mode = "VOXEL"
rem.voxel_size = 0.012
rem.use_smooth_shade = False
bpy.ops.object.modifier_apply(modifier=rem.name)
print(f"[tpose] 笼子 voxel remesh 完成：{len(cage.data.vertices)} 顶点")

bpy.ops.object.select_all(action="DESELECT")
cage.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
if weight_count(cage) > 0:
    bind_mode = "cage-heat"
    # 笼子权重 -> 原网格（最近面插值）
    bpy.ops.object.select_all(action="DESELECT")
    cage.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.data_transfer(
        data_type="VGROUP_WEIGHTS", use_create=True,
        vert_mapping="POLYINTERP_NEAREST",
        layers_select_src="ALL", layers_select_dst="NAME",
    )
    arm = obj.modifiers.new("temprig", "ARMATURE")
    arm.object = rig
    cage.hide_render = True
    cage.hide_viewport = True

if bind_mode is None and weight_count() == 0:
    # 兜底：按顶点到骨段胶囊（半径取 RADII）的距离写平滑权重
    import numpy as np2
    bind_mode = "segment"
    for g in list(obj.vertex_groups):
        obj.vertex_groups.remove(g)
    seg = []
    for b in rig.data.bones:
        r = RADII.get(b.name, 0.08)
        r = r if isinstance(r, tuple) else (r, r)
        grp = obj.vertex_groups.new(name=b.name)
        seg.append((np2.array(b.head_local), np2.array(b.tail_local),
                    0.5 * (r[0] + r[1]), grp))
    P = np2.empty(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", P)
    P = P.reshape(-1, 3)
    for i in range(0, len(P), 4096):
        block = P[i:i + 4096]
        w_acc = {}
        for a, b, radius, grp in seg:
            d = b - a
            ln2 = d @ d or 1e-12
            t = np2.clip((block - a) @ d / ln2, 0, 1)[:, None]
            dist = np2.linalg.norm(block - (a + t * d), axis=1)
            sigma = max(radius * 0.9, 0.05)
            w = np2.exp(-(dist / sigma) ** 2)
            w[dist > radius * 2.4] = 0.0
            w_acc[grp] = w
        sums = sum(w_acc.values()) + 1e-9
        for grp, w in w_acc.items():
            wn = w / sums
            for j, val in enumerate(wn):
                if val > 0.02:
                    grp.add([i + j], float(val), "REPLACE")
    if not any(m.type == "ARMATURE" for m in obj.modifiers):
        arm = obj.modifiers.new("temprig", "ARMATURE")
        arm.object = rig
print(f"[tpose] 权重绑定完成（{bind_mode}）：组 {len(obj.vertex_groups)}，"
      f"权重条目 {weight_count()}")
assert weight_count() > 0, "所有权重方案都失败"

# ---------- 抬臂到 T-pose ----------
# 直接写 pose bone 的 armature 空间矩阵（setter 会自动换算 basis），
# 三块骨都取"rest y 轴 -> 水平外展"的最小旋转，保证整条胳膊刚直不绕父级累积。
from mathutils import Matrix, Quaternion

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
Y_AXIS = Vector((0, 1, 0))
IDENTITY = Matrix.Identity(4)
for side, sign in (("L", -1.0), ("R", 1.0)):
    target = Vector((sign, 0, 0))
    for bname in (f"upper_arm.{side}", f"forearm.{side}"):
        pb = rig.pose.bones[bname]
        m_rest = pb.bone.matrix_local
        rest_y = (m_rest.to_3x3() @ Y_AXIS).normalized()
        qw = rest_y.rotation_difference(target)
        # 绕骨头自身旋转：平移保持 rest，旋转部分左乘 qw（不能直接 qw @ m_rest，
        # 那会连骨头位置一起绕骨架原点转飞）
        r0 = m_rest.to_3x3().to_4x4()
        desired = Matrix.Translation(m_rest.translation) @ qw.to_matrix().to_4x4() @ r0
        if pb.parent:
            parent_term = pb.parent.bone.matrix_local @ pb.parent.matrix.inverted()
        else:
            parent_term = IDENTITY
        # pb.matrix = parent.matrix @ parent_rest^-1 @ bone_rest @ matrix_basis
        pb.matrix_basis = m_rest.inverted() @ parent_term @ desired
        bpy.context.view_layer.update()
        check = (pb.matrix.to_3x3() @ Y_AXIS).normalized()
        print(f"[tpose] {bname} -> head={tuple(round(c, 2) for c in pb.head)} "
              f"y={tuple(round(c, 2) for c in check)}")
bpy.context.view_layer.update()
for mk in marker_objs:
    mk.hide_render = True
shoot("tpose_front", 0)
shoot("tpose_side", 90)
print("[tpose] T-pose 叠图已写出（tpose_front/tpose_side）")

# ---------- 烘焙姿势进网格 ----------
bpy.ops.pose.select_all(action="SELECT")
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
for m in list(obj.modifiers):
    if m.type == "ARMATURE":
        bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
for m in marker_objs:
    bpy.data.objects.remove(m, do_unlink=True)
bpy.data.objects.remove(rig, do_unlink=True)
if bind_mode == "cage-heat":
    bpy.data.objects.remove(cage, do_unlink=True)

# ---------- 导出 FBX + OBJ ----------
fbx_path = OUT_NOEXT + ".fbx"
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=fbx_path, use_selection=True, object_types={"MESH"},
    mesh_smooth_type="EDGE", apply_unit_scale=True, global_scale=1.0,
    axis_forward="-Z", axis_up="Y", path_mode="COPY",
)
obj_path = OUT_NOEXT + ".obj"
bpy.ops.wm.obj_export(filepath=obj_path, export_selected_objects=True,
                      forward_axis="NEGATIVE_Z", up_axis="Y")
print(f"[tpose] 导出完成：{fbx_path}（{os.path.getsize(fbx_path)/1e6:.1f} MB）")
print(f"[tpose] 导出完成：{obj_path}（{os.path.getsize(obj_path)/1e6:.1f} MB）")
