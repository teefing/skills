---
name: bytedance-triton
description: "Use bytedcli Triton commands for DataLeap permission workflows: apply for Hive table, column, or row-scoped data permission (delegates to Coral, with 304 合规问卷 flow), answer questionnaire, create application, list obtained privileges (我的权限 / obtained list), directly grant database or table permissions without approval (grant), inspect granted privileges (managed), renew expiring permissions, keep redundant privileges from being recycled (冗余权限保留 keep), and approval center (list/get/approve/reject). Use when the task mentions Triton, 权限申请, 我的权限, obtained privileges, obtained list, 直接授权, 免审授权, Hive 库级授权, 库/表已授权清单, managed privileges, grant, 分区权限, 权限续期, 续期, 一键续期, 冗余权限, 权限保留, 冗余权限回收, 冗余回收, 80天未用, 90天未用, keep privileges, 审批中心, approval center, dataleap triton, or 304 / 合规问卷."
---

# bytedcli Triton

Use this skill when the task mentions Triton, 权限申请 (permission apply), 我的权限 (obtained
privileges), Hive 库级/表级直接授权 (direct grant), 库或表已授权清单 (managed privileges), 审批中心 (approval
center), approval, 申请权限, dataleap triton, or 304 / 合规问卷 (compliance questionnaire).

Triton 的权限管理 + 审批中心后端就是 Coral 的权限 API（`coral_<cluster>_api`，同一个
DataLeap host 与认证）。apply/answer/create 直接 delegate 给 Coral；审批中心命令读
`applications/merged/*` / `approvals/merged/*` 端点；grant / managed 走 `privileges/add`
与 `privileges/managed`。

## Invocation

```bash
bytedcli --json triton <command> [options]
bytedcli --json --site i18n-tt triton <command> [options]
```

`--json`, `--site`, `--http-proxy`, `--socks5-proxy`, and every other bytedcli
global flag must appear after `bytedcli` and before `triton`. Keep domain flags such as
`--region` after the Triton subcommand. For example:

```bash
bytedcli --json --site i18n-tt triton approval get --region us-eastred --id 1001
```

本仓库本地测试用：

```bash
node dist/bytedcli.js --json triton <command> [options]
```

The commands below match the current CLI contract and can be used directly. Use
`triton --help` / `triton apply --help` / `triton approval --help` only for options not
covered here; do not guess flags.

库级授权和回查支持 Triton 当前全部 region：`cn | sg | va | gcp | us-eastred |
eu-ttp2 | us | mycis | sglark | jplark | uspipo`，以命令 `--help` 为准。`cn` 会映射到国内 DataLeap 的
`coral_api` / `cluster=default`；`mycis` 会映射到 DataLeap MYCIS 的
`coral_pinnacle_api` / `cluster=pinnacle`，适合
DataLeap MYCIS Triton 权限申请页面抓包里的 Hive 权限工单。
不传时按 `--site` 映射出默认 region。

库级 `grant` 与 `managed list` 共用上述 region 路由及各区域既有鉴权。`eu-ttp2`
对应 `cluster=norway`；`gcp` 与 `us-eastred` 是不同的控制面，分别对应 `texas`
和 `i18ngcp`，不能互换。库级能力不额外放宽各区域后端的审批、TTL 或资源策略。

### Preserve region across the workflow

Treat the CLI region as routing context, not as a property to rediscover from the returned
resource:

1. Preserve an explicit region from the user, alert, URL, draft, or prior command context.
2. `triton apply` and `triton apply create` return `data.region`; keep that value for later
   `approval list/get/approve/reject` calls. When a group id comes from `approval list`, use
   the same `--region` that produced the list.
3. If the only routing evidence is `groupName=i18ngcp` or `cluster=i18ngcp`, use
   `--site i18n-tt --region us-eastred`.
4. Do not replace that route because an application detail or resource reports
   `cluster=gcp`. That is resource metadata. CLI `--region gcp` selects the separate
   `cluster=texas` permission gateway; it is not the route for i18ngcp.

A wrong region can return HTTP 401 even when the current credential is valid. On 401, first
verify that site and region were preserved or mapped as above, then evaluate authentication;
do not immediately conclude that login is broken.

### Keep target routing separate from network transport

`--site` and `--region` select the target. A proxy only changes how the same request reaches
that target. On a network-class failure such as DNS failure, timeout, or `fetch failed`, keep
the target flags and all Triton arguments unchanged and follow the runtime-specific network
guidance for a read-only retry. Put any proxy flag before `triton`:

```bash
bytedcli --socks5-proxy <proxy-url> --json --site i18n-tt \
  triton approval get --region us-eastred --id 1001
```

Do not copy a development-machine proxy value into this generic skill, and do not change
site/region merely because a proxy is needed.

## 权限申请（apply → answer → create）

`apply --dry-run` 仅预览申请 payload。不带 `--dry-run` 时，无待答问卷会直接创建申请；
若返回 `status: draft`，则按问卷逐题作答后再 `apply create`。

`--requirement-type` 支持 `data-analysis`（挖掘分析）、`index-calculation`（指标计算）和
`data-production`（数据生产/看板建设）。显式指定的类型不会被 AI 生成结果覆盖。
数据生产理由按“项目背景、建设内容、使用方式”组织；AI 失败或缺少有效字段时，使用
`--reason` 原文补齐。需要 365 天时显式传 `--ttl 365`；平台限制由资源策略决定，CLI
会原样传递期限，拒绝时不会自动缩短期限或更换用途类型。

```bash
# 1) 发起申请；无待答问卷直接建单，有问卷则返回草稿
bytedcli --json triton apply \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --permission read --ttl 365

# 数据生产/看板建设：预览个人读权限 365 天；核对后去掉 --dry-run 发起申请
bytedcli --json --site i18n-tt triton apply \
  --region sg --db-name example_db --table-name example_table \
  --auth-type person --auth-object demo-user --permission read --ttl 365 \
  --requirement-type data-production --lang zh_CN \
  --reason '项目背景：示例项目；建设内容：示例数据链路与看板；使用方式：持续开发、验收与维护。' \
  --dry-run

# 列级权限：重复 --column；分区/行级权限：重复 --row-filter column=value
# 注意：传 --column 时默认会自动查询元数据并补齐表的分区字段（如 date, p_date 等），避免后续查询报 403；若不需要补齐可加 --no-auto-partition
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --auth-object demo-user
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --column sample_col --no-auto-partition --auth-object demo-user
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --row-filter app=sample-app --auth-object demo-user

# 同一字段允许多个精确值；每个值重复一次 --row-filter
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --row-filter app=sample-app --row-filter app=sample-app-lite --auth-object demo-user

# PSM 接收方：--auth-type psm（ttl 默认 0）
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --auth-type psm --auth-object demo.psm --permission write --ttl 0

# 跨库转储 / 写入权限（ETL 跨库写入、数据回流清洗场景）
# --can-dump 开启转储权限；--dump-database 指定允许转储的目标数据库（可重复或逗号分隔）
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --can-dump --dump-database target_db --auth-object demo-user
bytedcli --json triton apply --region sg --db-name example_db --table-name example_table \
  --can-dump --dump-database db1,db2 --auth-object demo-user --dry-run

# CN：国内机房默认走 coral_api / cluster=default
bytedcli --json triton apply --region cn \
  --db-name example_db --table-name example_table \
  --auth-object demo-user --permission read --ttl 365

# MYCIS / pinnacle：发起 Hive 表读权限审批工单，PSM 接收方 ttl 通常为 0
bytedcli --json triton apply --region mycis \
  --db-name example_db --table-name example_table \
  --auth-type psm --auth-object demo.project.psm \
  --permission read --ttl 0 --lang zh_CN \
  --reason "Need read access for approved data analysis."

# PIPO US：保留页面 notice 确认（提交 ignore_notice=false）
bytedcli --json triton apply --region uspipo \
  --db-name example_db --table-name example_table \
  --auth-type psm --auth-object demo.psm \
  --permission read --ttl 0 --lang zh_CN --no-ignore-notice

# 2) 若检测到 304 合规问卷，逐题作答（question id / option 来自 apply 输出）
bytedcli --json triton apply answer \
  --draft-file /tmp/triton-permission-draft.json \
  --question-id q1 --answer "是 Yes"

# 3) 逐题答完后，用已作答的草稿创建申请工单
bytedcli --json triton apply create \
  --draft-file /tmp/triton-permission-answered-draft.json
```

### 304 合规问卷说明

- "304 文档" 是接口**内联返回**的结构化问答题（`resource_questions_answers{id,type,topic,options}`），
  **不是**要上传的合规文件。
- `triton apply` 默认发送 `ignore_notice=true`；只有产品抓包或页面流程明确要求
  `ignore_notice=false` 时，才加 `--no-ignore-notice`。
- apply 输出会列出每道题的 `id` / `type` / `topic` / `options`；用这些 id 去 `apply answer`。
- 给自己申请个人权限时，apply 会先查我的权限：已有无限制的库级或表级授权覆盖本次申请（写覆盖读）时，JSON 的 `existingPermissions.coveredBy` 列出这些授权，文本输出提示「已有权限覆盖本次申请」。只提示、不拦截；先用 `triton obtained list --query <表名>` 查有效期，不要为续期重新申请。`existingPermissions.checked: false` 表示无法判断（PSM、他人或只有用户组/部门授权），需要时用 `bytedcli coral permission list` 查看。
- 多选题：重复 `--answer`。question id 与 option 必须来自 apply/draft 输出，**禁止臆造**。
- 真实工作流里，作答前先问用户；不要擅自替用户回答合规问题。
- `--row-filter` 表示精确的行级/分区授权范围，不是 SQL 条件。格式必须是
  `column=value`；同一字段的多个值重复传参。不要用 `--column app` 代替
  `--row-filter app=sample-app`，前者只申请读取 `app` 列。

## Hive 库/表管理员直接授权（grant）

库或表 Owner/管理员可直接给用户或 PSM 授予权限。`--resource-type` 默认 `table`；
库级授权必须显式传 `--resource-type database`，只提供库名并省略 `--table-name`。
每次 `grant` 只接收一个获权方；`--auth-object` 不接受逗号分隔列表。多个获权方应
分别预览和提交，以便逐个区分新增授权与已有权限。

```bash
# 库级读权限：预览完整 endpoint/payload，确认资源是库名本身
bytedcli --json triton grant \
  --region sg --resource-type database --db-name example_db \
  --auth-object demo-user --auth-type person --permission read --ttl 365 --dry-run

# 已确认同一目标后的正式库级授权
bytedcli --json triton grant \
  --region sg --resource-type database --db-name example_db \
  --auth-object demo-user --auth-type person --permission read --ttl 365 --yes

# 预览授权计划（--dry-run）
bytedcli --json triton grant \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --dry-run

# 确认直接授权给个人用户（默认读权限 read，TTL 365天）
bytedcli --json triton grant \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --yes

# 授权给 PSM（PSM 授权 TTL 默认 0，即永不过期；支持写权限 write）
bytedcli --json triton grant \
  --region sg --db-name example_db --table-name example_table \
  --auth-type psm --auth-object demo.psm --permission write --ttl 0 --yes

# 指定自定义申请/授权理由
bytedcli --json triton grant \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user --reason "用于数据分析业务需求" --yes
```

- **确认门**：默认 dry-run 保护，只有传 `--yes` 时才会实际调用接口；JSON 模式无 `--yes`
  直接抛 `TRITON_CONFIRM_REQUIRED`。
- **TTL 默认值**：`--auth-type psm` 时默认 0（永不过期）；`person` 时默认 365 天。
- **资源范围**：表级必须带 `--table-name`；库级禁止带表名。`__NULL__` 不是库级占位符，CLI 会拒绝该值。库级请求为 `resource_type=0, name=example_db`，表级为 `1, name=example_db/example_table`。
- **权限使用范围**：库级授权关闭转储和权限再分发；预览 JSON 的 `payload.objects[*].permission_usage` 明确列出这两个值。
- **结果语义**：`action=granted, success=true` 表示本次提交成功；`action=existing, success=false, skipped=[...]` 表示后端忽略了已存在的权限，本次没有新增授权。授权后用同一 region、库名和接收方运行 `managed list` 回查。
- `--dry-run` 与 `--yes` 同时出现时只预览。资源策略、权限不足或合规错误由后端明确拒绝时，报告错误，不尝试 `force` 或修改资源编码。
- 库级直接授权使用 `grant`；`triton apply` 用于表/列/行范围的申请工单，不能用省略表名来申请整个库。整库的申请工单用 `bytedcli coral permission apply --resource-type database`（默认只预览，`--yes` 提交）。
- **TikTok 用户个人信息资源**：若后端提示主动授权最多有效 3 天，超过 3 天的 `grant` 会被拒绝；短期需求可在预览后用同一目标和 `--ttl 3` 授权。更长期访问必须由获权方在 Triton 页面提交 DataSecurity-304 申请审批，不能用 `force`、续期或重复直接授权替代审批。

## 我的权限（obtained list）

列出当前登录用户已获得的权限，适合作为自动化脚本的只读输入基线；它是**当前登录人的视角**，
不是表管理员反查某张表。命令会自动翻页拉全量，再按可选过滤条件筛选。

```bash
# 列出当前用户在指定 region / cluster 下已获得的权限
bytedcli --json triton obtained list --region sg

# 只看平台已建议续期的权限
bytedcli --json triton obtained list --region sg --renew-state suggested

# 只看 Hive 表权限，并按关键字过滤资源名 / 授权对象
bytedcli --json triton obtained list \
  --region sg --data-source hive --resource-type table --query example_table
```

- `obtained list` 走 `/api/v1/privileges/obtained`，返回的是**我已获得的权限**。
- 只想确认自己对某个库或表有没有权限（含覆盖它的库级授权、用户组和部门授权）时，用 `bytedcli coral permission list --region <region> --db-name <db> [--table-name <table>]`；全量清单、到期与续期用 `obtained list`。
- `managed list` 走 `/api/v1/privileges/managed`，返回的是**某个库或表当前授权给了谁**；它是
  管理员 / Owner 视角，不能替代 `obtained list`。
- `renew-state suggested` = 服务端明确建议续期；`renew-state renewable` = 当前允许续期；
  两者不要混为“7 天内到期”。

## 库/表已授权清单反查（managed list）

Owner/管理员反查 Hive 库或表当前已生效的授权列表。资源选项与 `grant` 相同，默认表级。

```bash
# 回查指定个人的库级读权限；检查授权对象、权限和到期时间
bytedcli --json triton managed list \
  --region sg --resource-type database --db-name example_db \
  --auth-object demo-user --auth-type person --permission read

# 查询表的已授权列表
bytedcli --json triton managed list \
  --region sg --db-name example_db --table-name example_table

# 按授权对象或类型过滤
bytedcli --json triton managed list \
  --region sg --db-name example_db --table-name example_table \
  --auth-object demo-user

# 分页查询
bytedcli --json triton managed list \
  --region sg --db-name example_db --table-name example_table \
  --page 1 --page-size 20
```

## 审批中心（approval center，只读）

```bash
# 单一 verb-last 的 list 命令，--type 选队列：submitted(我提交,默认) | todo(待我审批) | reviewed(我审批过)
# 我提交的权限申请（默认 --type submitted）；--days 仅 submitted 生效，默认 180
bytedcli --json triton approval list --region sg --page-size 5
bytedcli --json triton approval list --type submitted --region sg --days 30 --query example_table

# 待我审批：等我审批的工单
bytedcli --json triton approval list --type todo --region sg --page-size 5

# 审批记录：我历史的审批决策
bytedcli --json triton approval list --type reviewed --region sg --page-size 5

# 申请详情：按 group id 看单条申请
bytedcli --json triton approval get --region sg --id 1001

# i18ngcp：沿用 list/apply/create 的 us-eastred region；不要改成 gcp
bytedcli --json --site i18n-tt triton approval get --region us-eastred --id 1001
```

## 通过 / 拒绝（approve / reject）

```bash
# 通过：approve-as-requested，原样回写 ttl/permission/permission_usage（已 live 抓包验证）
bytedcli triton approval approve --region sg --id 100001 --yes

# 拒绝：强制 --reason（作为审批 comment）
bytedcli triton approval reject --region sg --id 100001 --reason "duplicate request" --yes
```

端点（已 live 抓包，见 `src/api/triton/AGENTS.md`）：先 `GET applications/merged/detail/{id}`
取 `application_dto.resources[].aid`，再 `POST /api/v1/applications/update/tasks`（per-resource
决策数组）。1-resource batch 通常即返回 `SUCCESS`，否则轮询 `GET /api/v1/tasks/{taskId}?cluster=`。

- **确认门**：不带 `--yes` 不会真改。JSON 模式无 `--yes` 直接报
  `TRITON_CONFIRM_REQUIRED`（不交互）；text 模式打印 summary 后让你加 `--yes` 重跑。
- 只操作 `--id` 单工单，绝不批量其他工单。
- ⚠️ **reject 的 `status:"REFUSED"` + `comment` 字段是未验证假设**（抓包时不会拒真实申请人，
  approve 才实测过）：**首次真实 reject 前，务必先在 DataLeap web 端人工复核该工单是否真被拒绝；
  若 CLI 返回与预期不符，按真实抓包修正后再用。** 不要把 reject 当成已验证行为陈述。

## 我的权限续期（renew）

一键续期当前用户在 Triton 上即将到期的权限。命令先列出"我的权限"，默认只续期服务端标记
`suggest_to_renew=true` 的权限（到期前 30 天内才会标记）；没有需要续期的权限时不调用
续期 API，直接返回"无需操作"。

```bash
# 预览哪些权限会被续期（不实际执行）
bytedcli --json triton renew --dry-run

# 确认续期（需要 --yes）
bytedcli --json triton renew --yes

# 指定 region / cluster（默认 cn / default）
bytedcli --json triton renew --region cn --cluster cn6 --yes

# 自定义续期时长（天，默认 365，不超过上次审批通过时长）
bytedcli --json triton renew --ttl 90 --yes

# 把服务端标记 can_renew（当前允许续期）但尚未建议续期的权限也一并处理
bytedcli --json triton renew --include-renewable --yes
```

- **默认只续期 `suggest_to_renew=true` 的权限**：这是平台在临期时主动给出的建议，无人值守
  任务只处理这一类。CLI 会先过滤，不会对全部权限发起续期。
- **`--include-renewable` 放宽到 `can_renew`**：服务端另有 `can_renew` 表示当前允许续期
  （Triton UI 据此点亮每行的续期按钮），它可能在远未到期时就为真，因此不纳入默认范围 ——
  否则会比平台预期早得多地续期。当默认范围为空但存在这类权限时，命令会说明有几条并提示
  该参数，避免出现"页面按钮可点、CLI 说没有需要续期的"这种困惑。
- **必填申请参数自动复用**：续期接口要求需求类型和非空的详细原因（UI 表单标红星的两项），
  缺失会被服务端逐条拒绝且任务仍报 SUCCESS。CLI 复用该资源上次提交的内容
  （`last_apply_desc_map`），无记录时兜底填 `其他 / Others` 加一段通用原因；空对象、空串、
  `null` 都按"无记录"处理。
- **TTL 按资源逐条收敛**：服务端限制续期时长不超过上次审批通过的时长，且该上限按资源不同。
  `--ttl` 只作上限，每个对象取 `min(请求值, 自己的 last_ttl)`。
- **跨 cluster 自动分组**：如果待续期权限分布在多个 cluster（如 default 和 cn6），CLI
  会按 cluster 分组发送续期请求，结果按 cluster 返回明细；同一 cluster 内每 50 条分批提交。
- **单批失败不影响其余批次**：批次是彼此独立的服务端任务，某批失败时其余批次继续提交，
  失败批次会在结果中列出它提交过的资源。
- **续期 0 条视为失败**：任务返回 SUCCESS 但 `successCount=0` 时报错退出，避免把静默失效
  报成续期成功。
- **确认门**：与 approve/reject 一致，`--dry-run` 预览、`--yes` 才提交；JSON 模式无
  `--yes` 报 `TRITON_CONFIRM_REQUIRED`。
- L4 数据不允许自助续期，到期后需重新走审批。
- 返回结果包含 `action`（`none` / `dry-run` / `renewed`）、`renewed`（成功数）、
  `batches`（每个 cluster 的任务明细）、`privileges`（权限明细），以及 `failures`
  （未成功续期的资源，按批次给出 `cluster` / `resources` / `exact`；`exact=false` 表示
  服务端只回了计数、无法精确定位到具体某条，只能确定失败发生在该批次内）。

## 冗余权限保留（keep）

Triton 会把 90 天没用过的个人权限当成「冗余权限」，在 80 天时发飞书通知，10 天后自动回收。
页面上每条提供「保留」按钮。现有 `renew` 只管快到期续期，无法处理此类回收。
使用 `bytedcli triton keep` 可一键保留冗余权限，避免权限被自动回收。

```bash
# 预览哪些冗余权限会被保留（不实际执行）
bytedcli --json triton keep --dry-run

# 确认保留全部可保留权限（需要 --yes）
bytedcli --json triton keep --yes

# 指定 region / cluster（默认按站点映射）
bytedcli --json triton keep --region va --yes

# 只保留指定的几条权限（支持多次传参或逗号分隔）
bytedcli --json triton keep --name example_db/example_table --yes
bytedcli --json triton keep --name table_1,table_2 --yes
```

- **默认保留全部 `can_keep=true` 的权限**：CLI 先查询「我的权限」，筛选出处于回收名单中的
  条目；无待保留条目时直接返回"无需操作"（退出码 0）。
- **`--name` 精确过滤**：传入一个或多个资源名，仅保留指定的条目。
- **回读校验闭环**：因为底层接口即使空 body 或空 objects 也会返回 ok，为防止静默失败，
  CLI 发送保留请求后会自动重新拉取 `obtained` 列表，逐条校验目标权限的 `can_keep` 是否
  变为 `false`；目标中只要仍有条目未成功保留（`can_keep=true`），命令即
  报错失败（退出码非 0）。
- **确认门**：与 renew 一致，`--dry-run` 预览、`--yes` 才提交；JSON 模式无 `--yes` 抛
  `TRITON_CONFIRM_REQUIRED`。

## Rules that matter

- 草稿、debug payload 写 `/tmp`，不要把临时文件写进仓库。
- apply/answer/create 的 question id、option id 必须来自 Coral draft/API 输出，禁止编造 schema 或答案 id。
- 真实工作流里，作答合规问卷前先问用户；只有在明确授权的测试里才随机作答。
- `--auth-type psm` 时 `--ttl` 默认 0；`person` 时默认 365。
- `approval get` 的 `--id` 是申请的 group id（与列表返回的 group id 同源）。
- `approval list --type submitted` 对应 DataLeap「申请记录」，文本输出带状态中文标签（如 `all_closed 全部通过`、`under_approval 审批中`、`partial_closed 部分通过`、`cancelled 已撤销`）、cluster、权限与资源名。申请命令中断或报 `CORAL_PERMISSION_SUBMIT_UNKNOWN` 时，先用 `--days 1` 查是否已建单，再决定是否重新申请。
- 查询、通过或拒绝已有工单时，沿用 apply/create/list 的 CLI region；
  `groupName/cluster=i18ngcp` 对应 `--region us-eastred`，不能因返回资源含
  `cluster=gcp` 改成 `--region gcp`。
- 写操作（approve/reject/renew/keep）必须 `--yes` 确认；⚠️ reject 的 REFUSED 字段为未验证假设，
  首次真实 reject 前务必先在 DataLeap web 端人工复核该工单是否真被拒绝；
  若 CLI 返回与预期不符，按真实抓包修正后再用。不要把 reject 当成已验证行为陈述。
- renew 默认只续期 `suggest_to_renew=true` 的权限，`--include-renewable` 才放宽到
  `can_renew`；没有待续期权限时不调用 API，返回"无需操作"。
- keep 默认保留全部 `can_keep=true` 的权限；提交后自动回读核验目标权限状态，未完全保留时退出码非 0。
