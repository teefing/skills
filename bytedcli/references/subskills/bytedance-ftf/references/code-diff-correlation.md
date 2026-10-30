# FTF 与代码 Diff 关联判断

目录：[用途](#用途) · [Canonical Analyzer 路由](#canonical-analyzer-路由) · [非 canonical 本地 / MR 分析](#非-canonical-本地--mr-分析)

## 用途

当 FTF diff 需要判断“是否本分支代码引入”，或需要解释同一 commit 在不同任务执行输入下为何
进入不同业务分支，或用户提供本地 `git diff`、Codebase MR URL、commit、branch 时，使用本流程。

本流程只判断代码相关性，不替代 FTF 平台取证。先用 `task-diff-triage.md` 或
`flow-diff-root-cause.md` 拿到具体 method、diff path、base/replay 值和日志证据，并按
`diff-denoise.md` 完成随机值和数组乱序降噪检查；最终判断依据遵循 `diff-analysis.md`
的“归因证据规范”。可剔除降噪项不要继续硬找代码根因；待核验降噪候选可以保留为低权重线索。
这些名称是降噪处理状态，不是 Finding 的 `confidence`；后者只允许“高 / 低”。
任务 URL 先按 `SKILL.md` 冻结站点；下列 ID-only FTF 示例固定为 cn，zg 使用全局前缀
`--site cn --vregion China-Pay`。裸 ID 未附站点时先索取，不得猜测。

## Canonical Analyzer 路由

当当前请求上下文已提供或可权威解析出 `task_id + similar_diff_id`，且任务要求判断字段 Diff
是否由 base→target 代码变更导致时，使用独立的 `ftf-code-analyzer`，不要执行本文件后面的
手工代码分析路径。

该路由只垄断 **base→target 代码变更因果**。FTF 只向 wrapper 提供冻结任务的 `task_id` 和与其
绑定的唯一 `similar_diff_id`；不得在委派前查询、比较或组装 repository、base revision、target
revision。Code resolver 是这些代码身份的唯一解析点，FTF 只对 canonical 返回值执行后置校验。

当前流程已进入任务归因或 DIFF 根因分析、目标身份唯一，且现有降噪检查未将该 DIFF 判为
“可剔除降噪项”时，必须调用一次 wrapper。待核验降噪候选、尚未定位根因、未发现代码候选、
日志不足或已初判为配置/平台问题均不是跳过理由。同一 execution attempt 先按 `similar_diff_id`
去重，再按冻结清单的稳定顺序调用，每个目标只调用一次。
Code resolver 的内部版本回退策略由 `ftf-code-analyzer` 契约定义，FTF 不假设或复述其内部算法，
只消费 canonical `base_ref` / `target_ref`，也不执行版本回退查询。wrapper 最终返回比较版本不可得的
失败或证据边界时，停止该分支并进入可恢复交互检查点：保留任务快照与已完成取证，请求用户补充带
来源的精确版本信息或所需访问权限；用户补充或授权后只重跑该受阻分支并继续。
不得用任务级 `base_commit_hash` / `commit_hash`、base task、`record_commit`、target parent 或默认分支替代。

FTF 不在 wrapper 前读取或比较 base/replay commit；只有 wrapper 返回
`not_applicable/no_revision_delta` 后才转入下文“同 commit 运行时路径分析”。

### 依赖能力

- Skill 名称：`ftf-code-analyzer`。
- 推荐 AgentBuddy 分发坐标：`skills:skills.byted.org/default/public/ftf-code-analyzer`；该坐标只用于
  定位制品，不是唯一来源，也不参与兼容性判断。
- 兼容性按能力判断：提供接受 `task_id + similar_diff_id` 的 canonical `run` 入口，并返回
  身份一致、满足六态与 artifact 完整性约束的 canonical JSON。版本仅用于部署追踪，不作为
  调用门禁；Analyzer 自行校验其运行依赖。
- `bytedance-ftf` 不包含 Analyzer 的脚本或二进制，安装、挂载与升级两者相互独立。普通
  FTF 查询、diff triage、计划管理和 Smart Access 不因 Analyzer 缺失而阻断。

查询并下载部署方选定的制品：

```bash
bytedcli --json --site cn agentbuddy skill get \
  --namespace skills.byted.org/default/public \
  --name ftf-code-analyzer

bytedcli --json --site cn agentbuddy skill download \
  --namespace skills.byted.org/default/public \
  --name ftf-code-analyzer \
  --version <selected-version> \
  --out <download-path>/ftf-code-analyzer.zip
```

`agentbuddy skill download` 只下载制品，不自动注册到当前 Agent。使用当前平台的 Skill
安装机制解压并激活，随后开启新会话；不要把某个宿主的 `/root`、`/opt` 或工作目录写成
公共固定路径。调用时优先使用平台已经解析出的 `ftf-code-analyzer` Skill 绝对目录。

### Readiness

按阶段准备当前目标：先读取适用的响应、Mock 判据并取得当前 DIFF 所需的 FTF 证据；再读取本节
公开调用与结果契约及调用方的输出要求，最后进入一次 canonical run。复用已取得的字段、枚举和
证据，不要求整包或整份无关 reference 全文读取。版本、token 和仓库准备均由 Code Skill 负责。

task-level 内部 `single-diff-attribution` worker 在进入 canonical run 前按以下固定顺序完成 FTF 侧准备：

1. 复用协调者冻结的 task 和唯一 `similar_diff_id`，取得目标 cluster 的值、similar cases 和 outbound；
   仅在信号要求时补代表 Flow、Mock 或降噪证据。worker 不查询 task、`update_time` 或生成最终报告。
2. 执行当前场景适用且可访问的 Mock / 环境检查；每项都记录已确认结果，或记录真实获取尝试、
   阻塞原因和明确的 evidence boundary。未取得或未闭环的 Mock / 环境证据不得单独成为跳过当前
   合法目标 mandatory Analyzer 的理由。`failed_reason != 0` 和已证明可剔除降噪项仍按现有分支退出。
3. 调用一次 wrapper 并返回结构化证据包。task `update_time` 仅由 task-level 协调者在所有 worker 完成后
   统一复核；worker 不逐 DIFF 重读快照。
4. terminal barrier 禁止同一 attempt 对同一 `similar_diff_id` 二次调用 Code、失败后回退手工代码变更
   归因或改写 canonical 六态；不阻断冻结 worklist 中已计划的非 Code 取证，也不阻断
   `not_applicable/no_revision_delta` 后的同 commit 运行时路径。

受控单 DIFF 调用必须等待同一个 run 明确结束，期间不得并行取证或探测产物。结束后只整合已有
证据和生成结论；新的 gap/blocker 保留为缺口，不补查、不重跑、不提升状态。同 commit 的后续
运行时路径取证只属于允许继续取证的交互流程；受 terminal barrier 约束时留给后续独立请求。

运行前先确认：

1. 当前 Agent 能发现并完整读取 `ftf-code-analyzer/SKILL.md`。
2. Skill 提供上述 canonical `run` 输入与六态 JSON 输出能力。
3. `scripts/tool.py` 可读，Python `>=3.9`、Git 可用；其他运行依赖由 Analyzer fail closed 校验。
4. 当前站点的登录态、网络、任务权限和仓库权限由本次真实 `run` fail closed 验证，不通过
   假响应或第二次试跑预判。

Universal 受控模式不得用 `tool.py --help` 或 `tool.py run --help` 探测 readiness。包级检查
只验证依赖和上述能力存在；真正的 endpoint、鉴权、任务身份和 clone 能力交给标准 `run`。

### Canonical wrapper 调用

自管理与 Universal 受控宿主都先读取当前已加载 FTF 与 Analyzer 的 `SKILL.md`，使用其绝对目录调用 FTF
wrapper。路径是编排期内部参数，不得让用户填写，也不得从当前工作目录推断：

```bash
node <bytedance-ftf-dir>/scripts/run-code-analyzer.mjs \
  --analyzer-skill-dir <ftf-code-analyzer-dir> \
  --task-id <task_id> \
  --diff-id <similar_diff_id> \
  --site <cn|i18n-tt> \
  --vregion <China-North|Singapore-Central> \
  [--network <office|prod>]
```

`task-id` 来自冻结任务，`diff-id` 是当前唯一 `similar_diff_id`；同一报告先按 diff ID 去重，再按
稳定顺序逐个调用，每个目标只调用一次。地域必须来自冻结任务上下文：仅接受
`cn/China-North` 与 `i18n-tt/Singapore-Central`，未知、不完整、错配或 China-Pay 均直接拒绝。
wrapper 固定启动一次 `python3 <ftf-code-analyzer-dir>/scripts/tool.py run`，不传 repository、
revision 或 method，不重试、不扫描历史 artifact，也不回退手工代码归因。
Agent 不得绕过 wrapper 直接执行 Python Analyzer。受控宿主可在启动 wrapper 前删除继承的同名变量，
并注入由当前 run 推导的 `FTF_PREPARED_CONTEXT_DIR` 与固定
`BYTEDANCE_FTF_WRAPPER_TIMEOUT_SECONDS=450`；自管理调用继续使用 wrapper 的安全临时 workspace。

### Universal 受控模式

Universal 受控宿主同样只调用上述 Node wrapper，不存在 Agent 可选择的 Python 直连兼容入口。wrapper
启动时只注入由当前 run 推导的 `FTF_PREPARED_CONTEXT_DIR` 与固定
`BYTEDANCE_FTF_WRAPPER_TIMEOUT_SECONDS=450`，并
校验 workspace 为绝对、非符号链接、当前用户
所有且权限受限的目录，将 artifact 固定为
`<workspace>/task-<task_id>/result-artifacts/<similar_diff_id>/result.json` 并作为 `--output` 传给
Code；Code 超时仍为 300 秒，外层 Guard 保持 480 秒，任何一层都不重试。

### 结果与失败边界

wrapper 退出码为 0 时只接受 `contract_version=ftf-code-analysis/v1` 的
`accepted | not_applicable | rejected` 信封；唯一机器定义位于
`assets/schemas/ftf-code-analysis.schema.json`。未知主版本、未知状态、缺失必填字段或互斥字段共存均 fail
closed，v1 新增可选字段允许忽略。完整代码身份的 `accepted.analyzer_run` 写入当前 DIFF Finding 的
`analyzer_runs[]`；`rejected.evidence_boundary` 只写入该 Finding 或根级边界中的一处。
wrapper 已绑定进程终态、canonical stdout 与 artifact，并校验：

- stdout 读取前受 FTF 自有 64 KiB 硬上限保护；`projection` 的 strategy、实际序列化字节数和
  producer 自声明上限必须一致，自声明上限不得超过 FTF 硬上限。
- 请求 `task_id + similar_diff_id` 与返回身份一致，目标 `diff_results[]` 存在且唯一。
- stdout 允许新增展示或诊断字段；FTF 仅比较任务、聚合结论和目标 DIFF 的稳定核心字段。完整包含
  `presentation_contract + presentation_validation` 的 bounded stdout 会在删除整个 `projection` 元数据、
  把 `result_artifact` 替换为公共 `{bytes, sha256}` 后，作为可选 opaque
  `analyzer_run.presentation_projection` 透传；其他未知字段不参与机器准入，也不得进入最终报告。
- 安全化后的 `presentation_projection` 命中 token、JWT、Cookie、鉴权头、私钥或带敏感 query 的 URL
  时整体省略，accepted 机器信封保持不变；不得局部改写 Code Skill 拥有的展示投影。
- artifact descriptor 的路径、bytes、SHA-256 与受控目录中的实际文件严格一致；repository、
  base/target revision identity 与目标分析一致。
- 每项 `analysis_state` 只能是 `invalid_observation`、`analysis_incomplete`、
  `evidence_blocked`、`proven_code_caused`、`proven_not_code_caused`、
  `runtime_unresolved` 之一，并满足对应状态对象的互斥约束。
- 对完整 artifact 校验对应状态专属对象、兼容 evidence 投影、`self_proof` 和 warnings；
  准入后的 `analyzer_run.result_artifact` 只保留 bytes 和 SHA-256，不得带出同宿主绝对路径；
  不得提升非终态、改写状态或用自然语言摘要覆盖 canonical 结果。

`presentation_projection` 只为上层展示候选提供 bounded 事实和展示合同，其中
`presentation_validation` 只供 Code Skill validator 校验身份与格式。FTF wrapper 不生成 Summary/Reason，
不读取 artifact 补写展示字段，也不重组 projection 内部状态语义。

pre-source `evidence_blocked` 采用同一 v1 信封中的能力
`capabilities=["pre_source_evidence_blocked_presentation"]` 和
`analyzer_run.adapter_kind=legacy_pre_source_evidence_blocked`。仅当 artifact 完整性、请求 task/diff、
唯一 stdout diff 均匹配，顶层 blocker 的 stage 为 `evidence_resolve`、`codebase_token_get` 或
`repository_resolve`，且没有已解析代码身份或 proof 时准入。blocker 必须有错误码和恢复动作；
stdout 中的 blocker 字段必须与 artifact 一致，presentation 必须完整且不含敏感信息。
此分支保留 blocker 与原始 presentation projection，省略 repository/base_ref/target_ref/path/op，
确定性输出 `unknown/null/low` 和聚合 `unknown/null/0`。accepted 表示协议准入，不表示代码因果成立。
能力消费者须复核原始 artifact，再使用既有 Code Skill presentation validator 校验候选文案。
任务报告的 `analyzer_runs[]` 仍要求完整代码身份；该分支的 blocker 进入既有 Evidence Boundary，
不得作为 proof 写入 `analyzer_runs[]` 或 `defects[]`。独立与受控调用都不增加版本绑定或第二次 Analyzer 调用。

只有完成上述全部校验后，base 与 target 相等、状态为 `proven_not_code_caused`、verdict 为
`not_caused`、因果值为 `false`，且 `exclusion_proof.proof_type=revision_tree_delta_empty` 时，才输出
`not_applicable/no_revision_delta`。该信封保留 task、DIFF、repository、唯一 revision 和
`result_artifact {bytes, sha256}`，不包含 `analyzer_run` 或本地路径，并转入固定提交运行时路径
分析。base=target 但证明不完整时返回 `rejected/state_contract_invalid`；base≠target 即使 tree diff
为空也继续输出 `accepted/proven_not_code_caused`。

依赖缺失、地域不支持、runner 失败/中断、stdout/identity/revision/六态/artifact 校验失败都返回
`rejected`，不是 Analyzer 第七态。wrapper 自身非零退出时，调用方生成 `[adapter_failed]` 的
material `EvidenceBoundary`；任何失败都不得伪造六态或回退到其他代码归因路径。

非零退出的公共失败 JSON 若包含 `blocker`、`input_diagnostics` 或顶层 `code`，wrapper 在
`rejected.failure` 中保留 `exit_code` 及去重的 `diagnostics[]`：stage、code、message、site、
vregion、HTTP `status_code`、upstream_code/message、log_id、request_id、trace_id 和 endpoint。
只复制这些脱敏字段，不传播 token、响应原文或任意异常对象；endpoint 去掉凭据、query 和 fragment。
诊断最多 8 项、每个文本最多 512 UTF-8 字节、合计最多 8 KiB，截断时标记 `truncated=true`。
未知错误码仍保留，分类兜底不删除诊断；同一安全诊断也进入 `evidence_boundary.reason`，使忽略
v1 可选字段的调用方仍能排障。该诊断不构成通过准入的六态结果，不触发换 token、clone 或重试。
非零退出没有上述结构化字段时，wrapper 仍保留真实 `exit_code`，并生成一条固定的
`stage=analyzer_run` 通用诊断；公共信封不复制任意 stdout/stderr 文本，也不推断内部失败阶段。
原始 stderr 仅由宿主按受控诊断产物策略留存和授权读取。
当 rejected 或 wrapper 失败可通过用户补充必要信息或申请代码仓库权限解除时，按 `SKILL.md` 的
interactive recovery checkpoint 进入 `awaiting_user_input` 或 `awaiting_authorization`；用户响应后校验
授权、可信输入或 observation 已真实变化并复核 task `update_time`。快照未变时创建一个私有 recovery
attempt，仅重跑该 Analyzer 分支一次；快照变化时废弃旧检查点并重建完整 execution attempt。同一 attempt
内不得原样重跑，最终 `analyzer_runs[]` 只保留最新有效 canonical 终态，旧 blocked/invalid 检查点仅用于
私有审计。

`accepted` 下的 Code 六态只提供代码子结论，必须结合 FTF 调查矩阵裁决：`invalid_observation` 不把 code
标为已检查；`analysis_incomplete` 只有真实代码证据才可标为 checked；Code `evidence_blocked` 及关键代码
未取得映射为 FTF 私有 `evidence_blocked`；`proven_code_caused` 仍需生产、传递、消费和影响证据闭环；
`proven_not_code_caused` 继续检查配置、部署、输入、稳定性和平台；`runtime_unresolved` 在运行时已查但不足
时才可 `exhausted_unresolved`，未取得时仍为私有 `evidence_blocked`。不得把任一 Code 状态直接等同为
FTF 状态或提升 Finding 强度。

当前报告首个 `accepted` 信封以 `repository + base_ref + target_ref`、首个 `not_applicable` 信封以
`repository + revision` 建立代码身份，并回填现有 metadata；`not_applicable.revision` 同时写入 base/target
commit。后续信封必须与已绑定身份完全一致。冻结 PSM
仓库非空但不一致，或后续代码身份冲突时，生成 `[report_identity_mismatch]` material
EvidenceBoundary 并停止最终报告，不得覆盖 metadata。`rejected` 不提供报告身份；全部调用均为
`rejected` 时不得用 Flow commit 冒充 Analyzer 身份。

## 同 commit 运行时路径分析

canonical 返回 `not_applicable/no_revision_delta`，或非 canonical 情况下已用可靠来源确认
base/replay commit 相同时，按以下顺序取证：

1. 用 `ftf psm get --psm <psm>` 冻结 PSM 与 Codebase 仓库绑定。
2. 从 task detail 读取 method 级 before/after script、请求头、参数和组件选择，明确 base/replay
   实际注入值；只有具体字段和值才构成任务执行配置证据。
3. 在该固定 commit 中定位消费这些值的函数、条件分支及响应组装路径，使用不可变 commit 的
   Codebase 行号深链。
4. 用代表 flow 的 `logid_comparison` 查询任务时间窗日志 / Trace，确认实际命中的模式、分支、
   组件或返回路径。若冻结输入与固定代码已唯一决定路径且没有外部状态参与，可直接闭环；若路径
   受 TCC、实验、缓存、下游返回或其他运行时状态影响，日志不可得时只能证明设计机制，不能声称
   代表流量已命中。
5. 用一个代表 response / Flow DIFF 闭合结果证据，并明确这不是代码提交差异。

任务执行配置与固定提交源码能够唯一决定路径、且无外部状态参与时，可以形成配置驱动的机制
结论；若路径仍受 TCC、实验、缓存或下游结果影响，必须取得对应运行时证据，否则降级为未闭环。

## 非 canonical 本地 / MR 分析

以下固定提交 Codebase 路径只适用于 `not_applicable/no_revision_delta`、base/replay commit
完全相同、用户明确提供本地 workspace/MR/commit/branch，或请求不属于 base→target 字段因果判断。
它不替代上面的 canonical Analyzer 路由。

这是一条只读诊断路径，不修改仓库、代码、任务、规则、部署或回放状态。

### 用户指定的本地 / MR 代码对象

用户明确提供本地 workspace、MR、commit 或 branch 时，必须读取该对象的真实 diff，而不是只读
任务绑定的 replay commit。先记录该代码对象与任务 target commit 的身份关系；两者不一致时将
结论限定为候选修复相关性，不得冒充任务已执行代码。

```bash
# 本地 workspace / commit
git status --short
git diff --stat HEAD
git diff HEAD -- path/to/file.ts
git ls-files --others --exclude-standard
git show <commit> -- path/to/file.ts

# Codebase MR
bytedcli --json codebase mr diff 821 -R "example-org/example-repo"
bytedcli --json codebase mr diff 821 \
  -R "example-org/example-repo" --file "path/to/file.ts"
```

若任务具备权威 `task_id + similar_diff_id` 且问题仍是 base→target 字段因果，不能用上述本地/MR
分析绕过 canonical Analyzer；本地/MR diff 仅作为后续修复候选证据。
`git diff HEAD` 覆盖 staged 与 unstaged 已跟踪改动；未跟踪文件必须从
`git ls-files --others --exclude-standard` 的清单中单独只读检查，不得假定 `git diff` 已包含。

## 证据入口

先冻结任务和代表 Flow：

```bash
bytedcli --json --site "<task_site>" --vregion "<task_vregion>" ftf task get --id "<task_id>"
bytedcli --json ftf task diff-cluster get \
  --url "<task_url>" --direction inbound \
  --similar-diff-id "<similar_diff_id>" \
  --with-values --sample-values 3 --with-similar-cases --with-outbound
bytedcli --json ftf flow diff get \
  --url "<flow_diff_url>" --with-values --with-outbound
```

从任务详情冻结：

- `run_psm`
- `psm_replay_param_detail.<psm>.commit_hash`
- `base_commit_hash`
- `replay_env`、`replay_cluster`
- `base_task_id`、`base_task_id_realtime`

从代表 Flow 复核 `base_commit`、`replay_commit`、`record_commit` 和 `record_time`。
提交不一致时停止合并代码证据；不得使用默认分支 HEAD 或查询时刻的最新提交替代任务版本。

## 解析任务绑定仓库

必须通过 PSM 官方绑定读取仓库，不得按 PSM 名称猜测：

```bash
bytedcli --json --site cn ftf psm get --psm "<psm>"
```

从返回的 `git_url` / `scm` 获得 Codebase 仓库。若 PSM 绑定为空、与任务 PSM 不一致、
或当前执行人无仓库读取权限，记录 `evidence_blocked`，并说明唯一恢复动作。

## 固定提交读取代码

```bash
bytedcli --json codebase repo file "<path>" \
  -R "<repo>" --revision "<replay_commit>"
```

候选文件可用跨仓搜索发现，但最终证据必须重新用固定提交读取：

```bash
bytedcli --json codebase search code \
  --query "<method-or-field>" \
  --repo-filter "^<repo-regexp>$" --lang go --limit 50
```

必要时读取固定提交的目录和 blame：

```bash
bytedcli --json codebase repo directory list \
  -R "<repo>" --path "<dir>" --revision "<replay_commit>" --page-size 1000
bytedcli --json codebase repo blame "<path>" \
  -R "<repo>" -r "<replay_commit>"
```

## 链路定位顺序

对每个 `similar_diff_id` 单独建立代码证据，不跨 finding 借用：

1. **入口**：method 的 RPC handler、请求参数和 method 分流。
2. **路径选择**：灰度、实验、TCC、提前返回、旧链路/新链路、采样控制。
3. **字段生产**：diff path 对应字段的默认值、复制、转换、排序、分页和过滤。
4. **下游调用**：RPC、ES、DB、缓存或 Mock 请求构造、批量拆分、重试和调用次数。
5. **响应组装**：字段缺失/新增、错误映射、`BaseResp`、`ErrorInfo` 和最终 response。

使用代码行号和固定提交深链描述链路，不仅引用文件名或字段名。

## 同一版本比较

当 `base_commit == replay_commit` 时，代码证据只能说明固定版本的设计机制：

- 不得写成“本次提交引入”或“代码 diff 导致”；
- 若 Page 直接从请求回填，必须继续核对请求输入；
- 若字段依赖下游返回、TCC、实验、缓存、数据或 Mock，代码只能给出可能路径；
- 只有任务时间窗日志/Trace、请求/响应或配置证据确认实际分支后，才能提升为实际根因。

## 相关性分级

| 等级          | 判定                                                             |
| ------------- | ---------------------------------------------------------------- |
| `strong`      | 固定版本代码路径唯一决定字段差异，且任务窗口运行证据确认实际命中 |
| `possible`    | 固定版本代码明确提供差异机制，但缺少运行时分支或外部状态证据     |
| `weak`        | 代码位于邻近链路，尚不能连接到本次字段差异                       |
| `no_evidence` | 已检查相关入口和响应链，未见能解释该差异的机制                   |

## Findings 输出

每个 finding 至少包含：

- task、PSM、method、direction、`similar_diff_id`、diff path；
- repository、固定 commit 和 Codebase 文件行号；
- `confirmed_facts`：代码实际观察；
- `code_chain`：入口 → 分支 → 字段生产/下游 → 响应组装；
- `code_relation`：`strong|possible|weak|no_evidence`；
- `evidence_gaps`：唯一缺失的运行时/配置/数据证据；
- `conclusion`：不得把静态机制写成运行时已证实根因；
- `repair_target`、`repair_action`、`verification`。

若源码读取或提交身份校验失败，finding 必须保持 `evidence_blocked`，不得改用本地未绑定
仓库、默认分支、Analyzer 结果或用户未提供的代码版本。
