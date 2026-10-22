# -*- coding: utf-8 -*-
"""小王子角色图生3D参考图批量准备（喂混元3D 网页 V3.1）。

流程：Pollinations turbo(SDXL，免登录、走本机代理 7897) 出 Q 版角色图
→ GrabCut 抠图（中央框 PR_FGD、外框+水印区 BGD）合成白底
→ 取最大连通块去漂浮残片 → 裁边留白 5% → 长边 1024。

为什么不用漫水填充：turbo 出的柔光 3D 渲染图没有描边，暗背景角落实例
+ 大容差会把黑礼服灌白（vainman/merchant 实测全毁），白胡子又和亮背景
同亮度被吃；GrabCut 按颜色分布分类，与背景同明度的主体也保得住。
粗描边卡通图仍用 tools/prep_props.py 的 floodFill 管线。

跑法：E:/1workspace/TripoSR/.venv/Scripts/python.exe tools/gen_character_refs.py [名字...]
不传名字 = 全部；已下载的原图不重复请求（删 assets/input/_raw/<name>.jpg 可重生）。
"""
import pathlib
import sys
import time

import cv2
import numpy as np
import requests
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "assets" / "input" / "_raw"
OUT_DIR = ROOT / "assets" / "input"
PROXY = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
# Pollinations 实测可国内直连；直连失败再回退本机代理（代理常开时照走代理）。
PROXY_CHAIN = (None, PROXY)

# 统一基调：Q 版 chibi、大头小身、大眼、柔光黏土玩具质感（与 hunyuan-prince
# 同一路数），正面全身，主体居中，背景刻意只要求纯色——后处理统一灌白。
STYLE = (", chibi 3D toy figure style, soft matte shading, big head small body, "
         "cute big eyes, full body standing front view, centered, "
         "plain solid background, no text, no watermark")

CHARACTERS = {
    "pilot": ("a little boy pilot aviator with brown leather bomber jacket and "
              "fur collar, tan scarf flowing, vintage leather aviator cap with "
              "goggles on forehead, brown hair, friendly smile" + STYLE),
    "snake": ("a cute coiled desert snake, golden yellow scales with brown diamond "
              "patterns, big friendly hypnotic eyes, tiny red forked tongue, "
              "coiled spiral pose, head raised facing forward"
              ", chibi 3D toy figure style, soft matte shading, big cute eyes, "
              "centered, plain solid background, no text, no watermark"),
    "king": ("a chibi old king with long fluffy white beard, golden crown with red "
             "jewels, red royal robe with white ermine trim, holding a golden scepter"
             + STYLE),
    "vainman": ("a chibi conceited handsome man in fancy red tailcoat suit with gold "
                "trim, tall black top hat, bow tie, one hand on hip, holding a small "
                "hand mirror, proud smirk" + STYLE),
    "drunkard": ("a chibi tired drunkard man in rumpled dark grey suit and loosened "
                 "red tie, messy hair, sitting and hugging an empty wine bottle, "
                 "sleepy droopy eyes" + STYLE),
    "merchant": ("a chibi serious stout businessman with neat combed dark hair and "
                 "small round glasses, dark grey business suit with red tie, "
                 "full body standing front view, normal chibi body proportions, "
                 "both arms hugging a thick open red account ledger book against "
                 "his chest" + STYLE),
    "lamplighter": ("a little boy lamplighter in dark green railway cap and "
                    "brass-button uniform coat, holding up a glowing vintage street "
                    "lamp on a pole" + STYLE),
    "geographer": ("a chibi old wise geographer scholar with fluffy white hair and "
                   "small round glasses, long dark teal scholar robe with gold trim, "
                   "full body standing front view, hugging a giant open world atlas "
                   "book, a quill pen tucked behind one ear, gentle smile" + STYLE),
}

SEEDS = {"pilot": 21, "snake": 33, "king": 44, "vainman": 55,
         "drunkard": 66, "merchant": 123, "lamplighter": 11,
         "geographer": 99}


def download(name: str, prompt: str) -> pathlib.Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw = RAW_DIR / f"{name}.jpg"
    if raw.exists() and raw.stat().st_size > 5000:
        print(f"[skip] {raw.name} exists")
        return raw
    import urllib.parse
    url = "https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
    params = {"width": 1024, "height": 1024, "nologo": "true",
              "model": "turbo", "seed": SEEDS[name]}
    for attempt in range(6):
        proxies = PROXY_CHAIN[attempt % len(PROXY_CHAIN)]
        via = "proxy" if proxies else "direct"
        try:
            r = requests.get(url, params=params, proxies=proxies, timeout=240)
        except requests.RequestException as exc:
            print(f"[retry {attempt+1}/{via}] {name} conn error: {exc}")
            time.sleep(15 + 15 * attempt)
            continue
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
            raw.write_bytes(r.content)
            print(f"[ok] {name}: {len(r.content)//1024} KB (try {attempt+1})")
            return raw
        print(f"[retry {attempt+1}] {name} status={r.status_code} body={r.content[:80]!r}")
        time.sleep(20 + 15 * attempt)
    raise RuntimeError(f"download failed: {name}")


def _largest_component(fg: np.ndarray) -> np.ndarray:
    """只保留最大前景连通块（去水印残片/漂浮噪点），并填掉它内部的洞。"""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg.astype(np.uint8), 8)
    if n <= 1:
        return fg
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    keep = (labels == largest).astype(np.uint8)
    holes = np.zeros_like(keep)
    mask = np.zeros((keep.shape[0] + 2, keep.shape[1] + 2), np.uint8)
    cv2.floodFill(keep.copy(), mask, (0, 0), 2)
    holes[(mask[1:-1, 1:-1] == 0) & (keep == 0)] = 1
    return (keep | holes).astype(bool)


def _bglike_map(bgr: np.ndarray, gc_mask: np.ndarray,
                tol: int = 30, sat_margin: int = 25) -> np.ndarray:
    """返回背景似然图（四边样本中位数色，色差/饱和度双门控）。

    背景是低饱和摄影棚渐变：四边样本估中位数色，色差<=tol 且饱和度不超过
    四边样本上限+sat_margin 才算背景色。肤/手饱和更高、白胡子/白衣明度差
    更大，都过不了门控；金权杖/红头发等饱和物更安全。容差按角色配色调：
    白发+浅背景（国王）要收紧防吃发，深背景+青袍（地理学家）放宽靠饱和拦。
    """
    h, w = gc_mask.shape
    ring = np.zeros((h, w), bool)
    ring[:4, :] = ring[-4:, :] = ring[:, :4] = ring[:, -4:] = True
    ring &= (gc_mask == cv2.GC_BGD) | (gc_mask == cv2.GC_PR_BGD)
    samples = bgr[ring].astype(np.float32)
    sat_ring = cv2.cvtColor(samples.reshape(1, -1, 3).astype(np.uint8),
                            cv2.COLOR_BGR2HSV)[0, :, 1]
    sat_max = int(sat_ring.max())
    # 摄影棚渐变从暗角到主体旁亮区跨度可达 50+，单一中位数+容差两头够不着
    # （地理学家暗灰背景实测）。四边样本 kmeans 两中心（暗/亮），到任一中心
    # 距离<=tol 即背景色；高饱和的袍子/皇冠/权杖自然落在门外。
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(
        samples, 2, None, criteria, 3, cv2.KMEANS_PP_CENTERS
    )
    dist_stack = np.stack([
        np.abs(bgr.astype(np.int16) - c.astype(np.int16)).max(axis=2)
        for c in centers
    ])
    dist = dist_stack.min(axis=0)
    sat = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[:, :, 1]
    return (dist <= tol) & (sat <= sat_max + sat_margin)

    def _border_reachable(plane: np.ndarray) -> np.ndarray:
        n, lab = cv2.connectedComponents(plane.astype(np.uint8), 8)
        border_lab = np.unique(np.concatenate([
            lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        return np.isin(lab, border_lab) & (lab > 0)

    # 纯颜色连通块：判断"被围住的背景色岛"（手/脸与外部背景同块，不误伤）。
    color_reachable = _border_reachable(bg_like)
    # FGD 硬种子作屏障的连通图：只清理与外相通的窄缝背景，
    # 钻不进被 FGD 边缘包住的手。
    traversable = bg_like & (gc_mask != cv2.GC_FGD)
    return bg_like, color_reachable, _border_reachable(traversable)


# 背景色补刀容差：默认中灰背景；国王白发+浅背景要收紧防吃发/白裙；
# 地理学家青袍+暗背景靠饱和度门控拦袍子，色差容差可放宽啃掉暗灰岛。
BG_GATE = {
    "king": (22, 15),
    "geographer": (35, 20),
}


def segment_subject(bgr: np.ndarray, name: str = "") -> np.ndarray:
    """GrabCut 抠主体 → alpha(0/255)。

    漫水填充在柔光 3D 渲染图上必翻车：深灰背景顶角 + tol 65 会把黑色礼服
    当背景灌掉，白胡子/白袍又因与亮背景同亮度被吃。GrabCut 按颜色分布
    （而非到角落实例的亮度差）分类，黑白主体都保得住。

    两道补救：中轴 FGD 硬种子把白发白须教给前景 GMM；首轮分割后再按四边
    背景样本做颜色门控，把 PR_FGD 里的背景色像素（含被主体围住的背景岛：
    皇冠后方背板、地理学家肩侧灰岛、商人腿间三角）一律打回 BGD 重估。
    """
    tol, sat_margin = BG_GATE.get(name, (30, 25))
    h, w = bgr.shape[:2]
    gc_mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    side = min(h, w)
    border = max(2, int(0.02 * side))           # 外框：确定背景
    gc_mask[:border, :] = cv2.GC_BGD
    gc_mask[-border:, :] = cv2.GC_BGD
    gc_mask[:, :border] = cv2.GC_BGD
    gc_mask[:, -border:] = cv2.GC_BGD
    gc_mask[int(h * 0.92):, int(w * 0.76):] = cv2.GC_BGD   # pollinations 水印
    rect_margin = int(0.04 * side)              # 中央框：疑似前景
    gc_mask[rect_margin:h - rect_margin,
            rect_margin:w - rect_margin] = cv2.GC_PR_FGD
    # 内部硬前景种子：白发白须（国王）与浅灰背景同色，光靠 GMM 会把头整个
    # 归到背景类；沿头-躯干中轴锁一条窄 FGD（40%~60% 宽、14%~82% 高），
    # 把白色像素强制教给前景 GMM。条带必须窄、且不上探到冠尖——宽了或高
    # 了会把头发外侧/皇冠后方的背景也锁成前景，留下矩形背板。
    gc_mask[int(h * 0.14):int(h * 0.82),
            int(w * 0.40):int(w * 0.60)] = cv2.GC_FGD
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(bgr, gc_mask, None, bgd_model, fgd_model,
                6, cv2.GC_INIT_WITH_MASK)
    # 背景色补刀：PR_FGD（FGD 硬种子天然豁免）里只要颜色像四边背景就打回，
    # 连通到边的窄缝和被主体围住的背景岛一起清。标完直接出 mask，不再
    # GC_EVAL——实测重估会让 GMM 借新 BGD 把相邻脸颊/手部软前景一起瓜分。
    bg_like = _bglike_map(bgr, gc_mask, tol, sat_margin)
    gc_mask[bg_like & (gc_mask == cv2.GC_PR_FGD)] = cv2.GC_BGD
    fg = (gc_mask == cv2.GC_FGD) | (gc_mask == cv2.GC_PR_FGD)
    fg = _largest_component(fg)
    alpha = np.where(fg, 255, 0).astype(np.uint8)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE,
                             np.ones((3, 3), np.uint8))
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)   # 1px 羽化，去掉描边毛边
    return alpha


def clean(raw_path: pathlib.Path, name: str) -> pathlib.Path:
    bgr = cv2.imread(str(raw_path))
    h, w = bgr.shape[:2]
    alpha = segment_subject(bgr, name)
    fg_ratio = float((alpha > 160).mean())
    white = np.full_like(bgr, 255)
    a = (alpha.astype(np.float32) / 255.0)[..., None]
    comp = (bgr.astype(np.float32) * a + white.astype(np.float32) * (1 - a))
    out = np.clip(comp, 0, 255).astype(np.uint8)
    im = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
    # 按 alpha 裁边留 5%（白胡子主体不能靠"暗像素"求 bbox）。
    ys, xs = np.where(alpha > 160)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pad = int(0.05 * max(y1 - y0, x1 - x0))
    im = im.crop((max(0, x0 - pad), max(0, y0 - pad),
                  min(w, x1 + pad), min(h, y1 + pad)))
    s = 1024 / max(im.size)
    if s < 1:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    dst = OUT_DIR / f"hunyuan-{name}-input.png"
    im.save(dst)
    print(f"[clean] {name}: fg={fg_ratio:.3f} -> {dst.name} {im.size}")
    return dst


def main() -> None:
    names = sys.argv[1:] or list(CHARACTERS)
    for name in names:
        prompt = CHARACTERS[name]
        raw = download(name, prompt)
        clean(raw, name)
        time.sleep(4)          # 温和限速，减少 402


if __name__ == "__main__":
    main()
