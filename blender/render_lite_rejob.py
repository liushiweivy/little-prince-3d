# -*- coding: utf-8 -*-
"""rejob 五件 lite 档渲染核对（decimate 后是否破损/变色）。

用法：blender --background --python blender/render_lite_rejob.py
输出：blender/views/lite_hunyuan-<name>_a25.png
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_check import ROOT, VIEWS, render_view
from render_rejob import save_png

NAMES = ['hunyuan-glass-dome', 'hunyuan-volcano-extinct', 'hunyuan-fountain',
         'hunyuan-well', 'hunyuan-wooden-bench']
SRC = os.path.join(ROOT, 'web', 'models', 'lite')


def main():
    for name in NAMES:
        glb = os.path.join(SRC, name + '.glb')
        arr = render_view(glb, 25.0)
        out = os.path.join(VIEWS, f'lite_{name}_a25.png')
        save_png(arr, out)
        print(f'[LITE] {out}')


if __name__ == '__main__':
    main()
