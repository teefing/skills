# Argos Agent 调查

`bytedcli argos run` 把开放式调查交给服务端 Argos Agent。适用于需要根据中间证据决定下一步、跨日志/监控/Trace/报警关联、解释异常或形成根因结论的任务。已知输入的取数和停止条件固定的多步编排继续使用 Tool 或专用 CLI，不因步骤多就调用 Agent。

## 调查场景

| 场景 | 提供的必要上下文 | 预期结果与边界 |
| --- | --- | --- |
| 服务健康与可用性 | PSM、region、绝对时间窗、异常表现 | 汇总关键证据并指出不确定项；普通确定性 QPS/SLA 取数可先用 APM |
| Dashboard 巡检 | Dashboard/团队、时间窗、关注指标 | 识别异常面板并给出证据；修改大盘须单独走预览/授权流程 |
| 报警归因 | 报警链接/ID、服务、region、触发时间 | 解释触发证据和可能根因；查规则或计划等确定性操作不必走 Agent |
| 报警规则优化 | rule UID/PSM/群、目标控制面、误报/漏报目标 | 读取 [报警规则优化](./alarm-rule-optimization.md)；只生成待采纳方案，不自动应用 |
| 日志原因分析 | PSM、region、固定时间窗、关键词/样例日志 | 根据日志决定是否补查其它信号；普通日志取数仍优先专用 log |
| APM/Trace 分析 | Trace/Log ID 或服务、region、时间窗、异常目标 | 关联错误/耗时/依赖；仅获取 span 时用确定性 Trace Tool |
| GenAI 调用分析 | PSM、trace/session/turn、时间窗、关注问题 | 解释 Agent/Model/Tool/Prompt 证据；业务 session 取数仍可用确定性 CLI |
| 多轮业务会话归因 | 业务 PSM、session ID、相关 turn 或现象 | 跨 turn 归因；不要把业务 session ID 当作 Argos 执行 session ID |
| 运行证据关联源码 | 已核实的运行版本、证据、可访问的安全工作区 | 只能分析执行端实际可见的代码；宿主目录不会自动成为服务端工作区 |

## 新建与继续调查

```bash
# 新建调查
bytedcli argos run \
  --prompt '分析 example.service 在 China-North 2026-10-15 10:00-10:30+08:00 错误率突增的原因'

# 继续同一个 Argos 执行 session
bytedcli argos run \
  --session '<session-id>' \
  --prompt '基于已取得证据，继续核对最可疑下游'

# 海外 TT 控制面
bytedcli --site i18n-tt argos run \
  --prompt '分析 example.i18n.service 在 Singapore-Central 最近 30 分钟的异常'
```

恢复使用 `--session`；不要写成独立 argos CLI 的 `run resume`。查询中明确 PSM、region、绝对时间窗、用户已知现象和已做过的查询，避免重复取证。

## 常用参数

| 参数 | 说明 |
| --- | --- |
| `--prompt <text>` | 发送给 Agent 的自然语言任务 |
| `--project <name>` | 指定服务端 project；用户 JWT 可省略，服务账号 JWT 必须显式传入 |
| `--session <id>` | 继续既有 Argos 执行 session |
| `--fs-base-path <path>` | interactive 模式本地 `fs.*` 根目录；默认按 `ARGOS_HOME`、`~/.sre-agent`、`/tmp/.sre-agent-<UID>` 选择可读写位置，再使用其下 `sessions/<session-id>/` |
| `--model <name>` | 模型覆盖 |
| `--max-turns <n>` | 最大 Agent 工具轮次 |
| `--timeout-ms <ms>` | 默认 300000；复杂任务可显式使用 600000 |
| `--format text\|stream-json` | 默认文本或 JSONL 实时事件流 |
| `--execution-profile interactive\|server\|auto` | WS 交互、同步 HTTP 或自动降级 |
| `--verbose` | 增加经过脱敏和截断的工具参数/结果摘要 |

```bash
# 机器可读最终对象；全局 --json 必须放在 argos 前
bytedcli --json argos run --prompt '分析 example.service 最近的报警'

# JSONL 实时事件流
bytedcli argos run --prompt '分析 example.service 最近的报警' --format stream-json

# 同步 HTTP，只返回最终终态，不提供实时工具进度或反向本地工具
bytedcli argos run --prompt '分析 example.service 最近的报警' --execution-profile server

# 限制 interactive 模式可访问的本地工作区
bytedcli argos run --prompt '关联当前版本源码定位异常路径' --fs-base-path ./safe-workspace
```

全局 `--json` 与 `--format stream-json` 不能同时使用。

## 输出与终态

- **默认文本**：stdout 只输出最终回答；stderr 展示 session、连接、用户可见的简短 thought/工具动作、告警和人工动作。模型内部 thinking、工具结果以及内部 `fs.*` / `finish` 不直接展示。
- **全局 JSON**：stdout 只输出一个最终对象，适合脚本读取；它不是实时进度流。
- **`stream-json`**：stdout 每行一个 `{type,timestamp,data}` 事件；每次运行只有一个 `result`、`needs_input` 或 `error` 终态。工具事件以 `call_id` 关联，`tool_finished` 包含 `duration_ms` 和 `success`。
- 机器可读工具事件使用 `name` 并通过 `call_id` 关联；其它过程事件按类型使用 `session_id`、`status`、`stage` 或 `code`。最终对象的 `tool_calls[].duration_ms` 稳定为数字或 `null`；`--verbose` 只增加经过截断、脱敏的有界摘要。
- **`server` profile**：同步 HTTP，固定 `stream=false, async=false`，不伪造实时工具事件，也不接受服务端反向发起的本地 `fs.*` 调用。`auto` 只在 WS 不可用时降级到同一同步 HTTP 路径。需要实时进度或本地工具时用默认 `interactive`。
- 终态退出码：成功 0、失败/异常 1、`needs_input` 2。

全局 JSON 成功对象的核心字段包括 `status`、`data.session_id`、`data.content`、`data.success`、`data.token_usage` 和 `data.files_modified`。不要只看自然语言文本而忽略终态、待处理事项和证据范围。

## `needs_input`、权限与恢复

- 普通问答型 `needs_input`：补充用户信息后，使用返回的执行 session ID 通过 `--session` 继续。
- 权限型 `needs_input`：只报告待授权 Tool、pending 状态与执行 session。bytedcli 当前不实现 Tool 审批交互，必须转到组织认可且支持该流程的客户端；不能用普通 follow-up 假装批准，也不要自动绕过权限。批准后是否自动恢复或仍需续接由审批客户端/服务端决定，不在这里承诺。
- project、控制面或服务端没有提供某能力时，保留原始错误并说明缺口，不要把缺失 Tool 当作数据为空。
- 用户 JWT 且未传 `--project` 时使用个人 project；服务账号 JWT 无法可靠派生个人 project，`argos run` 必须显式传 `--project`。
- 多次独立调查串行执行，避免会话证据和输出交叉。

## 本地工作区与源码证据

interactive 模式可通过 SDK 处理服务端发起的 `fs.*` 本地工具调用。默认按 Argos CLI 的顺序尝试 `ARGOS_HOME`、`~/.sre-agent`、`/tmp/.sre-agent-<UID>`，会话文件根目录是所选位置下的 `sessions/<session-id>/`。每个候选会话目录先创建并检查读、写和遍历权限，不可用则尝试下一位置；所有位置都不可用时保留 `ARGOS_SESSION_DIRECTORY_UNAVAILABLE` 错误码和修复提示，`details.attempts` 按尝试顺序仅记录候选根目录 `root` 与失败错误码 `code`，不包含原始错误 `message`。不可信临时目录使用统一拒绝码 `UNTRUSTED_TMP_DIRECTORY`；无可用错误码的目录初始化失败使用 `DIRECTORY_INITIALIZATION_FAILED`。没有 `getuid` 的平台使用进程 ID 代替 UID。

新建目录使用 `0700` 权限。仅 `/tmp/.sre-agent-<UID>` 回退分支会逐级检查临时根目录、`sessions` 和具体会话目录：它们必须是真实目录，且不可由组或其他用户写入；有 UID 时还检查归属当前用户。该回退分支拒绝不可信既有目录或符号链接，也不会对它们修改权限。`ARGOS_HOME` 和 `~/.sre-agent` 分支仅创建会话目录并检查读、写和遍历（R/W/X）权限，不执行这套临时目录的类型、归属与组或其他用户写权限校验。

运行产物位于会话目录，例如 `workspace/outputs/`，当前项目通过会话内的 `projectspace` 符号链接访问。同一可用位置下继续既有会话会复用目录和原有项目链接。项目链接创建发生非 `EEXIST` 错误时，返回 `ARGOS_PROJECTSPACE_LINK_UNAVAILABLE`，保留原始错误为 `cause`，并通过 `hint` 提示开启符号链接支持、使用支持符号链接的文件系统或显式传入 `--fs-base-path`。Windows 未启用符号链接支持（如开发者模式）及不支持符号链接的文件系统可能触发此错误；运行仍会中断，不会降级为警告后继续。

显式传入 `--fs-base-path` 时，`fs.*` 直接使用指定目录，不创建默认会话目录或项目链接。关联源码前先核实线上运行版本与本地 checkout 是否匹配，并确认实际执行 profile 能访问目标工作区。

## Dashboard 操作

Dashboard/Folder 创建、修改、复制、迁移或导入由 Agent Session 内服务端提供的 `dashboard-operation` 能力执行，不注册为直接 `argos tool`，`tool list` 也不能判断其会话内可用性。写任务必须明确对象、site/region，并要求先预览；详见 [Dashboard Agent Session 操作](./dashboard-operation.md)。

## 执行 session 管理

```bash
bytedcli argos session list
bytedcli argos session list --project my-team-project --page 2 --page-size 10
bytedcli --json argos session list

bytedcli argos session get --id '<execution-session-id>'
bytedcli --json argos session get --id '<execution-session-id>'
```

这里管理的是 **Argos 执行 session**。业务 GenAI session 的 PSM/session ID/turn 取数见 [Trace、GenAI 与业务会话](./ai-observability-tools.md)。

## 结果判断

结论应给出时间窗、控制面、使用过的主要证据、已确认事实、推断和未验证项。若 Agent 只取得部分日志、无权限、某控制面不支持或代码版本未核实，必须显式降低结论强度。调查完成不等于执行了任何建议变更；写操作仍需按能力的预览、授权和确认边界处理。
