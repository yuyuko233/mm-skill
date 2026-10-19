# mm 参数参考

> [mm - 3D matmul visualizer](https://bhosmer.github.io/mm/ref.html) 的参数手册。
> 上游资料：[在线工具](https://bhosmer.github.io/mm) · [完整手册](https://bhosmer.github.io/mm/ref.html) · [源码](https://github.com/bhosmer/mm) · [讲解文章 Inside the Matrix](https://bhosmer.github.io/mm/intro/)
> 英文默认版：[`params-reference.md`](params-reference.md)
>
> mm 把矩阵乘法画成 3D "立方体"：左操作数、右操作数、结果矩阵分别贴在立方体的三个面上，可旋转/缩放/放大查看数值，并支持动画演示算法与分块。它接受的唯一输入是一个 **params JSON**（通过 URL `?params=` 传入，或 iframe 内 postMessage 实时更新）。

---

## 0. 快速示例

> 下列 JSON 都是 **postMessage setParams 的 payload**（深度合并、支持部分参数、推荐用法）。

最小配置 —— 默认 32×32 单矩阵乘：

```json
{ "expr": "L @ R" }
```

两层注意力（全部 32×32，无需外部数据，离线可用）：

```json
{
  "expr": "out = (attn = Q @ K) @ V",
  "sync_expr": true,
  "anim": { "alg": "vmprod", "fuse": "sync", "speed": 16 },
  "left": { "epilog": "softmax(tril(x/sqrt(k)))" }
}
```
（`left.epilog` 即 attn 层的后处理；根节点的 `epilog` 作用于 `out`。）

指定叶子形状（按树路径定位叶子）：

```json
{
  "expr": "out = (attn = Q @ K) @ V",
  "sync_expr": true,
  "left": {
    "left": { "h": 32, "w": 16 },
    "right": { "h": 16, "w": 32 }
  }
}
```
（attn.left = Q，attn.right = K；形状须满足 K.h == Q.w、V.h == K.w。）

带投影的完整注意力（节点路径与官方 attngpt2 示例一致；全部默认 32×32）：

```json
{
  "expr": "out = ((attn = (Q = input @ wQ) @ (K_t = wK_t @ input_t)) @ (V = input @ wV)) @ wO",
  "sync_expr": true,
  "anim": { "alg": "vmprod", "fuse": "sync" },
  "left": { "left": { "epilog": "softmax(tril(x/sqrt(k)))" } }
}
```

要点：
- 只有 `expr` 定义结构，其余字段缺省用默认值；改表达式必须带 `sync_expr: true`，mm 按名字尽量保留已有配置。
- 表达式语法 `left @ right`、`result = left @ right`、括号分组右结合；名字任意（`Q`、`wQ`、`input_t`…）。
- 表达式里出现的名字会自动生成默认叶子节点（32×32、行列渐变初值），不必逐个声明。
- **重要**：部分参数只能用 `setParams`（深度合并）应用；URL `?params=` 是顶层整体替换，部分对象会破坏结构（详见下一节）。

---

## 1. 嵌入与 URL 机制

mm 是纯静态前端应用。两种运行时来源：

| 模式 | URL | 说明 |
| --- | --- | --- |
| 线上（默认） | `https://bhosmer.github.io/mm/index.html` | 需要能访问 GitHub Pages |
| 离线副本 | `/mm/index.html` | 由本 skill 的 `serve.py` 提供 |

把 mm 放进 `<iframe>`。**参数应用有两种机制，合并语义不同（关键区别！）**

| 机制 | 合并语义 | 适用 |
| --- | --- | --- |
| postMessage `setParams` | **深度递归合并**，支持任意部分参数 | 推荐；模板默认做法 |
| URL `?params=<json>` | **顶层键整体替换**（`left`、`anim` 等整个对象被替换） | 仅当提供**完整**参数树（如官方 attngpt2 示例）才安全 |

- 部分参数（如 `left: {h:32}`）经 URL 传入会**破坏默认树结构并报错**（`Cannot read properties of undefined`），必须走 `setParams`。
- URL 里的 `expr` 字符串是**派生字段**：初始化时会被 `genExpr` 从参数树重新生成；只有 `setParams` + `sync_expr: true` 才能让 `expr` 驱动结构重建。
- `?config=<url>` —— 让 mm 从该 URL 同步加载完整 params JSON（大配置适用；跨域需 CORS）。**URL 必须是绝对的完整地址**：源码用 `new URL(config)` 解析（无 base），相对路径会抛 `Invalid URL` 并被静默忽略、回退到默认参数（只在 console 留日志）。
- 用户在 mm 里操作后，mm 会把会话状态写进它自己的 URL（参数较大时用内部压缩格式，如 `?0=...&1=...`），并（在 iframe 中）向父页面 postMessage 一条 `{ search_params }`。

**postMessage API**

| 方向 | 消息 | 响应 |
| --- | --- | --- |
| 父→mm | `{ getUrlInfo: undefined }` | `{ url_info: { json, url, compressed, search_params } }` |
| 父→mm | `{ getParams: undefined }` | `{ params }`（当前完整参数） |
| 父→mm | `{ setParams: { props, reset } }` | 无（直接生效） |
| mm→父 | `{ search_params }` | 自发，mm URL 变化时 |

- `props` 是**部分参数**，递归合并进当前 params。
  例：`{ setParams: { props: { anim: { alg: 'vvprod' } } } }`
- `reset: true` 会先重置为 **mm 内置默认** 再应用 `props`；想"复位到我的初始状态"就把初始 params 全量传回。
- 想改结构（表达式）：`{ setParams: { props: { expr: 'X = A @ B @ C', sync_expr: true } } }`。
- 跨域发送用 `postMessage(msg, '*')` 即可（mm 的监听端不校验 origin；回包 origin 为 mm 页面 origin）。
- **限制**：`pause` / `step`（暂停/单步）只在 mm 界面里控制（GUI 或空格键），postMessage 无法设置。

---

## 2. 顶层参数

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `expr` | `"L @ R"` | 表达式；定义整个可视化结构 |
| `name` | `"L @ R"` | 结果矩阵名；编辑 expr 时自动同步 |
| `epilog` | `"none"` | 顶层结果的后处理 |

`epilog` 取值：`none`, `relu`, `gelu`, `sigmoid`, `silu`, `tanh`, `layernorm`（整矩阵归一化），`softmax`（按行），`softmax(x/sqrt(k))`（SDPA 缩放），`softmax(tril(x/sqrt(k)))`（因果注意力）。

---

## 3. left / right：矩阵叶子节点

`matmul: false`（默认）时的字段：

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `name` | `"L"` / `"R"` | 名字（与 expr 同步） |
| `matmul` | `false` | 是否为主表达式 |
| `h` `w` | `32` `32` | 高/宽；与相邻操作数共享的 k 维自动同步 |
| `init` | `"row major"` 左 / `"col major"` 右 | 数值初始化方式（见下） |
| `url` | `""` | `init: "url"` 时的 CSV 地址 |
| `expr` | — | `init: "expr"` 时的 JS 表达式 |
| `min` `max` | `-1` `1` | 取值范围（仅部分 init 生效） |
| `dropout` | `0` | 稀疏化比例 0..1（row/col 与随机初值） |

`init` 全部取值：

| init | 效果 |
| --- | --- |
| `rows` / `cols` | 行/列内同值，按 min..max 渐变 |
| `row major` / `col major` | 行主序/列主序从 min 到 max 均匀铺开 |
| `pt linear` | PyTorch Linear 风格均匀分布 |
| `uniform` / `gaussian` | min..max 上的均匀/高斯随机 |
| `tril mask` / `triu mask` | 下/上三角为 1 |
| `eye` | 单位阵 |
| `diff` | 对角 1，次对角 -1（差分算子） |
| `url` | 从 `url` 指向的 CSV 加载；数据按行消费，不足时行列循环复用 |
| `expr` | JS 表达式，可用变量 `i, j, h, w`（下标与形状） |

CSV 提示：跨域 CSV 必须允许 CORS（`raw.githubusercontent.com` 可以）；本地文件放到 viz 目录，用 `/viz/xx.csv` 同源加载。

---

## 4. left / right：子表达式节点

`matmul: true` 时，节点变成"子立方体"，字段为：

- `name`：子表达式的名字（结果矩阵名）
- `left` / `right`：递归的子操作数（叶子或子表达式）
- `epilog`：作用在该子结果上的后处理（同上 epilog 表）
- `anim`：该子表达式的动画配置（`alg: "inherit"` 默认继承父级）
- `block`：该子表达式的分块（通常在全局生效）
- `layout`：该子立方体的摆放（`scheme: "custom"` 时才在子菜单中出现）

子表达式可任意深度嵌套；动画按依赖从叶到根推进，独立子表达式并行。

---

## 5. anim：动画

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `alg` | `"none"` | 算法（见下表） |
| `speed` | `20` | 速度 1..100（每帧一步，与算法无关） |
| `fuse` | `"none"` | 相邻矩阵乘的融合：`none` / `sync` / `async` |
| `spin` | `0` | 自旋：+1 逆时针，-1 顺时针，0 停 |
| `hide inputs` | `false` | 动画时隐藏输入面，便于观察内部中间结果 |

`alg` 取值：`none`, `dotprod (row major)`, `dotprod (col major)`, `axpy`, `vmprod`, `mvprod`, `vvprod`；子节点另有 `inherit`。
- `dotprod`：成对点积逐元素
- `axpy`：按 k 维逐列"向量-标量"累积
- `vmprod`：按左矩阵行做向量×矩阵
- `mvprod`：按右矩阵列做矩阵×向量
- `vvprod`：按 k 维外积累加

融合 `fuse`：相邻两层算法生成平行平面时才可融合（例如 `A @ B @ C` 全 `vmprod` 沿 i，或左 `mvprod`/父 `vvprod` 沿 k）。`sync` 仅同时开始者融合，`async` 允许错时融合；多数表达式两者一致。

---

## 6. block：分块

| 字段 | 默认 | 轴 |
| --- | --- | --- |
| `i blocks` | `1` | 根矩阵的行方向（沿左侧连续链传播） |
| `k blocks` | `1` | 归约维；父级的 k 变成左子的 j、右子的 i |
| `j blocks` | `1` | 根矩阵的列方向（沿右侧连续链传播） |

- 分块是全局的（切割面贯穿子表达式），代表整个表达式的并行化；动画会在块内并行。
- 块大小均匀，除不尽时最后一块较短。
- 典型语义：`i blocks` ≈ 数据并行（按 batch 切），`j blocks` ≈ 张量并行（按隐藏维切）。

---

## 7. layout：布局

间距（默认值通常够用；深度嵌套饱和表达式可调）：

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `gap` | `4` | 三个面之间的间隙（单位≈一行/列） |
| `scatter` | `0` | 子**表达式**与父级间的固定距离（叶子矩阵不受影响） |
| `molecule` | `1` | 多大（含矩阵乘个数）开始算"大分子"从而应用 scatter |
| `blast` | `0` | scatter 按子表达式规模的指数缩放；正值越大越散，负值反之 |

朝向：

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `scheme` | `"blocks"` | 子立方体布局生成规则 |
| `polarity` | `"negative"` | `positive`/`negative`：操作数法线朝结果矩阵增长/减小方向 |
| `left placement` | `"left"` | 左操作数在左/右面 |
| `right placement` | `"top"` | 右操作数在上/下面 |
| `result placement` | `"front"` | 结果在前/后面 |

`scheme` 取值：
- `blocks`（默认）：凸凹交替展开，通常较易读、抗碰撞
- `zigzag`：交替但不换凹凸，流程更简单但遮挡更多
- `wheel`：每层转 90°，线性表达式呈圆形，易碰撞（用 spacing 化解）
- `custom`：不做推导，子菜单暴露 layout 参数手动摆

---

## 8. deco：装饰

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `legends` | `6` | 名字/形状图例大小，0 关闭 |
| `shape` | `true` | 是否显示形状刻度图例 |
| `spotlight` | `2` | 放大时显示数值的聚光区域大小 |
| `lens size` | `0.5` | 放大镜区域大小 |
| `magnification` | `7` | 放大倍数（ctrl+拖拽/长按触发） |
| `row guides` | `0.6` | 行辅助线亮度 0..1 |
| `flow guides` | `0.5` | 流向箭头亮度与大小 0..1 |
| `interior spotlight` | `false` | 放大时是否显示立方体内部中间结果数值 |
| `axes` | `false` | 是否显示坐标轴 |

---

## 9. viz：颜色与尺寸

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `sensitivity` | `"global"` | 数值→大小/亮度/色相的归一化范围 |
| `min size` / `min light` / `max light` | `0.2` / `0.4` / `0.7` | 最小渲染尺寸 / 亮度范围（HSL，亮度趋 1 趋白） |
| `elem scale` | `1.25` | 全体元素缩放 |
| `zero hue` | `0.77` | 零值色相；正高负低 |
| `hue gap` | `0.74` | 零色相到取值色相的间距（正负颜色差） |
| `hue spread` | `0.04` | 色相随幅值变化速率 |

`sensitivity` 取值：`global`（全局统一），`local`（逐矩阵归一），`semilocal`（全局与局部的几何平均），`superlocal`（局部且下限取该矩阵最小绝对值）。
矩阵间方差大时优先 `local`；可用 `deco`/`viz` 微调可读性。

---

## 10. cam：相机

| 字段 | 默认 |
| --- | --- |
| `cam` | `{ "x": -48, "y": 48, "z": 48, "target": {"x":0,"y":0,"z":0} }`（相机位置 = 默认维度 32 的 `-1.5i, 1.5j, 1.5k`，target 为注视点） |

一般不用设置；用户可直接旋转视角。

---

## 11. 默认值一览

```json
{
  "expr": "L @ R", "name": "L @ R", "epilog": "none",
  "left":  { "name": "L", "matmul": false, "h": 32, "w": 32, "init": "row major", "min": -1, "max": 1, "dropout": 0 },
  "right": { "name": "R", "matmul": false, "h": 32, "w": 32, "init": "col major", "min": -1, "max": 1, "dropout": 0 },
  "anim":  { "alg": "none", "speed": 20, "fuse": "none", "spin": 0, "hide inputs": false },
  "block": { "i blocks": 1, "k blocks": 1, "j blocks": 1 },
  "layout":{ "scheme": "blocks", "gap": 4, "scatter": 0, "molecule": 1, "blast": 0,
             "polarity": "negative", "left placement": "left", "right placement": "top", "result placement": "front" },
  "deco":  { "legends": 6, "shape": true, "spotlight": 2, "lens size": 0.5, "magnification": 7,
             "row guides": 0.6, "flow guides": 0.5, "interior spotlight": false, "axes": false },
  "viz":   { "sensitivity": "global", "min size": 0.2, "min light": 0.4, "max light": 0.7,
             "elem scale": 1.25, "zero hue": 0.77, "hue gap": 0.74, "hue spread": 0.04 }
}
```

子表达式节点默认：`epilog: "none"`, `anim: { "alg": "inherit" }`, `block: {i/k/j: 1}`，默认 layout。

---

## 12. 交互操作

| 操作 | 笔记本 | 移动端 |
| --- | --- | --- |
| 缩放 | 双指纵向拖动 / 上下方向键 | 捏合 |
| 旋转 | 单击拖动 / shift+左右方向键 | 单指拖动 |
| 平移 | Cmd/Ctrl+单击拖动 / 左右方向键 | 双指拖动 |
| 放大看数值 | 长按或 Ctrl+单击拖动 | 长按拖动 |
| 暂停/继续动画 | 空格（或 GUI） | GUI |

右上角 **mm** 菜单可交互式调整全部参数；URL 即完整会话（可在 **diag** 菜单查看 JSON / URL）。右下角 GUI 为 lil-gui 面板。

---

## 13. 常见配方

- **MLP 链**：`expr: "out = (x1 = (x0 = batch @ w0) @ w1) @ w2"`，anim `vmprod` + `fuse: "sync"` 展示数据并行面。
- **低秩分解**：`expr: "out = (x0 = batch @ (w0 = w0_L @ w0_R)) @ ..."`。
- **QKV 投影形状**：宽→窄 `left {h:32,w:48}, right {h:48,w:12}`；窄→宽 `left {h:32,w:12}, right {h:12,w:48}`。
- **因果注意力**：对 `attn` 层设 `epilog: "softmax(tril(x/sqrt(k)))"`。
- **展示分块并行**：`block: {"i blocks": 4}` + `anim.alg: "vmprod"`（i 向切分≈数据并行）；`j blocks` 对应用张量并行。
- **只看几何形状**：`deco: {legends:0, shape:false, "row guides":0, "flow guides":0}`，`viz.sensitivity: "local"`。
- **对齐官方示例数据**：可用 `https://raw.githubusercontent.com/bhosmer/testdata/main/weights/gpt2/...csv` 作 `init: "url"` 数据源（跨域可用）。

---

## 14. 注意事项

- **参数合并语义（最重要）**：`setParams` 深度合并、支持部分参数；URL `?params=` 顶层整体替换、必须给完整树（否则破坏结构报 `Cannot read properties of undefined`）。`expr` 只在 `setParams` + `sync_expr: true` 时驱动结构重建。
- **暂停/单步**：不可通过 postMessage 控制（GUI/空格键专用）。
- **URL 长度**：超长参数（数 KB）在 Safari 地址栏会被截断；分享用 **diag** 菜单的 URL，或改用 `?config=<绝对URL>`（见第 1 节：必须绝对地址）。参数超长时 mm 自动改用内部压缩格式。
- **CSV 跨域**：`init: "url"` 的数据源必须允许 CORS；本地文件请放 viz 目录经服务器同源访问。
- **尺寸性能**：32–128 边长交互顺畅；256/768 量级（如 GPT-2 单头示例）可渲染但较重，动画速度会受限。
- **碰撞**：深层嵌套可能出现空间重叠；调 `layout.gap/scatter/molecule/blast` 或换 `scheme`。默认 `blocks` 一般在前三代内不碰撞。
- **`sync_expr` 只在 setParams/编辑 expr 时作为一次性指令**，不会持久化到参数里。
- **可视化截图**：浏览器截屏即可；无内置导出。`cam` 配合固定视角可做可复现的截图。
