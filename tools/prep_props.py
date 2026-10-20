# -*- coding: utf-8 -*-
"""道具参考图预处理（喂混元3D Pro）：
- 狐狸：自带真 alpha 的 PNG 合白底 -> 高容差四角漫水填充吃掉手绘阴影盘
- 玫瑰：底部水印带近白像素刷白 -> 低容差漫水填充兜底 -> 白底
- 裁边 + 长边 1024
用 TripoSR venv 跑：E:/1workspace/TripoSR/.venv/Scripts/python.exe tools/prep_props.py

关键原理：粗描边平涂插画的黑色轮廓线会阻断 cv2.floodFill，
所以从四角种子 FIXED_RANGE 漫水只会灌满背景/阴影，灌不进主体。
rembg 对这类图反而会把狐耳/花茎啃坏，勿用。
"""
import cv2
import numpy as np
from PIL import Image

INPUT_DIR = "assets/input"


def whiten_rose_band(bgr):
    """千图浅灰水印几乎全在白底上：带内近白像素直接刷白，深色茎叶保留。"""
    out = bgr.copy()
    y0, y1, x0, x1, thr = 870, 975, 140, 890, 190
    region = out[y0:y1, x0:x1]
    region[np.all(region > thr, axis=2)] = (255, 255, 255)
    return out


def white_bg_floodfill(bgr, lo=12, hi=20):
    """主体四周都有背景余量 -> 四角种子漫水填充得到背景，背景置白。"""
    h, w = bgr.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    flags = 4 | (255 << 8) | cv2.FLOODFILL_MASK_ONLY | cv2.FLOODFILL_FIXED_RANGE
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        cv2.floodFill(bgr, mask, seed, 0, (lo,) * 3, (hi,) * 3, flags)
    bg = mask[1:-1, 1:-1] > 0
    out = bgr.copy()
    out[bg] = (255, 255, 255)
    return out


def autocrop(im, pad_frac, thr=245):
    arr = np.asarray(im.convert("RGB"))
    content = np.any(arr < thr, axis=2)
    ys, xs = np.where(content)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    h, w = arr.shape[:2]
    pad = int(pad_frac * max(y1 - y0, x1 - x0))
    return im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(w, x1 + pad), min(h, y1 + pad)))


def resize_max(im, longest=1024):
    w, h = im.size
    s = longest / max(w, h)
    if s < 1:
        im = im.resize((round(w * s), round(h * s)), Image.LANCZOS)
    return im


def composite_alpha_white(src):
    """自带真 alpha 的 PNG：合白底。"""
    im = Image.open(src).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return cv2.cvtColor(np.asarray(bg.convert("RGB")), cv2.COLOR_RGB2BGR)


def erase_painted_shadow(bgr):
    """狐图自带手绘浅灰阴影盘：四角漫水填充迭代刷白（深色外轮廓线阻断，进不了主体）。"""
    # FIXED_RANGE 以四角白为基准：容差 120 吃满阴影盘与腿间地面（核≈150），
    # 橙色主体蓝通道 <100 被天然排除，深色轮廓线再兜底
    return white_bg_floodfill(bgr, 110, 120)


def main():
    fox_pipe = lambda: erase_painted_shadow(composite_alpha_white(f"{INPUT_DIR}/fox16_vect.png"))

    def rose_pipe():
        bgr = cv2.imread(f"{INPUT_DIR}/rose5_qiantu.jpg")
        return white_bg_floodfill(whiten_rose_band(bgr), 8, 12)

    jobs = [
        ("hunyuan-fox-input.png", 0.06, fox_pipe),
        ("hunyuan-rose-input.png", 0.04, rose_pipe),
    ]
    for dst, pad, cutout in jobs:
        bgr = cutout()
        im = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        im = autocrop(im, pad)
        im = resize_max(im)
        im.save(f"{INPUT_DIR}/{dst}")
        print(f"{INPUT_DIR}/{dst} {im.size}")


if __name__ == "__main__":
    main()
