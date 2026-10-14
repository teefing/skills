---
name: context-init
description: 一键初始化仓库的 AI Context 结构（AGENTS.md + docs/context/ + docs/specs/）。当用户想要初始化项目的 AI 上下文、设置 AGENTS.md、创建 Context 文件、给仓库加 Agent 配置、或提到"init context"、"初始化 context"、"context 初始化"、"创建 AGENTS.md"、"项目还没有 AGENTS.md"时触发。即使用户只是问"怎么让 Agent 更好地理解这个项目"，也应该建议使用此 skill。
---

# /context-init

为当前仓库生成标准化的 AI Context 文件结构：AGENTS.md（≤100 行入口）+ docs/context/（深度知识）+ docs/specs/（Spec 归档）。

Context 质量直接决定 AI Agent 的表现。ETH Zurich 2026 研究发现过长的 Context 文件反而降低任务成功率，因此本 Skill 严格控制 AGENTS.md 在 100 行以内，只放"删掉 Agent 就会犯错"的信息，深度知识拆到 docs/context/ 各个文件中。

## 执行步骤

### Step 1: 扫描仓库现状

执行以下命令收集信息，不做全文读取：

```bash
# 已有 Context 文件
ls AGENTS.md CLAUDE.md 2>/dev/null
ls -d docs/ docs/context/ docs/specs/ 2>/dev/null
ls -d .agents/ .claude/ .cursor/ 2>/dev/null

# 代码特征（推断技术栈）
ls package.json go.mod Cargo.toml pyproject.toml pom.xml build.gradle Makefile CMakeLists.txt 2>/dev/null

# 依赖服务
ls docker-compose.yml docker-compose.yaml 2>/dev/null

# 目录结构
ls -d */ 2>/dev/null | head -20

# 配置文件内容（只读前 30 行）
head -30 package.json 2>/dev/null
head -20 go.mod 2>/dev/null
head -30 Makefile 2>/dev/null
head -20 Cargo.toml 2>/dev/null
head -20 pyproject.toml 2>/dev/null

# 代码文件列表（推断目录结构和模块）
find . -name "*.go" -o -name "*.ts" -o -name "*.py" -o -name "*.rs" -o -name "*.java" 2>/dev/null | grep -v node_modules | grep -v vendor | grep -v .git | head -50
```

### Step 2: 判断场景

| 条件 | 场景 | 动作 |
|------|------|------|
| 无 AGENTS.md 且无 docs/context/ | 全新仓库 | 生成完整结构 |
| 有 AGENTS.md 且 ≤100 行 | 已有精简入口 | 不动 AGENTS.md，补缺失的 docs/context/ 和路由表 |
| 有 AGENTS.md 且 >100 行 | 入口过长 | 提出拆分方案（深度内容迁到 docs/context/），展示对比 |
| 有 AGENTS.md 但格式很不同 | 格式差异大 | 尊重已有结构，只补 docs/context/ |
| 有 CLAUDE.md 无 AGENTS.md | 仅 Claude 配置 | 提取通用内容生成 AGENTS.md，CLAUDE.md 保留 Claude 专属 |
| 有 docs/ 下已有类似文件 | 有历史文档 | 不覆盖，只补缺失文件 |

### Step 3: 生成内容

读取 `references/templates.md` 获取所有模板的完整内容。基于 Step 1 扫描结果填充模板：

**推断规则**：

| 信息来源 | 推断什么 | 写到哪 |
|---------|---------|--------|
| package.json `dependencies` / go.mod `require` | 语言版本、框架、主要依赖 | AGENTS.md 技术栈 |
| package.json `scripts` / Makefile targets | build / test / start / lint 命令 | AGENTS.md 构建 & 测试，testing.md 本地环境 |
| .eslintrc / .golangci.yml / rustfmt.toml | 代码规范工具和规则 | AGENTS.md 关键约定 |
| 目录结构（cmd/ internal/ src/ lib/） | 分层模式、模块划分 | architecture.md |
| import/require 关系 | 模块间依赖 | architecture.md |
| docker-compose.yml services | 外部依赖（DB/Cache/MQ） | dependencies.md，testing.md 本地环境 |
| Dockerfile / k8s yaml | 部署方式 | testing.md 云端部署 |

**推断出的内容必须标注 `<!-- 待确认 -->`**，提醒用户 review。

### Step 4: 展示变更摘要并确认

先展示紧凑摘要：

```
📋 初始化方案：

将创建以下文件：
  + AGENTS.md (52 行)
  + docs/context/architecture.md (35 行)
  + docs/context/dependencies.md (20 行)
  + docs/context/conventions.md (模板，需人工补充)
  + docs/context/testing.md (28 行)
  + docs/context/decisions.md (模板)
  + docs/specs/ (空目录)

查看详细内容？直接确认写入？或逐个调整？
```

用户要求查看时逐文件展示完整内容。确认后写入。

### Step 5: 写入后验证

```bash
wc -l AGENTS.md
find docs/context/ -name "*.md" -exec wc -l {} \;
```

报告各文件行数，确认 AGENTS.md ≤ 100 行。

## 约束

- AGENTS.md 绝对不超过 100 行。超出意味着有深度内容该迁到 docs/context/
- Agent 能从 package.json / go.mod / tsconfig.json 推断的技术信息，不要写进 AGENTS.md
- 不覆盖已有文件
- 不动 .claude/ / .cursor/ 等工具专属配置
- 所有写入需用户确认
- 推断内容标注 `<!-- 待确认 -->`
