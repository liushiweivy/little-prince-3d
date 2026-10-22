# -*- coding: utf-8 -*-
"""诊断：打印各 z 高度切片的 x 聚类，调 prep_tpose.py 的 GAP/DX 用。"""
import os
import sys
from mathutils import Vector
import bpy

SRC = os.path.abspath(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
bpy.ops.object.select_all(action="DESELECT")
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
obj = bpy.context.view_layer.objects.active
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
mx = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
obj.scale = (1.8 / (mx.z - mn.z),) * 3
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bbox = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
mn = Vector((min(v.x for v in bbox), min(v.y for v in bbox), min(v.z for v in bbox)))
mx = Vector((max(v.x for v in bbox), max(v.y for v in bbox), max(v.z for v in bbox)))
cx, cy = (mn.x + mx.x) / 2, (mn.y + mx.y) / 2
obj.location = (-cx, -cy, -mn.z)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

import numpy as np
verts = np.fromiter((c for v in obj.data.vertices for c in v.co),
                    dtype=float, count=len(obj.data.vertices) * 3).reshape(-1, 3)

DZ, DX, GAP = 0.03, 0.015, 0.045
z = 0.50
while z < 1.65:
    sel = verts[(verts[:, 2] >= z) & (verts[:, 2] < z + DZ)]
    cols = {}
    for x in sel[:, 0]:
        k = round(float(x) / DX)
        cols[k] = cols.get(k, 0) + 1
    groups, cur = [], []
    for k in sorted(cols):
        if cur and k - cur[-1] > GAP / DX:
            groups.append(cur); cur = []
        cur.append(k)
    if cur:
        groups.append(cur)
    desc = []
    for g in groups:
        n = sum(cols[k] for k in g)
        desc.append(f"[{g[0]*DX:+.3f},{(g[-1]+1)*DX:+.3f}]n{n}")
    print(f"z={z:.2f} nverts={len(sel):4d} clusters={len(groups)} {' '.join(desc)}")
    z += DZ
