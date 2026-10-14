---
name: context-settle
description: 从当前 AI 对话中提取值得长期保留的项目级知识（架构决策、红线、踩坑），沉淀到 AGENTS.md 或 docs/context/。当用户想要沉淀知识、总结经验、更新 Context，或提到"沉淀"、"settle"、"总结一下"、"记下来"、"更新 context"、"更新 AGENTS.md"时触发。开发完一轮后用户说"整理一下"也应建议使用此 skill。
---

# /context-settle — 对话知识沉淀

从当前对话中提取值得**长期保留**的项目级知识，更新到 AGENTS.md 或 docs/context/。

按需触发，不调用 = 零影响。

## 命名

settle = 沉淀。就像水中的颗粒经过沉淀，有价值的沉到底部保留下来，浮沫（调试细节、临时方案）自然过滤掉。

## 前置检查

```bash
ls AGENTS.md docs/context/ 2>/dev/null
```

不存在？提示先运行 `/context-init`。

## 核心原则：只沉淀项目级知识，过滤开发过程噪声

这是本 Skill 最重要的判断标准。开发过程中会产生大量信息，但只有极少部分值得写进 Context。

### ✅ 该沉淀的（项目级知识，换个人来也需要知道）

- **架构决策**："我们决定把用户服务拆成 user-core 和 user-profile"
- **红线/禁区**："禁止在 service 层直接写 SQL"
- **长期约定**："错误码统一用 6 位数字"
- **踩过的坑**（会反复出现的）："legacy_users 表 user_id 是 varchar，JOIN 要 CAST"
- **上下游依赖变更**："订单服务新增对支付服务的 gRPC 调用"
- **测试方法/测试集**："创建订单的冒烟测试：POST /api/v1/orders 期望 200"

### ❌ 不该沉淀的（开发过程噪声，只对本次开发有意义）

- 具体的代码修改细节："把第 42 行的 if 改成 switch"
- 调试过程："试了 A 不行，又试了 B"
- 临时 workaround："先 hardcode 绕过，后面再改"
- 依赖安装/环境配置步骤："跑了 npm install，然后改了 tsconfig"
- PR review 中的代码风格微调："这里变量名从 x 改成 userId"
- 报错信息和修复过程："遇到 NullPointerException，原因是..."
- 单次的 bug 修复细节（除非是会反复出现的坑）
- Agent 能从代码直接推断的事实

**判断公式**：问自己"如果一个新同事下周加入项目，这条信息对他有用吗？" 如果答案是"他看代码就知道了"或"这只跟这次改动有关"，就不沉淀。

## 执行步骤

### Step 1: 收集变更上下文

先收集本次开发的背景信息，作为沉淀内容的追溯元数据：

```bash
# 当前分支
git branch --show-current 2>/dev/null

# 最近的 commit（了解本次改了什么）
git log --oneline -5 2>/dev/null

# 变更的文件范围（了解涉及哪些模块）
git diff --name-only HEAD~5..HEAD 2>/dev/null || git diff --name-only --cached 2>/dev/null
```

同时从对话上下文中提取（如果有的话）：
- 开发任务 ID / MR 链接 / Bits 链接
- 开发人
- 涉及的模块/服务

这些信息**不写入 Context 文件正文**，而是作为 ADR 的元数据或 git commit message 的一部分，用于追溯。

### Step 2: 扫描现有 Context 状态

```bash
wc -l AGENTS.md 2>/dev/null
find docs/context/ -name "*.md" -exec wc -l {} \; 2>/dev/null
```

### Step 3: 提取知识（严格过滤）

回顾对话内容，**只提取通过"新同事测试"的知识**：

| 类型 | 写到哪 | 示例 |
|------|--------|------|
| 🚫 红线 | AGENTS.md | "禁止直接调用 legacy API" |
| 📏 长期约定 | AGENTS.md 或 conventions.md | "错误码统一 6 位" |
| 🏗️ 架构变更 | architecture.md | "用户服务拆为 user-core + user-profile" |
| 🔗 依赖变更 | dependencies.md | "新增对支付服务的 gRPC 调用" |
| 📝 技术决策 | decisions.md（ADR） | "选 gRPC 因为内部通信不需要 REST 可读性" |
| 🧪 测试知识 | testing.md | "冒烟测试用例 / 部署注意事项" |
| ⚠️ 反复踩的坑 | conventions.md | "legacy 表 user_id 是 varchar" |

**提取数量预期**：一次普通开发对话通常只有 0-3 条值得沉淀的知识。如果你提取了 5 条以上，大概率混入了开发噪声，回去重新过滤。

**如果没有可沉淀的知识**，直接告知"本次对话没有发现需要沉淀的项目级知识"并结束。大部分日常开发对话确实不产生需要沉淀的知识，这很正常。

### Step 4: 读取目标文件，合并写入

读取 `references/write-examples.md` 获取各文件的具体写入格式。

合并策略：
- 已有相同内容 → 跳过
- 已有但不够精确 → 替换为更精确的版本（不追加）
- 与已有矛盾 → 展示新旧对比，让用户选
- 全新内容 → 插入对应章节

### Step 5: 写入前检查

- AGENTS.md ≤ 100 行，docs/context/ 单文件 ≤ 500 行
- 引用的路径 `ls` 确认存在
- 不含相对时间（"昨天" → 2026-05-14）
- 不含叙事（"我们当时…" → "使用 X 方案，因为 Y"）

### Step 6: 展示摘要并确认

```
📋 本次沉淀 2 条项目级知识：

变更上下文: 分支 feat/payment-integration, MR !342

1. [🔗 依赖] → dependencies.md
   新增下游: 支付服务 (payment-service), gRPC, PaymentService.CreatePayment

2. [📝 决策] → decisions.md
   新增 ADR-003: 选择 gRPC 而非 HTTP 作为内部通信协议
   背景: 订单服务需调用支付服务 | 分支: feat/payment-integration

（对话中的代码修改细节、调试过程已过滤，不沉淀）

确认写入？查看完整 diff？或逐条调整？
```

## Spec 处理

对话涉及 Spec 驱动开发时：

1. 提炼关键**决策**（为什么选 A 不选 B）
2. 写入 decisions.md，ADR 中补充追溯信息：
   ```markdown
   ## ADR-NNN: [决策标题]
   - **日期**: 2026-05-14
   - **状态**: accepted
   - **背景**: [从 Spec 提取]
   - **决策**: [选了什么]
   - **替代方案**: [放弃了什么，为什么]
   - **影响**: [带来的约束]
   - **来源**: [Spec 链接 / MR 链接 / 开发任务 ID]
   ```
3. 问用户是否归档原始 Spec 到 docs/specs/

## 约束

- 所有写入需用户确认
- 没有可沉淀知识时直接告知，不硬凑
- **一次沉淀通常 0-3 条，超过 5 条要重新审视是否混入噪声**
- 合并优于追加，精简优于冗余
- AGENTS.md 不超过 100 行
