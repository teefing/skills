# FTF 智能归因噪音查询与修复

使用此流程查询 LLM 归因的噪音候选或明细，并在用户明确授权后提交平台修复。
该能力使用 CN-only scene-mining 控制台；bytedcli 自动使用 ByteCloud JWT，不使用浏览器 Cookie。

## Use Cases

- 当需要查询指定 FTF 任务和 PSM 的 LLM 噪音归因结果时使用。
- 当已确认具体 Diff 聚类和修复范围，需要检查 value 或提交明确修复操作时使用。
- 不用于一般 DIFF 根因分析。`ftf remediation plan create`
  会自动使用新契约的 `sample` dry-run 明细采证；确认后通过本节的 execute 写入流程。
  repair plan 仍按自身五元组下钻、worklist 与 array-mirror 门禁产出 schema `1.9` 计划；
  证据不足时把对应 finding 标记为 `subtype: evidence_incomplete`、`disposition: needs_human`，
  不进入本节 execute 流程。

## Remediation Execution Workflow

`ftf remediation plan create` 生成的 action 仍是待确认建议，`execution_available=false`
表示不能直接把 repair plan 当作写入计划。确认后使用独立的 execution workflow：

```bash
bytedcli --site cn --json ftf remediation execution prepare \
  --plan <repair-plan.json> \
  --action-ids ACT-001 \
  --output-json <execution-report.json>

bytedcli --site cn --json ftf remediation execution execute \
  --execution-plan <execution-report.json> \
  --confirm-hash <execution_hash> \
  --yes
```

`prepare` 会按每个 source finding 执行只读 preflight，并冻结数组父配置；preflight 成功的子集会生成
execution plan，失败项保留在 `action_results` 中。只有全部 preflight 都失败、没有可用差异时才返回
`execution_plan: null`（`no_actions_ready`）。`execute` 只接受 hash 匹配的计划，逐 Action 写入并回读；
写入结果未知或回读不匹配时停止后续写入，结果中的 `write_executed=unknown` 不得解释为未写入。

## Inputs

- 必填：FTF 顶层任务 ID 和目标 PSM，来自任务详情或可信的 FTF 链接。
- 查询明细或修复时必填：查询结果中的一个或多个 `similar_diff_id`。

## Agent Workflow

### 1. 列候选

候选查询固定使用 `process_mode=dry_run` 和 `detail_level=summary`，不接受 Diff ID：

```bash
bytedcli --site cn --json ftf attribution-noise list \
  --task-id <task-id> \
  --psm example.psm \
  --method GetDemo \
  --page 1 \
  --page-size 20
```

从 `candidates` 选择目标。不要在此阶段请求完整 value。

### 2. 读取选中明细

`get` 必须指定 1 到 100 个 `similar_diff_id`。默认 `sample` 足以用于修复前核对：

```bash
bytedcli --site cn --json ftf attribution-noise get \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1,diff-2
```

只有确需聚合 outbound value 时使用 `aggregate`；每次最多 5 个 ID，不自动拆批。多批必须串行：

```bash
bytedcli --site cn --json ftf attribution-noise get \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1,diff-2 \
  --outbound-value-mode aggregate
```

`none` 明确跳过 outbound value。`base_value` / `replay_value` 可能是包含 JSON 的原始字符串，
必须按返回值解释，不得 parse 后再 stringify 并宣称逐字等价。

### 3. 确认并执行

向用户展示任务、PSM、Diff ID、明确 operation、预期变化和 dry-run 明细。只有用户确认同一
目标后才执行；execute 必须携带 `--yes`，不提供隐式 dry-run。
`set-time-offset` 必须传 `--offset-seconds <seconds>`，支持有符号安全整数（包含 0），
语义为 `replay - base = seconds`；不会默认秒数或降级为容差规则。
先使用 `ftf remediation schema update --operation set-time-offset --offset-seconds 1`
配合任务、PSM 和 Diff ID 预览，再携带同一秒数和 `--yes` 执行。
`operation_details` 返回精确目标、有效参数、前后配置；执行时还返回写入状态和回读状态。
只有保存值与指定秒数一致、无数值容差且回读确认，才能报告成功。
若回读未确认，先独立查询字段配置，再决定是否重试；`no_op` 表示已验证配置一致且本次未写入。

```bash
bytedcli --site cn --json ftf attribution-noise execute \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --operation add-noise-template \
  --yes
```

可执行 operation 为 `add-noise-template`、`set-time-offset`、`update-array-match` 和
`ignore-outbound-diff`；`undecided` 不可执行。`update-array-match` 的 execute 入口使用与
`ftf remediation array-match update` 相同的 `--method`、`--scene`、`--mode`、`--path`、
`--match-type`、`--key-list` 及 outbound 定位选项。`ignore-outbound-diff` 还必须携带恰好一个
`--method` 和至少一个 `--outbound-method`：

```bash
bytedcli --site cn --json ftf attribution-noise execute \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --operation ignore-outbound-diff \
  --method GetDemo \
  --outbound-method GetDownstream \
  --yes
```

执行后逐条检查 `execution_results[].outcome` 和 `error_code`。只有
`all_succeeded=true` 才能宣称整体成功；顶层 `status_code=0` 不代表每项成功。

## Compatibility Commands

以下四个 `ftf remediation ...` 命令是正式向下兼容入口，继续保留已有选项、输出和
dry-run/execute 语义。新 Agent 编排优先使用上面的三个 `ftf attribution-noise` 工具。
新版 CLI 将动作参数统一组装为 `operation_params`。只读能力声明支持版本选择；
旧服务端的已有数组与 outbound 忽略动作仍使用兼容请求，固定偏移必须升级服务端及断言引擎。
认证、网络和响应解析错误不会触发旧格式重试；写入失败后不会切换格式重试。

### 1. 旧查询入口

先查询汇总。默认请求 `dry_run`，不会写入平台：

```bash
bytedcli --site cn --json ftf remediation noise list \
  --task-id <task-id> \
  --psm example.psm \
  --method GetDemo \
  --page 1 \
  --page-size 20
```

JSON 结果中的 `noise_clusters` 始终是当前页聚类数组，`page` 和 `page_size` 位于 `data`
顶层。后端提供总数时输出 `total`；否则不伪造总数，改为输出当前页条数 `page_count`。
完整后端回执保留在 `context.backend`。需要一个或多个聚类的完整明细时，使用逗号分隔的
`similar_diff_id`，结果位于 `noise_details`：

```bash
bytedcli --site cn --json ftf remediation noise multi-get \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1,diff-2
```

`--is-outbound` 是布尔开关，`--noise-key` 是精确单值。`--op-source`、`--method`、
`--outbound-psm` 和 `--outbound-method` 支持逗号分隔的多个筛选值。

### 2. 旧预览与修复入口

仅当用户已确认准确的任务、PSM、`similar_diff_id` 和修复范围时才进入本节。两类写入均先发送
`process_mode=dry_run` 预览；只有加上 `--yes` 才发送 `process_mode=execute`。

Schema 噪音或时间偏移修复：

```bash
bytedcli --site cn --json ftf remediation schema update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --operation add-noise-template

bytedcli --site cn --json ftf remediation schema update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --operation add-noise-template \
  --yes
```

旧数组匹配修复入口还需目标 method、scene、精确数组 path、匹配方式和后端父配置中的
mode；出向修复还需 outbound 定位信息。`--outbound-psm` 取自目标
diff 元数据或代表 Flow 中 outbound 的 `TargetPsm`；`bizmethod`、`biz_data`
等伪 outbound 的 `TargetPsm` 为空时应省略该参数，不得伪造 PSM。`--mode` 必须读取对应
`PSM + Method + Scene` 的 FTF 断言父配置，值为 `system` 或 `sandbox`，不得猜测。
数组修复接口的入向 `--mode system` 转换为 `operation_params.mode=0`；
出向 `system` 及 `sandbox` 沿用现有的 `1`、`2` 映射。此处的模式编码与
噪音模板接口的 `taskMode` 不同。`order` 不接受 `--key-list`；`key`
必须提供一个或多个稳定键：

入向 Diff 可以省略 `--outbound-psm` 和 `--outbound-method`，CLI 会限定
`is_outbound=false`。出向修复使用 `--is-outbound`，必须提供 `--outbound-method`；
已有携带出向方法的调用方式保持兼容。

`--path` 必须指向实际发生元素对齐问题的精确数组 path。父数组配置不会自动覆盖元素
内部的嵌套数组。例如 Diff 位于
`query_dsl->bool->must->[*]->bool->should->[*]`，而现有配置只有
`query_dsl->bool->must->[*]` 时，必须向 `arrayPrimaryKeyList` 新增前者，不能
改为配置父 path。执行后须回读并确认精确 path 已保存；写接口返回成功本身不构成
生效证据。

```bash
# 入向数组修复预览
bytedcli --site cn --json ftf remediation array-match update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --method GetDemo \
  --scene default \
  --mode system \
  --path 'Result->items->[*]' \
  --match-type key \
  --key-list id

# 出向数组修复预览
bytedcli --site cn --json ftf remediation array-match update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --method GetDemo \
  --scene default \
  --is-outbound \
  --outbound-psm downstream.example \
  --outbound-method GetDownstream \
  --mode system \
  --path '$.items' \
  --match-type key \
  --key-list id

bytedcli --site cn --json ftf remediation array-match update \
  --task-id <task-id> \
  --psm example.psm \
  --similar-diff-id diff-1 \
  --method GetDemo \
  --scene default \
  --is-outbound \
  --outbound-psm downstream.example \
  --outbound-method GetDownstream \
  --mode system \
  --path '$.items' \
  --match-type key \
  --key-list id \
  --yes
```

## Write Constraints

- 未经用户明确确认，不得追加 `--yes`。
- 新 execute 不自动重试，不携带分页或 value-mode 参数。
- 新 `get` 与 `execute` 必须使用相同的任务、PSM 和 Diff ID；execute 还必须显式指定
  operation。
- 兼容命令的 dry-run 与 execute 必须使用相同的任务、PSM、Diff ID 和修复参数。
- 写入结果未知时停止后续写入，先重新查询相同 selector；不得盲目重试。
- 通过旧数组匹配入口写入后必须回读精确 path，确认保存结果与预览一致。

## Results

- `requested_process_mode` 表示客户端请求模式；`process_mode` 和 `executed` 表示后端确认的
  执行模式与是否实际写入，后端未返回时为 `null`，不能只根据本地 `--yes` 推断完成。
- 新 execute 输出 `operation_status`、逐项 `execution_results`、`summary` 和
  `all_succeeded`；部分失败返回非零退出状态并保留所有逐项结果。
- 成功：查询返回目标和分页回执；写入返回 `executed=true`，并通过后续查询确认目标状态。
- 部分完成：查询结果可用但某些明细缺失时，只报告已验证范围和缺口，不执行修复。
- 失败：输入、鉴权或 API 契约错误时停止，并按结构化错误的 hint 恢复。
- 新 execute 写入后重新运行 `attribution-noise get`；兼容写入命令继续使用 `noise list`
  或 `noise multi-get`，确认目标噪音的服务端状态。
- `FTF_AUTH_REQUIRED` 时按主 Skill 的 ByteCloud JWT 恢复流程处理；不要提供 Cookie、JWT 或
  浏览器抓包头。
- `FTF_API_ERROR` 时保留脱敏的 endpoint、`status_code` 和 `status_message`。未知结果不要重试
  写入；先用相同 selector 重新查询。
- 常见业务码：`40901` 表示任务明细过期，`40902` 表示未执行任何动作，`50001` 表示执行失败。
