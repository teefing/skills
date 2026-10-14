# 写入范例

展示每种知识类型写入目标文件时的具体格式，确保输出一致性。

---

## 红线 → AGENTS.md

在 `## 红线` 章节下追加一行：

**写入前**：
```markdown
## 红线

- 禁止在代码中硬编码密钥、Token 或数据库密码
- 禁止绕过 golangci-lint 检查提交代码
```

**写入后**（新增第 3 条）：
```markdown
## 红线

- 禁止在代码中硬编码密钥、Token 或数据库密码
- 禁止绕过 golangci-lint 检查提交代码
- 禁止直接调用 legacy API，必须通过 gateway 转发
```

**合并示例**（已有类似条目时替换而非追加）：

写入前：`- 禁止在 handler 层直接操作数据库，必须通过 repository 层`
写入后：`- 禁止在 handler 或 service 层直接写 SQL，所有数据库操作必须通过 repository 层`

→ 范围扩大了（handler → handler/service），用更精确的版本替换旧版本。

---

## 约定 → conventions.md

在对应章节追加：

**业务规则示例**：
```markdown
## 业务规则

- 订单状态只能单向流转：created → paid → shipped → delivered → completed，不可回退
```

**踩坑记录示例**：
```markdown
## 踩坑记录

- user_id 字段在 legacy_users 表中是 varchar(64) 不是 int，JOIN 时不走索引，需要显式 CAST
- Redis 缓存订单数据的 TTL 不能超过 30 分钟，否则与数据库状态不一致（2026-05-14 发现）
```

**Review 规则示例**：
```markdown
## Code Review 规则

- 所有 error 必须 wrap context 后返回，不允许裸 return err
- 新增 API 必须同时补充 testing.md 中的冒烟测试用例
```

---

## 架构 → architecture.md

**新增模块**：
```markdown
### user-profile（用户画像）
- **职责**: 管理用户偏好、标签、画像数据
- **入口**: internal/service/user_profile.go
- **依赖**: user-core（基础用户数据）、Redis（缓存）
```

**更新已有模块**（追加依赖信息）：

写入前：
```markdown
### order（订单）
- **职责**: 订单 CRUD
- **入口**: internal/handler/order.go
- **依赖**: repository 层
```

写入后：
```markdown
### order（订单）
- **职责**: 订单创建、查询、状态管理
- **入口**: internal/handler/order.go
- **依赖**: repository 层, payment-service (gRPC)
```

---

## 依赖 → dependencies.md

**新增下游服务**：

在 `## 下游` 表格中新增一行：

```markdown
| 支付服务 (payment-service) | 订单支付 | gRPC | PaymentService.CreatePayment |
```

---

## 决策 → decisions.md（ADR 格式）

追加一个新的 ADR：

```markdown
## ADR-003: 使用 gRPC 作为内部服务通信协议

- **日期**: 2026-05-14
- **状态**: accepted
- **背景**: 订单服务需要调用支付服务，需要选择通信协议
- **决策**: 使用 gRPC，基于 protobuf 定义接口
- **替代方案**: HTTP REST — 放弃原因：内部服务间调用不需要 REST 的可读性优势，gRPC 性能更好且有强类型约束
- **影响**: 需要维护 proto 文件，服务间依赖通过 proto 定义而非文档
- **来源**: MR !342 | 分支 feat/payment-integration | 开发人 @zhangsan
```

---

## 测试 → testing.md

**新增冒烟测试用例**：

在 `### 冒烟测试` 表格中追加：

```markdown
| 创建订单 | POST /api/v1/orders `{"item":"book","qty":1}` | 200, 返回 order_id |
| 查询订单 | GET /api/v1/orders/123 | 200, 返回订单详情 |
```

**新增测试注意事项**：

```markdown
## 测试注意事项

- 涉及支付的测试必须走 mock，不能调真实支付网关
- 集成测试前需要先 make seed-db 导入测试数据
```

**新增部署信息**：

```markdown
## 云端部署 & 测试

### 部署到 PPE 环境
使用 bits_env_cli 部署：
bits_env_cli deploy --env ppe --psm order.service --branch main

### 泳道选择
- 默认泳道: base
- Feature 测试: 创建独立泳道 bits_env_cli lane create --name feature-xxx
```

---

## ⚠️ 反面示例

### 不要沉淀开发过程噪声

以下是开发对话中常见的内容，看起来像"知识"但实际不值得沉淀：

```
❌ "把 OrderService 的 CreateOrder 方法中第 42 行的 if err != nil 改成了 switch"
   → 代码改动细节，看 git diff 就知道，不需要写进 Context

❌ "先试了用 sync.Map 做缓存，发现并发性能不够，改用了 Redis"
   → 调试过程。如果最终决策值得记录，只记结论："使用 Redis 做缓存（非 sync.Map），因为多实例共享"

❌ "运行 go test 报错 connection refused，发现是 MySQL 没启动，docker-compose up 后解决"
   → 一次性的环境问题，不会反复出现

❌ "在 handler 里加了参数校验，检查 order_id 非空"
   → 具体代码实现，Agent 读代码就知道

❌ "安装了 grpc-go 依赖，版本 1.62.0"
   → go.mod 里有，不需要重复
```

### 不要写叙事历史

```
❌ 2026-05-14 小明发现 user_id 类型不对导致慢查询，经过排查后修复
✅ user_id 字段在 legacy_users 表中是 varchar(64) 不是 int，JOIN 时不走索引
```

**不要写调试过程**：
```
❌ 先试了直接 JOIN，发现慢，然后加了索引，还是慢，最后发现是类型不匹配
✅ user_id 字段在 legacy_users 表中是 varchar(64)，JOIN 时需要显式 CAST 或加函数索引
```

**不要写相对时间**：
```
❌ 上周发现的问题
✅ 2026-05-08 发现的问题
```

**不要无脑追加**：
```
❌ 已有："禁止直接写 SQL"
   追加："禁止在 service 层写 SQL"（重复了）
✅ 将已有条目更新为更精确的版本："禁止在 handler/service 层直接写 SQL"
```
