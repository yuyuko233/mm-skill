#!/usr/bin/env python3
"""
Fetch the "mm" 3D matmul visualizer (https://github.com/bhosmer/mm) into the
skill's runtime directory so visualizations can be previewed fully offline.

Downloads only the files required to run mm (index.html + JS + libs + assets).

Usage:
  python fetch_mm.py                          # direct connection (default, no proxy)
  python fetch_mm.py --proxy http://host:port # route through an HTTP proxy
  python fetch_mm.py --dest <dir> --ref main  # custom destination / git ref

The proxy can also be set via the MM_PROXY environment variable.
"""

import argparse
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = "bhosmer/mm"

# Minimal file set required to run mm (verified against index.html / viz.js /
# util.js / gui.js import graph - see reference/params-reference.md).
FILES = [
    "index.html",
    "ref.html",
    "viz.js",
    "util.js",
    "gui.js",
    "lib/es-module-shims.js",
    "lib/three.module.js",
    "lib/jsm/controls/OrbitControls.js",
    "lib/jsm/loaders/FontLoader.js",
    "lib/lil-gui.js",
    "assets/ball.png",
    "assets/droid_sans_regular.typeface.js",
    "LICENSE",
    "README.md",
]

DEFAULT_PROXY = os.environ.get("MM_PROXY", "")


def build_opener(proxy: str | None):
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    else:
        handlers.append(urllib.request.ProxyHandler({}))  # disable env proxies too
    return urllib.request.build_opener(*handlers)


def fetch_one(opener, url: str, dest: Path, retries: int = 3):
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mm-skill"})
            with opener.open(req, timeout=60) as resp:
                data = resp.read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return len(data)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == retries:
                raise
            print(f"    retry {attempt}/{retries - 1} after error: {e}")
            time.sleep(2 * attempt)


def main():
    parser = argparse.ArgumentParser(description="Fetch mm runtime files for offline use")
    parser.add_argument("--dest", default=None, help="destination directory (default: <repo>/skills/mm-skill/runtime/mm)")
    parser.add_argument("--ref", default="master", help="git ref to fetch (default: master)")
    parser.add_argument("--proxy", default=DEFAULT_PROXY, help="HTTP proxy, e.g. http://host:port (default: none, or $MM_PROXY)")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_dir = script_dir.parent
    dest = Path(args.dest) if args.dest else repo_dir / "skills" / "mm-skill" / "runtime" / "mm"
    proxy = args.proxy or None

    print(f"mm-skill fetch")
    print(f"  repo : https://github.com/{REPO} (ref: {args.ref})")
    print(f"  dest : {dest}")
    print(f"  proxy: {proxy if proxy else '(none)'}")
    print()

    opener = build_opener(proxy)
    base = f"https://raw.githubusercontent.com/{REPO}/{args.ref}/"

    total = 0
    failed = []
    for rel in FILES:
        url = base + rel
        target = dest / rel
        try:
            n = fetch_one(opener, url, target)
            total += n
            print(f"  ok   {rel:48s} {n:>9,} bytes")
        except Exception as e:  # noqa: BLE001 - report and continue
            failed.append(rel)
            print(f"  FAIL {rel:48s} {e}")

    print()
    print(f"fetched {len(FILES) - len(failed)}/{len(FILES)} files, {total:,} bytes total")
    if failed:
        print("failed files: " + ", ".join(failed))
        print("hint: check network connectivity; if you are behind a proxy, pass --proxy <url> or set MM_PROXY")
        return 1

    (dest / "VERSION.txt").write_text(
        f"source: https://github.com/{REPO}\n"
        f"ref: {args.ref}\n"
        f"fetched (UTC): {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())}\n"
        f"license: MIT (see LICENSE) - Copyright (c) Meta Platforms, Inc. and affiliates.\n",
        encoding="utf-8",
    )
    print(f"done -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
