#!/usr/bin/env python3
"""Hunyuan 3D cloud generation client (Tencent Cloud API, TC3-HMAC-SHA256).

Actions used (service hunyuan, version 2023-09-01):
  SubmitHunyuanTo3DProJob    / QueryHunyuanTo3DProJob     - Pro, high quality
  SubmitHunyuanTo3DRapidJob  / QueryHunyuanTo3DRapidJob   - Rapid, fast

Credentials (never committed):
  env HUNYUAN_SECRET_ID / HUNYUAN_SECRET_KEY, or tools/hunyuan.local.json
  {"secret_id": "...", "secret_key": "..."}

Usage:
  python hunyuan3d.py probe
  python hunyuan3d.py run <image> [out.glb] [--rapid] [--facecount N] [--pbr]
  python hunyuan3d.py submit <image> [--rapid] [--facecount N] [--pbr]
  python hunyuan3d.py poll <jobId> [--rapid]
  python hunyuan3d.py call <Action> '<json body>'
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

# China: standalone ai3d service (2025-05-13). International: hunyuan service.
SITES = {
    "cn": {
        "host": "ai3d.tencentcloudapi.com",
        "service": "ai3d",
        "version": "2025-05-13",
        "region": "ap-guangzhou",
    },
    "intl": {
        "host": "hunyuan.intl.tencentcloudapi.com",
        "service": "hunyuan",
        "version": "2023-09-01",
        "region": "ap-singapore",
    },
}
HERE = Path(__file__).resolve().parent


def load_credentials():
    secret_id = os.environ.get("HUNYUAN_SECRET_ID")
    secret_key = os.environ.get("HUNYUAN_SECRET_KEY")
    if secret_id and secret_key:
        return secret_id, secret_key
    cfg = HERE / "hunyuan.local.json"
    if cfg.exists():
        data = json.loads(cfg.read_text(encoding="utf-8"))
        return data["secret_id"], data["secret_key"]
    sys.exit("Missing credentials: env HUNYUAN_SECRET_ID/KEY or tools/hunyuan.local.json")


def sign_request(action, payload, secret_id, secret_key, site):
    conf = SITES[site]
    host, service = conf["host"], conf["service"]
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    timestamp = int(time.time())
    date = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d")
    content_type = "application/json; charset=utf-8"

    canonical_headers = (
        f"content-type:{content_type}\nhost:{host}\nx-tc-action:{action.lower()}\n"
    )
    signed_headers = "content-type;host;x-tc-action"
    canonical_request = "\n".join([
        "POST", "/", "", canonical_headers, signed_headers,
        hashlib.sha256(body.encode("utf-8")).hexdigest(),
    ])
    scope = f"{date}/{service}/tc3_request"
    string_to_sign = "\n".join([
        "TC3-HMAC-SHA256", str(timestamp), scope,
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])

    def hmac_sha(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    secret = hmac_sha(("TC3" + secret_key).encode("utf-8"), date)
    secret = hmac_sha(secret, service)
    secret = hmac_sha(secret, "tc3_request")
    signature = hmac.new(
        secret, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    authorization = (
        f"TC3-HMAC-SHA256 Credential={secret_id}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    headers = {
        "Authorization": authorization,
        "Content-Type": content_type,
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": conf["version"],
        "X-TC-Region": conf["region"],
    }
    response = requests.post(f"https://{host}/", headers=headers, data=body.encode("utf-8"), timeout=60)
    return response.json()


def unwrap(response):
    if "Response" not in response:
        return response
    inner = response["Response"]
    if "Error" in inner:
        raise RuntimeError(f"{inner['Error'].get('Code')}: {inner['Error'].get('Message')}")
    return inner


def submit(args, secret_id, secret_key):
    image_path = Path(args.image)
    image_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    mode = "rapid" if args.rapid else "pro"
    action = f"SubmitHunyuanTo3D{mode.title()}Job"
    body = {"ImageBase64": image_b64}
    if args.rapid:
        body.update(ResultFormat="GLB", EnablePBR=args.pbr, EnableGeometry=False)
    else:
        body.update(
            GenerateType="Normal",
            FaceCount=args.facecount,
            EnablePBR=args.pbr,
            ResultFormat="GLB",
        )
    result = unwrap(sign_request(action, body, secret_id, secret_key, args.site))
    return result["JobId"]


def query(job_id, rapid, site, secret_id, secret_key):
    action = f"QueryHunyuanTo3D{'Rapid' if rapid else 'Pro'}Job"
    return unwrap(sign_request(action, {"JobId": job_id}, secret_id, secret_key, site))


def run(args, secret_id, secret_key):
    job_id = submit(args, secret_id, secret_key)
    print(f"JobId: {job_id} ({'rapid' if args.rapid else 'pro'})", flush=True)
    while True:
        info = query(job_id, args.rapid, args.site, secret_id, secret_key)
        status = info.get("Status")
        print(f"  status: {status}", flush=True)
        if status in (5, "DONE", "SUCCESS"):
            files = info.get("ResultFile3Ds") or []
            print(json.dumps(files, ensure_ascii=False, indent=2))
            if args.out:
                glb = next((f for f in files if f.get("Type", "").upper() == "GLB"), files[0] if files else None)
                if glb:
                    out = Path(args.out)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    out.write_bytes(requests.get(glb["Url"], timeout=300).content)
                    print(f"saved: {out} ({out.stat().st_size // 1024} KB)")
            return
        if status in (6, "FAIL", "FAILED", "ERROR"):
            raise RuntimeError(f"job failed: {info.get('ErrorCode')} {info.get('ErrorMessage')}")
        time.sleep(10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", choices=list(SITES), default="cn")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("probe")

    def add_submit(p):
        p.add_argument("image")
        p.add_argument("--rapid", action="store_true")
        p.add_argument("--facecount", type=int, default=500000)
        p.add_argument("--pbr", action="store_true")

    p_submit = sub.add_parser("submit")
    add_submit(p_submit)

    p_run = sub.add_parser("run")
    add_submit(p_run)
    p_run.add_argument("out", nargs="?")

    p_poll = sub.add_parser("poll")
    p_poll.add_argument("job_id")
    p_poll.add_argument("--rapid", action="store_true")

    p_call = sub.add_parser("call")
    p_call.add_argument("action")
    p_call.add_argument("body_json")

    args = parser.parse_args()
    secret_id, secret_key = load_credentials()

    if args.cmd == "probe":
        result = sign_request(
            "QueryHunyuanTo3DProJob", {"JobId": "probe-invalid-id"},
            secret_id, secret_key, args.site,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.cmd == "call":
        print(json.dumps(unwrap(sign_request(
            args.action, json.loads(args.body_json), secret_id, secret_key, args.site
        )), ensure_ascii=False, indent=2))
    elif args.cmd == "submit":
        print(submit(args, secret_id, secret_key))
    elif args.cmd == "poll":
        print(json.dumps(query(
            args.job_id, args.rapid, args.site, secret_id, secret_key
        ), ensure_ascii=False, indent=2))
    elif args.cmd == "run":
        run(args, secret_id, secret_key)


if __name__ == "__main__":
    main()
