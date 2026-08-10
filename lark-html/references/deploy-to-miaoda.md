# 部署为独立妙搭应用（Deploy to Miaoda）

> 当用户需要一个**独立可分享的 URL**（而非嵌入文档内部）时，使用本路由。HTML 将被部署为飞书妙搭应用，生成公网可访问链接。

## 触发条件

用户明确提到以下任一意图时走本路由：
- "独立链接" / "单独的 URL" / "可分享链接"
- "deploy" / "部署" / "发布成应用"
- "让别人直接打开" / "公网可访问"

## 前提

```bash
# 一次性授权妙搭域（如已授权可跳过）
lark-cli auth login --domain apps
```

## 端到端流程

### Step 1: 准备 HTML

- 入口文件**必须是 `index.html`**
- 如果是单文件，创建一个临时目录放入：`mkdir -p ./app && cp page.html ./app/index.html`
- 如果是多文件（CSS/JS/图片），整个目录即可，确保根目录有 `index.html`
- 扫描排除：不要包含 `.env`、`.npmrc`、`credentials.json` 等敏感文件

### Step 2: 创建应用

```bash
lark-cli apps +create --name "<应用名称>" --app-type HTML
# 返回 app_id，后续步骤使用
```

### Step 3: 发布 HTML

```bash
lark-cli apps +html-publish --app-id <app_id> --path ./app
# 返回公网可访问 URL
```

`--path` 必须是**相对路径**，指向包含 `index.html` 的目录。

### Step 4: 设置访问范围（默认全租户）

```bash
lark-cli apps +access-scope-set --app-id <app_id> --scope tenant
```

| scope | 说明 |
|-------|------|
| `tenant` | 同租户所有人可访问（默认推荐） |
| `public` | 公网所有人可访问 |
| `specific` | 仅指定人员可访问 |

---

## 与内嵌路由的关键区别

| 维度 | 内嵌（embed） | 独立发布（deploy） |
|------|--------------|-------------------|
| 产物位置 | 文档内部的一个区块 | 独立 URL |
| `window.magic` | ✅ 可用 | ❌ 不可用 |
| 用户身份 | 可通过 magic 获取 | 需自行实现登录 |
| 数据持久化 | magic.redis | 需自建后端或用飞书 API |
| 适合场景 | 文档内交互组件 | 独立工具/页面/分享 |

⚠ **独立发布的 HTML 没有 `window.magic` 运行时**——它不在文档的 iframe 沙箱中运行。如果需要用户身份或持久化数据，要么改用内嵌路由，要么在 HTML 中自行接入飞书 OAuth 或其他后端。

---

## 更新已发布应用

对同一 `app_id` 重新执行 `+html-publish` 即为更新，URL 不变：

```bash
lark-cli apps +html-publish --app-id <app_id> --path ./app
```
co
---

## 错误处理

| 错误 | 原因 | 解法 |
|------|------|------|
| `missing_scope` | 未授权 apps 域 | `lark-cli auth login --domain apps` |
| `path must contain index.html` | 入口文件缺失 | 确保目录根有 `index.html` |
| 发布超时 | 目录过大 | 排除 `node_modules`、`.git` 等 |

---

## 何时不走本路由

如果用户的 HTML 需要 `window.magic`（读用户身份、文档数据、共享存储），则**必须走内嵌路由**。独立发布仅适合纯展示型或自带后端的应用。
