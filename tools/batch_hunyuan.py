# -*- coding: utf-8 -*-
"""小王子角色批量混元3D Pro 生成驱动（云 API，全脚本化）。

复用 hunyuan3d.py 的签名/提交/查询；所有任务先并行 submit 拿 JobId，
状态落 jobs.json（中断可重入），再 wait 轮询、download 拉 GLB。

用法（Python312，cwd=项目根）：
  python tools/batch_hunyuan.py submit pilot snake king ...
  python tools/batch_hunyuan.py wait                 # 轮询全部未完成任务
  python tools/batch_hunyuan.py download             # 拉取已完成的 GLB
  python tools/batch_hunyuan.py status
  python tools/batch_hunyuan.py auto pilot snake ... # submit+wait+download 一条龙

产物：assets/models/hunyuan-<name>.glb（并镜像 web/models/）。
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hunyuan3d  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "assets" / "input"
MODELS_DIR = ROOT / "assets" / "models"
WEB_MODELS_DIR = ROOT / "web" / "models"
JOBS_FILE = INPUT_DIR / "_hunyuan_jobs.json"

FACE_COUNT = 100000          # 与 hunyuan-fox/rose 一致，web 体积友好
POLL_INTERVAL = 15           # 秒
DONE = {5, "DONE", "SUCCESS"}
FAILED = {6, "FAIL", "FAILED", "ERROR"}


def load_jobs() -> dict:
    if JOBS_FILE.exists():
        return json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    return {}


def save_jobs(jobs: dict) -> None:
    JOBS_FILE.write_text(
        json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def input_path(name: str) -> Path:
    return INPUT_DIR / f"hunyuan-{name}-input.png"


def submit_one(name: str, secret_id: str, secret_key: str) -> str:
    image = input_path(name)
    if not image.exists():
        raise FileNotFoundError(f"missing input: {image}")
    import base64
    payload = {
        "ImageBase64": base64.b64encode(image.read_bytes()).decode("ascii"),
        "GenerateType": "Normal",
        "FaceCount": FACE_COUNT,
        "EnablePBR": True,
        "ResultFormat": "GLB",
    }
    result = hunyuan3d.unwrap(hunyuan3d.sign_request(
        "SubmitHunyuanTo3DProJob", payload, secret_id, secret_key, "cn"
    ))
    return result["JobId"]


def query_one(job_id: str, secret_id: str, secret_key: str) -> dict:
    return hunyuan3d.unwrap(hunyuan3d.sign_request(
        "QueryHunyuanTo3DProJob", {"JobId": job_id},
        secret_id, secret_key, "cn",
    ))


def cmd_submit(names: list[str]) -> None:
    secret_id, secret_key = hunyuan3d.load_credentials()
    jobs = load_jobs()
    for name in names:
        rec = jobs.get(name, {})
        if rec.get("jobId"):
            print(f"[skip] {name}: already submitted ({rec['jobId']})")
            continue
        try:
            job_id = submit_one(name, secret_id, secret_key)
        except Exception as exc:  # 单张失败不影响其余提交
            print(f"[fail] {name}: {exc}")
            continue
        jobs[name] = {"jobId": job_id, "status": "SUBMITTED"}
        save_jobs(jobs)
        print(f"[submit] {name}: {job_id}")
    save_jobs(jobs)


def cmd_wait() -> None:
    secret_id, secret_key = hunyuan3d.load_credentials()
    jobs = load_jobs()
    pending = [n for n, r in jobs.items() if r.get("status") not in
               ("DONE", "FAILED")]
    while pending:
        for name in pending:
            rec = jobs[name]
            try:
                info = query_one(rec["jobId"], secret_id, secret_key)
            except Exception as exc:
                print(f"[warn] {name}: query error {exc}")
                continue
            status = info.get("Status")
            rec["rawStatus"] = str(status)
            if status in DONE:
                files = info.get("ResultFile3Ds") or []
                glb = next(
                    (f for f in files
                     if f.get("Type", "").upper() == "GLB"),
                    files[0] if files else None,
                )
                if glb is None:
                    rec["status"] = "FAILED"
                    rec["error"] = "DONE but no GLB url"
                else:
                    rec["status"] = "DONE"
                    rec["url"] = glb["Url"]
                print(f"[done] {name}")
            elif status in FAILED:
                rec["status"] = "FAILED"
                rec["error"] = f"{info.get('ErrorCode')}: {info.get('ErrorMessage')}"
                print(f"[failed] {name}: {rec['error']}")
            else:
                print(f"[..] {name}: {status}", flush=True)
        save_jobs(jobs)
        pending = [n for n, r in jobs.items() if r.get("status") not in
                   ("DONE", "FAILED")]
        if pending:
            time.sleep(POLL_INTERVAL)
    print("all jobs settled")


def cmd_download() -> None:
    jobs = load_jobs()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, rec in jobs.items():
        if rec.get("status") != "DONE" or not rec.get("url"):
            continue
        dst = MODELS_DIR / f"hunyuan-{name}.glb"
        if dst.exists() and dst.stat().st_size > 100_000:
            print(f"[skip] {dst.name} exists")
            continue
        resp = requests.get(rec["url"], timeout=600)
        resp.raise_for_status()
        dst.write_bytes(resp.content)
        print(f"[save] {dst.name}: {len(resp.content) // 1024} KB")


def cmd_status() -> None:
    jobs = load_jobs()
    for name, rec in jobs.items():
        extra = f" {rec.get('rawStatus', '')}" if rec.get("status") == "SUBMITTED" else ""
        print(f"{name:14s} {rec.get('status', '?')}{extra}")


def mirror_to_web() -> None:
    WEB_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for glb in MODELS_DIR.glob("hunyuan-*.glb"):
        dst = WEB_MODELS_DIR / glb.name
        if not dst.exists() or dst.stat().st_size != glb.stat().st_size:
            dst.write_bytes(glb.read_bytes())
            print(f"[mirror] {glb.name} -> web/models/")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_sub = sub.add_parser("submit")
    p_sub.add_argument("names", nargs="+")
    sub.add_parser("wait")
    sub.add_parser("download")
    sub.add_parser("status")
    p_auto = sub.add_parser("auto")
    p_auto.add_argument("names", nargs="+")
    args = parser.parse_args()

    if args.cmd == "submit":
        cmd_submit(args.names)
    elif args.cmd == "wait":
        cmd_wait()
        cmd_download()
        mirror_to_web()
    elif args.cmd == "download":
        cmd_download()
        mirror_to_web()
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "auto":
        cmd_submit(args.names)
        cmd_wait()
        cmd_download()
        mirror_to_web()


if __name__ == "__main__":
    main()
