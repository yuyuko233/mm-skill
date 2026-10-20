# mm 3D 矩阵乘法可视化器

> 本文件是 [`SKILL.md`](SKILL.md) 的中文翻译，供人工阅读；智能体执行时以英文 `SKILL.md` 为准。
> 通用 skill：遵循 Agent Skills 规范（`SKILL.md` + frontmatter），将本目录放入任意宿主智能体的 skills 目录即可使用，如 `~/.claude/skills/mm-skill`、`~/.qoder/skills/mm-skill`、`~/.agents/skills/mm-skill` 等。

封装 [mm](https://bhosmer.github.io/mm) 可视化器，在讲解/教学会话中进行矩阵乘法的 3D 可视化（如注意力、MLP、矩阵乘链）。

mm 是一个静态 Three.js Web 应用：完全由 **params JSON** 驱动，通过 **postMessage `setParams`** 应用（深度合并、支持部分参数；模板在 iframe 加载时应用）。它把左操作数 / 右操作数 / 结果渲染在 3D 立方体的三个面上，支持动画、分块与数值放大。

## Skill 目录

`<skill>` = 本 skill 所在目录（安装位置任意，如 `~/.claude/skills/mm-skill` 或 `~/.qoder/skills/mm-skill`）：

| 路径 | 用途 |
| --- | --- |
| `templates/viz-basic.html` | 复制它创建简单的嵌入页面（中英双语界面，按钮切换） |
| `templates/viz-interactive.html` | 复制它创建带实时控制面板的页面（中英双语界面） |
| `scripts/serve.py` | 本地服务器：`/mm/*` = 离线 mm 运行时，`/viz/*` = 可视化页面 |
| `scripts/mcp.py` | MCP 服务器（stdio JSON-RPC）：内嵌同一 HTTP 服务，并提供 create/update/list/delete/open 等可视化工具 |
| `runtime/mm/` | mm 离线副本，含官方手册 `ref.html`（应用内 "Reference" 链接可用；MIT 许可） |
| `reference/params-reference.md` | 完整参数手册（英文）——手写复杂参数前先读 |
| `reference/params-reference.zh.md` | 参数手册（中文） |
| `reference/upstream-ref.md` | 存档的官方参考（从 ref.html 提取，英文；中文版 `upstream-ref.zh.md`）——需要原文措辞/示例时使用 |
| `SKILL.zh.md` | 本文件（中文翻译；权威版本为 `SKILL.md`） |

仓库级维护脚本（skill 目录之外）：`<repo>/scripts/fetch_mm.py` 重新下载/更新 `runtime/mm/`。

## 工作流：创建一个可视化

在用户的项目目录中工作（服务器会自动创建 `./.mm-viz` 存放页面）。

1. **创建页面** —— 复制模板并编辑 `MM_PARAMS`：
   ```bash
   mkdir -p .mm-viz
   cp "<skill>/templates/viz-basic.html" ".mm-viz/<name>.html"
   ```
   然后编辑复制文件中 `MM_PARAMS` 对象（见下方"参数速查"）。
2. **自动启动服务器** —— 不要要求用户手动运行。已有健康实例则复用，否则后台启动：
   ```bash
   curl -sf http://127.0.0.1:8019/health >/dev/null 2>&1 || \
     (nohup python "<skill>/scripts/serve.py" >/tmp/mm-skill-serve.log 2>&1 &)
   sleep 1
   cat /tmp/mm-skill-serve.log 2>/dev/null || true   # 新启动时显示实际端口（默认 8019，被占用时自动递增）
   ```
   服务器同时**提供可视化页面与离线运行时**——线上/离线两种模式都需要它运行。可视化目录可覆盖：`--viz-dir <path>`。
3. **把 URL 交给用户**：`http://127.0.0.1:<port>/viz/<name>.html`（使用服务器日志中的实际端口——默认 8019，被占用时自动递增；汇总页 `http://127.0.0.1:<port>/`）。若宿主智能体提供预览/链接界面，可通过它展示。
4. **验证**（推荐）：检查 `http://127.0.0.1:<port>/health` 返回 `ok`；若有浏览器工具（Playwright MCP 等），截图确认立方体渲染正常（黑屏 = 失败；检查 console）。
5. **迭代**：编辑 `MM_PARAMS` 让用户刷新，或推送实时更新（见下）。

**线上 vs 离线 mm**：模板默认使用线上构建（`https://bhosmer.github.io/mm/index.html`）。如果网络无法访问 GitHub Pages，在页面 URL 上加 `?src=local`（或点击切换按钮）使用 `/mm/index.html` 提供的离线副本。离线模式需要 `serve.py` 运行。

## MCP 服务器（可选）

提供两种传输方式，暴露同一套工具：

- **stdio** —— `scripts/mcp.py` 通过 stdio 提供按行分隔的 JSON-RPC（零依赖），并自动内嵌 HTTP 服务器：
  ```json
  { "mcpServers": { "mm-skill": { "command": "python", "args": ["<skill>/scripts/mcp.py"] } } }
  ```
- **Streamable HTTP** —— HTTP 服务器（`serve.py` 或 mcp.py 内嵌的服务）暴露 `POST /mcp` 端点（JSON-RPC over HTTP；`GET /mcp` 返回 405，不提供 SSE 推送）：
  ```json
  { "mcpServers": { "mm-skill": { "url": "http://127.0.0.1:8019/mcp" } } }
  ```

工具：`create_viz`（name、params、template basic|interactive、offline）返回预览 URL；`update_viz`、`get_viz`、`list_vizzes`、`delete_viz`、`open_viz`、`get_server_info`。
- `params` 与 `MM_PARAMS` 使用同一套 mm 参数 schema（见下方"参数速查"）。
- 默认值：可视化目录 `./.mm-viz`（`--viz-dir`）、HTTP 端口 8019（`--port`，被占用时自动递增）、离线 `?src=local` URL。

## 实时驱动 mm（postMessage）

在浏览器自动化工具或页面 console 中，对 viz 页面：

```js
mmSet({ anim: { alg: 'vvprod', fuse: 'sync' } })      // 部分更新，递归合并
mmSet({ expr: 'X = A @ B @ C', sync_expr: true })     // 重建结构；sync_expr 按名字保留设置
mmSet(MM_PARAMS, true)                                 // reset:true -> mm 默认值，再重新应用我们的参数
```

直接 iframe 形式（等价于 `mmSet`）：`document.getElementById('iframe').contentWindow.postMessage({ setParams: { props: {...}, reset: false } }, '*')`。

其他 API（父 <-> mm）：`{getUrlInfo}` -> `{url_info:{url,...}}`（可分享会话 URL），`{getParams}` -> `{params}`；用户改动时 mm 还会向父页面 postMessage `{search_params}`。**暂停/单步只能通过 GUI**（空格键）——postMessage 无法设置。

## 参数速查（常用字段）

完整手册：`reference/params-reference.md`（中文版：`params-reference.zh.md`）。规则：

- `expr`：`"out = (attn = Q @ K) @ V"` —— 名字定义矩阵；未指定的叶子使用默认值（32x32 渐变）。复合表达式需 `sync_expr: true`。
- 叶子：`{ h, w, init, url, expr, min, max, dropout }`；`init` 取 rows / cols / row major / col major / pt linear / uniform / gaussian / tril mask / triu mask / eye / diff / url / expr。
- 矩阵乘节点：`{ matmul: true, left, right, epilog, anim, block, layout }`；每个节点的 `anim.alg`（子节点默认 `inherit`）。
- `anim`：`alg` = none / dotprod (row major) / dotprod (col major) / axpy / vmprod / mvprod / vvprod；另有 `speed` 1-100、`fuse` none/sync/async、`spin` -1/0/1、`"hide inputs"`。
- `epilog`：none / relu / gelu / sigmoid / silu / tanh / layernorm / softmax / `softmax(x/sqrt(k))` / `softmax(tril(x/sqrt(k)))`（因果注意力）。
- `block`：`"i blocks"`、`"k blocks"`、`"j blocks"`（全局分区；i ~ 数据并行，j ~ 张量并行）。
- `layout`：`scheme` blocks/zigzag/wheel/custom；间距 `gap`/`scatter`/`molecule`/`blast`；朝向 `polarity`、`left placement`、`right placement`、`result placement`。
- `viz.sensitivity`：global/local/semilocal/superlocal（高方差数据用 local）。
- 带空格的键就是字面 JSON 键，如 `"i blocks"`、`"row guides"`、`"hide inputs"`。

## 讲解配方

| 目标 | 参数草图 |
| --- | --- |
| 讲解普通矩阵乘 | `{ "expr": "L @ R" }` + `anim.alg: "vmprod"` 然后 `"vvprod"` 对比算法 |
| 注意力 | `expr: "out = (attn = Q @ K) @ V"`，attn 的 `epilog`: `softmax(x/sqrt(k))` 或因果版；anim `vmprod` + `fuse: "sync"` |
| 带投影的注意力 | 前置 `(Q = input @ wQ)` 等；k=64, d=768 风格维度 |
| 数据并行 | 左结合链 `X = A @ B @ C`、`anim.alg: "vmprod"`、`fuse: "sync"`、`block: {"i blocks": 4}` |
| 低秩分解 | `expr: "out = x @ (w = wL @ wR)"` |
| 张量并行 | 同链 + `block: {"j blocks": 4}` / `{"k blocks": 4}` |
| 只看几何（无值） | `deco: { legends: 0, shape: false, "row guides": 0, "flow guides": 0 }`、`viz.sensitivity: "local"` |

教学用途下，优先使用可编辑的 `expr` 加 1-3 个可调控件（见 `templates/viz-interactive.html`），而不是堆砌几十个旋钮。

## 参数正确性检查清单

展示可视化前确认：

1. **机制** —— 参数通过 `setParams` 应用（深度合并、部分参数 OK）；URL `?params=` 仅在完整参数树时使用（否则会抛 `Cannot read properties of undefined`）。
2. **结构** —— expr 变更始终带 `sync_expr: true`；expr 中的名字定义叶子（未列出的叶子获得 32x32 默认值）。
3. **形状** —— 每个矩阵乘必须满足 `left.w == right.h`；复合表达式中按树路径设置正确的叶子维度（`left.left` = Q，当 expr 为 `out = (attn = Q @ K) @ V`）。
4. **枚举** —— alg / epilog / init / sensitivity / scheme / fuse / polarity / placements 必须与文档值完全一致（从上方速查表复制）。
5. **验证** —— 应用后用 `{getParams}` 回读并截图；留意 mm console 的 `HEY left width ... != right height ...` 警告（形状不匹配）。

## 坑与注意事项

- **合并语义不同**：`setParams` 深度合并（部分参数 OK，模板用法）；URL `?params=` **顶层键整体替换** —— 部分 `left: {h:32}` 经 URL 会破坏树并抛 `Cannot read properties of undefined`。永远不要用 URL 初始化部分参数；在 iframe load 时用 setParams。另外，URL 的 `expr` 字符串是初始化时派生/重新生成的 —— 只有 `setParams` + `sync_expr: true` 才能让 `expr` 驱动结构。
- **`expr` 仅在 `sync_expr: true` 时重建结构** —— 否则表达式从当前树重新生成，你的字符串被忽略。
- **复合表达式中的叶子形状按树路径定位**（`left.left` = Q，当 expr 为 `out = (attn = Q @ K) @ V`）；形状须满足 K.h == Q.w、V.h == K.w。
- **外部 CSV 初始化（`init: "url"`）需要 CORS**；本地 CSV 放在 viz 目录并引用为 `/viz/<file>.csv`。
- **超长 `?params=` URL** 会被 Safari 截断；超大配置改用 `?config=<绝对URL>`（必须是完整绝对地址 —— 相对路径会抛 `Invalid URL` 并静默回退默认值），或减小维度。
- **维度 32-128 流畅**；256/768 级可以渲染但很慢 —— 设置 `cam` 并避免该规模下的重动画。
- **深度饱和表达式会碰撞** —— 调大 `layout.scatter`/`gap` 或切换 `scheme`。
- **右上角 `mm` 菜单是参数的 ground truth**；用户在菜单里的设置都会写进 URL，可复制回 `MM_PARAMS`。

## 更新离线运行时

```bash
python "<repo>/scripts/fetch_mm.py"                          # 直连（默认，无代理）
python "<repo>/scripts/fetch_mm.py" --proxy http://host:port # 经 HTTP 代理
```

`--proxy` 也可通过 `MM_PROXY` 环境变量设置；`--dest` 覆盖目标目录（默认 `<repo>/skills/mm-skill/runtime/mm`）。

面向人的概览：`<repo>/README.md`（中文，英文版 `README.en.md`）；中文 AI 说明：本文件。
