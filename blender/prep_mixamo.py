# -*- coding: utf-8 -*-
"""混元小王子 GLB -> Mixamo 上传用 FBX（立正、A-pose 检查、脚底 z=0、居中、1.8m）。

Blender 5.x headless:
  blender --background --python blender/prep_mixamo.py -- <in.glb> <out.fbx> <view_dir>

先产出 front/back/left/right 四向正交渲染图（view_dir），再导出 FBX。
"""
import bpy
import math
import os
import sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT_FBX, VIEW_DIR = (os.path.abspath(a) for a in argv[:3])
os.makedirs(VIEW_DIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT_FBX), exist_ok=True)

# ---- 干净场景 ----
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---- 导入 GLB ----
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
assert meshes, "GLB 里没有网格"

# 全部合并为一个对象（本模型只有 1 个网格，join 顺带烘焙节点旋转）
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
obj.name = "prince"

# 应用全部变换（导入的 Z-up->Y-up 节点旋转烘焙进网格，Blender 内 z 朝上）
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# ---- 归一化：脚底 z=0、XY 居中、真实高度 1.8m ----
bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
mx = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
h = mx.z - mn.z
scale = 1.8 / h
obj.scale = (scale, scale, scale)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
mx = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
cx, cy = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2
obj.location = (-cx, -cy, -mn.z)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
print(f"[prep] 归一化完成：身高 {mx.z - mn.z:.3f}m -> 1.8m，脚底 z=0")

# ---- 四向正交渲染（workbench，纯色看姿势）----
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.75, 0.78, 0.85)
scene.render.resolution_x = 700
scene.render.resolution_y = 900
scene.render.film_transparent = False

cam_data = bpy.data.cameras.new("ortho_cam")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("ortho_cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

views = {  # 名字 -> 相机方位角（度，绕 z 轴，0 = 从 -Y 看向 +Y，即 Blender 前视图）
    "front": 0,
    "right": 90,
    "back": 180,
    "left": 270,
}
dist = 3.0
target = Vector((0, 0, 0.9))  # 水平看向身体中上部，不俯视
for name, az in views.items():
    a = math.radians(az)
    cam.location = Vector((math.sin(a) * dist, -math.cos(a) * dist, 0.9))
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam_data.ortho_scale = 2.05  # 略高于 1.8m 身高
    scene.render.filepath = os.path.join(VIEW_DIR, f"{name}.png")
    bpy.ops.render.render(write_still=True)
print(f"[prep] 四向视图已写入 {VIEW_DIR}")

# ---- 导出 FBX（二进制，Mixamo 只收 FBX/OBJ/ZIP）----
bpy.ops.export_scene.fbx(
    filepath=OUT_FBX,
    use_selection=False,
    object_types={"MESH"},
    mesh_smooth_type="EDGE",
    apply_unit_scale=True,
    global_scale=1.0,
    axis_forward="-Z",
    axis_up="Y",
    path_mode="COPY",
)
print(f"[prep] FBX 已导出：{OUT_FBX}（{os.path.getsize(OUT_FBX)/1e6:.1f} MB）")
