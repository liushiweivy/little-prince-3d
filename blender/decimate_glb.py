# -*- coding: utf-8 -*-
"""混元 GLB 批量减肥：Decimate 减面 + 4K 贴图降 1024，输出到 web/models/lite/。

在 Blender 5.2 headless 下运行：
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background --python blender/decimate_glb.py -- --only king
  （不加 --only 则按 JOB_TABLE 全量处理）

实测依据（2026-10-22，Blender 5.2.2 / glTF I/O v4.0.43）：
- 混元 GLB 均为 1 mesh / 1 材质 / 3 张 4096^2 PNG（basecolor、normal、metallic-roughness），skins=0。
- Decimate COLLAPSE 的 ratio 即面数比率，命中精确；全 UV 展开模型上
  UV/SEAM delimit 无收益，用 NORMAL 防跨硬法线折缝坍缩。
- MR 贴图 metallic 通道大量非 0，绝不能转 JPEG（4:2:0 压色度通道出伪光斑）；
  normal 同理保 PNG。
- 贴图编码实测（5.2.2）：packed 图 filepath 为空，filepath_raw+save+reload 会失败
  导致导出器回退原 4K；只 scale() 置 dirty，导出器自动重编码 PNG 嵌入。
  export_image_format='AUTO' 不尊重 per-image file_format（想 JPEG 会三张全 JPEG），
  故统一 PNG 1024：实测 king 三图 0.62+1.38+1.13MB，可接受（KISS）。
- 每个文件之间 read_factory_settings(use_empty=True) 彻底重置数据块。
- RNA 写入 ratio 后须 view_layer.update()，evaluated mesh 才反映新面数。
- 已存在产物默认跳过，--force 重跑（便于补跑/调参）。
"""
import bpy
import os
import sys

# ---------- 作业表（按 worlds.js / player.js 实际引用显式列出，不 glob） ----------
# 面数档位（Blender 5.2.2 实测 ratio 线性命中）：
# - 角色近景（相机最近 1.7m）脸/手最容易显多边形，NPC 给 3 万；
# - 玩家常驻且占画面最大，prince 4.5 万；100k 变体源就 10 万，给 3 万；
# - 道具 1.5 万起，大场景（树/火山/坠机）按表 1.8-2 万。
NPC_FACES = 30000
PRINCE_FACES = 45000
PRINCE_100K_FACES = 30000
PROP_FACES = 15000
PER_FILE_FACES = {
    'hunyuan-prince': PRINCE_FACES,
    'hunyuan-prince-100k': PRINCE_100K_FACES,
    'hunyuan-baobab': 20000,
    'hunyuan-volcano-active': 20000,
    'hunyuan-volcano-extinct': 18000,
    'hunyuan-plane-wreck': 20000,
    'hunyuan-well': 18000,
    'hunyuan-throne': 35000,
    'hunyuan-fountain': 18000,
    'hunyuan-glass-dome': 26000,  # 玫瑰近景主体
}
NPC_FILES = [
    'hunyuan-glass-dome', 'hunyuan-king', 'hunyuan-vainman', 'hunyuan-drunkard',
    'hunyuan-merchant', 'hunyuan-lamplighter', 'hunyuan-geographer',
    'hunyuan-pilot', 'hunyuan-snake', 'hunyuan-fox',
]
PLAYER_FILES = ['hunyuan-prince', 'hunyuan-prince-100k']
PROP_FILES = [
    'hunyuan-volcano-active', 'hunyuan-volcano-extinct', 'hunyuan-baobab',
    'hunyuan-chair', 'hunyuan-sheep-box', 'hunyuan-throne', 'hunyuan-fountain',
    'hunyuan-grapes', 'hunyuan-streetlamp', 'hunyuan-globe',
    'hunyuan-giant-book', 'hunyuan-plane-wreck', 'hunyuan-well',
    'hunyuan-wooden-bench',
]

TEX_LONGEST = 1024

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, 'web', 'models')
OUT_DIR = os.path.join(SRC_DIR, 'lite')


def target_for(name):
    if name in PER_FILE_FACES:
        return PER_FILE_FACES[name]
    if name in NPC_FILES:
        return NPC_FACES
    if name in PLAYER_FILES:
        return PRINCE_100K_FACES
    return PROP_FACES


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    only = None
    tex = TEX_LONGEST
    force = False
    for i, a in enumerate(argv):
        if a == '--only' and i + 1 < len(argv):
            only = [x.strip() for x in argv[i + 1].split(',') if x.strip()]
        elif a == '--tex' and i + 1 < len(argv):
            tex = int(argv[i + 1])
        elif a == '--force':
            force = True
    return only, tex, force


def count_faces():
    total = 0
    for me in bpy.data.meshes:
        total += len(me.polygons)
    return total


def shrink_textures(tex_longest):
    """把超尺寸贴图缩到 <=tex_longest（保持纵横比）。

    混元 GLB 的图是 packed FILE（filepath 空），scale() 置 dirty 后，
    glTF 导出器会重编码 PNG 嵌入；统一 PNG 保证 MR/normal 不出现 JPEG 块效应。
    """
    for img in bpy.data.images:
        if img.size[0] <= 0:
            continue
        w, h = img.size
        scale = min(1.0, tex_longest / max(w, h))
        if scale < 1.0:
            img.scale(max(1, round(w * scale)), max(1, round(h * scale)))


def process(name, tex_longest, force=False):
    src = os.path.join(SRC_DIR, name + '.glb')
    dst = os.path.join(OUT_DIR, name + '.glb')
    if not os.path.exists(src):
        print(f'[MISS] {name}: {src}')
        return False
    if os.path.exists(dst) and not force:
        print(f'[SKIP] {name}: lite 已存在（--force 覆盖）')
        return True
    src_size = os.path.getsize(src)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    src_faces = count_faces()

    target = target_for(name)
    for me in bpy.data.meshes:
        ratio = min(1.0, target / max(1, len(me.polygons)))
        if ratio < 0.999:
            mod = None
            for obj in bpy.data.objects:
                if obj.type == 'MESH' and obj.data == me:
                    mod = obj.modifiers.new(name='DecimateLite', type='DECIMATE')
                    break
            if mod:
                mod.decimate_type = 'COLLAPSE'
                mod.ratio = ratio
                mod.use_collapse_triangulate = False
                # 实测（Blender 5.2.2）：全 UV 展开模型上 UV/SEAM delimit 无收益，
                # NORMAL 防跨硬法线折缝坍缩（脸/手指/薄片边缘）
                mod.delimit = {'NORMAL'}
    # RNA 写入后必须 update 才重算；evaluated mesh 与 export_apply 的结果一致
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    dst_faces = 0
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            eval_obj = obj.evaluated_get(deps)
            ev = eval_obj.to_mesh()
            dst_faces += len(ev.polygons)
            eval_obj.to_mesh_clear()

    shrink_textures(tex_longest)
    bpy.ops.export_scene.gltf(
        filepath=dst,
        export_format='GLB',
        export_apply=True,
        export_yup=True,
        export_image_format='AUTO',
    )

    dst_size = os.path.getsize(dst)
    print(f'[OK] {name}: {src_faces/1000:.0f}k/{src_size/1048576:.1f}MB '
          f'-> {dst_faces/1000:.0f}k/{dst_size/1048576:.2f}MB')
    return True


def main():
    only, tex, force = parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    jobs = NPC_FILES + PLAYER_FILES + PROP_FILES
    if only:
        jobs = only
    print(f'=== decimate {len(jobs)} files, tex<={tex} force={force} -> {OUT_DIR}')
    ok = fail = 0
    for name in jobs:
        try:
            if process(name, tex, force):
                ok += 1
            else:
                fail += 1
        except Exception as e:  # 单文件失败不中断批次
            fail += 1
            print(f'[FAIL] {name}: {type(e).__name__}: {e}')
    print(f'=== done ok={ok} fail={fail}')
    if fail:
        sys.exit(1)


if __name__ == '__main__':
    main()
