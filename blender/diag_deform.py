# -*- coding: utf-8 -*-
import os, sys
from mathutils import Vector, Matrix
import bpy

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
rig = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]

for m in obj.modifiers:
    print(f"[d] modifier {m.name} type={m.type} object={getattr(m,'object',None)} "
          f"use_vgroups={getattr(m,'use_vertex_groups',None)} "
          f"invert_vg={getattr(m,'invert_vertex_group',None)} vg={getattr(m,'vertex_group',None)}")
print("[d] rig parent of obj?", obj.parent == rig, obj.parent_type)
ad = rig.animation_data
print("[d] action:", ad.action.name if ad and ad.action else None)
if ad and ad.action:
    act = ad.action
    curves = []
    for layer in act.layers:
        for strip in layer.strips:
            cb = strip.channelbag(ad.action_slot, ensure=False)
            if cb:
                curves.extend(cb.fcurves)
    print("[d] fcurve 数:", len(curves))
    for c in list(curves)[:10]:
        print("   ", c.data_path, c.array_index, "keys", len(c.keyframe_points))

# 直接旋转左前臂 twist 骨（带权重的），看评估后顶点是否移动
mesh0 = obj.to_mesh()
v0 = obj.matrix_world @ mesh0.vertices[0].co
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
pb = rig.pose.bones["CC_Base_L_UpperarmTwist01"]
pb.rotation_mode = "XYZ"
pb.rotation_euler[1] = 1.2
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
eo = obj.evaluated_get(deps)
me = eo.to_mesh()
# 找随手动的顶点数（比较包围盒）
import numpy as np
A = np.empty(len(me.vertices)*3); me.vertices.foreach_get("co", A)
B = np.empty(len(mesh0.vertices)*3); mesh0.vertices.foreach_get("co", B)
diff = (A.reshape(-1,3)-B.reshape(-1,3))
moved = int((np.linalg.norm(diff,axis=1) > 0.01).sum())
print(f"[d] 旋转 Twist01 后移动顶点数(>1cm)：{moved} / {len(me.vertices)}")
eo.to_mesh_clear()
