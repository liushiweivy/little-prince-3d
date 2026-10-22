# -*- coding: utf-8 -*-
import os, sys
from mathutils import Vector, Matrix
import bpy
import numpy as np

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
rig = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
rig.animation_data.action = None
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
Y = Vector((0,1,0)); I = Matrix.Identity(4)
for bname, sign in (("CC_Base_L_Upperarm",1.0),("CC_Base_R_Upperarm",-1.0)):
    pb = rig.pose.bones[bname]; mr = pb.bone.matrix_local
    qw = ((mr.to_3x3()@Y).normalized()).rotation_difference(Vector((sign,0,0)))
    desired = Matrix.Translation(mr.translation) @ qw.to_matrix().to_4x4() @ mr.to_3x3().to_4x4()
    pt = pb.parent.bone.matrix_local @ pb.parent.matrix.inverted()
    pb.matrix_basis = mr.inverted() @ pt @ desired
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode="OBJECT")

deps = bpy.context.evaluated_depsgraph_get()
eo = obj.evaluated_get(deps)
me = eo.to_mesh()
mw = eo.matrix_world
A = np.empty(len(me.vertices)*3); me.vertices.foreach_get("co", A)
B = np.empty(len(obj.data.vertices)*3); obj.data.vertices.foreach_get("co", B)
A = A.reshape(-1,3); B = B.reshape(-1,3)
# 都换世界系（mesh data 是 cm，父级 0.01）
Aw = np.array([list(mw @ Vector(c)) for c in A[:0]])  # placeholder
mA = np.array(obj.matrix_world)
def xform(P, m):
    Ph = np.concatenate([P, np.ones((len(P),1))], axis=1)
    return (Ph @ m.T)[:, :3]
Aw = xform(A, mA)
Bw = xform(B, mA)
disp = np.linalg.norm(Aw-Bw, axis=1)
idx = np.argsort(disp)[-12:][::-1]
groups = {g.index: g.name for g in obj.vertex_groups}
for i in idx:
    v = obj.data.vertices[int(i)]
    ws = ", ".join(f"{groups[g.group]}={g.weight:.2f}" for g in v.groups)
    print(f"[s] v{i} disp={disp[i]*100:.0f}cm rest={tuple(round(c*100,1) for c in Bw[i])} "
          f"posed={tuple(round(c*100,1) for c in Aw[i])} :: {ws}")
# 权重统计：有多少顶点完全没有组
nogroup = sum(1 for v in obj.data.vertices if len(v.groups)==0)
print(f"[s] 无组顶点 {nogroup}/{len(obj.data.vertices)}")
eo.to_mesh_clear()
