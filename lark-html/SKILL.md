---
name: lark-html
metadata:
  version: "1.0"
description: |
  向飞书文档中插入、更新、读取、删除内嵌 HTML 块（AddOns Block），或将 HTML 部署为独立妙搭应用（独立 URL）。
  飞书文档里唯一能真实执行 CSS/JS 的载体（iframe 沙箱），支持 CSS 动画、ECharts、
  Canvas、WebGL、Three.js、SVG 动画、window.magic 数据交互等一切前端可视化。
  内嵌 HTML 还可通过 window.magic 实现用户身份识别、多人协作状态、持久化存储、
  AI 调用和多维表格读写——在文档内构建完整的交互应用。

  适用场景：
  - 在飞书文档中插入可交互/会动的 HTML 内容（动画、图表、大屏、协作组件）
  - 构建多人交互应用（投票、弹幕、游戏、论坛、协作画布）
  - 使用 window.magic 实现数据持久化、AI 生成、多维表操作
  - 更新/读取/删除已有的 HTML 块
  - 将 HTML 部署为独立可分享的链接（路由至妙搭）

  不适用场景：
  - 静态图片/SVG 插入（用文档原生图片块）
  - 可编辑的矢量图（用画板 board / design-lark-chart）
  - 纯迭代已有妙搭应用、不涉及 HTML 变更（直接用 lark-apps）

allowed-tools: Bash(lark-cli *), Read, Write
---

# lark-html: 飞书 HTML 统一技能

## 路由决策

| 用户意图 | 路由 | 读取 |
|----------|------|------|
| 默认（在文档中插入/更新 HTML） | **内嵌路由** | `references/embed-operations.md` |
| "独立链接"/"deploy"/"分享 URL"/"发布成应用" | **部署路由** | `references/deploy-to-miaoda.md` |

⚠ 两条路由的关键区别：**内嵌路由有 `window.magic`**（可读用户身份、可存数据），部署路由没有。

---

## 核心常量

```
block_type:          40
component_type_id:   blk_6900429af84180025ce76527
identity:            --as user（默认）| --as bot（Bot 建的文档）
```

---

## Quick Start

### 内嵌到文档（默认）

```bash
python3 scripts/build_payload.py create page.html > payload.json
lark-cli api POST "/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children" \
  --as user --data @payload.json
```

### 部署为独立链接

```bash
lark-cli apps +create --name "My App" --app-type HTML
lark-cli apps +html-publish --app-id <id> --path ./app
lark-cli apps +access-scope-set --app-id <id> --scope tenant
```

---

## References 索引

| 文件 | 何时读取 |
|------|----------|
| [`references/embed-operations.md`](references/embed-operations.md) | 执行内嵌 CRUD（插入/更新/读取/删除 HTML 块） |
| [`references/deploy-to-miaoda.md`](references/deploy-to-miaoda.md) | 用户需要独立 URL / 分享链接 / 说"deploy" |
| [`references/window-magic-api.md`](references/window-magic-api.md) | HTML 需要用户身份、文档元数据、持久存储、AI 或 Bitable |
| [`references/data-interaction-patterns.md`](references/data-interaction-patterns.md) | 构建协作/实时/多人交互功能（投票、弹幕、排行榜、论坛） |
| [`references/html-authoring-guide.md`](references/html-authoring-guide.md) | 首次编写 HTML、调试白屏、处理 CDN/高度/深色主题 |

---

## Top 3 避坑

1. **白屏无报错** — iframe 内异常不可见，必须先在本地 Chrome 测试通过
2. **magic 未就绪** — DOMContentLoaded 时 magic 可能还没注入，必须用 `waitForMagic()` 轮询
3. **批量限流** — 连续插入多块时加 `sleep 0.5`，否则 `99991400`

详见 [`references/html-authoring-guide.md`](references/html-authoring-guide.md)。
