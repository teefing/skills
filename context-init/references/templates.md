# Context 文件模板全集

生成文件时严格基于这些模板，根据扫描结果填充 `[占位符]` 部分。无法推断的内容用 `<!-- 待确认 -->` 标注。

---

## AGENTS.md 模板（目标 ≤100 行）

```markdown
# [项目名称]

[一句话描述项目的核心功能和技术定位]

## 技术栈

- 语言: [例: Go 1.22]
- 框架: [例: Gin (HTTP) + gRPC]
- 数据库: [例: MySQL 8.0 (GORM)]
- 缓存: [例: Redis 7]
- 部署: [例: Docker / Kubernetes]

## 红线

- 禁止在代码中硬编码密钥、Token 或数据库密码
- 禁止绕过 lint 检查提交代码
- [根据项目特征补充，例: 禁止在 handler/service 层直接写 SQL，必须走 repository]

## 构建 & 测试

[根据 Makefile / package.json scripts 填充实际命令]

## 关键约定

- [根据项目实际填充，例: API 路由前缀 /api/v1/，RESTful 风格]
- [例: 分层结构 handler → service → repository → model]
- [例: 错误码统一通过 pkg/errors 定义]

## 深度知识

| 需要了解… | 读这个文件 |
|-----------|-----------|
| 模块怎么分层、怎么交互 | docs/context/architecture.md |
| 上下游服务、外部依赖 | docs/context/dependencies.md |
| 业务规则、踩坑、Review 规范 | docs/context/conventions.md |
| 为什么做了某个技术决策 | docs/context/decisions.md |
| 怎么测试、怎么部署、测试集 | docs/context/testing.md |
```

**自检清单**（生成后逐条对照）：
- [ ] 总行数 ≤ 100
- [ ] 每条内容删掉后 Agent 会犯无法恢复的错误
- [ ] 没有 Agent 能从 package.json / go.mod 等推断的信息
- [ ] 没有叙事历史（"2026-03 上线了 XX"）
- [ ] 构建命令可直接复制执行

---

## docs/context/architecture.md 模板

```markdown
# 模块架构

## 分层概览

[描述整体分层，例:]
Handler (HTTP/gRPC) → Service (业务逻辑) → Repository (数据访问) → Model (数据模型)

## 核心模块

### [模块名称]
- **职责**: [一句话描述]
- **入口**: [关键文件路径，如 internal/handler/order.go]
- **依赖**: [依赖的其他模块]

[为每个核心模块重复上述结构]

## 核心流程

### [流程名称，例: 订单创建]

[简述关键步骤:]
1. Handler 接收请求，校验参数
2. Service 执行业务规则
3. Repository 写入数据库
4. 返回结果
```

**填充指南**：
- 从目录结构推断分层（cmd/ internal/ src/ lib/ pkg/）
- 从文件名和 import 关系推断模块职责
- 推断内容标注 `<!-- 待确认：从目录结构推断 -->`

---

## docs/context/dependencies.md 模板

```markdown
# 上下游依赖

## 下游（本项目调用的）

| 服务 | 用途 | 调用方式 | 关键接口 |
|------|------|---------|---------|
| [服务名] | [用途] | [RPC/HTTP/MQ] | [接口名或 topic] |

## 上游（调用本项目的）

| 服务 | 调用方式 | 关键接口 |
|------|---------|---------|
| [服务名] | [RPC/HTTP/MQ] | [接口名] |

## 外部依赖

| 依赖 | 版本 | 注意事项 |
|------|------|---------|
| [例: MySQL] | [8.0+] | [例: 使用 JSON 字段类型] |
| [例: Redis] | [7+] | [例: 用作缓存，TTL 30 分钟] |
```

**填充指南**：
- 外部依赖从 docker-compose.yml 的 services 推断
- 上下游服务通常无法自动推断，生成空表格即可

---

## docs/context/conventions.md 模板

```markdown
# 约定、踩坑与 Review 规则

## 领域术语

| 术语 | 含义 |
|------|------|
| <!-- 待补充 --> | |

## 业务规则

- <!-- 待补充 -->

## 踩坑记录

- <!-- 待补充：开发中遇到的坑会通过 /context-distill 持续积累 -->

## Code Review 规则

- <!-- 待补充：团队 Review 规范 -->
```

**填充指南**：
- 此文件内容高度依赖团队经验，初始化时生成空模板即可
- 内容会通过 /context-distill 在日常开发中持续积累

---

## docs/context/testing.md 模板

```markdown
# 测试指南

## 本地环境

### 启动依赖服务

[从 docker-compose 推断，例:]
docker-compose up -d    # 拉起 MySQL + Redis

### 启动本项目

[从 Makefile / package.json 推断，例:]
go run ./cmd/server     # 默认监听 :8080

### 运行测试

[从 Makefile / package.json 推断，例:]
go test ./... -v -count=1    # 单元测试
golangci-lint run ./...      # Lint 检查

## 云端部署 & 测试

<!-- 待补充：PPE/BOE 部署方式、泳道选择、接口测试工具 -->

## 可用测试集

### 冒烟测试

| 场景 | 请求 | 期望结果 |
|------|------|---------|
| <!-- 待补充：核心接口的基本测试用例 --> | | |

### 边界 & 异常

| 场景 | 请求 | 期望结果 |
|------|------|---------|
| <!-- 待补充：边界和异常场景 --> | | |

### 性能基线

| 接口 | P99 延迟 | QPS 上限 | 备注 |
|------|---------|---------|------|
| <!-- 待补充 --> | | | |

## 测试注意事项

- 测试数据不要写入生产环境
- <!-- 待补充 -->
```

**填充指南**：
- 本地环境部分从 docker-compose + Makefile/package.json 推断
- 测试集部分生成空表格，通过 /context-distill 持续积累
- 如果项目有 test/ 或 __tests__/ 目录，可以列出已有测试文件供参考

---

## docs/context/decisions.md 模板

```markdown
# 技术决策记录

<!-- 使用 ADR 格式记录重要的技术决策 -->
<!-- 通过 /context-distill 从对话中自动提炼 -->

[如果能从代码中推断出明显的技术选型（如选了 gRPC 而非 REST、选了 MySQL 而非 PostgreSQL），可以生成一条示例 ADR]
```

**ADR 格式**：
```markdown
## ADR-NNN: [决策标题]

- **日期**: YYYY-MM-DD
- **状态**: accepted / superseded / deprecated
- **背景**: [为什么需要做这个决策]
- **决策**: [选了什么]
- **替代方案**: [放弃了什么，为什么]
- **影响**: [带来的约束]
```

---

## 生成示例

以下是一个 Go + Gin + MySQL + Redis 项目的生成结果示例，展示实际填充后的效果：

### AGENTS.md 示例（49 行）

```markdown
# Order Service

订单微服务，提供订单的创建、查询和状态管理能力。

## 技术栈

- 语言: Go 1.22
- 框架: Gin (HTTP) + gRPC
- 数据库: MySQL 8.0 (GORM)
- 缓存: Redis 7
- 部署: Docker

## 红线

- 禁止在代码中硬编码密钥、Token 或数据库密码
- 禁止绕过 golangci-lint 检查提交代码
- 禁止在 handler 或 service 层直接写 SQL，所有数据库操作必须通过 repository 层
- 禁止直接操作生产数据库

## 构建 & 测试

go mod download            # 安装依赖
go test ./... -v -count=1  # 运行测试
go run ./cmd/server        # 本地启动
go build -o bin/server ./cmd/server  # 构建
golangci-lint run ./...    # Lint 检查

## 关键约定

- API 路由前缀: /api/v1/，RESTful 风格
- 分层结构: handler → service → repository → model
- 错误码统一通过 pkg/errors 定义
- 外部服务依赖通过 docker-compose 启动

## 深度知识

| 需要了解… | 读这个文件 |
|-----------|-----------|
| 模块怎么分层、怎么交互 | docs/context/architecture.md |
| 上下游服务、外部依赖 | docs/context/dependencies.md |
| 业务规则、踩坑、Review 规范 | docs/context/conventions.md |
| 为什么做了某个技术决策 | docs/context/decisions.md |
| 怎么测试、怎么部署、测试集 | docs/context/testing.md |
```

### architecture.md 示例

```markdown
# 模块架构

## 分层概览

Handler (Gin HTTP) → Service (业务逻辑) → Repository (GORM) → Model

## 核心模块

### handler（请求处理）<!-- 待确认：从目录结构推断 -->
- 职责: 接收 HTTP 请求，参数校验，调用 service 层
- 入口: internal/handler/
- 依赖: service 层

### service（业务逻辑）<!-- 待确认 -->
- 职责: 订单业务逻辑，事务编排
- 入口: internal/service/
- 依赖: repository 层

### repository（数据访问）<!-- 待确认 -->
- 职责: 数据库 CRUD
- 入口: internal/repository/
- 依赖: GORM + MySQL
```
