# FTF 修复计划深度下钻

目录：[Use Cases](#use-cases) · [Inputs](#inputs) · [Workflow](#workflow) ·
[Report Contract](#report-contract) · [Completion Gate](#completion-gate) · [Results](#results)

## Use Cases

- 当用户要求继续分析 remediation plan、补齐 `needs_human`、解释高影响逻辑桶，或生成最终只读修复报告时使用。
- 当初始计划中大量逻辑桶的 `difference_mechanisms` 包含 `missing_value_pairs` 或 `query_failed`
  时，必须进入本工作流；不得把初始 `repair plan create` 产物直接当作最终分析报告交付。
- 不用于执行噪音规则、修改代码或配置、部署、录制或回放。用户要求持续修改并回放验证时，转到
  [`diff-remediation-loop.md`](diff-remediation-loop.md)。

## Inputs

- 必填：由 [`remediation-plan.md`](remediation-plan.md) 生成且通过 schema 校验的初始 JSON 和
  Markdown。
- 必填：初始计划的任务 URL、`task.update_time`、`plan_hash`、`evidence_hash`、完整逻辑桶和
  finding worklist。
- 默认下钻至少 10 个最高影响逻辑桶；逻辑桶不足 10 个时全部下钻。
- 默认累计覆盖目标为全量 catalog `diff_details` 的 80%。Top 10 未达到 80% 时，继续按排序扩展，
  直到达到 80% 或全部逻辑桶均已入选。用户可以明确指定更大的范围，但不能在事后缩小范围来掩盖
  未完成项。
- 每个逻辑桶至少选择一个代表 Cluster。桶内原始 Method、Outbound Method、具体 Path、值形状、
  缺失方向或风险等级存在异质性时，追加覆盖每一种异质机制的 Cluster。

## Workflow

### 1. 冻结快照和深度下钻集合

1. 重新解析任务 URL并读取任务详情，核对 site、task ID、space ID 和 `update_time`。
2. 如果 `update_time` 与初始计划不同，停止使用旧证据，重新生成初始计划；不得把两个快照合并。
3. 只按以下稳定顺序排列逻辑桶：
   - `diff_details` 降序；
   - `affected_flows` 降序；
   - `cluster_count` 降序；
   - 逻辑桶 ID 升序。
4. 选择 Top 10；若其累计 `diff_details` 占比不足 80%，继续取最短排序前缀直到达到 80%。
5. 记录入选桶数、累计覆盖率、未入选桶数和每个桶的代表/异质 Cluster 身份。未入选桶只能标记为
   “本轮未下钻：低于影响优先级边界”，不得写成已经分析后的 `needs_more_evidence`。

排序只决定资源投入顺序，不改变证据门禁。高影响不能降低噪音判定标准。

### 2. 为每个入选桶建立证据台账

每个入选桶必须维护以下字段，缺一项不得进入最终报告：

```text
bucket_id
psm
method
direction
outbound_psm
outbound_method
path_family
cluster_ids
diff_details
affected_flows
catalog_share
sample_flow_ids
counterexample_flow_ids
evidence_ids
confirmed_facts
excluded_hypotheses
evidence_gaps
conclusion
confidence
repair_target
repair_action
verification
```

`confidence` 只允许 `high` 或 `low`。`conclusion` 只允许第 7 步定义的四个值。

### 3. Cluster 和 Flow 事实下钻

1. 对每个代表和异质 Cluster 执行 `ftf task diff-cluster get`。Inbound 使用
   `--with-values --sample-values 5 --with-similar-cases --with-outbound`；Outbound 使用
   `--with-outbound`，不得传 inbound-only 参数。
2. 使用 finding 的真实 `flow_diff_url` 执行 `ftf flow diff get --with-values --with-outbound`。
3. 为每个桶建立同质 Flow inventory。至少检查 3 至 5 条跨 Flow 样本；可用样本不足时检查全部并
   记录实际数量。
4. 主动寻找至少一条反例：同一 method、方向和机制候选下，不满足主模式或未出现该 DIFF 的 Flow。
   找不到反例时，记录已检查的 Flow 数、页数、时间范围和“未发现反例”，不得伪造反例。
5. 禁止把不同 method、方向、`similar_diff_id` 或值机制的样本混用。一个代表 Flow 不能证明整个桶。

### 4. 归纳具体 key/value 机制

按路径和值形状执行专项分析，不得只看字段名：

| 差异类型              | 必查事实                                               | 可以形成的机制表述                                  |
| --------------------- | ------------------------------------------------------ | --------------------------------------------------- |
| 时间或数字            | 每个样本的 base、replay、差值、单位、分布和异常点      | 固定偏移、比例变化、边界截断或不稳定数值            |
| 动态 ID/Header        | 双边是否非空、跨样本唯一性、跨侧对应、是否改变业务响应 | 每次请求变化且业务无关，或真实鉴权/身份差异         |
| null/default          | present/found、类型、默认结构和业务语义                | 默认值等价、默认结构缺失或真实业务值丢失            |
| 数组/对象             | 元素增删、顺序、镜像 pair、公共字段和稳定业务键        | 纯顺序变化、按稳定键错配、真实元素增删或字段变化    |
| Outbound 调用         | 请求参数/header、调用次数、匹配复用、未匹配原因和响应  | Mock 错配、调用次数变化、请求构造变化或下游响应变化 |
| ParamsMap/动态 Method | 原始 Method、归一化 Method、具体 key 和缺失方向        | 指定 key 缺失/新增/变值，不得只写 ParamsMap 不同    |

如果多个 Cluster 显示不同机制，拆分结论或明确列出异质机制；不得用“机制冲突”结束下钻。
敏感值必须脱敏，但仍需保留 `present`、类型、长度/形状、相等性和变化关系等可判定事实。

### 5. 执行反证检查

在判定噪音前逐项排除：

- 金额、状态、数量、库存、权限、实验、配置、业务时间和业务 ID 的真实变化；
- 单边非默认业务值丢失；
- 数组真实增删、重复键或不唯一键；
- 值在不同 Flow 中稳定重复，或在 base/replay 间发生跨侧对应；
- Outbound 调用次数、请求条件或响应内容真实变化；
- 仅凭路径名称、平台标签或单条 Flow 推断动态噪音。

`excluded_hypotheses` 必须记录实际检查过的替代解释和排除证据，不能写成泛化模板。

### 6. 按需完成因果定位

值和 Flow 证据不能确定修复目标时，继续以下只读链路：

1. base→target 存在 revision delta：对每个去重 `similar_diff_id` 使用 canonical
   `ftf-code-analyzer`，只传 `task_id + similar_diff_id`。
2. Analyzer 返回 `not_applicable/no_revision_delta` 或同版本：解析官方 PSM 仓库绑定，在任务 replay
   commit 上沿 RPC/handler、字段生产、默认值、下游请求构造、错误映射和响应组装追踪。
3. 使用代表 Flow 的真实 replay LogID 和任务时间窗查询日志或 Trace，确认实际命中的分支、下游和
   首个字段变化点。
4. 只有 Trace/outbound 已给出资源身份时，才查询任务时间窗内的配置、部署或数据状态。

代码只能证明设计机制；必须与同一 Flow 的日志、Trace、请求/响应或下游证据闭合，才能形成
`code_or_config_fix`。权限、历史数据或资源身份阻塞时记录真实查询、错误和唯一恢复动作。

### 7. 应用结论门禁

每个入选桶必须落到以下之一：

- `confirmed_noise`：至少 3 条同质样本（不足时为全部样本）证明同一非业务机制，反证检查通过，
  且修复规则能限定到精确 PSM、method、direction、outbound 和 path。
- `code_or_config_fix`：固定版本代码/配置/Mock/环境机制能够预测 DIFF，并由任务时间窗的真实 Flow
  运行时证据闭合。
- `excluded`：已有精确平台规则、前置过滤或可信范围证据证明该桶不属于当前修复集合。
- `needs_more_evidence`：所有当前可访问且适用的入口已经实际检查，仍只缺一项决定性证据。必须写明
  已完成查询、唯一证据缺口、该缺口阻止的判断、下一条精确只读查询和责任/权限边界。

出现权限或必要历史证据阻塞时，流程状态先记为 `evidence_blocked`，暂停最终报告并请求用户选择补权、
跳过或停止。只有用户明确选择跳过后，才可把该桶转为 `needs_more_evidence`，同时保留
`evidence_skipped_by_user` 和完整 Evidence Boundary。沉默不等于允许跳过。

禁止用 `undecided`、`missing_value_pairs`、`query_failed`、`暂无`、`未知`、`未检查`、`待检查` 或
“可能是”替代上述结论。无法满足前三类门禁时，必须诚实进入 `needs_more_evidence`。

### 8. 复核快照并生成报告

1. 所有入选桶完成后重新读取任务 `update_time`。发生变化则停止合并并重新生成计划。
2. 保留初始 remediation JSON/Markdown，不修改其 `plan_hash` 或 `evidence_hash`。
3. 生成独立的深度下钻报告；不得把初始计划中的未取值或查询失败状态复制为最终结论。
4. 明确声明只执行了读取和 `repair denoise dry_run`，未执行标注、规则写入、代码修改、部署、录制或回放。
5. 最终报告必须由已校验的结构化 finding/detail 数据渲染；不得用手工摘要表替代五元组主表。
   使用 `<bytedance-ftf-dir>/scripts/validate-remediation-report.mjs` 执行本地硬门禁；
   硬门禁失败时不得进入飞书导入。
6. 用户要求飞书交付时，导入后必须用 `lark-cli docs +fetch --doc-format markdown --detail full`
   回读同一文档，并使用同一 gate 的 `--lark-json` 模式逐行逐格比较。只要表头、行数、
   `Outbound PSM`、`Outbound Method`、`Diff Value` 或 `Diff 链接` 任一项不一致，就停止交付；
   不能以导入成功回执或文档 URL 代替回读校验。

## Report Contract

最终 Markdown 按以下顺序输出：

1. **任务快照**：任务 URL、`update_time`、初始 `plan_hash` / `evidence_hash`。
2. **接口级全量分析**：完整 catalog 的 Cluster、Diff 明细、影响 Flow 统计和口径。
3. **深度下钻选择**：排序规则、入选桶数、累计覆盖率、未入选桶数。
4. **Top 影响桶结论**：每桶的具体 key/value 机制、结论、置信度、修复目标和证据链接。
5. **逐桶证据台账**：样本、反例、已确认事实、已排除假设、证据缺口、修复动作和验证方式。
6. **未入选桶**：只说明优先级边界和后续队列，不伪装成已下钻。
7. **Evidence Boundary**：权限、历史数据或资源身份阻塞及其影响。
8. **只读声明**：列出未执行的写操作。

Top 影响桶表至少包含：

```text
桶 | PSM | Method | Direction | Outbound | Diff Path | Diff 明细 | 具体机制 | 结论 | 置信度 | 修复目标 | 证据
```

“具体机制”必须描述已观察到的 key/value 关系。对于 `needs_more_evidence`，该列写已确认的最窄事实，
证据缺口放入逐桶台账；不能写“待下钻”。

### 五元组主表硬契约

深度下钻报告中的“五元组下钻”是人工审阅主入口，必须在接口级全量分析之后出现，并严格使用
以下 8 列，顺序不可变：

```text
PSM | Method | Outbound PSM | Outbound Method | Diff Path | Diff Value | 修复建议 | Diff 链接
```

每个 finding 至少生成一行；同一 finding 的多个 repair denoise detail 必须逐 detail 展开，
失败、跳过、无 detail 的查询也必须保留一行。`Outbound PSM` 和 `Outbound Method` 不得合并；
不可得时写 `无` 或 `未返回`，不能把它们塞进“Outbound”摘要列。`Diff Value` 必须是脱敏、
截断后的结构化 base/replay 变化；`Diff 链接` 必须是当前 FTF Flow 路由或 `链接不可用`。
修复建议只能使用五元组工作流定义的 5 个枚举值。

渲染器和回读 gate 必须共同验证：

- 主表存在且表头精确匹配 8 列；
- 期望行数等于 finding/detail 展开行数；
- 每个 finding 的 PSM + Method 至少命中一行；
- 每行 8 个单元格均存在，建议值合法，链接可用或明确不可用；
- 飞书回读的表头、行数和 8 列单元格与本地 Markdown 完全一致。

任何一项失败，流程状态为 `report_gate_failed`，不得生成“已完成”交付状态或发送飞书链接。

## Completion Gate

交付前逐桶执行严格检查。任一入选桶不满足即不得声称工作流完成：

- 身份包含 bucket、Cluster、PSM、method、direction、outbound 和 path；
- 有代表样本，且满足 3 至 5 条跨 Flow 样本要求或说明样本总量不足；
- 有反例，或记录了有界反例搜索范围和“未发现反例”；
- 有具体 base/replay 变化机制，不含禁用占位语；
- 有实际执行过的反证检查和 `excluded_hypotheses`；
- 有可复查 `evidence_ids` 或稳定链接；
- 五元组主表通过固定 8 列、逐 finding/detail 行数和合法枚举门禁；
- 如交付飞书，回读表格与本地 Markdown 逐行逐格一致；
- `conclusion` 属于四值枚举且满足对应门禁；
- 有置信度、修复目标、最小动作和验证方式；
- `needs_more_evidence` 只有一个决定性缺口和一条精确恢复查询；
- 报告的入选桶数和累计覆盖率与冻结 catalog 可机械复算；
- 最终 `update_time` 与冻结快照一致；
- 全文不宣称执行了任何未发生的写操作。

协调者必须串行完成样本归属校验、结论门禁、覆盖率复算和最终渲染。可以并行读取不同桶，但不得让
子任务自行合并结论或直接写最终报告。

## Results

- 成功：所有入选桶通过 Completion Gate，达到至少 `min(10, 全部逻辑桶)` 且累计覆盖目标，交付独立深度下钻报告。
- 部分完成：只允许在用户明确接受权限/历史证据阻塞或主动限定更小范围后输出；逐桶保留 Evidence
  Boundary，不能称为完整最终报告。
- 失败：任务快照变化、初始计划无效、样本归属混淆、覆盖无法复算或任一入选桶仍使用禁用占位语时
  停止交付，并给出唯一恢复动作。
