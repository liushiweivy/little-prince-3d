# -*- coding: utf-8 -*-
"""本地开发静态服务器：比 python -m http.server 多了 no-store 头。

ES module 在 http.server 下会被 Chrome 启发式缓存（同 URL 改文件不 revalidate，
只刷页面会拿到旧模块），开发时一律起这个。
用法：python tools/dev_server.py [port] [web根目录，默认 web]
"""
import http.server
import os
import sys
import functools


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8850
    root = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
    handler = functools.partial(NoCacheHandler, directory=root)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"serving {root} at http://127.0.0.1:{port} (no-store)")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
