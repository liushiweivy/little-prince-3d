# -*- coding: utf-8 -*-
"""给正交渲染图叠 0.1m 网格（相机：700x900, ortho_scale=2.05, 目标 z=0.9）。

用法（Python312 + Pillow）：
  python overlay_grid.py <in.png> <out.png> <横轴: x|y>
"""
import sys
from PIL import Image, ImageDraw, ImageFont

IN, OUT, HAXIS = sys.argv[1], sys.argv[2], sys.argv[3]
PPM = 900 / 2.05
CX, CZ = 350.0, 450.0
ZTARGET = 0.9

im = Image.open(IN).convert("RGB")
d = ImageDraw.Draw(im)
try:
    font = ImageFont.truetype("arial.ttf", 13)
except OSError:
    font = ImageFont.load_default()


def u(world):
    return CX + world * PPM


def v(z):
    return CZ - (z - ZTARGET) * PPM


# 主网格每 0.1m，次网格每 0.05m
xmin, xmax = -CX / PPM, (700 - CX) / PPM
zlo, zhi = ZTARGET - CZ / PPM, ZTARGET + (900 - CZ) / PPM
i = int(xmin / 0.05)
while i * 0.05 <= xmax:
    w = i % 2 == 0
    col = (255, 60, 60) if i == 0 else ((200, 200, 200) if w else (230, 230, 230))
    px = u(i * 0.05)
    d.line([(px, 0), (px, 900)], fill=col, width=1 if w else 1)
    if w:
        d.text((px + 2, 2), f"{HAXIS}={i*0.05:+.1f}", fill=(200, 0, 0), font=font)
    i += 1
j = int(zlo / 0.05)
while j * 0.05 <= zhi:
    w = j % 2 == 0
    col = (60, 120, 255) if j * 0.05 == 0 else ((180, 180, 220) if w else (225, 225, 240))
    pv = v(j * 0.05)
    d.line([(0, pv), (700, pv)], fill=col, width=1)
    if w:
        d.text((610, pv + 1), f"z={j*0.05:+.1f}", fill=(0, 0, 180), font=font)
    j += 1
d.line([(0, CZ), (700, CZ)], fill=(60, 120, 255), width=1)
d.line([(CX, 0), (CX, 900)], fill=(255, 60, 60), width=1)
im.save(OUT)
print(OUT)
