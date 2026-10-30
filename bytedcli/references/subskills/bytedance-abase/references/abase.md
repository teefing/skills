# ABase

ABase2 namespace、table、存储与 RU 使用量、大/热 Key 采样、容量扩容与在线查询命令。

```bash
bytedcli abase list --scope all --keyword "demo.namespace" --limit 20
bytedcli abase list --scope mine --limit 20
bytedcli abase list --scope favor --limit 20
bytedcli abase search --psm "demo.namespace"
bytedcli abase search --psm "bytedance.abase2.demo_namespace"
bytedcli abase get --psm "demo.namespace"
bytedcli abase get --namespace-id 1001 --cluster "sample-cluster"

# 共享控制面：用 --site 选控制面，--region 选具体 deployment
bytedcli --site us-ttp abase get --psm "demo.namespace" --region US-TTP2
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-TTP2
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region US-EastRed
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-Compliance
bytedcli --site eu-ttp abase get --psm "demo.namespace" --region EU-Compliance2
bytedcli --site i18n-tt abase get --psm "demo.namespace" --region Singapore-Central
bytedcli --site i18n-tt abase get --psm "demo.namespace" --region US-East
```

Table 查询：

```bash
bytedcli abase table list --psm "demo.namespace"
bytedcli abase table list --cluster "sample-cluster" --namespace "demo_namespace"
bytedcli abase table get --psm "demo.namespace" --table "sample_table"
bytedcli abase table get --cluster "sample-cluster" --namespace "demo_namespace" --table-id 2001
```

`table get` 的 JSON `data.table.id` 保留服务端 ID，服务端未返回时为 `null`；
`requested_table_id` 单独记录实际请求的 ID（显式传入或由表清单按名称解析）。
`data_center` 兼容历史标量和字符串数组，`support_cds` 兼容历史布尔值和数组，
JSON 保留数组原值，缺失/null 保持未知；空数组不转换为 false。表清单仍要求 ID。
返回的 ID、cluster、namespace 或显式表名与请求矛盾时，返回 `ABASE_RESPONSE_MISMATCH`。

容量查询与新计费模式扩容：

```bash
# 共享 namespace 不传 table；独占 namespace 必须传 --table
bytedcli --json abase capacity get --psm demo.namespace
bytedcli --json abase capacity get --cluster demo-cluster --namespace demo_namespace --table demo_table

# 20 表示增加 20%，范围为整数 0–100；区域/VDC 名称使用 capacity get 的返回值
bytedcli --json abase capacity submit --psm demo.namespace \
  --storage-increase-percent 20 --read-increase demo-region=20 \
  --write-increase demo-region=30 --idempotency-key demo-capacity-001 --dry-run

# 确认预览后，使用同一参数、幂等键与返回的 plan_sha256
bytedcli abase capacity submit --psm demo.namespace \
  --storage-increase-percent 20 --read-increase demo-region=20 \
  --write-increase demo-region=30 --idempotency-key demo-capacity-001 \
  --yes --expected-plan-sha256 <preview-hash>

# VDC 读扩容（与区域 --read-increase 互斥）
bytedcli abase capacity submit --psm demo.namespace \
  --read-vdc-increase demo-region/demo-vdc=20 --idempotency-key demo-vdc-capacity-001

# submitted 是已提审批工单，按返回的 ticket_id 跟进
bytedcli abase ticket get --id 123
```

`capacity submit` 默认只读预览；`--dry-run` 与 `--yes` 互斥。至少一项增加，
不传的维度不请求修改。区域读扩容同时增加区域默认配额和该区域 VDC 配额；
VDC 模式只修改所选配额，不得超过区域默认值，也不支持 LEADER_ONE。
预览为本地估算，后端 RU 下限可能提高最终配额，完整资源准入与审批由服务端执行。
Kvcache 存储硬上限会在本地阻止提单。哈希覆盖目标、配额与请求；
配额变化后需重新预览，但校验不是服务端原子锁。
若报 `ABASE_CAPACITY_OUTCOME_UNKNOWN`，保留幂等键，先查工单和控制台，不能自动重提。
扩容需要 IAM operator/owner 权限；ACP SDK 授权不等同于该权限。
仅支持 ABase2 RW_SPLIT 扩容，不支持缩容或新增机房。

存储与 RU 使用量和 Key 采样：

```bash
bytedcli --json abase capacity usage get --psm demo.namespace
bytedcli --json abase capacity usage get --psm demo.namespace --table demo_table
bytedcli abase hot-key list --psm demo.namespace --range 1h
bytedcli abase big-key list --cluster demo-cluster --namespace demo_namespace --table demo_table --range 7d
bytedcli --json abase hot-key list --psm demo.namespace \
  --start 1700000000 --end 1700003600 --partition-id 9007199254740995 --page 2 --page-size 10

# 扩容工单状态与实际配额，必须使用该次提交返回的 ticket_id
bytedcli --json abase capacity status --ticket-id 123
bytedcli --json abase capacity status --ticket-id 123 --wait --timeout-ms 60000 --interval-ms 5000
```

- 目标选择 `--psm` 或成对的 `--cluster --namespace`；全局 `--site` 选择控制面，`--region` 校验 deployment，并选择存储查询地域，RU 配额地域保持控制面返回值。
- `capacity usage get` 返回 RU / GB quota 用量。存储共享 namespace 对应整个底层物理表，禁止 `--table`；独占 namespace 必须指定 `--table`。`storage.observations[]` 按地域/DC 返回 `used_gib/quota_gib/utilization/sampled_at`，GB 的实际单位为 GiB（2^30 字节），利用率为比例（0.5 = 50%），采样时间为 Unix 秒。分子/分母来自同一地域/DC/时间的 rootserver engine_used/disk_quota，取最近 15 分钟内最新成对采样；默认查所有部署地域，DC 不累加。数值指标不保证 uint64 字节精度；`scope=physical_table`、`physical_table` 标明目标。
- RU 仅适用于共享 RW_SPLIT namespace。JSON 的 `regions[].vdcs[]` 包含 `read_usage/read_quota/read_utilization`，`regions[]` 包含 `write_usage/write_quota/write_utilization/write_coverage`；利用率为比例。缺失采样不算零，VDC 覆盖不全不汇总地域写用量，零分母输出 null。
- 存储每行和 `ru` 各自报告 `state/reason/error`，一项或一个地域失败不会丢弃其他观测；整体 `availability=complete/partial/unavailable`，存储 `coverage=complete/partial/none`。不支持的 RU 为 unsupported，缺失或 15 分钟内无成对存储指标为 unavailable，缺失值为 null；零用量有效，零分母的利用率为 null。`capacity usage get` 不接受历史时间窗；`observed_at` 是查询完成时间，RU 采样时间与周期未提供（`sampling_period=null`）。
- `storage.coverage_scope=queried_regions_and_returned_dcs`，覆盖率仅针对查询地域和已返回的 DC。完全没有返回指标的 DC 无法识别，`deployment_dc_coverage=unknown`，complete 不表示全部部署副本健康。
- 热 Key 默认最近 1h，大 Key 默认最近 24h，两者最大 7d；`--range` 与 `--start/--end` 互斥，时间支持 ISO、epoch 秒/毫秒和相对时间。共享 namespace 可用 `--table` 过滤子表，独占 namespace 必须传 table；表名精确匹配列表，namespace 名跨 cluster 重复时拒绝查询。partition/replica ID 保留十进制字符串。
- Key 按 OPS/size 降序做本地分页；`--page` 默认 1，`--page-size` 默认 20，范围 1–1000。`items` 是当前页，`returned_count` 是接口返回条数，`current_count` 是当前页条数；`has_more` 只表示还有本地页，`source_completeness=unknown`。这些是已有采样，命令不会触发全量扫描。
- `capacity status` 从特定工单获得 cluster/namespace/table 和服务端计算的目标配额，支持共享和独占 RW_SPLIT 扩容。输出 `workflow` 原始阶段和归一化状态，`verification` 单独列出每项 `expected/actual/relation`。缺少目标/当前配额或读取失败为 unknown；实际配额大于目标仍视为 reached。核验是当前时点比较，无法排除后续变更；独占 table ID 必须与工单一致，共享 namespace 历史 ID 可能缺失。
- `--wait` 仅在工单成功且配额 reached 时成功结束；工单 running 时即使配额已达标也继续等待。驳回、关闭、失败或未知终态立即停止。`--timeout-ms` 默认 60000、范围 1–600000，`--interval-ms` 默认 5000、范围 100–60000，两者仅与 `--wait` 使用。超时返回最近观测和 `timed_out=true`；首次查询失败报结构化错误，后续工单查询失败保留最近观测并设置 `observation_error`。

在线查询：

```bash
bytedcli abase command list
bytedcli abase command list --psm "demo.namespace" --table "sample_table"
bytedcli abase command run --psm "demo.namespace" --table "sample_table" --command "GET" --inputs "sample-key"
bytedcli abase command run --cluster "sample-cluster" --namespace "demo_namespace" --table "sample_table" --payload-json '{"command":"GET","inputs":"sample-key"}'
```

区域元数据：

```bash
bytedcli abase region list
bytedcli abase location list
bytedcli --site i18n-tt abase region list --region "Singapore-Central"
```

ABase classic（1.0）集群查询（只读，使用独立的 ByteCloud gateway path）：

```bash
# 服务（集群）列表；--keyword 与 --limit 均为客户端本地过滤/截断（后端一次性返回全量）
bytedcli abase cluster list
bytedcli abase cluster list --keyword demo --limit 50

# 单集群详情 + 概要（version / shard_num / 磁盘用量）
# --psm 用集群 PSM（如 abase_demo_service），不是 list 里显示的短名
bytedcli abase cluster get --psm abase_demo_service
bytedcli abase cluster get --psm abase_demo_service --no-summary
```

ACP 鉴权（SDK 运行态授权，查询/新增/删除走 option 参数）：

```bash
# 查询某 namespace 已授权的 PSM / 用户（--region 为按 region 值的本地过滤，可省略）
bytedcli abase acp list --namespace "demo_namespace"
bytedcli abase acp list --namespace "demo_namespace" --perm-region "sinf"

# 新增授权：先 --dry-run 预览，再换成 --yes 提交（会生成 BPM 审批工单）
bytedcli abase acp add --namespace "demo_namespace" --perm-region "ChinaSinf-North" --psm "demo.service.psm" --perm r --dry-run
bytedcli abase acp add --namespace "demo_namespace" --perm-region "ChinaSinf-North" --psm "demo.service.psm" --perm r --yes
bytedcli abase acp add --namespace "demo_namespace" --perm-region "ChinaSinf-North" --user "demo-user" --perm rw --yes

# 删除授权（同样生成审批工单）
bytedcli abase acp delete --namespace "demo_namespace" --perm-region "ChinaSinf-North" --psm "demo.service.psm" --perm r --dry-run

# 对账修复该 namespace 的 ACP 授权（对应控制台「一键修复 ACP 授权」）
bytedcli abase acp sync --namespace "demo_namespace" --dry-run
bytedcli abase acp sync --namespace "demo_namespace" --yes
```

工单（BPM workflow record，`target_system=abase2`）：

```bash
# 工单列表 / 详情 / 审批人
bytedcli abase ticket list --namespace "demo_namespace" --creator "demo-user"
bytedcli abase ticket list --status "owner_approve" --page 1 --page-size 10
bytedcli abase ticket get --id 108000001
bytedcli abase ticket approvers --id 108000001

# 审批 / 驳回 / 取消（高风险写，先 --dry-run 再 --yes）
bytedcli abase ticket approve --id 108000001 --dry-run
bytedcli abase ticket approve --id 108000001 --comment "lgtm" --yes
bytedcli abase ticket reject --id 108000001 --reason "duplicate request" --yes
bytedcli abase ticket cancel --id 108000001 --yes

# 执行失败后重试（无需重新审批）
bytedcli abase ticket retry --id 108000001
```

在 DataLeap 上创建 ABase 逻辑表：

```bash
bytedcli abase logic-table create \
  --namespace "demo_namespace" \
  --database "demo_db" \
  --table "demo_table" \
  --column "author_id:BIGINT:author" \
  --column "data_col_type:INT" \
  --column "date:VARCHAR:date" \
  --primary-key "author_id,data_col_type" \
  --key-format 'demo_table:${author_id}:${data_col_type}' \
  --value-type "general" \
  -r cn
```

按当前用户权限搜索 ABase 逻辑表（biowner）：

```bash
bytedcli abase logic-table list --name "demo_tbl" --parent-name "demo_db" -r cn
bytedcli abase logic-table list --page 2 --page-size 10 --sort-field name --sort-order asc
```

Notes:

- 国内生产默认使用 `--site cn`（可省略）；跨站点时用全局 `--site boe|i18n-bd|i18n-tt|us-ttp|eu-ttp`，再用 `--region` 选择共享控制面上的 deployment。
- `us-ttp` 站点由 `US-TTP` 与 `US-TTP2` deployment 共享控制面，`eu-ttp` 站点由 `EU-TTP`、`EU-TTP2`、`US-EastRed`、`EU-Compliance` 与 `EU-Compliance2` deployment 共享控制面。`i18n-tt` 用 `--region Singapore-Central` 或 `--region US-East` 选择 ROW 成员。使用 `--psm` 解析 namespace 时，CLI 会先聚合完整 PSM 与 suffix 的全部精确同名候选，再读取候选详情，并按 `--region` 指定的 deployment 精确筛选。
- `--region US-TTP`、`--region US-TTP2`、`--region EU-TTP`、`--region EU-TTP2`、`--region US-EastRed`、`--region EU-Compliance`、`--region EU-Compliance2`、`--region Singapore-Central` 和 `--region US-East` 是 deployment 选择条件，不是同名 namespace 的跨区域回退条件。指定 deployment 中没有候选时返回 `ABASE_NOT_FOUND`；筛选后仍有多个候选时返回 `ABASE_AMBIGUOUS`，不会接受 ROW/SG 或其他 deployment 的同名 namespace。旧 overlay 简写（如 `us`、`gcp`、`i18n`）不会进入这张表，只回落到当前 `--site` 的 default host，不要用它们选 deployment。
- 在 `i18n-tt`（默认/sg）站点，ABase2 namespace、table、command、region、location 和 ACP 请求统一通过 ByteCloud gateway；CLI 会自动补齐所需 routing header，用户无需手工传 header。Classic cluster 与 BPM ticket 继续使用各自的 gateway path，DataLeap logic-table 保持独立。
- `abase search --psm` 支持完整 PSM（例如 `bytedance.abase2.demo_namespace`）；首查无结果时会自动按 suffix（例如 `demo_namespace`）重试，短 namespace 也可直接搜索。
- `abase acp add/delete` 用 `--perm-region` 指定授权所属的 **ABase 可读 region 名**（如 `ChinaSinf-North`），与其他命令的 `--region` deployment 选择（如 `US-TTP`）不是一回事；工单 config 里的 `region` 字段用的就是这个可读名。
- `abase acp list --perm-region` 是对回读结果的本地过滤，取值是**短名**（如 `sinf`），与提交授权用的可读名不同，按 `acp list` 回读到的值填。
- 旧的 `--region` 在这三个 acp 命令上保留为**隐藏兼容别名**（`!2359` 已上线，避免破坏既有脚本），新脚本一律用 `--perm-region`；同传两个且值不同会报 `ABASE_INPUT_ERROR`。其他 abase 命令（`list`/`get`/`table`/`ticket` 等）的 `--region` 是 deployment 选择条件（如 `US-TTP`、`Singapore-Central`），语义不同，别混。
- `abase acp list` 的 JSON 输出字段名仍是 `region`（未改名，保持向后兼容）。
- `abase acp sync` 对应控制台「一键修复 ACP 授权」，请求体只有 `{namespace}`（与控制台前端一致，CLI 只发送这一个字段）；与 `acp add` / `delete` 不同，它不返回工单 id，执行后用 `acp list` 回读确认实际授权。
- ACP `add` / `delete` / `sync` 和工单 `approve` / `reject` / `cancel` 都是写操作，必须带 `--dry-run`（预览）或 `--yes`（执行）之一；两者都不带会返回 `ABASE_CONFIRMATION_REQUIRED`。
- 授权提交后返回 BPM 工单 id，生效需要 namespace owner 审批；用 `abase ticket get --id <id>` 跟进状态，`abase ticket approvers --id <id>` 查看每个阶段可审批人（`config._context_.assignees_map`），当前阶段列出的任何人都可审批。
- `abase ticket *` 使用独立的 ByteCloud gateway BPM 工单路径；`--status` 过滤用 BPM 状态 key（如 `owner_approve`、`done`）。
- `abase ticket list` 后端未返回 total 时，JSON 用 `current_count` + `page`/`page_size` 表达当前页上下文，不会用页内条数冒充 total。
- Redis / Cache 服务仍使用 `bytedcli cache ...`，ABase2 namespace / table 使用 `bytedcli abase ...`。
- `--limit` 对 namespace list/search 是本地输出上限；后端列表接口当前不返回可靠 total，JSON 输出使用 `current_count`。
- `abase logic-table create` 走 DataLeap CoralNG（`management/data-store`，`typeName=ABaseLogicalTable`），region 参数与 hive/paimon 一致；命令不生成 DDL，也不做 explain，`--primary-key` 中的列必须先出现在 `--column` 里。
- `abase logic-table create --column name:type[:comment]` 里的 `type` 是 **ByteSchema 大写枚举**：`INT / BIGINT / VARCHAR / DOUBLE / FLOAT / BOOLEAN / DATE / TIMESTAMP / BINARY`。**不要**沿用 hive / paimon skill 里的小写 `bigint / int / string`——CoralNG 后端拒识大小写敏感，会返回 `校验Schema错误: not find the byteSchemaType, the typeName = bigint`；handler 已加入拒识与 hint。
- `abase logic-table list` 走 DataLeap CoralNG（`data-stores/info/self`，`filterMode=biowner`），只返回当前登录用户有 biowner 权限的表；`--name` 匹配逻辑表名，`--parent-name` 匹配物理表 / app group 名，两者都是模糊匹配。
