---
name: mm-skill
description: Build interactive 3D visualizations of matrix multiplications with the mm visualizer (github.com/bhosmer/mm) - single matmuls, attention, MLP chains, blocking, and algorithm animations (dotprod, vmprod, mvprod, vvprod). Use when the user asks for a 3D visualization of matmul/attention/transformer computations and the tool is "mm", wants interactive teaching material about matrix multiplication, animated views of matmul algorithms, or 3D visual guidance of tensor-parallel/data-parallel blocking.
---

# mm 3D Matmul Visualizer

Wrap the [mm](https://bhosmer.github.io/mm) visualizer for 3D matmul visualization (e.g. attention, MLP, matmul chains) during guidance/teaching sessions.

mm is a static Three.js web app: you drive it entirely with a **params JSON** applied via **postMessage `setParams`** (deep merge, partials OK; templates apply it on iframe load). It renders left arg / right arg / result on three faces of a 3D cube with animations, blocking, and value magnification.

## Skill layout

`<skill>` = this skill's directory (wherever it is installed, e.g. `~/.claude/skills/mm-skill` or `~/.qoder/skills/mm-skill`):

| Path | Purpose |
| --- | --- |
| `templates/viz-basic.html` | Copy this to create a simple embed page (bilingual UI: zh/en toggle) |
| `templates/viz-interactive.html` | Copy this for a page with a live control panel (bilingual UI) |
| `scripts/serve.py` | Local server: `/mm/*` = offline mm runtime, `/viz/*` = viz pages |
| `scripts/mcp.py` | MCP server (stdio JSON-RPC): embeds the same HTTP service and exposes create/update/list/delete/open viz tools |
| `runtime/mm/` | Vendored offline copy of mm incl. its official manual `ref.html` (the in-app "Reference" link works against it; MIT license) |
| `reference/params-reference.md` | Full params manual (English) - read before hand-authoring complex params |
| `reference/params-reference.zh.md` | Chinese translation of the params manual |
| `reference/upstream-ref.md` | Archived official reference (extracted from ref.html, English; Chinese: `upstream-ref.zh.md`) - use when you need the original wording/examples |
| `SKILL.zh.md` | Chinese translation of this file (human-readable; this file is authoritative) |

Repo-level maintenance script (outside the skill dir): `<repo>/scripts/fetch_mm.py` re-downloads/updates `runtime/mm/`.

## Workflow: create a visualization

Work in the user's project directory (server auto-creates `./.mm-viz` for pages).

1. **Create the page** - copy a template and edit `MM_PARAMS`:
   ```bash
   mkdir -p .mm-viz
   cp "<skill>/templates/viz-basic.html" ".mm-viz/<name>.html"
   ```
   Then edit the `MM_PARAMS` object in the copied file (see "Params cheatsheet").
2. **Start the server automatically** - never ask the user to run it by hand. Reuse a healthy instance if one exists, otherwise start it in the background:
   ```bash
   curl -sf http://127.0.0.1:8019/health >/dev/null 2>&1 || \
     (nohup python "<skill>/scripts/serve.py" >/tmp/mm-skill-serve.log 2>&1 &)
   sleep 1
   cat /tmp/mm-skill-serve.log 2>/dev/null || true   # actual port when newly started (default 8019, auto-increments if busy)
   ```
   The server always serves the viz pages and the offline runtime - online and offline modes both need it running. Viz dir can be overridden: `--viz-dir <path>`.
3. **Hand the URL to the user**: `http://127.0.0.1:<port>/viz/<name>.html` (use the actual port from the server log - default 8019, auto-incremented if busy; the index is listable at `http://127.0.0.1:<port>/`). If the host agent has a preview/link UI, surface it there.
4. **Verify** (recommended): check `http://127.0.0.1:<port>/health` returns `ok`; if a browser tool (Playwright MCP etc.) is available, screenshot the page and confirm the cube renders (a black scene = failure; check console).
5. **Iterate**: edit `MM_PARAMS` + user refreshes, or push live updates (below).

**Online vs offline mm**: templates default to the online build (`https://bhosmer.github.io/mm/index.html`). If the network can't reach GitHub Pages, add `?src=local` to the page URL (or click the toggle) to use the offline copy served at `/mm/index.html`. Offline mode requires `serve.py` running.

## MCP server (optional)

Two transports are available; both expose the same tools:

- **stdio** - `scripts/mcp.py` speaks newline-delimited JSON-RPC over stdio (zero dependencies) and embeds the HTTP server automatically:
  ```json
  { "mcpServers": { "mm-skill": { "command": "python", "args": ["<skill>/scripts/mcp.py"] } } }
  ```
- **Streamable HTTP** - the HTTP server (`serve.py` or mcp.py's embedded server) exposes `POST /mcp` (JSON-RPC over HTTP; `GET /mcp` returns 405, no SSE push):
  ```json
  { "mcpServers": { "mm-skill": { "url": "http://127.0.0.1:8019/mcp" } } }
  ```

Tools: `create_viz` (name, params, template basic|interactive, offline) returns the preview URL; `update_viz`, `get_viz`, `list_vizzes`, `delete_viz`, `open_viz`, `get_server_info`.
- `params` uses the same mm params schema as `MM_PARAMS` (see "Params cheatsheet").
- Defaults: viz dir `./.mm-viz` (`--viz-dir`), HTTP port 8019 (`--port`, auto-increments if busy), offline `?src=local` URLs.

## Driving mm live (postMessage)

From a browser automation tool or the page console, on the viz page:

```js
mmSet({ anim: { alg: 'vvprod', fuse: 'sync' } })      // partial update, merges recursively
mmSet({ expr: 'X = A @ B @ C', sync_expr: true })     // restructure; sync_expr preserves settings by name
mmSet(MM_PARAMS, true)                                 // reset:true -> mm defaults, then re-apply ours
```

Direct iframe form (equals `mmSet`): `document.getElementById('iframe').contentWindow.postMessage({ setParams: { props: {...}, reset: false } }, '*')`.

Other APIs (parent <-> mm): `{getUrlInfo}` -> `{url_info:{url,...}}` (shareable session URL), `{getParams}` -> `{params}`; mm also posts `{search_params}` to the parent whenever the user changes something. **Pause/step are GUI-only** (spacebar) - not settable via postMessage.

## Params cheatsheet (most common fields)

Full manual: `reference/params-reference.md`. Rules:

- `expr`: `"out = (attn = Q @ K) @ V"` - names define matrices; leaves you don't specify get defaults (32x32 gradient). Compound expr + `sync_expr: true`.
- Leaf: `{ h, w, init, url, expr, min, max, dropout }`; `init` in rows / cols / row major / col major / pt linear / uniform / gaussian / tril mask / triu mask / eye / diff / url / expr.
- Matmul node: `{ matmul: true, left, right, epilog, anim, block, layout }`; per-node `anim.alg` (child default `inherit`).
- `anim`: `alg` = none / dotprod (row major) / dotprod (col major) / axpy / vmprod / mvprod / vvprod; plus `speed` 1-100, `fuse` none/sync/async, `spin` -1/0/1, `"hide inputs"`.
- `epilog`: none / relu / gelu / sigmoid / silu / tanh / layernorm / softmax / `softmax(x/sqrt(k))` / `softmax(tril(x/sqrt(k)))` (causal attention).
- `block`: `"i blocks"`, `"k blocks"`, `"j blocks"` (global partitions; i ~ data parallel, j ~ tensor parallel).
- `layout`: `scheme` blocks/zigzag/wheel/custom; spacing `gap`/`scatter`/`molecule`/`blast`; orientation `polarity`, `left placement`, `right placement`, `result placement`.
- `viz.sensitivity`: global/local/semilocal/superlocal (use local for high-variance data).
- Keys with spaces are literal JSON keys, e.g. `"i blocks"`, `"row guides"`, `"hide inputs"`.

## Guidance recipes

| Goal | Params sketch |
| --- | --- |
| Explain plain matmul | `{ "expr": "L @ R" }` + `anim.alg: "vmprod"` then `"vvprod"` to contrast algorithms |
| Attention | `expr: "out = (attn = Q @ K) @ V"`, `epilog` on attn: `softmax(x/sqrt(k))` or causal; anim `vmprod` + `fuse: "sync"` |
| Attention with projections | prepend `(Q = input @ wQ)` etc.; shape k=64, d=768 style dims |
| Data parallelism | left-assoc chain `X = A @ B @ C`, `anim.alg: "vmprod"`, `fuse: "sync"`, `block: {"i blocks": 4}` |
| Low-rank factorization | `expr: "out = x @ (w = wL @ wR)"` |
| Tensor parallelism | same chain with `block: {"j blocks": 4}` / `{"k blocks": 4}` |
| Geometry only (no values) | `deco: { legends: 0, shape: false, "row guides": 0, "flow guides": 0 }`, `viz.sensitivity: "local"` |

For teaching, prefer an editable `expr` plus 1-3 tunable controls (see `templates/viz-interactive.html`) over dozens of knobs.

## Params correctness checklist

Before showing a visualization, confirm:

1. **Mechanism** - params are applied via `setParams` (deep merge, partials OK); URL `?params=` only with a complete params tree (otherwise it throws `Cannot read properties of undefined`).
2. **Structure** - expr changes always carry `sync_expr: true`; names in the expr define the leaves (unlisted leaves get 32x32 defaults).
3. **Shapes** - every matmul must satisfy `left.w == right.h`; in compound exprs set dims on the correct leaf by tree path (`left.left` = Q for `out = (attn = Q @ K) @ V`).
4. **Enums** - alg / epilog / init / sensitivity / scheme / fuse / polarity / placements must exactly match the documented values (copy from the cheatsheet above).
5. **Verify** - after applying, read back with `{getParams}` and screenshot; watch the mm console for `HEY left width ... != right height ...` warnings (shape mismatch).

## Pitfalls

- **Merge semantics differ**: `setParams` merges deeply (partials OK, this is what templates use); URL `?params=` replaces **top-level keys wholesale** - a partial `left: {h:32}` via URL corrupts the tree and throws `Cannot read properties of undefined`. Never init partial params via URL; use setParams on iframe load. Also, the URL `expr` string is derived/regenerated at init - only `setParams` + `sync_expr: true` makes `expr` drive structure.
- **`expr` restructures only with `sync_expr: true`** - without it the expression is regenerated from the current tree and your string is ignored.
- **Leaf shapes in compound exprs are addressed by tree path** (`left.left` = Q when the expr is `out = (attn = Q @ K) @ V`); shapes must satisfy K.h == Q.w and V.h == K.w.
- **External CSV init (`init: "url"`) needs CORS**; local CSVs go in the viz dir and are referenced as `/viz/<file>.csv`.
- **Very long `?params=` URLs** can be truncated by Safari; for huge configs use `?config=<absolute-url-to-json>` instead (must be a full absolute URL - relative paths throw `Invalid URL` and silently fall back to defaults) or reduce dims.
- **Dims 32-128 are smooth**; 256/768-level dims render but are slow - set `cam` and avoid heavy animations at that scale.
- **Deep saturated expressions collide** - bump `layout.scatter`/`gap` or switch `scheme`.
- **The `mm` menu (top-right) is the ground truth** for discovering params; whatever the user sets there lands in the URL and can be pasted back into `MM_PARAMS`.

## Updating the vendored runtime

```bash
python "<repo>/scripts/fetch_mm.py"                          # direct connection (default, no proxy)
python "<repo>/scripts/fetch_mm.py" --proxy http://host:port # via an HTTP proxy
```

`--proxy` can also be set via the `MM_PROXY` env var; `--dest` overrides the target directory (default `<repo>/skills/mm-skill/runtime/mm`).

Human-facing overview: `<repo>/README.md` (Chinese; English: `README.en.md`); Chinese AI instructions: `SKILL.zh.md`.
