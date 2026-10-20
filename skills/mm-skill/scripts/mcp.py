#!/usr/bin/env python3
"""
MCP (Model Context Protocol) server for mm-skill.

Exposes the mm 3D matmul visualizer as MCP tools over stdio, and serves the
visualization pages from an embedded HTTP server (reusing serve.py's routing):

  /mm/*   -> <skill>/runtime/mm/   (offline vendored mm build)
  /viz/*  -> <viz-dir>/*           (generated visualization pages)
  /       -> index listing all pages

Tools:
  create_viz       create a viz page from an mm params JSON, return its URL
  update_viz       replace the MM_PARAMS of an existing page
  get_viz          read the MM_PARAMS embedded in a page
  list_vizzes      list pages with preview URLs
  delete_viz       delete a page
  open_viz         open a page in the default browser
  get_server_info  server URL / port / viz dir

Zero dependencies: newline-delimited JSON-RPC 2.0 over stdio + http.server.

Usage:
  python mcp.py [--port 8019] [--viz-dir <dir>] [--quiet]

Client config (Claude Desktop / Qoder / any MCP client):
  {
    "mcpServers": {
      "mm-skill": { "command": "python", "args": ["<skill>/scripts/mcp.py"] }
    }
  }

stdout carries only JSON-RPC messages; all logs go to stderr.
"""

import argparse
import json
import re
import sys
import threading
import webbrowser
from http.server import ThreadingHTTPServer
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATES = {
    "basic": SKILL_DIR / "templates" / "viz-basic.html",
    "interactive": SKILL_DIR / "templates" / "viz-interactive.html",
}

SERVER_NAME = "mm-skill"
SERVER_VERSION = "1.0.0"
DEFAULT_PROTOCOL = "2024-11-05"
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def log(msg: str):
    print(f"[mm-skill-mcp] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# embedded HTTP server (reuses serve.py routing)
# ---------------------------------------------------------------------------

def start_http(viz_dir: Path, preferred_port: int, quiet: bool):
    from serve import make_handler  # same directory; lazy import keeps --help fast

    handler = make_handler(viz_dir)
    if quiet:
        handler.log_message = lambda *a, **k: None
    last_error = None
    for port in range(preferred_port, preferred_port + 20):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
        except OSError as e:
            last_error = e
            continue
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        return httpd, port
    raise RuntimeError(f"no free port in {preferred_port}..{preferred_port + 19}: {last_error}")


# ---------------------------------------------------------------------------
# page helpers (MM_PARAMS block in the templates)
# ---------------------------------------------------------------------------

def find_matching_brace(s: str, start: int) -> int:
    """Return the index of the '}' matching the '{' at s[start] (quote-aware)."""
    depth = 0
    quote = None
    i = start
    while i < len(s):
        c = s[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in ("'", '"'):
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced braces in MM_PARAMS block")


def locate_mm_params(html: str):
    marker = "const MM_PARAMS ="
    i = html.find(marker)
    if i < 0:
        raise ValueError("MM_PARAMS block not found in template")
    start = html.index("{", i + len(marker))
    end = find_matching_brace(html, start)
    return i, start, end


def replace_mm_params(html: str, params: dict) -> str:
    i, _start, end = locate_mm_params(html)
    block = "const MM_PARAMS = " + json.dumps(params, ensure_ascii=False, indent=2)
    return html[:i] + block + html[end + 1:]


def extract_mm_params(html: str):
    _i, start, end = locate_mm_params(html)
    raw = html[start:end + 1]
    try:
        return json.loads(raw), raw
    except json.JSONDecodeError:
        return None, raw


def page_path(viz_dir: Path, name) -> Path:
    if not isinstance(name, str) or not SAFE_NAME.match(name):
        raise ValueError(
            "invalid page name: use letters, digits, '.', '-', '_' (e.g. 'causal-attention')")
    if not name.endswith(".html"):
        name += ".html"
    return viz_dir / name


# ---------------------------------------------------------------------------
# tool implementations
# ---------------------------------------------------------------------------

class ToolBox:
    def __init__(self, viz_dir: Path, port: int):
        self.viz_dir = viz_dir
        self.port = port
        self.base = f"http://127.0.0.1:{port}"

    def _url(self, path: Path, offline: bool) -> str:
        url = f"{self.base}/viz/{path.name}"
        return url + "?src=local" if offline else url

    # -- create ------------------------------------------------------------
    def create_viz(self, args):
        template = args.get("template", "interactive")
        if template not in TEMPLATES:
            raise ValueError(f"unknown template '{template}' (basic | interactive)")
        offline = bool(args.get("offline", True))
        params = args.get("params")
        html = TEMPLATES[template].read_text(encoding="utf-8")
        if params is not None:
            if not isinstance(params, dict):
                raise ValueError("params must be a JSON object")
            html = replace_mm_params(html, params)
        path = page_path(self.viz_dir, args.get("name"))
        self.viz_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        return {
            "name": path.stem,
            "path": str(path),
            "url": self._url(path, offline),
            "template": template,
            "offline": offline,
            "note": "params are applied via postMessage setParams; use sync_expr:true with expr",
        }

    # -- update ------------------------------------------------------------
    def update_viz(self, args):
        params = args.get("params")
        if not isinstance(params, dict):
            raise ValueError("params must be a JSON object")
        offline = bool(args.get("offline", True))
        path = page_path(self.viz_dir, args.get("name"))
        if not path.is_file():
            raise ValueError(f"page not found: {path.name}")
        html = replace_mm_params(path.read_text(encoding="utf-8"), params)
        path.write_text(html, encoding="utf-8")
        return {"name": path.stem, "path": str(path), "url": self._url(path, offline)}

    # -- read --------------------------------------------------------------
    def get_viz(self, args):
        path = page_path(self.viz_dir, args.get("name"))
        if not path.is_file():
            raise ValueError(f"page not found: {path.name}")
        params, raw = extract_mm_params(path.read_text(encoding="utf-8"))
        out = {"name": path.stem, "path": str(path), "url": self._url(path, True)}
        if params is not None:
            out["params"] = params
        else:
            out["raw"] = raw
            out["note"] = "MM_PARAMS is not strict JSON (hand-edited JS literal?)"
        return out

    # -- list --------------------------------------------------------------
    def list_vizzes(self, args):
        pages = sorted(self.viz_dir.glob("*.html")) if self.viz_dir.is_dir() else []
        return {
            "viz_dir": str(self.viz_dir),
            "pages": [{"name": p.stem, "url": self._url(p, True)} for p in pages],
        }

    # -- delete ------------------------------------------------------------
    def delete_viz(self, args):
        path = page_path(self.viz_dir, args.get("name"))
        if not path.is_file():
            raise ValueError(f"page not found: {path.name}")
        path.unlink()
        return {"deleted": path.stem}

    # -- open in browser ---------------------------------------------------
    def open_viz(self, args):
        path = page_path(self.viz_dir, args.get("name"))
        if not path.is_file():
            raise ValueError(f"page not found: {path.name}")
        url = self._url(path, True)
        opened = webbrowser.open(url)  # may be a no-op on headless machines
        return {"opened": bool(opened), "url": url}

    # -- server info -------------------------------------------------------
    def get_server_info(self, args):
        pages = list(self.viz_dir.glob("*.html")) if self.viz_dir.is_dir() else []
        return {
            "base_url": self.base,
            "port": self.port,
            "viz_dir": str(self.viz_dir),
            "templates": sorted(TEMPLATES),
            "pages": len(pages),
            "endpoints": {
                "index": f"{self.base}/",
                "mm_offline": f"{self.base}/mm/index.html",
                "mm_reference": f"{self.base}/mm/ref.html",
                "health": f"{self.base}/health",
            },
        }


TOOL_METHODS = {
    "create_viz", "update_viz", "get_viz",
    "list_vizzes", "delete_viz", "open_viz", "get_server_info",
}


def dispatch(box: ToolBox, name, arguments):
    if name not in TOOL_METHODS:
        raise ValueError(f"unknown tool: {name}")
    return getattr(box, name)(arguments or {})


def tool_defs():
    return [
        {
            "name": "create_viz",
            "description": (
                "Create a 3D matmul visualization page from an mm params JSON and return its preview URL. "
                "mm renders matmuls as interactive 3D cubes (attention, MLP chains, blocking). "
                "params follows the mm params schema: {expr, sync_expr, anim:{alg,fuse,speed}, "
                "block:{'i blocks','k blocks','j blocks'}, epilog, left/right, layout, deco, viz}. "
                "Example: {\"expr\": \"out = (attn = Q @ K) @ V\", \"sync_expr\": true, "
                "\"anim\": {\"alg\": \"vmprod\", \"fuse\": \"sync\"}}"
            ),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Page name: letters, digits, '.', '-', '_' (e.g. 'causal-attention')",
                    },
                    "params": {
                        "type": "object",
                        "description": "mm MM_PARAMS JSON object (optional; defaults to the template's attention example)",
                    },
                    "template": {
                        "type": "string",
                        "enum": ["basic", "interactive"],
                        "description": "Page template: basic (embed only) or interactive (live control panel). Default: interactive",
                    },
                    "offline": {
                        "type": "boolean",
                        "description": "Use the offline vendored mm build (?src=local). Default: true",
                    },
                },
                "required": ["name"],
            },
        },
        {
            "name": "update_viz",
            "description": "Replace the MM_PARAMS of an existing visualization page (same params schema as create_viz).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Existing page name"},
                    "params": {"type": "object", "description": "New mm MM_PARAMS JSON object"},
                    "offline": {"type": "boolean", "description": "Return URL with ?src=local. Default: true"},
                },
                "required": ["name", "params"],
            },
        },
        {
            "name": "get_viz",
            "description": "Read the MM_PARAMS JSON embedded in a visualization page, plus its preview URL.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Page name"}},
                "required": ["name"],
            },
        },
        {
            "name": "list_vizzes",
            "description": "List all visualization pages with their preview URLs.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "delete_viz",
            "description": "Delete a visualization page.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Page name"}},
                "required": ["name"],
            },
        },
        {
            "name": "open_viz",
            "description": "Open a visualization page in the user's default browser.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string", "description": "Page name"}},
                "required": ["name"],
            },
        },
        {
            "name": "get_server_info",
            "description": "Return the embedded HTTP server URL, port, viz directory and endpoint list.",
            "inputSchema": {"type": "object", "properties": {}},
        },
    ]


# ---------------------------------------------------------------------------
# JSON-RPC message processing (shared by the stdio server below and the
# Streamable HTTP endpoint in serve.py: POST /mcp)
# ---------------------------------------------------------------------------

def process_message(box: ToolBox, msg):
    """Handle one JSON-RPC message.

    Returns the response object to send back, or None when no response is
    required (notifications).
    """
    if not isinstance(msg, dict):
        return {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32600, "message": "invalid request"}}

    mid = msg.get("id")
    method = msg.get("method")
    is_notification = "id" not in msg

    if method == "initialize":
        params = msg.get("params") or {}
        version = params.get("protocolVersion") or DEFAULT_PROTOCOL
        return {
            "jsonrpc": "2.0", "id": mid,
            "result": {
                "protocolVersion": version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": tool_defs()}}
    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        try:
            result = dispatch(box, name, params.get("arguments"))
            return {
                "jsonrpc": "2.0", "id": mid,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}],
                    "isError": False,
                },
            }
        except Exception as e:  # noqa: BLE001 - tool errors are reported in-band
            return {
                "jsonrpc": "2.0", "id": mid,
                "result": {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True},
            }
    if is_notification:
        return None  # unknown notifications are ignored (protocol courtesy)
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


# ---------------------------------------------------------------------------
# stdio transport
# ---------------------------------------------------------------------------

class MCPServer:
    def __init__(self, box: ToolBox):
        self.box = box

    def send(self, obj):
        sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    def error(self, mid, code, message):
        self.send({"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}})

    def handle(self, msg):
        resp = process_message(self.box, msg)
        if resp is not None:
            self.send(resp)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="MCP server for mm-skill (stdio + embedded HTTP)")
    parser.add_argument("--port", type=int, default=8019, help="preferred HTTP port (default: 8019)")
    parser.add_argument("--viz-dir", default=None, help="directory for viz pages (default: ./.mm-viz)")
    parser.add_argument("--quiet", action="store_true", help="suppress HTTP request logging")
    args = parser.parse_args()

    viz_dir = Path(args.viz_dir).resolve() if args.viz_dir else (Path.cwd() / ".mm-viz")
    viz_dir.mkdir(parents=True, exist_ok=True)

    try:
        _httpd, port = start_http(viz_dir, args.port, args.quiet)
    except Exception as e:  # noqa: BLE001 - fatal for the whole server
        log(f"ERROR: failed to start embedded HTTP server: {e}")
        return 1

    log(f"embedded HTTP server on http://127.0.0.1:{port} (viz dir: {viz_dir})")
    server = MCPServer(ToolBox(viz_dir, port))

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            server.error(None, -32700, f"parse error: {e}")
            continue
        server.handle(msg)

    log("stdin closed, exiting")
    return 0


if __name__ == "__main__":
    sys.exit(main())
