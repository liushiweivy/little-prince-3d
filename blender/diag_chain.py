# -*- coding: utf-8 -*-
import os, sys
from mathutils import Vector, Matrix
import bpy

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
rig = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"][0]
rig.animation_data.action = None

CHAIN = ["CC_Base_L_Clavicle", "CC_Base_L_Upperarm",
         "CC_Base_L_UpperarmTwist01", "CC_Base_L_UpperarmTwist02",
         "CC_Base_L_Forearm", "CC_Base_L_ForearmTwist01",
         "CC_Base_L_ForearmTwist02", "CC_Base_L_Hand"]
for n in CHAIN:
    b = rig.data.bones[n]
    ml = b.matrix_local
    s = ml.to_scale()
    print(f"[c] {n:30s} inherit_rot={b.use_inherit_rotation} inherit_scale={b.inherit_scale} "
          f"connected={b.use_connect} scale=({s.x:.3f},{s.y:.3f},{s.z:.3f}) parent={b.parent.name if b.parent else '-'}")

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode="POSE")
Y = Vector((0, 1, 0)); I = Matrix.Identity(4)

def show(tag):
    bpy.context.view_layer.update()
    print(f"--- {tag}")
    for n in CHAIN[1:]:
        pb = rig.pose.bones[n]
        y = (pb.matrix.to_3x3() @ Y).normalized()
        h = pb.head
        print(f"   {n:28s} y=({y.x:+.2f},{y.y:+.2f},{y.z:+.2f}) head=({h.x:.1f},{h.y:.1f},{h.z:.1f})")

def rot_world(key, target):
    pb = rig.pose.bones[key]
    mr = pb.bone.matrix_local
    qw = ((mr.to_3x3() @ Y).normalized()).rotation_difference(target)
    desired = Matrix.Translation(mr.translation) @ qw.to_matrix().to_4x4() @ mr.to_3x3().to_4x4()
    pt = pb.parent.bone.matrix_local @ pb.parent.matrix.inverted() if pb.parent else I
    pb.matrix_basis = mr.inverted() @ pt @ desired

show("rest")
rot_world("CC_Base_L_Upperarm", Vector((1, 0, 0)))
show("只转 Upperarm")
rot_world("CC_Base_L_Forearm", Vector((1, 0, 0)))
show("再转 Forearm")
rot_world("CC_Base_L_Hand", Vector((1, 0, 0)))
show("再转 Hand")
