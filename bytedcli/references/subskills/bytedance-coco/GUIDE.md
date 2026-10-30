---
name: bytedance-coco
description: "Coco AI Code Agent 的 bytedcli 命令，含两套入口：旧 Codebase Copilot（coco task/chat/sandbox/env）直接发编程任务；Coco Managed Agent（MA，OpenAPI Next）按资源操作 workspace/device/agent/session/run，包括创建 Agent 与 Session、发多模态消息、SSE 订阅、确认工具调用、查历史事件与 Run、取消 Run、查 token 用量、中断和清理。当用户提到 Coco、Codebase Copilot、Coco Managed Agent、Coco MA、OpenAPI Next，或 coco task/workspace/agent/session/run 命令，或要创建、订阅、中断 Coco session、批准其中待确认的工具调用时使用。"
---

# Coco AI Code Agent

Coco 目前有两套并行入口，先按用户意图选对模型：

- **Copilot（旧入口）**：一次性或多轮编程任务，使用 `coco task/chat/sandbox/env`。
- **Managed Agent（Coco MA，OpenAPI Next）**：先创建长期 Agent 配置，再按任务创建 Session，使用 `coco workspace/device/agent/session/run`。

## 前置条件

- 与 Codebase 共用认证：先执行 `bytedcli auth login`。
- 通用调用方式见 `../../invocation.md`。
- 需要稳定机器输出时把全局 `--json` 放在 `coco` 前：`bytedcli --json coco ...`。

## Managed Agent：完整创建闭环

Agent 创建必须显式使用 Workspace 中的 Device。不要猜或自动选择 Device ID。

```bash
# 1. 创建 Workspace；创建后平台会注册系统 Device
bytedcli coco workspace create \
  --name "demo-managed-agent" \
  --slug demo-managed-agent

# 2. 查询 Device，选择 Kind=system，记录其 Device ID 和 Runtimes
bytedcli coco device list --workspace-id <workspace-id>

# 3. 创建长期 Agent 配置
bytedcli coco agent create \
  --workspace-id <workspace-id> \
  --name "demo-agent" \
  --device-id <system-device-id> \
  --runtime traex \
  --instruction "Reply concisely." \
  --permission-mode dont-ask

# 4. 每次任务创建 Session
bytedcli coco session create \
  --workspace-id <workspace-id> \
  --agent-id <agent-id>

# 5. 发送消息；记录返回的 Event ID
bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --message "Reply with READY"

# 6. 从用户消息之后订阅，收到 Idle/Terminated 后退出
bytedcli coco session subscribe \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --after-event-id <event-id> \
  --until-idle \
  --timeout-ms 300000
```

`--after-event-id` 是事件游标，不是 Run ID。断线后用最后一个 `last_event_id` 续订：

```bash
bytedcli coco session subscribe \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --after-event-id <last-event-id>
```

订阅默认持续运行。Text 模式将 `AgentMessage` 流式写到 stdout，将 thinking、tool、queued/running/idle/terminated，以及子线程（`[thread created]`、`[thread message]`、`[thread idle]` 等）和模型请求排队/重试（`[model queued]`、`[model retry]`）摘要写到 stderr；`--until-idle` 只在 Session 级 idle/terminated 时退出，子线程 idle 不会结束订阅；JSON 模式每行输出完整事件 envelope，并在正常结束时输出带 `last_event_id`、`requires_action_event_ids` 的 success 总结。

## Managed Agent：工具确认

Agent 使用 `--permission-mode default` 等需要审批的模式时，工具调用会让 Session 停在 idle，`SessionStatusIdle.StopReason.RequiresAction.EventIds` 列出待确认的 `agent.tool_use` 事件 ID。`subscribe` 的 text 模式会实时打印 `[idle] action required: <ids>`，订阅结束时（例如加了 `--until-idle`）再在 stderr 给出带 `--decision allow` 的 `confirm` 命令模板；JSON 模式看 success 总结里的 `requires_action_event_ids`。是否需要审批由 runtime 决定（例如 `traex` 在 `default` 模式下也可能直接执行工具），以是否出现 `RequiresAction` 为准，不要预设。

```bash
# 列出整个 Workspace 里所有待确认的工具调用；Event ID 即 --tool-use-event-id，Session ID 即 --session-id
bytedcli coco session pending --workspace-id <workspace-id>

# 允许；可用 --updated-input-json 改写工具入参（必须是 JSON 对象）
bytedcli coco session confirm \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --tool-use-event-id <event-id> \
  --decision allow

# 拒绝；--deny-message 会反馈给 Agent
bytedcli coco session confirm \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --tool-use-event-id <event-id> \
  --decision deny \
  --deny-message "Do not modify files"

# 确认后从 idle 事件之后继续订阅
bytedcli coco session subscribe \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --after-event-id <last-event-id> \
  --until-idle
```

- allow / deny 是用户的决定：先用 `session pending` 把工具名和入参展示给用户，按用户的选择确认，不要替用户自动批准。
- `--tool-use-event-id` 必须显式传，CLI 不自动挑选；优先用 `SessionStatusIdle.StopReason.RequiresAction.EventIds[0]`，多个待确认时对每个事件分别确认。
- `--deny-message` 只能配 `deny`，`--updated-input-json` 只能配 `allow`。
- 同一事件重复发送相同决定会成功返回；改成相反决定会报 `Conflict: tool already confirmed`。事件 ID 不是 `agent.tool_use` 时报 `NotFound.Tool event`。

## Managed Agent：查询 Session、历史事件与 Run

```bash
bytedcli coco session get --workspace-id <workspace-id> --session-id <session-id>
bytedcli coco session list --workspace-id <workspace-id> --agent-id <agent-id> --status idle --status running

# 历史事件：默认从最早开始正序；--order desc 从最新开始倒序
bytedcli coco session events --workspace-id <workspace-id> --session-id <session-id>
bytedcli coco session events --workspace-id <workspace-id> --session-id <session-id> --after-event-id <next-after-event-id>
bytedcli coco session events --workspace-id <workspace-id> --session-id <session-id> --order desc --page-size 50
bytedcli coco session events --workspace-id <workspace-id> --session-id <session-id> --order desc --before-event-id <next-before-event-id>

# 每个 Run 的 token 用量与执行耗时
bytedcli coco session stats --session-id <session-id>

# Run：list 必须带 --session-id 或 --agent-id
bytedcli coco run list --workspace-id <workspace-id> --session-id <session-id> --status running
bytedcli coco run get --run-id <run-id>
bytedcli coco run cancel --workspace-id <workspace-id> --run-id <run-id> --reason "no longer needed" --yes

# Device 详情（云端 Device 带 Sandbox ID 和 Webshell URL）
bytedcli coco device get --device-id <device-id>
```

`session events` 的游标是事件 ID，不是 `--page-token`：

- `--page-size` 取 1–500，默认 100。JSON 输出带 `page_size`、`current_count`、`next_after_event_id`、`next_before_event_id`，没有 `has_more`。
- 正序翻页：把 `next_after_event_id` 传给 `--after-event-id`，直到它不再变化；子 Agent 的事件会被跳过但仍推进游标，所以一页可能条数不足甚至为空，不要把空页当成结束。`next_after_event_id` 也可以直接传给 `session subscribe --after-event-id` 接着看实时事件。
- 倒序翻页：`--order desc` 加 `--before-event-id <next_before_event_id>`，直到 `next_before_event_id` 为 `null`。
- Text 模式与 `subscribe` 渲染一致（Agent 文本到 stdout，状态摘要到 stderr），`--order desc` 时按时间正序打印当页内容，并在 stderr 给出下一页命令。

`run cancel` 后 Run 状态变为 `closed`；对已结束的 Run 再次取消也会成功返回，结果以 `run get` 为准。`session stats` 中的 `TokenUsage` 视 runtime 而定，可能为空。

## Managed Agent：多模态消息

快捷模式固定按“文本 → 本地媒体 → URL 媒体 → Workspace FileId”组装。参数可重复：

```bash
bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --message "Compare these inputs" \
  --media-file ./sample-image.png \
  --media-file ./sample-report.pdf \
  --media-url https://example.com/sample.png \
  --file-id <workspace-file-id>
```

本地媒体读取后以内联 Base64 发送；已知扩展名会推断 MIME，未知扩展名使用 `application/octet-stream`。

需要保留 block 顺序或完整 wire shape 时，用精确模式，且不要与快捷参数混用：

```bash
bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --content-json '[{"Text":{"Text":"Inspect this"}},{"Media":{"SourceKind":"url","Url":"https://example.com/sample.png"}}]'

bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --content-file ./content-blocks.json
```

Media 分支规则：

- `base64`：必须有 `Data` 和 `MediaType`，不能有 `Url` / `FileId`。
- `url`：必须有 `Url`，不能有 `Data` / `FileId`。
- `file`：必须有 `FileId`，不能有 `Data` / `Url` / `MediaType`。

## Managed Agent：中断与清理

`interrupt` 直接发送，不需要 `--yes`。删除 Workspace/Agent、归档 Session、取消 Run 必须显式确认：

```bash
bytedcli coco session interrupt \
  --workspace-id <workspace-id> \
  --session-id <session-id>

bytedcli coco session archive \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --yes

bytedcli coco agent delete \
  --workspace-id <workspace-id> \
  --agent-id <agent-id> \
  --yes

bytedcli coco workspace delete \
  --workspace-id <workspace-id> \
  --yes
```

推荐按 Session → Agent → Workspace 的顺序清理。

## Markdown 多行换行（必读）

传多行 instruction 或 message 时使用 shell 的 `$'...'`，不要在普通双引号中写字面量 `\n`：

```bash
# 正确：shell 会传入真实换行
bytedcli coco agent create \
  --workspace-id <workspace-id> \
  --name demo-agent \
  --device-id <device-id> \
  --runtime traex \
  --instruction $'First line\nSecond line'

bytedcli coco session send \
  --workspace-id <workspace-id> \
  --session-id <session-id> \
  --message $'Check these items:\n- item one\n- item two'

# 错误：普通双引号不会把 \n 解释成换行
bytedcli coco session send ... --message "line one\nline two"
```

长文本优先使用 `--instruction-file` 或 `--message-file`。

## Copilot（旧入口）

旧能力保持不变，适合直接发任务，不需要先维护 Workspace/Agent/Session：

```bash
# 发任务并订阅结果
bytedcli coco task send --message "Fix the login bug" --repo-id 12345
bytedcli coco task subscribe --task-id <task-id>

# 多轮继续
bytedcli coco task send --task-id <task-id> --message "Add unit tests"

# Sandbox 模式
bytedcli coco task send \
  --agent-name sandbox \
  --message "Run the tests" \
  --repo-id 12345

# Sandbox / Environment 管理
bytedcli coco sandbox create --environment-id <env-id>
bytedcli coco env list --repo-id 12345

# 模型、Prompt、Chat、飞书授权
bytedcli coco model list
bytedcli coco prompt list --repo-id 12345
bytedcli coco chat --message "Explain this function" --repo-id 12345
bytedcli coco auth check-lark
```

## 命令索引

### Managed Agent / OpenAPI Next

| Resource  | Commands                                                                                |
| --------- | --------------------------------------------------------------------------------------- |
| Workspace | `workspace create/list/delete`                                                          |
| Device    | `device list/get`                                                                       |
| Agent     | `agent create/list/delete`                                                              |
| Session   | `session create/get/list/send/confirm/interrupt/subscribe/events/pending/stats/archive` |
| Run       | `run list/get/cancel`                                                                   |

支持的 permission mode：`default`、`accept-edits`、`plan`、`bypass-permissions`、`dont-ask`。

`workspace list`、`device list`、`agent list`、`session list`、`run list` 按游标分页：`--page-size` 取 1–100，默认 20；没有页码和总数。JSON 输出带 `page_size`、`current_count`、`has_more`、`next_page_token`；`has_more` 为 `true` 时用 `--page-token <next_page_token>` 取下一页，不要把单页结果当成全量：

```bash
bytedcli --json coco agent list --workspace-id <workspace-id> --page-size 100
bytedcli --json coco agent list --workspace-id <workspace-id> --page-size 100 --page-token <next-page-token>
```

### Copilot

| Resource       | Commands                                           |
| -------------- | -------------------------------------------------- |
| Task           | `task send/get/list/delete/share/events/subscribe` |
| Chat           | `chat`                                             |
| Model / Prompt | `model list`、`prompt list/get`                    |
| Sandbox        | `sandbox create/delete`                            |
| Environment    | `env create/get/list/update/delete/search`         |
| Auth           | `auth check-lark`                                  |

## Notes

- 当前 Managed Agent 不包含 `session execute`、Run 重跑（rerun）、Environment、Skill、Memory、Vault。
- `session create`、`session send`、`session interrupt` 不幂等：超时等结果不确定时不要直接重试，否则会产生重复的 Session 或重复的消息。
- 遇到认证或调用问题参考 `../../troubleshooting.md`。
