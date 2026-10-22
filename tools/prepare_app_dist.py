# -*- coding: utf-8 -*-
"""为 Tauri 打包准备白名单静态目录 dist-app/。

只拷贝游戏运行必需文件（绝不把 web/models 下 1GB 原档打进 exe）：
  index.html / css / js / vendor
  models/lite/          减面档（~84MB，默认资产）
  models 根下 3 个小旧档  fox/rose/little-prince（?model=triposr 变体用）

用法：python tools/prepare_app_dist.py
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_WEB = ROOT / "web"
DST = ROOT / "dist-app"

# models 根目录下的保留档：
# - fox/rose/little-prince：triposr 变体小档（合计约 6MB）
# - hunyuan-glass-dome：assets.js LITE_SKIP 指定走 full 原档（玻璃材质在 lite 下不可见），
#   桌面版没有 ?assets=full 可切，必须随包（约 39MB）
ROOT_MODEL_KEEP = {"fox.glb", "rose.glb", "little-prince.glb", "hunyuan-glass-dome.glb"}

COPY_DIRS = ["css", "js", "vendor"]
COPY_FILES = ["index.html"]


def wipe_dst() -> None:
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)


def copy_dir_rel(src: Path, dst: Path) -> int:
    """整目录拷贝，返回文件数。"""
    shutil.copytree(src, dst)
    return sum(1 for p in dst.rglob("*") if p.is_file())


def main() -> int:
    if not SRC_WEB.is_dir():
        print(f"[ERR] 找不到 {SRC_WEB}", file=sys.stderr)
        return 1

    lite_src = SRC_WEB / "models" / "lite"
    if not lite_src.is_dir():
        print("[ERR] web/models/lite 不存在，请先跑 blender/decimate_glb.py", file=sys.stderr)
        return 1

    wipe_dst()
    total_bytes = 0

    for name in COPY_FILES:
        shutil.copy2(SRC_WEB / name, DST / name)
        total_bytes += (SRC_WEB / name).stat().st_size
        print(f"[ok] {name}")

    for name in COPY_DIRS:
        n = copy_dir_rel(SRC_WEB / name, DST / name)
        size = sum(p.stat().st_size for p in (DST / name).rglob("*") if p.is_file())
        total_bytes += size
        print(f"[ok] {name}/  ({n} 文件, {size / 1048576:.1f} MB)")

    # lite 减面档
    lite_dst = DST / "models" / "lite"
    n = copy_dir_rel(lite_src, lite_dst)
    lite_size = sum(p.stat().st_size for p in lite_dst.rglob("*") if p.is_file())
    total_bytes += lite_size
    print(f"[ok] models/lite/  ({n} 个 GLB, {lite_size / 1048576:.1f} MB)")

    # triposr 变体小档
    root_models_dst = DST / "models"
    kept = 0
    for name in sorted(ROOT_MODEL_KEEP):
        f = SRC_WEB / "models" / name
        if f.is_file():
            shutil.copy2(f, root_models_dst / name)
            total_bytes += f.stat().st_size
            kept += 1
    print(f"[ok] models/ 旧变体小档 {kept} 个")

    print(f"=== dist-app 就绪：{total_bytes / 1048576:.1f} MB ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
