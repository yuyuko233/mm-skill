# mm-skill

**中文** | [English](README.en.md)

> **注意: 本项目代码均为 AI 生成, 未经人工精细审核 !**

[mm](https://bhosmer.github.io/mm)（`github.com/bhosmer/mm`）是一个把矩阵乘法、注意力、MLP 链渲染成 3D 立方体的交互式可视化工具。本 skill 把它封装成开箱可用的能力：**AI 可以用它生成/驱动 3D 可视化页面，用于讲解 Transformer、并行策略、矩阵乘法算法等。**

## 目录结构

仓库根目录存放项目说明与维护脚本，skill 本体位于 `skills/mm-skill/`；安装时将该目录放入所用智能体的 skills 目录即可（如 `~/.claude/skills/`、`~/.qoder/skills/`、`~/.agents/skills/`，或项目内的对应技能目录）。

```text
mm-3d-viz-skill/
├── README.md                 # 中文（本文件）
├── README.en.md              # English
├── scripts/
│   └── fetch_mm.py
└── skills/
    └── mm-skill/
        ├── SKILL.md
        ├── SKILL.zh.md
        ├── reference/
        │   ├── params-reference.md
        │   ├── params-reference.zh.md
        │   ├── upstream-ref.md
        │   └── upstream-ref.zh.md
        ├── scripts/
        │   ├── mcp.py
        │   └── serve.py
        ├── templates/
        │   ├── viz-basic.html
        │   └── viz-interactive.html
        └── runtime/
            └── mm/
```

> 内置文档：`SKILL.md`（AI 使用说明，英文默认）与 `SKILL.zh.md`（中文翻译）；`reference/params-reference.md`（英文参数手册，含全部参数枚举、默认值与正确传参规则）与 `reference/params-reference.zh.md`（中文版）；`reference/upstream-ref.md`（从官方 ref.html 提取的英文原文存档）与 `reference/upstream-ref.zh.md`（中文翻译）。
>
> 离线副本内含官方交互手册 `ref.html`：在 `/mm/index.html` 界面点左上角 **Reference** 即可打开（渲染需联网加载 CDN 组件，正文已随页面内置）。

## 快速开始

对 AI 说："用 mm 做一个**因果注意力**的 3D 可视化" 之类的需求即可。AI 会：

1. 把模板复制到你的项目 `.mm-viz/` 目录并配置参数；
2. **自动在后台启动本地服务器**（`serve.py`，默认端口 8019，你无需手动运行）；
3. 给你预览地址 `http://127.0.0.1:8019/viz/<名称>.html`，以及汇总页 `http://127.0.0.1:8019/`。

生成的页面与索引页均为中英双语，右上角按钮切换（默认跟随浏览器语言并记忆选择）。

若所用智能体支持 MCP，可通过两种方式接入并直接调用 `create_viz` 等工具：stdio（`scripts/mcp.py`）或 Streamable HTTP（服务器 `POST /mcp` 端点，如 `http://127.0.0.1:8019/mcp`），无需手动启动服务器（用法见 `SKILL.md`）。

手动体验（可选；正常使用 skill 时服务器由 AI 自动启动）：

```bash
# 将 $skill 替换为 skill 所在目录（本仓库为 skills/mm-skill，或安装后的技能目录）
skill="C:/path/to/mm-skill"

# 1) 复制一个模板到 .mm-viz（示例）
mkdir -p .mm-viz
cp "$skill/templates/viz-interactive.html" .mm-viz/demo.html

# 2) 启动服务器（在项目目录下执行）
python "$skill/scripts/serve.py"

# 3) 浏览器打开（按平台选择）
#    Windows:  start http://127.0.0.1:8019/viz/demo.html
#    macOS:    open  http://127.0.0.1:8019/viz/demo.html
#    Linux:    xdg-open http://127.0.0.1:8019/viz/demo.html
```

服务器可选参数：`--port 8020`、`--viz-dir /path/to/vizzes`、`--host 0.0.0.0`（局域网访问）。

## 线上 / 离线双模式

| 模式 | URL | 说明 |
| --- | --- | --- |
| 线上（默认） | `https://bhosmer.github.io/mm/index.html` | 使用原项目的 GitHub Pages 服务 |
| 离线副本 | `runtime/mm/index.html`（由 `serve.py` 提供） | 自带 mm 全套文件（1.8MB），完全离线可用 |

页面内可一键切换（或在 URL 后加 `?src=local` / `?src=online`）。

> 注意：离线模式依赖本地服务器；正常使用 skill 时它会自动在后台启动，无需手动操作。

## 更新 mm 离线副本

离线副本位于 `skills/mm-skill/runtime/mm/`。使用仓库级脚本 `scripts/fetch_mm.py` 重新下载/更新（默认直连、无代理；如需代理可通过 `--proxy` 或 `MM_PROXY` 环境变量指定）：

```bash
python scripts/fetch_mm.py                           # 直连（默认，无代理）
python scripts/fetch_mm.py --proxy http://host:port  # 经 HTTP 代理
```

## 上游资料

- 在线工具：<https://bhosmer.github.io/mm>
- 官方手册：<https://bhosmer.github.io/mm/ref.html>
- 源码：<https://github.com/bhosmer/mm>
- 原理文章：<https://bhosmer.github.io/mm/intro/>

## 许可

`runtime/mm/` 内的 mm 代码来自 [bhosmer/mm](https://github.com/bhosmer/mm)，为 MIT License，已随副本保留 `LICENSE` 文件。本 skill 的脚本与文档可自由修改。
