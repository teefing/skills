---
name: bytedance-argos
description: "Use Argos through bytedcli for monitoring and runtime data of backend services: logs, Measurement and Metrics, alarms, dashboards, APM and GenAI traces, and AI session evidence. Use it for Argos-specific deterministic queries, open-ended Argos Agent investigations, capabilities not covered by the dedicated log/APM entries, or explicit Argos requests."
---

# bytedcli Argos

查询与分析服务端服务的监控和运行数据。先按任务能力、数据对象和控制面选择入口，再选择确定性操作或开放式调查；不要把“步骤多”本身当作转入 Argos Agent 的理由。

## 最短调用

使用全局安装的 `bytedcli`，先确认认证，再按目标控制面调用：

```bash
bytedcli auth status
bytedcli argos tool list --search trace
bytedcli argos tool bytedtrace.get_trace --query-id '<trace-or-log-id>'
bytedcli argos run --prompt '分析 example.service 在 China-North 最近 30 分钟异常的原因'
```

安装、认证、全局参数和 JSON 输出见 [bytedcli 通用调用方式](./../../invocation.md)。

## 先选能力入口

1. **普通日志或 APM 任务且专用入口覆盖目标控制面**：优先读取 `bytedance-log` 或 `bytedance-apm`。它们仍负责 Footprint、Pod/实例/泳道、普通 LogID 分析、多 region、TTP、Bosun、报警规则/值班计划等各自能力。
2. **已知需要 Argos 独有能力、专用入口不覆盖，或用户明确指定 Argos / 某个 Argos tool**：直接使用本 Skill，不必先做一次注定不适用的调用。
3. **执行中才发现证据不足**：按缺少的数据或调查能力转入本 Skill；不要重复已经完成的查询。
4. **控制面先于命令**：`--site` 必须与目标 region 一致。EU/US TTP 使用各自的 canonical Argos 控制面，不能静默改用 `i18n-tt` 代查；USTS 兼容输入尚未完成可用性验证。

## 再选执行方式

| 任务形态 | 执行方式 |
| --- | --- |
| 已知输入的取数、元数据检查、单次调用 | `bytedcli argos tool <tool>` |
| 步骤和停止条件都确定的多步查询 | 依次调用 Tool，或使用现有确定性 CLI 编排 |
| 需要根据中间证据决定下一步、解释异常或归因 | `bytedcli argos run --prompt ...` |
| 继续一次 Argos 调查 | `bytedcli argos run --session '<id>' --prompt ...` |

例如，先取 session index 再取多个 turn、先查 metric 元数据再查 data，虽然是多步，仍属于确定性操作。同一 LogID/TraceID 的“把数据取出来”和“解释为什么异常”也可以选择不同方式。

## 能力目录

按任务只读取需要的参考页：

| 能力 | 首选路径 | 读取条件 |
| --- | --- | --- |
| 关键词/KV日志、LogID、错误聚合、Pod 本地日志 | [日志查询与分页](./references/log.md) | 明确使用 Argos 日志 Tool，或专用日志入口不覆盖 |
| Measurement、Metrics、Dashboard、Bosun/查询 URL | [监控对象与查询](./references/monitoring.md) | 先辨认对象，再选取数、纠偏、巡检或写入路径 |
| APM Trace、GenAI Trace、业务 AI session | [Trace、GenAI 与业务会话](./references/ai-observability-tools.md) | 已知 trace/log ID、PSM、业务 session ID 或 turn |
| 服务健康、报警归因、巡检、规则优化、跨证据分析 | [Argos Agent 调查](./references/argos-agent.md) | 调查方向需要随证据变化，或需要解释/归因 |
| 已有报警规则诊断与优化 | [报警规则优化](./references/alarm-rule-optimization.md) | 识别 rule UID/PSM/群输入；方案需在预览页人工采纳 |
| Dashboard/Folder 创建、修改、迁移或导入 | [Dashboard Agent Session 操作](./references/dashboard-operation.md) | 服务端 project 提供能力；写入前先预览并遵守授权 |
| site 与 region 对照 | [Region 与控制面](./references/regions.md) | 目标不是默认 CN，或 region/站点不确定 |
| 认证、参数、权限、连接问题 | [故障排查](./../../troubleshooting.md) | 命令失败或返回缺权限/不支持 |

## 监控对象与会话对象先辨识

| 用户给出的对象 | 不要混淆 | 正确下一步 |
| --- | --- | --- |
| Measurement / 服务测点 | Measurement 显示名不等于 metric 名 | 核实服务、精确标识/定义、维度和时间；已知查询的纠偏或元数据检查才用 `timeseries.inspect` |
| metric / 表达式 | 指标名、聚合/字段、Tag 是不同输入 | 使用专用 APM 或 Argos Metrics Tool；必要时先发现元数据 |
| Dashboard / Folder | 读面板数据、巡检和修改是不同任务 | 按目标路由；写入/导入走 Agent Session 服务端能力，不虚构直接 Tool |
| 业务 GenAI session | 业务 `session_id` 对应多个 turn | 已知 PSM 和秒级时间范围时用 `argos ai-agent-session list` 发现 Session；之后用 `get` 或 session index/detail Tool，仍是确定性查询 |
| Argos 执行 session | `argos run` 返回的调查会话 ID | 普通追问用 `argos run --session`；权限型待处理不能当作普通追问 |

## 控制面边界

| `--site` | 控制面 | 典型 Region |
| --- | --- | --- |
| `cn`（默认） | 国内 | China-North、China-East、ChinaSinf-North、China-PPE |
| `boe` | 测试 | China-BOE、US-BOE、ChinaSinf-BOE |
| `i18n` / `i18n-tt` | 海外 TT | Singapore-Central、US-East、Europe-Central、US-West |
| `i18n-bd` | 海外 BD/Lark | Singapore-SaaS、US-EE、Singapore-Common、Europe-WestBD |
| `us-ttp` | 美国 TTP | US-TTP、US-TTP2 |
| `eu-ttp` | 欧洲 TTP | EU-Compliance、EU-TTP、EU-TTP2、US-EastRed |

`argos tool` 与 `argos ai-agent-session list/get` 支持上表 site；`argos run`、`argos session list/get` 暂不接受 `i18n` 别名，应使用同路由的 `i18n-tt`。`eu-ttp-limited` / `eu-ttp-full` 归一化到 `eu-ttp`；`us-ttp-bdee` / `us-ttp-usts` 是归一化到 `us-ttp` 的兼容输入，不是独立 Argos 控制面，且 USTS 入口尚未完成可用性验证。TTP 不能改用 `i18n-tt` 代查。完整映射见 [Region 与控制面](./references/regions.md)。

## 服务账号 JWT

受管环境优先使用站点级变量，避免 credential partition 串用：

| Argos `--site` | 服务账号 JWT 环境变量 | credential site |
| --- | --- | --- |
| `cn` / `boe` | `BYTEDCLI_SERVICE_ACCOUNT_JWT_CN` | `cn` |
| `i18n-tt` | `BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_TT` | `i18n-tt` |
| `i18n` / `i18n-bd` | `BYTEDCLI_SERVICE_ACCOUNT_JWT_I18N_BD` | `i18n-bd` |
| `us-ttp` / `us-ttp-bdee` / `us-ttp-usts` | `BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP` | `us-ttp` |
| `eu-ttp` / `eu-ttp-limited` / `eu-ttp-full` | `BYTEDCLI_SERVICE_ACCOUNT_JWT_EU_TTP` | `eu-ttp` |

也可用通用 `BYTEDCLI_SERVICE_ACCOUNT_JWT`。credential site 只决定读取哪个 JWT，不决定数据 region 或入口已验证状态；不要创建 BDEE/USTS 专用的 US JWT 变量。

- `argos run` 使用服务账号时必须显式传 `--project`。
- `argos tool` 与 `argos ai-agent-session list/get` 没有 `--project`，服务账号场景必须设置 `BYTEDCLI_ARGOS_PROJECT`。`query_session_list` 是否允许服务账号还取决于 BytedTrace 当前路由权限，本命令不绕过后端鉴权。
- 设置 `BYTEDCLI_ARGOS_AGENT_HOST` 自定义 Agent Session transport 时，`argos run/session` 不会向该地址发送受管环境注入的服务账号 JWT；使用个人或显式测试凭据。该变量不影响 SDK transport。
- 设置 `ARGOS_SERVER_URL` 自定义 SDK transport 时，`argos tool` 与 `ai-agent-session` 不会向该地址发送受管环境注入的服务账号 JWT；使用个人或显式测试凭据。该变量不影响 Agent Session transport。

## Tool 通用调用

```bash
# 服务端当前开放的 tool 与 schema
bytedcli argos tool list
bytedcli --json argos tool list --namespace metrics
bytedcli argos tool bytedtrace.get_trace --schema
bytedcli argos tool bytedtrace.get_trace -h

# 结构化参数：会经过该 tool 的 bytedcli 参数优化
bytedcli argos tool bytedtrace.get_trace \
  --query-id '<trace-or-log-id>' \
  --region China-North

# 原始 JSON：单次透传，不补默认值，也不自动分页
bytedcli argos tool bytedtrace.get_trace \
  --input '{"query_id":"<trace-or-log-id>","region":"China-North"}'
```

- 静态子命令 schema 随 bytedcli 发布；服务端能力可能变化，用 `tool list` 和具体命令的 `-h` / `--schema` 核对。
- object/array 参数必须是合法 JSON；普通数组也可按命令帮助使用逗号分隔。
- 结构化时间参数可接受 RFC3339、Unix 秒/毫秒、`now`、`1h ago`；实际转换和默认值以对应 handler 及 `-h` 为准。
- 查询失败时先保留完整错误并判断参数、权限、控制面或服务端问题；不要无条件重试。参数校验错误先修正参数。
