# -*- coding: utf-8 -*-
"""rejob 新下载 GLB 渲染质检：每件渲两个方位角 PNG，供目检后再改名入位。

用法：blender --background --python blender/render_rejob.py
输入：assets/input/_rejob/<name>.glb
输出：blender/views/rejob_<name>_a25.png / _a205.png
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_check import ROOT, RES, VIEWS, render_view

SRC = os.path.join(ROOT, 'assets', 'input', '_rejob')


def save_png(arr, path):
    h, w = arr.shape[:2]
    import bpy
    img = bpy.data.images.new('out', w, h, alpha=True)
    rgba = np.flipud(arr).reshape(-1, 4).astype(np.float32) / 255.0
    img.pixels.foreach_set(rgba.reshape(-1))
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()


def main():
    os.makedirs(VIEWS, exist_ok=True)
    names = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith('.glb'))
    for name in names:
        glb = os.path.join(SRC, name + '.glb')
        for az, tag in ((25.0, 'a25'), (205.0, 'a205')):
            arr = render_view(glb, az)
            out = os.path.join(VIEWS, f'rejob_{name}_{tag}.png')
            save_png(arr, out)
            print(f'[REJOB] {out}')


if __name__ == '__main__':
    main()
