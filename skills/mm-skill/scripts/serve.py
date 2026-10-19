#!/usr/bin/env python3
"""
Local static server for mm-skill.

Serves two roots on one port so visualization pages can be previewed locally:
  /mm/*   -> <skill>/runtime/mm/       (offline copy of the mm visualizer)
  /viz/*  -> <viz-dir>/*               (visualization pages, default: ./.mm-viz)
  /       -> generated index listing all viz pages

Usage:
  python serve.py                          # serve from cwd, default port 8019
  python serve.py --viz-dir D:\\work\\vizzes
  python serve.py --port 8020
  python serve.py --host 0.0.0.0           # accessible from other devices

Run it in the background while previewing, e.g.:
  python serve.py   ->   open http://127.0.0.1:8019/viz/<page>.html
"""

import argparse
import html
import socket
import sys
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
MM_ROOT = SKILL_DIR / "runtime" / "mm"

DEFAULT_PORT = 8019
PREFIX_MM = "/mm/"
PREFIX_VIZ = "/viz/"


def make_handler(viz_dir: Path):
    class Handler(SimpleHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        # --- routing -----------------------------------------------------
        def translate_path(self, path: str) -> str:
            clean = urllib.parse.unquote(path.split("?")[0].split("#")[0])
            if clean.startswith(PREFIX_MM):
                return self._safe_join(MM_ROOT, clean[len(PREFIX_MM):])
            if clean.startswith(PREFIX_VIZ):
                return self._safe_join(viz_dir, clean[len(PREFIX_VIZ):])
            return str(SKILL_DIR / "__not_found__")  # non-existent path

        @staticmethod
        def _safe_join(root: Path, rel: str) -> str:
            parts = [p for p in rel.split("/") if p and p not in (".", "..")]
            return str(root.joinpath(*parts))

        def do_GET(self):
            clean = urllib.parse.unquote(self.path.split("?")[0].split("#")[0])
            if clean == "/health":
                return self._send_text(200, "ok")
            if clean in ("/", "/index.html"):
                return self._send_listing()
            if clean == "/viz" or clean == PREFIX_VIZ.rstrip("/"):
                self.send_response(301)
                self.send_header("Location", PREFIX_VIZ)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return super().do_GET()

        # --- helpers -----------------------------------------------------
        def _send_text(self, code: int, text: str, ctype="text/plain; charset=utf-8"):
            body = text.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def _send_listing(self):
            pages = sorted(p.name for p in viz_dir.glob("*.html")) if viz_dir.is_dir() else []
            items = "\n".join(
                f'<li><a href="{PREFIX_VIZ}{html.escape(n)}">{html.escape(n)}</a>'
                f' &nbsp;<a class="raw" href="{PREFIX_VIZ}{html.escape(n)}" target="_blank" data-i18n="open">↗ 新窗口</a></li>'
                for n in pages
            ) or '<li class="empty" data-i18n="noPages"></li>'
            body = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>mm-skill local server</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif; margin: 2rem auto; max-width: 720px; background: #111; color: #eee; }}
  a {{ color: #7ab8ff; }} a.raw {{ color: #888; font-size: 0.85em; }}
  code {{ background: #222; padding: 2px 6px; border-radius: 4px; }}
  li {{ margin: 6px 0; }} li.empty {{ color: #888; }}
  h1 {{ font-size: 1.3rem; }} h2 {{ font-size: 1rem; margin-top: 1.6rem; }}
  #lang-toggle {{ position: fixed; top: 1.2rem; right: 1.6rem; background: #222; color: #eee;
    border: 1px solid #444; border-radius: 6px; padding: 4px 10px; cursor: pointer; min-width: 52px; }}
  #lang-toggle:hover {{ background: #2c2c2c; }}
</style></head><body>
<button id="lang-toggle"></button>
<h1 data-i18n="h1"></h1>
<h2><span data-i18n="vizPages"></span> ({PREFIX_VIZ})</h2><ul>{items}</ul>
<h2 data-i18n="visualizer"></h2>
<p><a href="{PREFIX_MM}index.html">/mm/index.html</a> — <span data-i18n="mmDesc"></span></p>
<h2 data-i18n="notes"></h2>
<ul>
  <li><span data-i18n="vizDir"></span>: <code>{html.escape(str(viz_dir))}</code></li>
  <li><span data-i18n="online"></span>: <a href="https://bhosmer.github.io/mm/index.html">https://bhosmer.github.io/mm/index.html</a></li>
</ul>
<script>
  const I18N = {{
    zh: {{
      pageTitle: 'mm-skill · 本地预览服务器',
      h1: 'mm-skill · 本地预览服务器',
      vizPages: '可视化页面',
      noPages: '（暂无可视化页面）',
      open: '↗ 新窗口',
      visualizer: 'mm 可视化器',
      mmDesc: '离线副本（params 通过 URL 传递）',
      notes: '说明',
      vizDir: '页面目录',
      online: '在线版',
      langTitle: 'Switch to English / 切换到英文',
    }},
    en: {{
      pageTitle: 'mm-skill · local preview server',
      h1: 'mm-skill · local preview server',
      vizPages: 'Viz pages',
      noPages: '(no viz pages yet)',
      open: '↗ Open',
      visualizer: 'mm visualizer',
      mmDesc: 'offline copy (params via URL)',
      notes: 'Notes',
      vizDir: 'viz dir',
      online: 'online version',
      langTitle: '切换为中文 / switch to Chinese',
    }},
  }}
  let lang = (() => {{
    try {{
      const saved = localStorage.getItem('mm-skill-lang')
      if (saved === 'zh' || saved === 'en') return saved
    }} catch (e) {{}}
    return (navigator.language || '').toLowerCase().startsWith('zh') ? 'zh' : 'en'
  }})()
  const t = k => (I18N[lang] && I18N[lang][k]) || k
  function applyLang() {{
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en'
    document.title = t('pageTitle')
    document.querySelectorAll('[data-i18n]').forEach(el => {{ el.textContent = t(el.dataset.i18n) }})
    const btn = document.getElementById('lang-toggle')
    btn.textContent = lang === 'zh' ? 'EN' : '中文'
    btn.title = t('langTitle')
  }}
  document.getElementById('lang-toggle').onclick = () => {{
    lang = lang === 'zh' ? 'en' : 'zh'
    try {{ localStorage.setItem('mm-skill-lang', lang) }} catch (e) {{}}
    applyLang()
  }}
  applyLang()
</script>
</body></html>"""
            self._send_text(200, body, "text/html; charset=utf-8")

        # quieter, single-line logging
        def log_message(self, fmt, *args):
            sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))

        def end_headers(self):
            if self.path.startswith(PREFIX_MM) or self.path.startswith(PREFIX_VIZ):
                self.send_header("Cache-Control", "no-store")
            super().end_headers()

    return Handler


def main():
    parser = argparse.ArgumentParser(description="Serve mm runtime + viz pages locally")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--viz-dir", default=None, help="directory with viz pages (default: ./.mm-viz)")
    parser.add_argument("--quiet", action="store_true", help="suppress request logging")
    args = parser.parse_args()

    # 输出重定向到日志时也立即刷出 URL，便于调用方读取实际端口
    # Flush lines even when stdout is redirected to a log file (callers parse the URL)
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass

    if not (MM_ROOT / "index.html").is_file():
        print(f"ERROR: mm runtime not found at {MM_ROOT}")
        print("Run fetch_mm.py first:  python fetch_mm.py")
        return 1

    viz_dir = Path(args.viz_dir).resolve() if args.viz_dir else (Path.cwd() / ".mm-viz")
    viz_dir.mkdir(parents=True, exist_ok=True)

    # find a free port
    port = args.port
    for p in range(args.port, args.port + 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((args.host, p))
                port = p
                break
            except OSError:
                continue
    else:
        print(f"ERROR: no free port in range {args.port}-{args.port + 9}")
        return 1

    handler = make_handler(viz_dir)
    if args.quiet:
        handler.log_message = lambda *a, **k: None

    httpd = ThreadingHTTPServer((args.host, port), handler)
    base = f"http://{args.host if args.host != '0.0.0.0' else '127.0.0.1'}:{port}"
    pages = sorted(p.name for p in viz_dir.glob("*.html"))

    print("mm-skill server")
    print(f"  index      : {base}/")
    print(f"  mm runtime : {base}{PREFIX_MM}index.html")
    print(f"  viz dir    : {viz_dir}  ->  {base}{PREFIX_VIZ}")
    if pages:
        for n in pages:
            print(f"    page     : {base}{PREFIX_VIZ}{n}")
    else:
        print("    (no viz pages yet - create one and refresh the index)")
    print("Ctrl+C to stop.  按 Ctrl+C 停止")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
