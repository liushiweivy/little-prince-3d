# -*- coding: utf-8 -*-
"""小王子道具图生3D参考图批量准备（喂混元3D 网页 V3.1）。

复用 gen_character_refs 的 Pollinations 下载与 GrabCut 抠图，只换提示词表：
统一 chibi 3D toy / 黏土质感、单主体正面、纯色背景（后处理灌白），
与角色模型同一美术路数。

跑法：E:/1workspace/TripoSR/.venv/Scripts/python.exe tools/gen_prop_refs.py [名字...]
不传名字 = 全部；删 assets/input/_raw/<name>.jpg 可重生。
"""
import pathlib
import sys
import time
import urllib.parse

import requests

import gen_character_refs as gc

# 12 件核心道具（2026-10-22，12 免费点一批）。提示词刻意：单主体、居中、
# 无底座/无场景（底座会被混元做成一体雕像，正面半身同理）。
PROPS = {
    "volcano-active": (
        "a cute chibi 3D toy style small active volcano island, brown rocky "
        "crater with glowing bright red lava and a few lava drips, soft matte "
        "clay texture, single object centered, full view, plain solid light "
        "background, no base, no text, no watermark"),
    "volcano-extinct": (
        "a cute chibi 3D toy style small extinct volcano mountain, smooth "
        "grey-brown rocky slopes with a green grass top and empty rounded "
        "crater, a tiny flower sprout, soft matte clay texture, single object "
        "centered, plain solid light background, no base, no text"),
    "baobab": (
        "a chibi 3D toy style baobab tree, very thick brown twisted trunk "
        "splitting into three fat root-like branches with sparse small green "
        "leaves, soft matte clay texture, single object centered, full tree "
        "from roots to top, plain solid light background, no text"),
    "glass-dome": (
        "a chibi 3D toy style clear transparent glass bell jar cloche "
        "covering one small red rose with green leaves inside, thin round "
        "dark wooden base, tiny golden knob on top, glossy see-through glass "
        "with bright white highlights, single object centered, plain solid "
        "light grey background, no text"),
    "chair": (
        "a complete simple rustic wooden dining chair, four straight legs "
        "and a full tall backrest, warm brown wood, facing forward, chibi "
        "3D toy style soft matte clay texture, single object centered, full "
        "chair fully visible, plain solid white background, no text"),
    "throne": (
        "a chibi 3D toy style golden royal throne, red velvet seat and tall "
        "crown-shaped ornate gold back, facing forward, soft matte clay "
        "texture, single object centered, plain solid light background, no text"),
    "streetlamp": (
        "a chibi 3D toy style vintage black iron street lamp post, glowing "
        "warm yellow lantern glass on top, tall slender pole with round base, "
        "soft matte style, single object centered, plain solid dark grey "
        "background, no text"),
    "globe": (
        "a chibi 3D toy style antique desk world globe, blue map sphere with "
        "golden meridian arc on a dark wood three-leg base, soft matte clay "
        "texture, single object centered, plain solid light background, no text"),
    "giant-book": (
        "a chibi 3D toy style giant ancient grimoire book standing upright, "
        "thick dark brown leather covers with gold trim and a small golden "
        "lock, yellowed pages, soft matte clay texture, single object "
        "centered, plain solid light background, no text"),
    "plane-wreck": (
        "a chibi 3D toy style crashed vintage yellow propeller airplane, "
        "one broken wing and a bent propeller, tilted as if crash landed, "
        "soft matte clay texture, single object centered floating on plain "
        "solid light background, no sand, no ground, no base, no text"),
    "well": (
        "chibi 3D toy style tiny stone wishing well, low circular grey "
        "stone wall ring, two small wooden posts supporting a tiny pitched "
        "roof, one wooden bucket hanging from a rope between the posts, "
        "soft matte clay texture, single object floating centered, no "
        "house no grass no ground no base no scenery, plain solid white "
        "background, no text"),
    "sheep-box": (
        "chibi 3D toy style sealed wooden cube box, solid brown wood front "
        "plank with exactly three small round circular holes drilled in "
        "one horizontal row, nailed corners, closed box with solid sides, "
        "single object centered, no shelves no openings no interior no "
        "furniture, plain solid white background, no text"),
    "wine-bottle": (
        "a cute chibi 3D toy style short plump wine bottle, deep red matte "
        "clay body with red foil cap and blank cream paper label, cartoon "
        "vinyl figurine texture, not photorealistic, no glass no "
        "transparency, single object centered standing on nothing, plain "
        "solid white background, no table no ground no base, no text"),
    "wooden-bench": (
        "a chibi 3D toy style simple rustic wooden bench, two plank legs "
        "each side and one long seat plank, warm brown wood, soft matte "
        "clay texture, single object centered, plain solid white "
        "background, no ground, no text"),
}

SEEDS = {
    "volcano-active": 201, "volcano-extinct": 202, "baobab": 203,
    "glass-dome": 304, "chair": 305, "throne": 206, "streetlamp": 207,
    "globe": 208, "giant-book": 209, "plane-wreck": 210, "well": 411,
    "sheep-box": 412, "wine-bottle": 513, "wooden-bench": 214,
}


def download(name: str, prompt: str) -> pathlib.Path:
    raw = gc.RAW_DIR / f"{name}.jpg"
    if raw.exists() and raw.stat().st_size > 5000:
        print(f"[skip] {raw.name} exists")
        return raw
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    params = {"width": 1024, "height": 1024, "nologo": "true",
              "model": "turbo", "seed": SEEDS[name]}
    for attempt in range(6):
        proxies = gc.PROXY_CHAIN[attempt % len(gc.PROXY_CHAIN)]
        via = "proxy" if proxies else "direct"
        try:
            r = requests.get(url, params=params, proxies=proxies, timeout=240)
        except requests.RequestException as exc:
            print(f"[retry {attempt+1}/{via}] {name}: {exc}")
            time.sleep(15 + 15 * attempt)
            continue
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            raw.write_bytes(r.content)
            print(f"[ok] {name}: {len(r.content)//1024} KB (try {attempt+1})")
            return raw
        print(f"[retry {attempt+1}/{via}] {name}: {r.status_code} {r.content[:60]!r}")
        time.sleep(20 + 15 * attempt)
    raise RuntimeError(f"download failed: {name}")


def main() -> None:
    names = sys.argv[1:] or list(PROPS)
    for name in names:
        raw = download(name, PROPS[name])
        gc.clean(raw, name)
        time.sleep(4)


if __name__ == "__main__":
    main()
