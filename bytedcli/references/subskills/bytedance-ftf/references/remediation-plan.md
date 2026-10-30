# FTF 噪音修复计划预览

目录：[Use Cases](#use-cases) · [Inputs](#inputs) · [Workflow](#workflow) ·
[Structured Output](#structured-output) · [Results](#results)

当用户需要审核 DIFF 噪音修复建议，但尚未授权执行平台配置、代码修改、部署、流量录制或回放变更时，
使用此工作流。

## Use Cases

- 当需要从一个 FTF 任务生成可审阅、不可执行的噪音修复建议时使用。
- 不用于直接写入噪音规则、修改代码、部署或触发回放。

## Inputs

- 必填：可信 FTF 任务 URL，或顶层任务 ID 加明确站点。
- 可选：PSM、method、annotation 类型、最大聚类数和每个聚类的样本数。
- 输出文件路径必须尚不存在；调用方负责选择可写目录。

## Workflow

### 1. 生成计划

```bash
bytedcli --json ftf remediation plan create \
  --url "<ftf-task-url>" \
  --max-clusters 20 \
  --sample-size 5 \
  --output-markdown ./repair-plan.md \
  --output-json ./repair-plan.json
```

任务 URL 会固定站点和任务身份。仅提供任务 ID 时，必须按照 FTF 主 Skill 的约定显式指定全局站点或区域。

### 2. 检查计划契约

- 入向和出向均不限制 `diffType`，所有类型都可进入 catalog。
- `opType=8`（噪音模板命中）始终在入口处排除，不进入完整 Cluster catalog、接口级统计、
  Repair denoise 或五元组下钻 worklist；显式 `--annotation-op-type all` 也不能重新纳入。
- 交付 Markdown 的计划摘要必须展示标注来源、请求范围和入口排除项；当请求范围仅包含
  `opType=8` 等强制排除项时，必须明确提示本计划不会纳入对应 Cluster，不能静默输出空计划。
- 当任务 URL 未提供 `diffReasons` 时，两个方向默认额外排除 `opType=7`，其余页面标注状态均纳入。
  显式 `--annotation-op-type` 可以覆盖 `opType=7` 的默认排除，但不能覆盖 `opType=8` 的强制排除。
- 当任务 URL 已提供 `diffReasons` 时，按 URL 指定的页面标注状态 `opType` 筛选；
  显式 `--annotation-op-type` 优先于 URL，但两者都不能重新纳入 `opType=8`。
- 命令先读取符合筛选条件的完整 Cluster catalog，并在接口级统计 Cluster、各 Cluster
  `log_count` 之和、方向、原始/归一化 Method、Path family 和标注分布。`log_count`
  是 Cluster 维度求和，同一 Flow 可能在不同 Cluster 重复计数，不得宣称为去重流量。
- 动态下游 Method 只做保守归一化：仅移除 `数字_服务名::Method` 形态的数字前缀；
  原始 Method 必须保留在逻辑桶中。不得用模糊字符串规则合并无法证明同源的方法。
- Path family 同时归一化数组下标和动态字段名：数组数字下标统一为 `[*]`；位于路径开头，
  或以路径分隔符 `->` / 下划线 `_` 分隔、长度至少 12 位的纯数字 token 统一为 `*`，例如
  `button_line_123456789012` 归一化为 `button_line_*`。短编号、普通字段名和
  `order_id` 等业务字段不得仅因包含数字或 `id` 字样被合并。
- 全量 catalog 按
  `PSM + 归一化 Method + direction + outbound PSM + 归一化 outbound Method + Path family`
  形成逻辑接口桶。`diffType` 描述同一逻辑位置的具体差异形态，不用于拆分逻辑桶；同桶存在多个
  `diffType` 时 JSON 的 `diff_type` 固定为 `null`，权威复数字段 `diff_types` 按 code 升序保留
  `code + name + label + known` 描述器。`diff_types` 是后端 Cluster 类型与结构化差异机制逐项对应
  类型的并集：数组元素新增/缺失分别保留 `6` / `5`，不得按数量加减后只保留净变化类型；
  基准数组为空时新增对应 `12`，回放数组为空时缺失对应 `11`，数组长度变化不得映射为乱序 `8`；
  普通值变化对应 `2 DIFF_VALUE（内容不同）`。后端未返回 `diffType` 且机制也无法确定类型时
  `diff_types=[]` 且 `diff_type=null`，不得把空数组解释为多值。权威枚举覆盖
  `1/2/3/4/5/6/7/8/10/11/12`，禁止输出 `UNKNOWN`。真正超出权威枚举的编号保存在
  `unmapped_diff_type_codes`；有机制证据时 Diff Type 列只展示机制可证明的类型，无机制证据时显示
  “未解析（原始 code N）”，不得猜测未定义的数字语义。
  `opType` 是标注状态，不是差异机制，不得用于拆分因果桶；每个桶必须在
  `annotation_distribution` 中保留各 `opType` 的 Cluster、受影响 Flow 和 Diff 明细分布。
  先按 Diff 明细量排序宏观噪音类型，并优先审阅前三类及其累计覆盖率。
  对 `ParamsMap` 等已形成多个逻辑桶的结构，必须逐桶选择代表项；例如形成 6 个桶时，
  6 个桶分别抽样，不能把它们重新合成一个五元组结论。
- `--max-clusters` 限制的是五元组下钻 worklist，不限制接口级全量统计；最大为 500，
  超限请求会在访问后端前被拒绝。每个逻辑桶先选一个高影响代表 Cluster，再为每个不同
  `diffType` 至少保留一个代表 Cluster；桶内原始 Method、Outbound Method、具体 Path 或风险等级
  仍存在其他异质差异时，继续补选异常 Cluster。所有补选均受 `--max-clusters` 约束。报告必须分别
  声明完整 catalog 数、入选数、未下钻数和工作集是否截断。
- worklist 条目和逻辑桶代表 Cluster 必须同时保留
  `psm_task_id + direction + psm + method + cluster_id` 完整身份；不得只用可能跨
  PSM task 重复的 `cluster_id` 做关联。
- 对 CN 任务，命令只把冻结 worklist 中的代表 Cluster 和异质异常 Cluster 的 task ID、
  PSM、direction 和
  `similar_diff_id` 自动提交给 repair denoise，且固定使用 `process_mode=dry_run`。
  请求按有界并发执行，单个超时或接口错误只将 `repair_denoise.status` 标记为 `partial`，
  不会丢弃其他聚类的成功结果，也不会转为 execute。1000 次请求、50000 条 detail 和
  8 MiB 脱敏证据预算按聚类确定性分配；超出任一预算的查询按失败记录。
- repair denoise 返回的 `details` 只按白名单保留标识、路径和 `diff_value_list`，
  不保留 `judgement_basis` 等自由文本。每个 detail 最多保留 100 组值，并通过
  `diff_value_count` 和 `diff_values_truncated` 明确原始数量与是否截断；单个值最多保留
  64 KiB。上述字段用于在只读阶段补齐修复动作证据和参数；只有证据和参数完整时才生成对应动作，
  否则固定为 `undecided`；写入 JSON 前统一递归脱敏，敏感路径对应的录制值和回放值也会替换为
  脱敏占位符。
- `denoise_op_type` 非空时优先采用平台返回值，但 `add_noise_template` 和 `set_time_offset` 仍必须通过
  本地证据校验；校验不通过时统一改为 `undecided`，其他不支持的非空值不直接生成动作。
  仅当该字段为空、缺失或未设置时，本地后备判定才构造等价的 `DiffGroupInput` 并结合组内上下文逐一判断每个聚类。分组数据包含
  `diff_type`、`current_psm`、`current_method`、`diff_path` 和 `diff_inputs`；每个
  `diff_inputs` 成员保留唯一 `similar_diff_id`、原始 `diff_path`、`base_json_path`、
  `replay_json_path`、`diff_value_list` 和 `diff_number`。inbound 与 outbound 使用相同的严格
  分组键，只有 `current_psm + current_method + diff_path` 三者完全一致的聚类才能进入同一组，
  任一字段不同都必须拆组。

  ```text
  结合组内上下文，逐一判断 DiffGroupInput 中每个 diff 聚类是否为噪音。
  <DiffGroupInput>
  %s
  </DiffGroupInput>
  ```

- 多聚类组必须利用不同聚类之间的值、路径和缺失方向交叉验证。outbound 重点识别同名调用实例匹配
  乱序，以及单次 outbound 内数组元素乱序；只有实际参与值交叉对应、路径迁移或缺失方向互补的聚类
  才能取得乱序噪音证据，不得因同属一个组就统一判为噪音。单聚类组按自身样本独立判断，不得假设
  未提供的组内关联；每个 `similar_diff_id` 必须独立得出结论，不得遗漏或输出输入外编号。完成全部
  规则后仍无法判断时固定按 `is_noise=false` 处理，修复建议为 `undecided`，且不生成后备动作。
- outbound 数组路径且平台 `denoise_op_type` 为空时，不能只消费 repair denoise 已压平的
  `diff_value_list`。命令必须用代表 `recordId` 查询
  `getOutboundValueDiffDetail` 枚举该 `similar_diff_id` 对应的原始 `diffId`，再逐
  `diffId` 分页读取 `getOutboundSimilarCaseList`，保留每个 `diffId` 的顶层 `reason`。
  补充读取每个 `diffId` 最多 20 页、每页 100 条，并与 repair denoise 共享每次计划 1000 次请求
  的总预算；报告只保留脱敏后的 diffId/reason、记录数、配对数、匹配策略和残余字段，不保存全量
  对象值。预算不足时保持 `inconclusive`；补充采证失败时整体状态为 `partial`，不得把失败当作
  无噪音。
- 只有恰好存在一组“回放组数组新增 object 元素”和“回放组数组缺失 object 元素”的互补 reason，
  且按 `recordId + base/replay value` 去重后，每个 `recordId` 都恰好保留一条 base-only 和
  一条 replay-only 记录、形成唯一 object pair 时，才允许重建。接口按不同 `diffId`
  查询可能重复返回聚类的完整明细，这种完全相同的行只去重一次，不能重复计数。每对 object 必须
  至少有一个相等公共字段；重新执行字段级 diff 后，
  所有 record 的残余字段集合必须一致。缺行、重复行、无法解析 object、无公共字段或残余字段冲突
  都固定为 `inconclusive` 和 `undecided`。
- 重建成功后仍需单独证明匹配策略。`Args->[*]` 这类参数位置具有语义的数组使用 `order`；
  其他对象数组只有在某个业务键双边非空、每对相等、并在全部 record 中唯一时才使用 `key`，
  同时保留精确 `match_keys`。不得把普通相等字段当业务键，也不得在键缺失、重复或不唯一时猜测。
  仅当策略得到上述证据证明时，后备建议才可为 `update_array_match`。
- 数组匹配采用两阶段处理：先配置并回读精确数组 path，重新回放后再分析字段级残余差异。原始
  `Args->[*]` 等粗粒度数组 path 不得创建噪音模板；例如重建后只剩 `2_host` 时，必须等数组匹配
  生效后的新结果，再对精确 host 路径独立判断是否需要噪音处理。
- 完成上述组内上下文推导后，才按“先⑥，再①②③④⑤”的优先级检查：⑥ 单边存在明确非默认业务值，且组内没有乱序、路径迁移或
  默认结构关联证据时判为非噪音；① null 与默认值或默认结构差异通常是噪音；② 时间、ID、环境、
  网络或设备等动态字段必须结合样本值判断，不得只看字段名；③ 组内值交叉对应、路径关联或缺失方向
  互补证明乱序时判为噪音；④ 每次回放变化的数字或 ID 导致路径无法匹配时通常是噪音；⑤ 数值精度或
  小范围时间误差通常是噪音。无法证明时保持 `undecided`。
- 后备判定只能生成 `add_noise_template`、`set_time_offset`，或在上述镜像 pair 与匹配策略均被
  严格证明时生成 `update_array_match`。`add_noise_template` 要求所有样本
  双边均有实际内容、两边都具有可由值形态证明的随机或环境相关特征、不承载金额/状态/数量/库存/
  开关/业务时间等业务语义，并且多组样本无重复、无跨侧对应。单样本只有在 UUID、固定长度长
  十六进制串等强形态足以确认随机性时才允许。任一样本单边为空、属于乱序、来自有限枚举、出现重复、
  只是可疑但不能证明长期随机，或只是时间小偏差时都不得建议该动作。
- `set_time_offset` 仅用于路径和双边值都能证明为整数秒时间、且所有样本偏差均为同一整数秒的情况；任一边
  为空或缺失时不得建议。后备动作的判断依据会追加到 finding evidence；`add_noise_template` 的依据
  必须同时说明双边有值和具体随机形态。
- 逻辑接口桶必须在 repair denoise dry-run 后补充结构化 `difference_mechanisms`，并保留
  `difference_mechanism` 兼容字符串。只允许从结构化 `diff_value_list` 归纳可证明的 key/value
  变化；同一桶存在多种机制时全部列出并统计次数，Markdown 每种机制单独换行。需区分查询失败、
  查询跳过、未返回值对、脱敏值、空值新增/缺失、数组长度变化、布尔变化、数值或时间偏移、
  固定值、长值和复杂值变化；`query_skipped` 只描述平台或地域不支持等跳过状态，不得归类为
  `query_failed` 或触发深度下钻。长值和复杂值摘要截断并以 `...` 结尾，不得根据字段名猜测具体 key。
- Markdown 的“分析结论”固定使用以下 8 列，不得改回摘要式 6 列或省略失败、跳过项：
  `PSM | Method | Outbound PSM | Outbound Method | Diff Path | Diff Value | 修复建议 | Diff 链接`。
  同一聚类返回多个 repair denoise detail 时逐 detail 展开；没有 detail 时仍为 finding
  保留一行。Outbound、路径和值优先读取 detail 的 `outbound_psm`、`outbound_method`、
  `noise_key` 和 `diff_value_list`，缺失时回退 finding 或明确写“无/未返回”。值在 Markdown
  中必须脱敏并截断；JSON 保留递归脱敏后的结构化证据形状。
- ZG 或其他非 CN 任务将 `repair_denoise.status` 标记为 `skipped`，因为该接口仅支持 CN；
  不得把 skipped 或 failed 解释为“没有噪音”。
- 仅当字段路径具有链路追踪或请求身份标识语义，且至少三个样本的录制值和回放值均完全不同时，才会提升为候选动作。
- 不会仅根据值差异将业务 ID、状态、金额、库存、权限、实验或配置字段提升为候选动作。
- 数组路径只有在上述镜像重建证明 `order` 或稳定 `key` 策略，且 scene、mode、匹配参数均已补齐时，
  才输出 `update_array_match`；否则输出 `undecided`。
- 每个建议动作都包含 `approval=required`、精确的 PSM/方法/路径范围、回滚意图、回读要求和回放验证。
  `execution_available=false` 表示 repair plan action 不能直接写入；确认后必须通过
  `ftf remediation execution prepare/execute` 生成并执行带 hash 的 execution plan。
- `task.evidence_hash` 绑定本次实际分析的聚类与样本证据；`plan_hash` 包含该哈希但不包含展示时间，因此相同证据重新渲染时确认身份稳定，证据变化时确认身份失效。
- 不覆盖已有输出文件。

### 2.1 固定报告格式

最终交付必须同时包含 Markdown 和 JSON 两种报告。Markdown 必须先给出“接口级全量分析”，
至少包含完整 catalog 覆盖量、方向、归一化 Method、Path family、标注、宏观噪音类型和逻辑桶；
允许为可读性只展示各分布前 20 项和逻辑桶前 50 项，但必须明确 JSON 保留全量。

逻辑接口桶表列顺序固定为：

```text
桶 | PSM | 归一化 Method | 下游逻辑 Method | 方向 | Path family | Diff Type | Cluster | Diff 明细 | 占比 | 差异机制
```

`下游逻辑 Method` 对 outbound 使用移除动态数字前缀后的归一化 outbound Method；inbound 固定为空。
`差异机制` 必须遵守上面的结构化证据边界。逻辑桶可在 JSON 中保留异质性和标注分布等辅助字段，
但不得改变或省略上述 Markdown 列。

接口级分析之后才允许出现“五元组下钻”。其 Cluster 明细表列顺序固定为：

```text
PSM | Method | Outbound PSM | Outbound Method | Diff Path | Diff Value | 修复建议 | Diff 链接
```

五元组下钻固定且仅允许上述 8 列。Markdown、飞书 XML 和在线文档必须使用完全相同的列名与顺序；
不得合并 `PSM` 与 `Method` 或 `Outbound PSM` 与 `Outbound Method`，不得删除、追加、重命名或
重排任何列，也不得为了节省宽度降为 6 列或 7 列。字段无值时保留对应列并填写“无”；
`Diff 链接` 无法生成时填写“链接不可用”，不得删除该列。

该表是人工审阅主入口，不得只输出摘要表替代。每个入选五元组 finding 至少保留一行；
同一聚类返回多个 repair denoise detail 时逐 detail 展开；dry-run 成功、失败和跳过项都必须保留。
失败和跳过原因必须保留在 Diff Value 与 JSON query 状态中。

“修复建议”不是自由文本，只能返回确定枚举值：
`add_noise_template`、`set_time_offset`、`update_array_match`、`outbound_mock_unmatched`、`undecided`。后端未返回有效且唯一的
`denoise_op_type` 时，只有满足上面的严格后备条件才能返回 `add_noise_template` 或
`set_time_offset`，或在数组镜像与匹配策略均完整证明时返回 `update_array_match`；出向 mock 匹配
配置缺失或不一致时固定为 `outbound_mock_unmatched`（对应 `outbound_mock_match_config` 动作，目标范围必须完整）；
dry-run 失败或
跳过、证据不足、后备结论冲突时固定为 `undecided`。具体失败原因、
判断依据和补证动作分别保留在 query 状态、finding evidence 和 `next_action` 中，不得拼入“修复建议”
单元格。

同一聚类包含多个 detail 时，Markdown 每一行优先展示该 detail 自身非空且合法的
`denoise_op_type`；空值才回退到 finding 的后备建议。JSON 的 `repair_denoise.queries[].details[]`
保留同等逐 detail 动作，finding 的 `repair_suggestion` 是聚类级汇总结论；多个 detail 动作冲突时，
该汇总结论固定为 `undecided`，不得据此生成聚类级动作。

JSON 报告中必须保留可机器消费的同等字段；字段名可遵循现有 schema，但语义必须覆盖：

```json
{
  "psm": "...",
  "method": "...",
  "outbound_psm": "...",
  "outbound_method": "...",
  "diff_path": "...",
  "diff_value": {},
  "repair_suggestion": "...",
  "diff_url": "..."
}
```

当字段不存在时用 `null`、空数组或明确的状态字段表达缺失，不得省略整条 finding。
`Outbound PSM` 和 `Outbound Method` 优先使用 repair denoise detail；detail 缺失、跳过或失败时，
必须回退到 Cluster catalog 中的 `outboundPsm` / `outboundMethod`，已有 Cluster 证据时不得显示“无”。
Markdown 值必须脱敏并截断；JSON 只能保存递归脱敏后的结构化证据。

`caller_code_analysis` 是计划生成阶段自动执行的当前服务代码下钻结果，依赖 Codebase
搜索、仓库解析和文件读取权限。它记录 `status`、`scope`、`items` 及每个 item 的
`conclusion`、代码版本、入口/赋值位置和证据依据；`noise_candidate` 只能在当前服务证据
支持时把 undecided finding 提升为待确认的 `add_noise_template`，不能推断下游服务行为。
对应结构约束见 [`repair-plan.schema.json`](../assets/schemas/repair-plan.schema.json)；
执行计划结构见 [`execution-plan.schema.json`](../assets/schemas/execution-plan.schema.json)。

### 3. 审核结果

JSON 是事实来源，Markdown 是固定渲染结果。请求确认前检查：
`--output-json` 的调用方使用
[`repair-plan.schema.json`](../assets/schemas/repair-plan.schema.json) 校验计划结构后再读取字段。

1. 接口级统计必须覆盖全部 Cluster：
   `interface_analysis.coverage.mode=full_catalog`，且
   `scope.interface_analyzed_clusters=scope.total_clusters`。`--max-clusters` 只限制
   五元组 worklist，最大为 500，不限制接口级统计；不得要求
   `scope.analyzed_clusters=scope.total_clusters` 作为受限下钻报告的交付条件。
   本轮工作集完整性必须满足：
   `worklist.items.length=worklist.selected_clusters=scope.drilldown_clusters`，
   `scope.analyzed_clusters=scope.drilldown_clusters`，且 `findings[]`、
   `repair_denoise.queries[]` 与 worklist 按完整 Cluster 身份一一对应。
2. 如实保留 `scope.truncated`，允许为 `true`。报告必须同时披露
   `scope.total_clusters`、`scope.drilldown_clusters` 和
   `interface_analysis.worklist.omitted_clusters`，核对总数等于入选数加未下钻数；
   存在未下钻 Cluster 时不得宣称全部 Cluster 已完成五元组下钻。
3. 五元组表数据行数必须与 CLI 固定 Markdown 实际渲染结果一致，不得直接要求等于
   `scope.drilldown_clusters`。同一 Cluster 的多个 detail 必须逐行展开；无 detail
   的成功、失败或跳过项也至少保留一行。
4. 如实保留 `repair_denoise.status` 和成功、失败、跳过数量。`partial` 或 `skipped`
   不阻止交付只读修复计划，但必须逐项保留失败/跳过的 `cluster_id`、具体原因、
   影响范围和已有后续取证动作；不得把缺失证据写成确定结论。
5. 每个可执行结论都有精确的 Flow 链接，或明确说明链接不可用。
6. 每个动作都限定到具体方法和路径；拒绝全局忽略建议。
7. 每个 `needs_human` 结论都有一项具体的后续取证动作。
8. 完成前重新查询冻结站点和任务的 `update_time`；发生变化时重新生成计划，
   不得合并不同快照的证据。
9. 用户明确知晓 repair denoise 仅执行 dry-run，且未执行任何平台配置、业务代码、
   部署、录制或回放变更。

不得在同一轮自动执行建议动作；用户确认后必须通过
`ftf remediation execution prepare/execute` 生成并执行带 hash 的 execution plan。
`ftf remediation schema update` 和 `ftf remediation array-match update` 是独立的预览/写入工作流，
不能视为对计划中 `plan_hash` 或动作 ID 的确认。

### 3.1 飞书交付检查

用户要求飞书修复计划时，使用飞书能力新建文档并原样导入 CLI 固定 Markdown；
保留所有章节、表格行、空值、`undecided`、失败原因、多组 Diff Value 和可用链接，
不得用 Agent 摘要替代标准正文。补充解读只能追加在独立章节中，并区分事实、假设、
证据边界和建议动作。

交付前必须通过确定性报告门禁，禁止以“导入成功”替代内容校验：

```bash
node <bytedance-ftf-dir>/scripts/validate-remediation-report.mjs \
  --markdown ./repair-report.md \
  --plan ./repair-plan.json
```

门禁必须拒绝以下情况：

- 缺少 `## 接口级全量分析` 或 `## 五元组下钻`，或五元组章节顺序错误；
- 五元组主表表头不是且仅不是以下 8 列，或任一数据行不是 8 个单元格：
  `PSM | Method | Outbound PSM | Outbound Method | Diff Path | Diff Value | 修复建议 | Diff 链接`；
- finding/detail 展开后的行数与表格实际行数不一致，或任一 finding 没有表格行；
- `Outbound PSM`、`Outbound Method`、`Diff Value`、`Diff 链接` 被合并、隐藏或写入摘要列；
- 修复建议不属于 `add_noise_template`、`set_time_offset`、`update_array_match`、
  `outbound_mock_unmatched`、`undecided`；
- 缺失值删除整行或整列。无值必须写入 `无`、`未返回` 或 `链接不可用` 等明确值。

门禁通过后才能导入飞书。导入完成后必须使用用户身份回读同一文档；先用目录或关键词定位
“五元组下钻”，再按返回的表格 block 读取完整表格，不能把关键词命中的瘦身切片当作全表：

```bash
lark-cli docs +fetch \
  --as user \
  --doc "<imported-docx-url>" \
  --doc-format markdown \
  --detail full \
  --json > ./lark-readback.json

node <bytedance-ftf-dir>/scripts/validate-remediation-report.mjs \
  --markdown ./repair-report.md \
  --plan ./repair-plan.json \
  --lark-json ./lark-readback.json
```

回读门禁逐行逐格比较表头、行数及 8 列内容；重点检查 `Outbound PSM`、`Outbound Method`、
`Diff Value` 和 `Diff 链接`。回读失败时必须停止交付，修复同一文档或重新导入后再次回读；
不得返回飞书链接，也不得仅凭 import ticket/job_status 成功宣称交付完成。回读 JSON 只能保存
脱敏正文和校验结果，不得写入 token、Cookie、Authorization 或原始敏感值。

导入后先定位“五元组下钻”表格，再按完整 table block 读取，不得用关键词命中的
表格切片作为完整性证据。核对实际保存的行数、8 列名称及顺序，并逐格核对
Outbound PSM、Outbound Method、Diff Value 和 Diff 链接；行数以固定 Markdown
的实际展开行数为准。回查不一致时修复同一文档并重新读取，不得宣告交付完成。

飞书返回单表单元格上限时，保持原始 Markdown 文件不变，将超限表按原始行序写入
同一文档中的连续 table block，每张表重复相同表头，数据行不得删减、合并或改写。
逐张完整读取后，以数据行数之和及逐格内容核验标准表；同时保留所有后续章节。
导入返回成功也必须回查正文，不得仅凭导入回执判断内容完整。

### 4. 初始计划之后的深度下钻交接

当用户要求“继续分析”“补充证据”或“给出最终修复方案”时，不要重新猜测根因。
以初始计划 JSON 中的 `findings[].cluster_id`、`direction`、`method` 和
`flow_diff_url` 作为不可变 worklist，逐个 finding 完成只读取证。

此时必须完整加载并执行
[`remediation-deep-dive.md`](remediation-deep-dive.md)。初始计划中的
`difference_mechanisms` 中的 `missing_value_pairs` / `query_failed` 和 `undecided` 只是初筛状态，
不是最终分析结论；
不得把本命令生成的 Markdown 直接改名或原样上传为最终修复报告。下面 4.1 至 4.6
只列出可复用的证据入口；Top 10 / 80% 选择、跨 Flow 样本和反例、四类结论门禁、
报告契约及严格完成检查均由深度下钻工作流定义，并优先于本节的概述。

#### 4.0 Skill 路由和证据门禁

完整闭环需要按以下顺序加载 Skill；它们是按证据类型分工，不是全部无条件执行：

| 证据目标                              | Skill                                      | 触发条件                                                                     | 只读入口                                                                                        |
| ------------------------------------- | ------------------------------------------ | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| task/cluster/Flow、DIFF、任务执行配置 | `bytedance-ftf`                            | 始终                                                                         | `ftf target parse`、`ftf task get`、`ftf remediation`、`ftf task diff-cluster`、`ftf flow diff` |
| base→target 字段变更因果              | `ftf-code-analyzer`                        | 已冻结 `task_id + similar_diff_id`，且存在待判断的 revision delta            | FTF wrapper；repository、base、target 仅由 Code resolver 解析                                   |
| 同版本或本地/MR 代码链路              | `bytedance-codebase`（由 `bytedcli` 路由） | Analyzer 返回 `not_applicable/no_revision_delta`，或用户明确要求本地/MR 分析 | `ftf psm get`、`codebase repo file`、`codebase search code`、`codebase repo blame`              |
| PSM/LogID 日志和调用树                | `bytedance-log`（由 `bytedcli` 路由）      | 已取得真实 PSM、LogID、任务时间窗或 TraceID                                  | `log get-logid-log`、`log trace-tree`、必要时 `log search-psm-log`                              |
| Trace tag/metric 语义                 | `bytedtrace-knowledge`                     | 需要解释 BytedTrace tag/metric，或 `trace-tree` 结果不足                     | 作为查询解释参考，不替代真实 Trace 查询                                                         |
| TCC 配置                              | `bytedance-tcc`（由 `bytedcli` 路由）      | Trace/outbound 明确出现 TCC namespace/config                                 | `tcc namespace get`、`tcc config get`、`tcc config version diff`                                |
| TCE 环境/集群/实例                    | `bytedance-tce`（由 `bytedcli` 路由）      | 需要核对任务时间窗内服务、cluster 或实例                                     | `tce service get`、`tce cluster list`、`tce instance list`                                      |
| RDS/数据库数据状态                    | `bytedance-rds`（由 `bytedcli` 路由）      | Trace 明确指向数据库且已有数据库资源身份                                     | `rds db overview`、`rds db table schema`、只读 `rds db query`                                   |

禁止仅因为出现一个字段名就猜测 TCC namespace、数据库名、cluster 名或日志区域。
外部资源身份、权限或时间窗缺失时，暂停对应 finding 为 `evidence_blocked`，
记录真实 blocker 和唯一恢复动作；不得用当前配置或当前日志替代任务时间窗证据。

#### 4.1 聚类详情

Inbound finding 使用：

```bash
bytedcli --json ftf task diff-cluster get \
  --url "<ftf-task-url>" \
  --direction inbound \
  --similar-diff-id "<cluster_id>" \
  --with-values \
  --sample-values 3 \
  --with-similar-cases \
  --with-outbound
```

Outbound finding 使用：

```bash
bytedcli --json ftf task diff-cluster get \
  --url "<ftf-task-url>" \
  --direction outbound \
  --similar-diff-id "<cluster_id>" \
  --with-outbound
```

Outbound 不要传 `--with-values`、`--sample-values` 或 `--with-similar-cases`，
因为这些参数当前只适用于 inbound value diff。即使不传这些参数，命令仍会返回
outbound cluster 详情和 `outbound` / `outboundDiff` 上下文。
当前 CLI 没有 outbound equivalent 的 similar-case 聚合入口；需要代表 Flow 时使用
finding 的 `flow_diff_url`，并执行 `ftf flow diff get --with-outbound`。
保留 `cluster.raw`、`inbound` / `outbound` 完整证据和所有 source endpoint。

#### 4.2 跨 Flow 与请求/输入证据

单个代表 Flow 不能证明跨 Flow 稳定性。先按 finding 的 method 建立 Flow inventory：

```bash
bytedcli --json --site "<task_site>" --vregion "<task_vregion>" ftf task flow list \
  --task-id "<task_id>" \
  --psm "<psm>" \
  --method "<method>" \
  --page-size 100
```

当返回 `has_more=true` 时，必须用返回的 `next_cursor` 续查，最多 20 页或 2000 条，
并记录覆盖范围。为每个 finding 选择同质样本和一个反例样本，不得把不同 method、方向或
`similar_diff_id` 的样本混用。

对每个选定 Flow：

```bash
bytedcli --json ftf flow diff get \
  --url "<flow_diff_url>" \
  --with-values \
  --with-outbound
```

对 inbound 样本额外记录：

- request 参数、分页/排序/过滤字段；
- base/replay 原始值的 `present`、`found`、类型和差异；
- response 状态码、错误字段和目标 path。

对 outbound 样本额外记录：

- outbound PSM、protocol、method；
- base/replay 请求参数和 header 差异；
- 调用次数、匹配状态、未匹配或重复使用情况；
- outbound response 是否能解释 inbound DIFF。

`--with-similar-cases` 只适用于 inbound value diff；outbound 使用 Flow inventory
和 `flow diff get --with-outbound` 扩展样本，不得强行传入冲突参数。

#### 4.3 代码归因分流与固定提交链路证据

对每个去重后的 `similar_diff_id`，先按
[`code-diff-correlation.md`](code-diff-correlation.md) 分流：

- base→target 字段变更因果使用 canonical `ftf-code-analyzer`，只传
  `task_id + similar_diff_id`；不得预先解析或传入 repository、base revision、target revision。
- Analyzer 返回 `not_applicable/no_revision_delta` 或 base/replay commit 完全相同时，使用冻结任务
  和执行人的 Codebase 权限完成下列固定版本静态链路分析。
- 用户明确要求本地 workspace/MR/commit/branch 分析时，读取
  `code-diff-correlation.md#用户指定的本地--mr-代码对象` 中该对象的真实 diff，再与任务 target
  commit 建立身份关系；不要把本地/MR 路径替换为 replay commit 的固定版本读取。

1. 先读取任务详情，冻结 `run_psm`、`psm_replay_param_detail.<psm>.commit_hash`、
   `base_commit_hash`、`replay_env`、`replay_cluster`、`base_task_id` 和 `base_task_id_realtime`。
2. 用任务 PSM 查询官方绑定：

```bash
bytedcli --json --site cn ftf psm get --psm "<psm>"
```

必须从返回的 `git_url` / `scm` 获取仓库，不得按 PSM 名称猜仓库。仓库、任务目标 commit、
代表 Flow 的 `base_commit` / `replay_commit` 必须相互核对；不一致时停止合并证据。
代码文件固定在 replay commit 读取：

```bash
bytedcli --json codebase repo file "<path>" \
  -R "<repo>" --revision "<replay_commit>"
```

3. 根据 method 和 diff path 沿以下顺序定位，而不是只搜字段名：
   - RPC/handler 入口和请求参数；
   - 字段生产、默认值、分页/排序/过滤、灰度和提前返回；
   - 下游 RPC/ES/DB/Mock 请求构造与调用次数；
   - 错误映射、响应组装和字段缺失/新增位置。
     可用 `codebase search code` 找候选文件，再用 `repo file --revision` 读取固定版本全文，
     必要时用 `repo blame` 校验提交归属。
4. 同一 commit 的 base/replay 只允许输出“同版本运行路径机制”；不能写成“本次代码变更引入”。
   代码证据只能证明固定版本设计机制，真实 Flow 是否命中该分支仍需任务时间窗日志/Trace，
   或可核验的请求/响应和下游证据闭合。
5. 每个 finding 必须记录仓库、固定 commit、文件行号、调用链、代码可解释的事实、
   未被代码证明的外部状态，以及下一条唯一补证查询。代码读取权限不足时记录
   流程状态 `evidence_blocked` 并暂停该 finding，不得改用默认分支或本地未绑定仓库；
   取得权限并恢复后，`conclusion` 再按证据选择 `code_or_config_fix` 或
   `needs_more_evidence`。

#### 4.4 日志和 Trace 运行时证据

使用真实代表 Flow 的 `logid_comparison`、`replay_psm`、`replay_time` 和 `replay_idc`。
`log_id` 只标识原始流量，不得用于查询回放链路。优先精确回放 LogID 查询：

```bash
bytedcli --json --site "<replay_site>" log get-logid-log "<logid_comparison>" \
  --psm "<replay_psm>" \
  --vregion "<replay_vregion>" \
  --start "<replay-window-start>" \
  --end "<replay-window-end>" \
  --rolling \
  --max-logs 200
```

仅当执行记录对应环境支持 BytedTrace 时查询调用树；BOE 等不支持环境保留精确日志证据，
不得把 Trace 不可用解释为业务链路不存在：

```bash
bytedcli --site "<replay_site>" log trace-tree \
  --log-id "<logid_comparison>" \
  --region "<replay_region>" \
  --output-file "<trace-output>"
```

需要按 method 和时间窗判断整体行为时，才使用：

```bash
bytedcli --site "<replay_site>" log analysis performance \
  --psm "<replay_psm>" \
  --method "<method>" \
  --start "<replay-window-start>" \
  --end "<replay-window-end>"
```

日志/Trace 必须核对：实际命中的下游 PSM、首个字段出现/改变/丢失的 span、
分页/过滤/路由分支、错误状态和 outbound 匹配。结果必须绑定真实 Flow ID；
日志文案或错误码单独不能证明根因。

#### 4.5 数据、配置和部署证据

只有 Trace/outbound 已明确给出资源身份时，才进入对应查询：

```bash
# TCC，只读
bytedcli --json --site cn tcc namespace get "<namespace>"
bytedcli --json --site cn tcc config get \
  "<namespace>" "<config_name>" \
  --env "<env>" \
  --region "<region>" \
  --dir "<dir>"

# TCE，只读
bytedcli --json --site cn tce service get --psm "<psm>" --env "<env>"
bytedcli --json --site cn tce cluster list \
  --psm "<psm>" --env "<env>" --page 1 --page-size 100
bytedcli --json --site cn tce instance list \
  --psm "<psm>" --env "<env>" --ordering cpu

# RDS，只读，数据库和表身份必须已由 Trace/资源证据确认
bytedcli --json --site cn rds db overview "<dbname>" --region "<region>"
bytedcli --json --site cn rds db table schema "<dbname>" "<table>" --region "<region>"
bytedcli --json --site cn rds db query "<dbname>" \
  "SELECT ... LIMIT 100" --region "<region>"
```

查询结果必须同时记录资源身份、环境/region、任务时间窗内的有效版本或数据状态。
不要用当前配置证明历史 replay 行为；无法取得历史状态时结论只能保持
`needs_more_evidence` 或 `evidence_blocked`。

#### 4.6 Flow 级取证

如果 finding 有 `flow_diff_url`，继续执行：

```bash
bytedcli --json ftf flow diff get \
  --url "<flow_diff_url>" \
  --with-values \
  --with-outbound
```

读取 base/replay 原始值、diff path、状态码、错误信息、outbound 匹配状态和代表 Flow
时间。Flow 链接只能证明可观测症状，不能单独证明代码根因。

按路径追加专项证据：

- 动态值或分布模式：`ftf diff path-profile get`；
- 数组或顺序差异：`ftf diff array-check get`；
- 单条 Flow 有失败状态：`ftf task flow get`，再按 `diag-replay-failure.md` 分流。

#### 4.7 Finding 结论素材

以下字段属于 `needs_human` 后续取证记录和最终修复方案，不是初始
`repair-plan.schema.json` 的 `findings[]` 字段：

```text
finding_id
cluster_id
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

`conclusion` 只允许：

- `confirmed_noise`：已证明是可安全忽略的动态值、数组顺序或精确规则命中；
- `code_or_config_fix`：证据指向业务代码、配置、环境或 Mock 行为需要修复；
- `needs_more_evidence`：仍缺少一项具体证据，不能下确定结论；
- `excluded`：平台已有精确规则或前置筛选已排除。

不能把“值不同”直接写成 `confirmed_noise`，也不能把 Flow 链接本身写成代码根因。
每个 `needs_more_evidence` 必须指出唯一缺失证据和下一条可执行的只读查询。
这些字段只有通过 `remediation-deep-dive.md` 的逐桶 Completion Gate 后才能进入最终报告。

#### 4.8 最终修复方案

最终修复方案必须由 `remediation-deep-dive.md` 生成。以下内容是最低信息集合，
不能替代该工作流的 Top 10 / 80% 覆盖目标、跨 Flow 反例、结论门禁和严格检查：

1. 任务快照和初始 `plan_hash` / `evidence_hash`；
2. 每个 finding 的取证结论、证据链接、置信度和证据缺口；
3. 按 `confirmed_noise`、`code_or_config_fix`、`needs_more_evidence` 分组；
4. 每个修复动作的目标 PSM、method、direction、path、最小变更、责任方和验证方式；
5. 预期影响范围、回滚方式和回放验证标准；
6. 未分析聚类、权限/数据阻塞和任务 `update_time` 变化；
7. 明确声明没有执行平台标注、规则写入、代码提交、部署、录制或回放。

如果任务快照或 `update_time` 在闭环中发生变化，停止合并旧证据，重新生成计划并标记旧 finding
失效。只有在每个适用证据入口都实际检查或记录了真实 blocker 后，才允许输出
`needs_more_evidence`；否则将 finding 的独立流程状态记为 `evidence_blocked`，保持
`conclusion` 未定并暂停最终报告。
没有足够证据时不要伪造最终修复结论。

## Structured Output

- 初始 repair plan JSON 必须通过
  [`repair-plan.schema.json`](../assets/schemas/repair-plan.schema.json) 校验。
- 4.7 的后续取证记录和 4.8 的最终修复方案是独立只读审阅材料，不得向 schema `1.9`
  的 `findings[]` 注入 `conclusion`、`evidence_blocked` 或其他未声明字段，也不得改写初始
  `plan_hash` / `evidence_hash`。
- `interface_analysis` 基于完整 catalog，`findings` 基于受限的五元组 worklist；
  两者覆盖范围不得混写。`repair_denoise.queries[]` 与初始 finding worklist 一一对应；成功项保留后端
  `process_mode`、`executed`、脱敏后的 `details` 和 endpoint，失败项保留结构化 error，
  跳过项保留明确 reason。
- `findings` 保存全部分类结论，`actions` 仅保存达到候选门槛且仍需审批的动作。
- `execution_enabled` 和每个 action 的 `execution_available` 固定为 `false`；写入前必须经过
  execution prepare 的逐 Action dry-run 和 execute 的 hash 确认。
- Markdown 只用于人工阅读，不替代 JSON 契约。

## Results

- 成功：输出 schema-valid JSON 和对应 Markdown；如指定文件路径，则以新文件写入且不覆盖旧文件。
- 部分完成：完整 catalog 无法取得时停止生成计划；`scope.truncated=true` 时必须明确
  全量 catalog、入选 Cluster 和未纳入本轮 Cluster 数量，但只要本轮 worklist 闭环完整，
  仍可生成本轮报告。
- 失败：任务身份、证据字段或输出路径不满足契约时停止，不生成可供确认的计划。
