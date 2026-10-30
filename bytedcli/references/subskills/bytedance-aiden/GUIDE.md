---
name: bytedance-aiden
description: "Use bytedcli aiden for Aiden Cloud tasks/runs, Agent/Buddy configuration, schedules, Meego rules and cloud development environments; also for Aiden CLI update checks and troubleshooting. Match Aiden task/run links and follow-ups about an Aiden task. Generic development requests without an Aiden context do not trigger this skill; D2C and DeepWiki use their own domain skills."
---

# bytedcli aiden

使用 `bytedcli aiden` 管理 Aiden Cloud 控制面。需要 Node.js >= 20、可用的 `node` / `npm`、公司网络和 Aiden 访问权限。本 Skill 负责入口、更新检查、自主排障和功能路由；业务操作细节按当前版本随包 Aiden Skill 与 Help/Schema 执行。

## 会话首次使用：固定入口并检查更新

1. 用 `command -v bytedcli` 确认可信入口，同一任务固定使用它。首次调用可能安装 Aiden 运行组件，连 `--version` / `--help` 也不能保证无写入。未获安装授权且无法证明已有安装可安全探测时，先说明限制；不要把只读业务请求当作安装授权。
2. 按需用 `bytedcli --no-auto-upgrade aiden ...` 或 `BYTEDCLI_NO_AUTO_UPGRADE=1` 关闭 bytedcli 自身自动升级；这不阻止 Aiden 缺包时的首次安装。后续示例省略该前置开关，实际调用沿用已固定的入口和开关。
3. 执行 `bytedcli aiden --version`，与已加载的随包 Aiden Skill 的 `metadata.version` 核对。缺少 Skill 或版本不匹配时，在取得本地 Skill 写入授权后先预览、再安装、读回并重新加载。安装位置以计划为准；磁盘更新不等于会话已加载。
4. 会话首次使用且 `AIDEN_CLI_NO_UPDATE_NOTIFIER` 未设置或为空时，主动执行一次 `bytedcli aiden self update check --json`。有新版只提示可选更新，继续使用当前已匹配版本；检查失败表示未知，不是“已最新”。变量非空时跳过，用户主动要求查新时仍可执行；同一会话不重复查新。

```bash
bytedcli aiden --version
bytedcli aiden self update check --json
# 仅在需要安装/刷新 Skill 且已获本地写入授权时执行
bytedcli aiden self skill install --dry-run --json
bytedcli aiden self skill install --json
bytedcli aiden self skill status --json
```

普通终端的自动查新提示不等于 Agent 已检查更新。`AIDEN_CLI_NO_UPDATE_NOTIFIER=1` 只关闭 Aiden 自动检查及提示，不关闭 bytedcli 的自动升级或缺包安装；查新本身不安装新版。

## 首次使用与认证

直接执行目标命令。没有有效首次检查标记时，命令会在首次平台请求前检查授权，通过后保存标记供后续调用复用。只有 ByteCloud 授权必需；Codebase、飞书、Meego 和 bytedcli SSO 的状态用于诊断。

```bash
# 单独建立本地登录态，不检查云端平台授权
bytedcli aiden auth login
# 复用现有身份或完成登录，再刷新平台授权状态
bytedcli aiden setup
# 检查现有凭证并刷新平台授权状态，不发起登录
bytedcli aiden auth status --json
# 仅检查本地凭证，不访问 Aiden API
bytedcli aiden auth status --local --json
```

- 认证缺失或检查异常时，先按返回的恢复指引及随包 Skill 的 `references/runtime-auth-context.md` 处理；不能用反复登录或升级代替业务授权。Runner/Buddy 已提供的受管身份失效时停止，不切换成本机账号。
- 登录链接和 Code 可能通过 stderr 展示，JSON 模式同样如此；将登录指引交给用户完成，再等待命令最终结果。
- `auth status --local` 成功仅证明本地凭证可用，不保证 SDK 取票完全离线；托管凭证返回 `userinfo_requires_remote` 时使用在线检查，不据此重新登录。完整检查的 `ready` 和 `setup` 的 `verified` 仅证明当前身份与必需授权通过，空间和具体业务权限仍由目标操作检查。

## 发现命令

以当前版本的帮助和 Schema 为准，不猜测业务参数。收到 task / run 链接时，先识别目标，再按帮助或 Schema 确认所需参数。

```bash
bytedcli aiden --help
bytedcli aiden task --help
bytedcli aiden task create --help
bytedcli aiden schema task create --json
bytedcli aiden schema types --json
# 从命令 Schema 的 success_output.schema 或结果的 $schema 取得类型 ID
bytedcli aiden schema type '<schema-id>' --json
bytedcli aiden task list --json
```

按用户结果选下面的入口，再以已安装随包 Skill 的实际目录读取对应参考（文件名相对于该 Skill 根目录，不是本 Skill 的文件）。不同版本与发行通道的功能、参考目录不保证互为超集；缺失不等于版本落后，也不保证升级能补齐。目标命令缺失时报告限制，是否升级按查新结果与用户授权判断；参考缺失时回到随包 Skill 的现行路由，不猜文件或参数、不自动切换 beta。

| 用户结果 | 命令入口 | 随包 Skill 参考 |
| --- | --- | --- |
| 创建或查询 Task，任务 manifest 与通知 | `task` | `references/task-workflows.md` |
| 跟进运行、回答问题、续聊、中断回合和管理消息队列 | `run` | `references/run-collaboration-workflow.md` |
| 状态、时间线、会话、产物、watch、收尾及唤醒 | `run` | `references/run-operations.md` |
| 在 run sandbox 中执行单命令，不建立交互式 shell | `run exec` | `references/sandbox-exec.md` |
| Coding Agent 模型/Prompt/Workflow、Plugin Source、Skill 导入上传绑定与市场候选预览 | `agent` / `team` / `plugin` / `skill` / `repo` | `references/agent-configuration.md` |
| Buddy 创建初始化、任务派发、模型/仓库/权限/通知/自动响应/Webhook | `buddy` | `references/buddy-configuration.md` |
| Agent/Buddy 定时任务与提示词；Meego 自动接单和模型路由 | `schedule` / `meego` | `references/schedule-management.md`、`references/meego-rules.md` |
| 查找和接入已有 Devbox、绑定空间、终端链接与注册恢复 | `devbox` | `references/devbox-management.md` |
| 云电脑创建配置维护、仓库与工作模式、电脑项目与分支、在电脑上创建/重试/继续任务（仅当前 Help 提供时） | `cloud-computer` / `workspace` / `task` | `references/cloud-computer.md` |
| 空间、默认上下文、运行环境与空间模型目录 | `space` / `context` / `runtime-environment` / `model` | `references/runtime-auth-context.md` |
| 批量迁移本人创建的 Agent/Buddy 模型 | `agent` / `buddy` / `model` | 随包 Skill 实际提供的模型迁移 SOP；没有该 SOP 时不据此表启动批量写入 |

模型候选以目标空间的成功目录响应为准；历史配置和列表可见不证明模型可绑定。批量迁移先限定本人集合和完整性，再逐项预览、提交与独立读回，不把默认模型保存当作已有运行已迁移。

## 输出与写入边界

- 需要结构化结果时传 `--json`，支持 `bytedcli --json aiden ...` 和 `bytedcli aiden ... --json`；短参数 `-j` 仅在 `aiden` 前启用 JSON 模式。业务结果保留 Aiden JSON 结构，帮助与版本文本在 JSON 模式下包装为 bytedcli JSON。
- `aiden` 后的 `-j` / `-json` 不作为 JSON 开关处理，例如 `--prompt -j` 保留字符串值；`--` 之后所有参数均保持原样。在 `--` 前同时启用 JSON 模式并使用 `--json=false` / `--no-json` 关闭 JSON 时，命令执行前返回结构化参数错误。
- 支持 Unix 管道：用 JSON/JSONL 输出接下游处理；需要从 stdin 读取 Prompt、manifest 或配置时，按命令 Schema 将对应文件参数设为 `-`，每次命令只消费一次 stdin。Shell 管道启用 `set -o pipefail` 或逐进程检查退出码。
- 仅使用叶子 Help/Schema 声明的格式；例如 `run watch` 使用 JSONL，不套用全局 `--json`。命令 Schema 说明调用与风险，类型 Schema 说明字段；同一会话已读的 Schema 可复用。
- 查询和诊断保持只读。写入按叶子帮助先 dry-run，并仅在要求时提供 `--yes` 或目标确认参数；已明确授权的同目标操作无需反复询问。PPE 查询、预览、写入和读回均显式保持同一 `--ppe`。
- 按随包 `references/output-and-errors.md` 区分操作受理、操作确认、Run 结束和用户目标完成。写入已受理、结果模糊或读回失败时只读恢复，不重放原写入，不猜成功或自动回滚。

## 自主排障

CLI 使用受阻时，主动保留版本、命令路径、退出状态和稳定错误码，读取目标 Help/Schema 与错误恢复指引，不把可诊断的问题直接退给用户。先区分入口/版本/Skill/客户端问题与认证、权限、参数、业务失败。

原恢复指引仍不能解决客户端阻塞时，读取[排障与升级复验](references/aiden-recovery.md)：告知主要动作并取得升级授权，更新后刷新 Skill，只安全复验一次；仍失败则查重并给出最小脱敏 issue 草稿，提交 issue 另行确认。检查到新版本身不触发这个升级流程。

## 更新 Aiden 命令

```bash
bytedcli aiden +update
bytedcli aiden +update <version>
```

以上是实际安装操作，执行前取得升级授权。省略版本时更新到 `latest`；只有用户明确选择其他版本或通道时才指定 `<version>`，不为补功能自动切换 beta。`bytedcli aiden update [version]` 是兼容入口。两者仅接受可选版本或 dist-tag，不支持 `--dry-run`；不要照搬随包 Skill 中独立安装入口的 `update --dry-run`，也不要改用其他可执行入口。需要 JSON 时把 `--json` 放在 `aiden` 前。

更新后用同一入口核对 `--version`，预览并刷新随包 Skill、读回状态并重新加载，再读目标 Help/Schema。更新失败或生效版本无法确认时停止，不循环升级；详细流程见[排障与升级复验](references/aiden-recovery.md)。
