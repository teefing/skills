# APM Trace、GenAI Trace 与业务 AI session

先辨认用户要的是通用调用链、GenAI 语义 span、业务 AI session 的多 turn 轨迹，还是 Argos Agent 的执行 session。已知 ID 的取数与固定多步编排是确定性任务，不因 span/turn 数量多就改走 `argos run`。

## 对象与入口

| 对象/目标 | 首选入口 | 说明 |
| --- | --- | --- |
| 已知 traceID/logID 的全量调用链 | `bytedtrace.get_trace` | 返回 RPC/HTTP/内部/GenAI 等全量 span |
| 只看 GenAI 语义 span | `bytedtrace.get_ai_trace` | 与 get_trace 入参相近，但只保留 Agent/Model/Tool/Prompt 等 GenAI span |
| 按 PSM 浏览通用 span | `bytedtrace.get_span_list` | 需要 category/type，可按 tag 和 cursor 过滤 |
| 按 PSM 浏览 GenAI span | `bytedtrace.get_ai_span_list` | 自动限定 GenAI scope，不需要 category/type |
| Trace 错误、耗时、LogID 提取 | `trace.inspect` | 查询后做结构化后处理，仍是确定性 Tool |
| 业务 AI session 发现 | `argos ai-agent-session list` | 在必填 Unix 秒时间范围内取一页 Session；显式 page token 翻页 |
| 业务 AI session 全轨迹 | `argos ai-agent-session get` | 先取 index，再固定并发取 turn detail 并聚合 |
| 业务 session 单次 index/detail | `query_session_index` / `query_session_detail` | 只调用一个 MCP Tool |
| Argos 调查执行 session | `argos run --session`、`argos session list/get` | 与业务 AI session 不是同一种 ID，见 `argos-agent.md` |

普通服务 APM、依赖拓扑、LogID 调用树与多 region/TTP 路径仍优先使用 `bytedance-apm` / `bytedance-log` 已有覆盖。用户明确要求 Argos 全量/GenAI span、这里的 session 编排或 `trace.inspect` 时可直接进入本页。

## Trace 查询

```bash
# 全量 span
bytedcli argos tool bytedtrace.get_trace \
  --query-id '<trace-or-log-id>' \
  --region China-North

# 只保留 GenAI span；可附带时间窗
bytedcli argos tool bytedtrace.get_ai_trace \
  --query-id '<trace-or-log-id>' \
  --start-at 1722848400 \
  --end-at 1722852000

# 按 PSM 检索 server span
bytedcli argos tool bytedtrace.get_span_list \
  --psm example.service \
  --category span \
  --type server \
  --duration 1h \
  --limit 50

# 通用 span 带 tag 过滤
bytedcli argos tool bytedtrace.get_span_list \
  --psm example.service \
  --category span \
  --type server \
  --filter-tags '[{"tag_key":"_status_code","operator":"=","values":["500"]}]' \
  --duration 1h

# GenAI span 列表
bytedcli argos tool bytedtrace.get_ai_span_list \
  --psm example.ai.service \
  --duration 1h \
  --limit 50

# 已知 ID 的错误/耗时/LogID 结构化诊断
bytedcli argos tool trace.inspect \
  --query-id '<trace-or-log-id>' \
  --region China-North
```

`get_span_list` 支持 span/event/metric category、server/client 等 type、时间窗和 cursor context；`get_ai_span_list` 自动聚焦 GenAI span。实际字段以 `-h` / `--schema` 为准。

## 业务 GenAI session：确定性 CLI 编排

```bash
# 查询一页 session；示例 PSM 是占位值，TRAE CLI/IDE 请以 live MCP schema 中的 canonical monitoring PSM 为准
bytedcli argos ai-agent-session list \
  --psm example.ai.service \
  --start 1761000000 \
  --end 1761003600 \
  --page-size 20

# 下一页必须重复同一时间范围，并原样传回 opaque page token
bytedcli argos ai-agent-session list \
  --psm example.ai.service \
  --start 1761000000 \
  --end 1761003600 \
  --page-size 20 \
  --page-token '<previous-page-token>'

# 查询 session index，并以固定 5 路并发取回 turn detail
bytedcli argos ai-agent-session get \
  --psm example.ai.service \
  --session-id '<business-session-id>' \
  --access-mode personal \
  --max-turns 50 \
  --timeout-ms 30000

# 只取某个 user message 对应的 turn
bytedcli argos ai-agent-session get \
  --psm example.ai.service \
  --session-id '<business-session-id>' \
  --user-message-id '<user-message-id>' \
  --access-mode viewer

# 完整结构化内容
bytedcli --json argos ai-agent-session get \
  --psm example.ai.service \
  --session-id '<business-session-id>'
```

`ai-agent-session list` 不提供默认时间范围或自动翻页。`--start/--end` 是 Unix 秒级左闭右开区间，必须满足 `start < end`；`--page-size` 默认为 20，必须在 1～100。默认 `access_mode=personal`；按指定 `--user-id` 查询时必须同时使用 `--access-mode viewer`。文本模式直接 pretty-print Tool 原始 JSON data，全局 `--json` 仅增加 bytedcli 标准 envelope，不组装表格。

省略 `--user-message-id` 时，CLI 先读取 session index，再并发获取 turn detail，并按 index 顺序输出；单个 turn 失败不会丢弃其它成功结果。默认最多 50 个 turn，`--max-turns` 范围 1–200。指定 `--user-message-id` 时只取对应 turn。

`--access-mode` 仅支持 `personal`（默认）或 `viewer`，并原样传给 index/detail Tool。每个调用默认超时 30 秒，`--timeout-ms` 可设 1000–120000 毫秒。文本模式只显示摘要与 turn 表格；全局 `--json` 返回完整轨迹。

结果字段：

- `query_scope` 区分 `session` 与 `single_turn`。
- `session_index_queried` 表示是否查过 index。
- `index_turns_truncated` 是后端 index 是否截断；`turns_limited_by_max` 是 CLI 是否因 `--max-turns` 截断。
- `failed_turn_message_ids` 支持逐 turn 重试；`returned_turn_count` 是本次成功返回数。即使全部 detail 失败，也保留失败 ID 清单。

命令按全局 `--site` 选择控制面。已验证 canonical site 为 `cn`、`boe`、`i18n`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`；`us-ttp-bdee` / `us-ttp-usts` 作为兼容输入归一化到 `us-ttp`，但 USTS 入口尚未完成可用性验证，调用时优先显式使用 `--site us-ttp`。不支持的控制面会在 MCP 调用前报错。

## 业务 session：单次 Tool

```bash
bytedcli argos tool bytedtrace.query_session_list \
  --psm example.ai.service \
  --start-time 1761000000 \
  --end-time 1761003600 \
  --limit 20 \
  --access-mode personal

bytedcli argos tool bytedtrace.query_session_index \
  --psm example.ai.service \
  --session-id '<business-session-id>' \
  --access-mode personal

bytedcli argos tool bytedtrace.query_session_detail \
  --psm example.ai.service \
  --session-id '<business-session-id>' \
  --user-message-id '<user-message-id>' \
  --access-mode personal
```

直接 Tool 的 `access_mode` 是后端原始字符串字段；示例显式使用 `personal`。需要全部 turn 时优先现有 CLI 编排，不要由宿主重复实现并发聚合。

## 不要混淆两类 session

- **业务 GenAI session**：由业务 PSM + `session_id` 标识，包含多个 user message/turn；用 `ai-agent-session list` 发现，再用 `get` 或 session index/detail 查询。
- **Argos 执行 session**：由 `argos run` 返回，记录一次服务端调查；追问用 `bytedcli argos run --session '<execution-session-id>' --prompt ...`。

如果需求只是恢复业务 turn 轨迹，固定 index→detail 多步已经有确定性 CLI；只有需要跨 turn 解释原因、按证据继续查其它域时，才进入 [Argos Agent 调查](./argos-agent.md)。

## 结果判断

确认 query ID/PSM、控制面、时间窗、span 范围和过滤条件。`get_ai_trace` 缺少通用 span 不代表链路缺失；它本来就过滤到 GenAI。session 部分 turn 失败时，结论必须标出失败 ID 与截断状态。Trace/turn 取数完成也不自动等于根因已确定；需要解释时再用开放式调查。
