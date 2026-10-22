# -*- coding: utf-8 -*-
"""Mixamo FBX 们 -> 单个带动画片段的 GLB（Three.js 直接用）。

输入：
  --skin   带皮肤的角色 FBX（Mixamo 下载时选 "With skin"）
  --anims  name=path 多对，name 是片段名（idle/walk/run/...），path 是
           Mixamo "Without skin" 动画 FBX（同一角色骨架，骨骼同名可直接合并）
  --out    输出 GLB 路径

Blender 5.x headless:
  blender --background --python blender/mixamo_to_glb.py -- \
    --skin assets/from-mixamo/prince.fbx \
    --anims idle=assets/from-mixamo/idle.fbx walk=.../walk.fbx \
    --out web/models/prince_rigged.glb

原理：第一个 FBX 的网格+骨架为基准；之后每个动画 FBX 只取其 Action，
重命名为片段名并打上 NLA 条带；glTF 导出器把每条 NLA 条带导成一个 animation clip。
"""
import bpy
import os
import sys


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:]
    skin, out = None, None
    anims = []
    i = 0
    while i < len(argv):
        if argv[i] == "--skin":
            skin = os.path.abspath(argv[i + 1]); i += 2
        elif argv[i] == "--out":
            out = os.path.abspath(argv[i + 1]); i += 2
        elif argv[i] == "--anims":
            i += 1
            while i < len(argv) and not argv[i].startswith("--"):
                name, path = argv[i].split("=", 1)
                anims.append((name, os.path.abspath(path)))
                i += 1
        else:
            i += 1
    assert skin and out and anims, "用法见文件头"
    return skin, anims, out


def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


def main():
    skin_path, anims, out_path = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # 1) 带皮肤的角色
    skin_objs = import_fbx(skin_path)
    armature = next(o for o in skin_objs if o.type == "ARMATURE")
    mesh_objs = [o for o in skin_objs if o.type == "MESH"]
    print(f"[merge] 角色：{len(mesh_objs)} 网格，骨架 {armature.name}")

    # Mixamo 骨架常见缩放 0.01；统一应用，避免动作与网格错位
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    for m in mesh_objs:
        m.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # 2) 逐带动画 FBX：取出 Action 挂到基准骨架的 NLA
    for clip_name, fbx_path in anims:
        imported = import_fbx(fbx_path)
        anim_arm = next((o for o in imported if o.type == "ARMATURE"), None)
        assert anim_arm, f"{fbx_path} 里没有骨架"
        action = anim_arm.animation_data.action if anim_arm.animation_data else None
        assert action and action.fcurves, f"{fbx_path} 里没有动画 Action"
        action.name = clip_name

        # 推一条 NLA 条带（导出器据此生成同名 clip）
        if not armature.animation_data:
            armature.animation_data_create()
        track = armature.animation_data.nla_tracks.new()
        track.name = clip_name
        track.strips.new(clip_name, 0, action)

        # 删掉动画 FBX 的骨架和网格（Action 已挂在基准骨架上，保留在 bpy.data.actions）
        for o in imported:
            bpy.data.objects.remove(o, do_unlink=True)
        print(f"[merge] 片段 {clip_name}: {action.frame_range[1]:.0f} 帧")

    # 3) 归位：角色脚底 z=0、动画自身是 in-place（Mixamo 下载时已勾 In Place）
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    for m in mesh_objs:
        m.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.location_clear()

    # 4) 导出 GLB：NLA 条带 -> 多 animation clips
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        export_apply=True,
        export_yup=True,
        export_animations=True,
        export_nla_strips=True,
        export_lights=False,
        export_cameras=False,
    )
    print(f"[merge] 完成：{out_path}（{os.path.getsize(out_path)/1e6:.1f} MB，"
          f"clips: {[a[0] for a in anims]}）")


if __name__ == "__main__":
    main()
