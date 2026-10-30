---
name: bytedance-decc
description: "Operate DECC via bytedcli: register US Application Gateway (AG) APIs from BAM with API-level annotations and approval readback; inspect Gateway endpoint tagging; read/update PSM common parameters and submit common-error approval; inspect/cancel DECC or OG tickets; create HDFS channels and register tables; fill type/description/reason/IDL, run AI Generate, import Hive IDL, and edit fields/category tags via data versions; configure cross-region transfers; annotate DES-RPC IDL; edit DES-MQ fields/labels/transfers; apply for channel/data or Gateway permissions. Use for DECC, AG API registration/BAM import, OG/API or USTTP/EUTTP tagging, PSM common parameters/errors, pending/rejected tickets or withdrawal, DES-HDFS schema changes, simplified data create, AI Generate, Hive IDL, des.tag/ROW Data Catalog dt_tag, DES-RPC annotations, DES-MQ/MQ Event fields or exemptions, data registration, transfer configs, and permissions."
---

# bytedcli DECC (Data Exchange & Cross-region Compute)

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- AG API 注册、BAM 导入、`/application_gateway/` PSM/API 页面：读取 [Application Gateway](references/application-gateway.md)，使用 `decc ag`；与 OG 的 `decc gateway` 分开。

- 创建 DECC HDFS channel（数据交换渠道）
- 在 channel 下注册 DECC HDFS data（表）
- 一次写入 type、description、reason 和 IDL：`hdfs-data simplified create`（默认 dry-run，`--yes` 才 POST）。这不是 `hdfs-data create`，也不是页面 AI Generate
- 页面 AI Generate：`hdfs-data ai check`，再 `ai submit --yes`，用 `ai status` 看任务，`ai adopt --yes` 记录采纳
- 创建跨区域 HDFS data transfer 配置（`data-transfer-config create`）
- 创建前先 `--dry-run` 校验 schema 解析与 HSQL 列同步是否可用
- 申请 Gateway 服务的 edit / manage / monitor 权限（`gateway permission apply`）；HDFS channel/data 的 Owner 权限用 `decc apply`
- 查询 DECC/OG ticket 历史工单列表和详情
- 查询 DECC ticket 评论详情
- DES-RPC Method 的 IDL 标注更新预检：从 BAM 最新版本生成 DECC Data Version load/parse 请求
- DES-RPC Data Version 的 load-idl、parse-idl、update、submit 操作
- DECC V3 的 Caller/Callee 注册、编辑和查询，以及 Caller → Callee 上下游拓扑的创建、编辑、启停
- DES-MQ（MQ Event，gateway 5）消息：查数据版本和字段标签，建草稿，按字段路径增改字段及其 category / sync 标签和样例值，提交 Geo Review 并查看审批进度和审批单链接
- DES-MQ 传输配置：新建引用已审批数据版本的传输配置版本，再 submit、apply；只读查看物理通道的豁免开关和字段过滤模式
- 跨区域数据交换（Cross-region Data Exchange）场景
- 查询待打标 API 服务与已有打标记录
- 按 `compliance_platform/detail/<entity_id>` URL 和目标 US/EU control plane 核验 approved/draft API 的叶子字段打标覆盖率
- 创建 API OG 打标草稿
- 对 API 进行 OG 打标（更新打标草稿）

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- DECC 控制面固定在 ROW，所有命令使用 `--site i18n-tt`（TikTok 国际站），需单独登录。USTTP/EUTTP 是业务 region，不是全局鉴权 site；不要改成 `--site us-ttp`、`--site us-ttp-usts` 或 `--site eu-ttp`：

```bash
# 检查认证状态
bytedcli --site i18n-tt auth status

# 登录（如未认证）
bytedcli --site i18n-tt auth login
```

DECC client 固定获取个人态 `i18n-tt` JWT，并从同一个 token 派生 operator，避免 `not support region: tx` 或多步骤操作中的身份错配。出现认证错误时使用：

```bash
bytedcli --json --site i18n-tt auth login --begin
```

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 查询 Gateway service 列表
bytedcli --site i18n-tt decc gateway service list

# 申请 Gateway 服务权限（Kani）：默认只预览，--yes 才提交；--role 默认 edit
bytedcli --site i18n-tt decc gateway permission apply \
  --entity-id demo-service-entity-id --reason 'Edit endpoint tags'

# 查自己的 Gateway 权限申请进度
# --namespace 取预览输出里的 request.policies[0].resource.ns
bytedcli kani openapi workflow list --region va --namespace demo-kani-namespace

# 按 service name、region、owner 或 source type 过滤
bytedcli --site i18n-tt decc gateway service list \
  --name demo.api_service \
  --region EU,US \
  --owners demo.user,sample.user \
  --source-type Web

# 查询指定 Gateway service entity 下的 endpoint，可按 HTTP path 过滤
bytedcli --site i18n-tt decc gateway endpoint list \
  --entity-id demo-service-entity-id \
  --stage draft \
  --path /demo/api \
  --page 1 \
  --page-size 15

# 带 {{n}} 通配段的 path 必须用单引号包裹；CLI 按静态前缀查询并本地精确过滤
bytedcli --site i18n-tt --json decc gateway endpoint list \
  --entity-id demo-service-entity-id \
  --stage approved \
  --path '/demo/api/{{4}}/execute' \
  --page 1 \
  --page-size 100

# 查询指定 Gateway endpoint
bytedcli --site i18n-tt decc gateway endpoint get \
  --id demo-endpoint-id \
  --entity-id demo-service-entity-id \
  --stage draft --version 0

# 已有 service 页面 URL 时，逐项传入从 IDL/runtime 契约确认的叶子字段
bytedcli --site i18n-tt decc gateway tagging get \
  --url https://decc.tiktok-row.net/compliance_platform/detail/demo-service-entity-id \
  --path /demo/api \
  --method POST \
  --stage approved \
  --region US \
  --expect-field query.page \
  --expect-field req.body.name

# 未传 --expect-field 时只核验 DECC 已登记字段，contract_verdict 固定为 unverified
bytedcli --site i18n-tt --json decc gateway tagging get \
  --entity-id demo-service-entity-id \
  --path /demo/first \
  --path /demo/second \
  --method POST \
  --region EU

# 提交前在 repo 外创建私有临时目录，保存不可覆盖的 review plan
decc_plan_dir="$(mktemp -d)"
bytedcli --site i18n-tt decc gateway endpoint submit \
  --draft-id demo-endpoint-id \
  --caller-vpc demo-office-net \
  --callee-vpc US_demo-vpc \
  --dry-run \
  --plan-file "$decc_plan_dir/decc-submit-plan.json"

# 复核 plan 内完整 diff 后，真实提交直接消费同一 plan
bytedcli --site i18n-tt decc gateway endpoint submit \
  --draft-id demo-endpoint-id \
  --caller-vpc demo-office-net \
  --callee-vpc US_demo-vpc \
  --plan-file "$decc_plan_dir/decc-submit-plan.json" \
  --yes

# 记录 ticket evidence 后清理，避免后续 git add 误提交完整 schema diff
rm "$decc_plan_dir/decc-submit-plan.json"
rmdir "$decc_plan_dir"

# 默认只输出 compact diff；排障时才显式展示完整 submit request
bytedcli --site i18n-tt decc gateway endpoint submit \
  --draft-id demo-endpoint-id \
  --show-request

# 预览 Gateway endpoint draft；默认不会写入
bytedcli --site i18n-tt decc gateway endpoint create \
  --entity-id demo-service-entity-id \
  --path /demo/api \
  --method GET \
  --description "demo endpoint"

# 更新 Gateway endpoint draft 的描述和 schema；先看完整状态 diff
bytedcli --site i18n-tt decc gateway endpoint update \
  --draft-id demo-endpoint-id \
  --description "updated demo endpoint" \
  --req-headers-file req_headers.json \
  --req-body-file req_body.json

# 单字段打标优先使用 field update；semantic 参数会写入 compliance_tag
bytedcli --site i18n-tt decc gateway field update \
  --draft-id demo-endpoint-id \
  --path req.body.user.id \
  --tx-catalog-id demo-tx-catalog-id

# tagging missing_fields 中的 JSON bracket path 可直接复用；外层用单引号保护
bytedcli --site i18n-tt decc gateway field update \
  --draft-id demo-endpoint-id \
  --path 'req.body["a.b"]' \
  --tt-catalog-id demo-tt-catalog-id

# response status 名为 body/header 时必须保留 bracket，避免与 legacy status-200 语法混淆
# 例如 tagging 输出的 'resp["body"].body.target' 应原样传入

# 确认 dry-run 后，真实写入必须同时带 --yes 和该次预览输出的 confirmation token
bytedcli --site i18n-tt decc gateway field update \
  --draft-id demo-endpoint-id \
  --path req.body.user.id \
  --tx-catalog-id demo-tx-catalog-id \
  --yes \
  --confirmation-token '<token-from-the-dry-run>'

# 幂等追加 assurance path；默认仅预览
bytedcli --site i18n-tt decc gateway assurance-path create \
  --draft-id demo-endpoint-id \
  --callee-vpc EU_VPC1

# 创建 HDFS channel
bytedcli --site i18n-tt decc hdfs-channel create \
  --name demo-database \
  --description "demo channel" \
  --owners demo.user \
  --vgeo-list CN \
  --scenario 4

# 在 channel 下注册 HDFS data（表）；先 --dry-run 核对 channel / scenario / 重名
bytedcli --site i18n-tt decc hdfs-data create \
  --channel-id demo-channel-id \
  --name demo_table_name \
  --owners demo.user \
  --region EU-TTP2 \
  --scenario 3 \
  --dry-run

bytedcli --site i18n-tt decc hdfs-data create \
  --channel-id demo-channel-id \
  --name demo_table_name \
  --owners demo.user \
  --region EU-TTP2 \
  --scenario 3

# simplified create 一次带上 type / description / reason / IDL。hdfs-data create 只登记表名。
# 默认 dry-run 只打印 body；确认后再加 --yes。--need-all-recommendation 不是页面 AI Generate
bytedcli --site i18n-tt decc hdfs-data simplified create \
  --channel-id demo-channel-id \
  --name demo_table \
  --owners demo.user \
  --type Aggregated \
  --description 'demo table' \
  --reason 'demo sync' \
  --source-vgeo EU \
  --target-vgeo ROW-TT \
  --idl-file demo.sql \
  --idl-type hive \
  --dry-run

# 已有 data 开新版本。同样默认 dry-run，--yes 才 POST
bytedcli --site i18n-tt decc hdfs-data simplified update \
  --data-id demo-data-id \
  --upstream-version 1 \
  --description 'demo table' \
  --dry-run

# 页面 AI Generate 走门户 automation_task。check 只读；submit / adopt 默认 dry-run
bytedcli --site i18n-tt decc hdfs-data ai check --body-file demo-ai.json
bytedcli --site i18n-tt decc hdfs-data ai submit --body-file demo-ai.json --dry-run
bytedcli --site i18n-tt decc hdfs-data ai status --data-id demo-data-id --data-version 1
bytedcli --site i18n-tt decc hdfs-data ai adopt \
  --task-id demo-task-id \
  --records-file demo-records.json \
  --dry-run

# 新注册的表自带空草稿 version 1：先灌 Hive DDL（默认 dry-run，打印 token）
# Hive 注释常是中文，DECC 拒收，所以 --strip-comments；或 --idl-file 传英文注释版 DDL
bytedcli --site i18n-tt decc hdfs-data data-version idl import \
  --data-id demo-data-id \
  --version 1 \
  --strip-comments \
  --tag 2.7.72

# 再填 Basic Info：描述 / 同步原因 / 方向（默认 dry-run，打印 token）
bytedcli --site i18n-tt decc hdfs-data data-version update \
  --data-id demo-data-id \
  --version 1 \
  --description 'This data contains demo records which is needed to demo billing and is taken from demo source.' \
  --sync-reason 'The data requires synchronization with demo region to run demo billing. If not synced, billing stops.' \
  --direction ROW-TT:CN

# 打标前先查 category 码表，确认哪些码真的能填
bytedcli --site i18n-tt decc hdfs-data category list --fillable-only
bytedcli --site i18n-tt decc hdfs-data category list --with-descriptions
# CN_CROSS_BORDER / TT_NONTT 表用 ROW Data Catalog（写 des.dt_tag）
bytedcli --site i18n-tt decc hdfs-data category list --scenario CN_CROSS_BORDER --fillable-only

# 给已有 HDFS 表增加字段：建草稿 → 改 IDL+category 标签 → 提交审批
# hdfs-data create 只负责注册表；字段增减必须走 data version
bytedcli --site i18n-tt decc hdfs-data data-version list --data-id demo-data-id

bytedcli --site i18n-tt decc hdfs-data data-version create \
  --data-id demo-data-id \
  --yes

# 默认 dry-run，打印 Hive DDL / json_schema diff 与 confirmation token
bytedcli --site i18n-tt decc hdfs-data data-version column create \
  --data-id demo-data-id \
  --version 13 \
  --column-name demo_column \
  --column-type string \
  --description 'demo column' \
  --tag 6.1

# 改已有字段：只传要改的字段，其余保持不动（重新打标最常用）
bytedcli --site i18n-tt decc hdfs-data data-version column update \
  --data-id demo-data-id \
  --version 13 \
  --column-name demo_column \
  --tag 1.3.1

# 删字段：dry-run 会打印被删声明和它带的 category 标签
bytedcli --site i18n-tt decc hdfs-data data-version column delete \
  --data-id demo-data-id \
  --version 13 \
  --column-name demo_column

bytedcli --site i18n-tt decc hdfs-data data-version submit \
  --data-id demo-data-id \
  --version 13 \
  --reason 'add demo column' \
  --yes

# 审批通过（Suspended）后 Apply 生效，transfer config 才能用新 schema（默认 dry-run）
bytedcli --site i18n-tt decc hdfs-data data-version apply \
  --data-id demo-data-id \
  --version 13 \
  --yes

# 撤回审批中的版本（Draft/Suspended 无效，见下方注意事项）
bytedcli --site i18n-tt decc hdfs-data data-version cancel \
  --data-id demo-data-id \
  --version 13 \
  --yes

# Load：先拉 Coral DDL，再生成 Annotation 树。--yes 才写回，并带上 gateway=6
bytedcli --site i18n-tt decc hdfs-data data-version load-schema \
  --data-id demo-data-id \
  --version 13 \
  --region US-EastRed \
  --channel-name demo_db \
  --data-name demo_table \
  --source-vgeo EU \
  --target-vgeo ROW-TT \
  --dry-run

# DES-RPC 标注更新预检：确认 BAM 最新 IDL，并输出 DECC Data Version 的 load/parse 请求
bytedcli --site i18n-tt decc des-rpc annotation-plan get \
  --psm example.demo.service \
  --bam-version latest \
  --data-id demo-data-id \
  --version 12

# DES-RPC Data Version：create 会自动基于 latest applied version 选择 upstream_version；后续再 load-idl、parse-idl、update、submit
bytedcli --site i18n-tt decc des-rpc data-version create \
  --data-id demo-data-id \
  --applied-region US

bytedcli --site i18n-tt decc des-rpc data-version load-idl \
  --data-id demo-data-id

bytedcli --site i18n-tt decc des-rpc data-version parse-idl \
  --data-id demo-data-id \
  --upstream-version 12 \
  --idl-file ./decc-idl.json

bytedcli --site i18n-tt decc des-rpc data-version update \
  --data-id demo-data-id \
  --version 12 \
  --body-file ./decc-des-rpc-annotation.json

bytedcli --site i18n-tt decc des-rpc data-version update \
  --data-id demo-data-id \
  --version 12 \
  --field-path _request.DemoOptions.SkipDemoField \
  --tag demo-tag \
  --entity demo-entity \
  --sync YES \
  --non-us-user-data-proof-field NO \
  --description "Skip demo field" \
  --reason "Refresh demo annotation"

bytedcli --site i18n-tt decc des-rpc data-version submit \
  --data-id demo-data-id \
  --version 12 \
  --reason "update IDL annotation to latest BAM version" \
  --wait

# 提交后可随时通过 CLI 查看 workflow、各区域状态以及生成的 ticket ID/URL
bytedcli --site i18n-tt decc des-rpc data-version status \
  --data-id demo-data-id \
  --version 12

# DES-RPC：查看 channel 下的方法及单个方法详情
bytedcli --site i18n-tt decc des-rpc data list --channel-id demo-channel-id
bytedcli --site i18n-tt decc des-rpc data get --data-id demo-data-id

# DES-RPC V3：补齐缺失的字段 Description 与 ROW Data Catalog；默认仅预览
bytedcli --site i18n-tt decc des-rpc data-version annotate \
  --data-id demo-data-id --version 12
bytedcli --site i18n-tt decc des-rpc data-version annotate \
  --data-id demo-data-id --version 12 --scenario 9 --yes

# DES-RPC V3：注册 Callee / Caller。scenario 必传；所有写命令默认只预览，加入 --yes 才会提交。
bytedcli --site i18n-tt decc des-rpc channel create \
  --role callee --name example.demo.callee --description "Demo callee service" \
  --owners demo.user --vgeo-list CN,ROW-TT --scenario 4,3
bytedcli --site i18n-tt decc des-rpc channel create \
  --role caller --name example.demo.caller --description "Demo caller service" \
  --owners demo.user --vgeo-list CN,ROW-TT --scenario 4,3 --yes

# 查询或编辑 Caller / Callee 服务。
bytedcli --site i18n-tt decc des-rpc channel list --role callee --owner demo.user
bytedcli --site i18n-tt decc des-rpc channel get --channel-id demo-callee-channel-id
bytedcli --site i18n-tt decc des-rpc channel update \
  --channel-id demo-callee-channel-id --description "Updated callee description" \
  --owners demo.user,sample.user --scenario 4,3 --yes

# DES-RPC V3：创建并维护 Caller → Callee 上下游，支持 CN → ROW-TT 与 ROW-TT → CN。
bytedcli --site i18n-tt decc des-rpc topology create \
  --source-channel demo-caller-channel-id --target-channel demo-callee-channel-id \
  --methods DemoMethod --directions CN:ROW-TT --yes
bytedcli --site i18n-tt decc des-rpc topology create \
  --source-channel demo-row-caller-channel-id --target-channel demo-cn-callee-channel-id \
  --methods DemoMethod --directions ROW-TT:CN --yes
bytedcli --site i18n-tt decc des-rpc topology update \
  --source-channel demo-caller-channel-id --target-channel demo-callee-channel-id \
  --source-site CN --target-site ROW-TT --priority-reason "Demo priority adjustment" --yes
bytedcli --site i18n-tt decc des-rpc topology operate \
  --config-id demo-topology-id --operation start --yes

# DES-RPC：apply 默认仅预览请求；确认后才加入 --yes 提交
bytedcli --site i18n-tt decc des-rpc data-version apply \
  --data-id demo-data-id --version 12 --vgeo ROW-TT
bytedcli --site i18n-tt decc des-rpc data-version apply \
  --data-id demo-data-id --version 12 --vgeo ROW-TT --yes

# DES-RPC：direction 默认仅预览；--all 可按 scenario 一次补齐标准方向
bytedcli --site i18n-tt decc des-rpc data-version set-direction \
  --data-id demo-data-id --version 12 --source-vgeo CN --target-vgeo ROW-TT --yes
bytedcli --site i18n-tt decc des-rpc data-version set-direction \
  --data-id demo-data-id --version 12 --scenario 9 --all --yes

# DES-MQ：查消息的数据版本，--fields 列出字段路径和标签（可带路径前缀）
bytedcli --site i18n-tt decc des-mq data-version list --data-id demo-data-id
bytedcli --site i18n-tt decc des-mq data-version get --data-id demo-data-id --fields Msg.

# DES-MQ 加字段：从最新 Approved 版本建草稿 → field create 预览 diff 和 token → 带 token 写入 → 提交
bytedcli --site i18n-tt decc des-mq data-version create --data-id demo-data-id --yes
bytedcli --site i18n-tt decc des-mq data-version field create \
  --data-id demo-data-id --version 4 \
  --field-path Msg.demo_field --field-type string --description 'demo field' --tag 2.7.72
bytedcli --site i18n-tt decc des-mq data-version field create \
  --data-id demo-data-id --version 4 \
  --field-path Msg.demo_field --field-type string --description 'demo field' --tag 2.7.72 \
  --yes --confirmation-token <token-from-dry-run>
bytedcli --site i18n-tt decc des-mq data-version submit --data-id demo-data-id --version 4 --yes
# 审批进度和审批单链接（decc ticket get 查不到这类审批单）
bytedcli --site i18n-tt decc des-mq data-version status --data-id demo-data-id --version 4

# DES-MQ 让通道用上新数据版本：传输配置版本 create（引用已审批的数据版本）→ submit → apply
bytedcli --site i18n-tt decc des-mq transfer-config list --data-id demo-data-id
bytedcli --site i18n-tt decc des-mq transfer-config version list --config-id demo-config-id
bytedcli --site i18n-tt decc des-mq transfer-config version create \
  --config-id demo-config-id --data-version 4 --yes
bytedcli --site i18n-tt decc des-mq transfer-config version submit \
  --config-id demo-config-id --version 9 --yes
bytedcli --site i18n-tt decc des-mq transfer-config version apply \
  --config-id demo-config-id --version 9
bytedcli --site i18n-tt decc des-mq transfer-config version apply \
  --config-id demo-config-id --version 9 --yes

# DES-MQ 物理通道：只读，看豁免开关和字段过滤模式
bytedcli --site i18n-tt decc des-mq channel get --channel-id demo-channel-id

# 创建前先 dry-run 校验 schema
bytedcli --site i18n-tt decc data-transfer-config create \
  --dry-run \
  --data-id 100001234 \
  --source-region EU-Compliance2 \
  --source-data-name demo_source_table \
  --target-region Singapore-Central

# 创建跨区域 HDFS data transfer 配置
bytedcli --site i18n-tt decc data-transfer-config create \
  --name demo-transfer \
  --owners demo.user \
  --data-id 100001234 \
  --source-region EU-Compliance2 \
  --source-data-name demo_source_table \
  --target-region Singapore-Central \
  --target-channel-name demo_channel \
  --target-data-name demo_target_table \
  --dorado-project-id 12345001 \
  --dorado-project-name demo-project \
  --dorado-folder-id 12345678 \
  --dorado-folder-name demo-folder

# 申请 channel Owner 权限
bytedcli --site i18n-tt decc apply \
  --object-type 1 \
  --object-key demo-channel-id \
  --users demo.user \
  --reason "申请 channel 权限"

# 申请 data Owner 权限
bytedcli --site i18n-tt decc apply \
  --object-type 2 \
  --object-key demo-data-id \
  --users demo.user \
  --reason "申请 data 权限"

# 查询 DECC/OG ticket 历史工单
bytedcli --site i18n-tt decc ticket list \
  --surface unified-v2 \
  --entity-id demo-entity-id \
  --region US \
  --page 1 \
  --page-size 20

# 查询指定 ticket 详情；省略 surface 时自动尝试 unified-v2、unified-v1、portal
bytedcli --site i18n-tt decc ticket get \
  --ticket-id demo-ticket-id \
  --version 3

# 已有 ticket URL 时直接传 URL，不要手拆 id/version
bytedcli --site i18n-tt --json decc ticket get \
  --url '<decc-ticket-detail-url>'

# unified-v2 JSON 会携带完整迭代历史；驳回字段从 review_comments 读取
bytedcli --site i18n-tt --json decc ticket get \
  --url '<decc-ticket-detail-url>'

# 共享评论池仅作兼容查询；字段级驳回优先读取上面的 full_iteration_history
bytedcli --site i18n-tt decc ticket comment list \
  --ticket-id demo-ticket-id

# 驳回单创建新迭代前先预览：只复制显式声明的 description-only 字段修正
bytedcli --site i18n-tt decc ticket iteration create \
  --url '<versioned-decc-ticket-url>' \
  --draft-id demo-draft-id \
  --caller-vpc demo-office-net \
  --callee-vpc EU_demo-vpc \
  --reason "Improve rejected field descriptions" \
  --expect-field resp.body.data.name \
  --dry-run

# 仅在用户明确授权真实创建后，使用同一参数和 snapshot_digest 执行并回读新迭代
bytedcli --site i18n-tt decc ticket iteration create \
  --url '<versioned-decc-ticket-url>' \
  --draft-id demo-draft-id \
  --caller-vpc demo-office-net \
  --callee-vpc EU_demo-vpc \
  --reason "Improve rejected field descriptions" \
  --expect-field resp.body.data.name \
  --expect-snapshot 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef \
  --yes

# 加急查询同时展示工单自身状态和该版本 BPM 状态
bytedcli --site i18n-tt decc ticket priority get \
  --ticket-id demo-ticket-id --version 3

# 加急申请默认预览 resolved payload、已有加急状态和确认 token
bytedcli --site i18n-tt decc ticket priority request \
  --ticket-id demo-ticket-id --version 3 \
  --level urgent --reason "Demo release deadline" --dry-run

# 用户明确授权后，用同一份预览的 token 创建发给申请人 +1 的 BPM 审批
bytedcli --site i18n-tt decc ticket priority request \
  --ticket-id demo-ticket-id --version 3 \
  --level urgent --reason "Demo release deadline" \
  --confirmation-token '<reviewed-token>' --yes

# 撤回前先 dry-run；命令会校验 exact version、pending 状态和 cancel action
bytedcli --site i18n-tt decc ticket cancel \
  --url '<decc-ticket-detail-url>' \
  --reason "Withdraw incorrect tagging" \
  --dry-run

# 仅在用户明确授权真实撤回后加 --yes；真实执行后会回读状态，重复撤回 cancelled 工单是幂等的
bytedcli --site i18n-tt decc ticket cancel \
  --ticket-id demo-ticket-id \
  --version 3 \
  --reason "Withdraw incorrect tagging" \
  --yes

# JSON 输出
bytedcli --site i18n-tt --json decc ticket list \
  --surface unified-v2 \
  --status pending \
  --region EU
```

## Agent Guidance：Ticket priority 与撤回

- `ticket priority get --url <url>` 或 `--ticket-id <id> --version <version>` 联合读取 exact version 的工单状态与 BPM 加急状态；US/portal 的 id-only URL 必须额外传 `--version <version>`。`priority.status: Approved` 不代表工单通过或仍有效：取消后的旧版本仍可能保留 Approved 加急记录，且它不转移到新版本。文本与 JSON 均输出工单自身 `ticket_status`。
- `ticket priority request` 只对 pending 工单申请，`--level urgent|expedited`、`--reason` 必填。默认 dry-run 输出完整 `payload`（包含 ticket id/version、申请人、级别、原因）、已有 priority、warnings 和 `confirmation_token`。payload 的 `data_version` 必须由详情明确提供，缺失时停止，不能用工单 version 猜测。真实写入会创建发给申请人 +1 的 BPM 审批，必须使用 `--yes --confirmation-token <token>`；payload、已有加急状态、操作者或 `--force-duplicate` 变化后需要重新预览。
- 若该版本加急为 Approved、Requested 或处理中，默认 `would_request: false`，live 报 `DECC_TICKET_PRIORITY_DUPLICATE`；只有明确需要重复申请时才带 `--force-duplicate` 重新预览。Rejected/Closed 不触发重复保护。不能用查询失败冒充「无加急」。
- `ticket cancel` 在 dry-run 和 live 都先查询加急。存在 Approved、Requested 或处理中加急时输出 warning；live 还需 `--discard-priority`，明确接受丢弃该版本的加急权益。查询失败时停止，`--discard-priority` 不绕过查询失败。取消仍按 exact version、pending/cancel action 校验并写后回读；已取消版本不重复写。
- **`priority request` 和 `cancel --discard-priority`：If the user's original request did not explicitly authorize this write, show the dry-run result and stop for affirmative user confirmation. An agent's own validation is not user authorization.** 用户未明确授权这次写入（包括丢弃加急权益）时，展示预览后停止等待肯定确认。
- 加急接口使用独立 `msg/data` 信封，认证复用 `x-jwt-token`。成功信封中显式 `data: null` 或仅含 `status: "Created"` 的 data 表示无申请，不阻断撤回；缺失或无法解析的 data 视为查询失败。`DECC_TICKET_PRIORITY_OUTCOME_UNKNOWN` 表示 BPM 可能已创建，先查询同一版本的 priority 和 BPM，不盲目重试或强制重复。

## Agent Guidance：Gateway 打标核验

涉及同名服务、多 entity 或按区域修改/提交时，先读 [Gateway 目标选择与诊断](references/gateway-targets.md)。

1. 核验单位是 `service entity + HTTP method + exact path + target control plane`。USTTP 与 EUTTP 必须分别查询，不能用另一地区、同结构接口或浏览器页面替代。
2. 用户给出 `compliance_platform/detail/<entity_id>` URL 并要求确认打标时，先从权威 IDL、HTTP binding 或真实 runtime request 确认该 API 应有的全部叶子字段，再对单个 exact path 运行 `gateway tagging get ... --expect-field <canonical-path>`，每个字段重复一次。命令分别输出 `registered_tag_verdict`、`contract_verdict` 和总体 `verdict`；只有总体为 `complete` 才能报告完整。
3. 不传 `--expect-field` 时，命令只统计 DECC schema 已登记叶子字段，`contract_verdict` 与总体 `verdict` 为 `unverified`。`0/0 no registered fields` 绝不表示 API 没有字段或已完成打标；禁止只凭 registered tag coverage、finished ticket 或页面状态得出契约完整结论。带 `--expect-field` 时一次只能查询一个 `--path`，避免把不同 API 的字段集合混用。单个 endpoint 的 `complete` 同时看已登记字段的打标覆盖和 `schema_contract`：只要有 `--expect-field` 声明的字段没在 DECC schema 里登记，该 endpoint 就是 `complete: false`，并出现在顶层 `expected_fields_missing` 里；这类「只是契约缺字段」的 endpoint 也计入 `incomplete_endpoint_count`，要区分「缺打标」和「缺字段」得看各 endpoint 的 `schema_contract`。schema 为空的 endpoint 是例外：即使有 `--expect-field` 字段没登记，它仍留在 `unverified_endpoint_count` 里，所以「哪些 endpoint 缺预期字段」要读 `expected_fields_missing`。不传 `--expect-field` 时 `schema_contract.complete` 为 `null`（unverified），既不判定完整也不判定不完整。
4. `--region US` 按 `tx_catalog_id`（或 `not_user_data=true`）核验，`--region EU` 按 `tt_catalog_id`（或 `not_user_data=true`）核验。两者都是业务区域；鉴权仍固定使用 `--site i18n-tt`。
5. approved 查询会固定目标区域 list 行的 exact version 和 assurance path；`DECC_GATEWAY_REGION_MISMATCH` 或 `DECC_GATEWAY_REGION_AMBIGUOUS` 都表示 CLI 无法证明结果属于唯一的目标 control plane。保留错误证据并停止，不要猜 assurance path、切换 region 或改用 Chrome 推断。
6. 带 `{{n}}` 通配段的 path（如 `/demo/api/inspection-task/{{4}}/execute`）不能直接作为服务端过滤值：DECC 把 `--path` 当前缀匹配，完整通配路径永远返回 0 行，URL 编码同样无效。通配 path 必须用单引号包裹，避免 shell 解释花括号。CLI 会自动改用「首个花括号之前的最长静态前缀」查询并在本地做精确匹配，`gateway tagging get --path '/demo/api/{{4}}/execute'` 因此可以正常核验（tagging 会自动翻完所有页）。`gateway endpoint list --path` 只在**带花括号**时改写：按静态前缀查询、对当前页做精确过滤，JSON 输出 `path_filter` 说明改写过程，本页无命中直接报 `DECC_GATEWAY_ENDPOINT_NOT_FOUND` 而不是返回空列表；不带花括号的 `--path` 原样下发，无命中仍是空列表成功。报错**不代表 endpoint 不存在**：它只说明本页没有命中。按 hint 给出的静态前缀命令递增 `--page` 直到 `scanned_all: true`，找到通配行后用 `gateway endpoint get --id <endpoint_id> --stage <stage>` 读取；页数不确定时直接用 `gateway tagging get`。通配 endpoint 常常只存在于 approved 或只存在于 draft，两个 stage 都要查。通配查询下 `page_info` 描述的是静态前缀结果集，真正的命中数只看 `path_filter.matched_count`，扫描行数看 `path_filter.scanned_count`。
7. `gateway endpoint submit` 默认是只读 preflight，也可显式传 `--dry-run`：按 `callee_vpc` 解析 US/EU，逐条 exact caller/callee pair 读取最新 approved baseline，并输出 `baseline_ticket_id`、`baseline_version`、`changed_fields`、`unexpected_fields` 和 `snapshot_digest`。POSIX 环境优先在 dry-run 使用 `--plan-file <path>` 保存完整 review plan；必须放在 repo 外的私有临时目录，live 完成或失败处理结束后删除。文件以 `0600` 独占创建，不覆盖既有文件，并绑定当前 CLI 版本、draft、selector、全部 changed path、完整 diff 与 snapshot。复核后 live 使用同一 `--plan-file --yes`，禁止混用手工 guards；Windows 使用手工 `--expect-field` + `--expect-snapshot` 流程。每个 POST 前都会重新读取 version-zero draft 与 exact pair 的 latest approved baseline，任一变化都停止。Live JSON 使用 `dry_run: false` 与 `submissions[]`，每项必须证明 exact assurance path 和完整 versioned ticket ID/version/URL；缺失 ticket evidence 视为 unknown outcome。
8. 多 assurance path 的 baseline 必须逐 pair 独立证明；同一区域不同 pair 的 baseline schema 不一致时输出 `regional_baseline_drift=true` 和 warning。不要把某个 pair 的 approved schema 当成另一个 pair 的基线。
9. 需要完整的 fail-closed 条件、预算限制与恢复步骤时，只读 `references/decc.md` 的 “Gateway tagging workflow and failure recovery”。

## Agent Guidance：Gateway 草稿修改

1. `gateway endpoint create/update`、`gateway field update`、`gateway assurance-path create` 全部默认 dry-run；只有用户明确授权真实写入后才能继续。Endpoint update、field update 和 assurance-path create 还必须对完全相同的参数带上该次 dry-run 输出的 `--confirmation-token`；draft 或 payload 变化后必须重新预览，不能复用旧 token。
2. 单字段描述或 catalog/tag 修改优先用 `gateway field update`。`--tx-catalog-id`、`--tt-catalog-id`、`--byte-data-tag`、`--not-user-data` 会归入 `compliance_tag`；未知属性以及 null/空/错误类型的 tag 会在写前拒绝，不能用 `null` 清空分类，也不能把 DECC 静默丢字段后的 success 当成成功。Tagging 输出的 primitive `req.body` / `resp.<status>.body` 根路径也可直接回灌。
3. shape 变更用 `gateway endpoint update`。先检查有界完整状态 diff；如果存在删除，只有确认每项删除都符合预期后才能使用 `--allow-delete --yes --confirmation-token <token>`。文本预览必须列出全部 captured deletion；删除清单被截断时 CLI 不会签发 confirmation token，且必须拒绝 live update，不能用 `--allow-delete` 绕过。`--http-schema-file` 接收默认 entry 的直接 patch，不含外层 `""` key，并与各 section file 互斥；raw patch 同样拒绝 null/空/错误类型及冲突的 classification tag。同一命令的 JSON 输入共享 6 MiB 预解析预算，读取期间文件变化会在解析前失败。
4. `gateway endpoint submit` 在发 POST 之前会用 draft 所属 entity 翻 `ticket list`，只要同一 endpoint 还有未结束的工单就直接拒绝，返回 `DECC_GATEWAY_SUBMIT_PENDING_TICKET_EXISTS` 并带上那张工单的 URL。这是硬性停止，没有绕过参数；DECC 本身也会拒绝这种提交，只是会返回无法解析的响应体。撤销那个版本会同时丢掉它上面已批准的加急申请（加急不随版本转移），所以先决定该版本是继续走审批还是撤销。dry-run 会跑同一次扫描，但把拒绝写进 `warnings` 而不是抛错，评审 diff 时就能看到这个阻塞。扫描本身出的其他问题——没有列工单的权限、列表读不出来、资源预算用尽——在 dry-run 下同样降级成一条「这次没能核对」的 warning，因为 dry-run 的用途是给出 diff，这道闸门不能把 diff 拿走；真实提交仍然对这些情况全部硬停。

   这次扫描有四点需要知道：
   - 列表请求**不带** region 参数，一次扫描覆盖本次提交的所有 region。带 region 的工单列表用 PSM id 而不是 Gateway `entity_id` 选实体，带上会返回空列表把硬停止变成静默放行；region 改在本地匹配，DECC 没返回 region、或返回了本 build 不认识的 region 值的工单，一样算命中。
   - "未结束"的判定是"不在已知终态集合内"。只有 approved / finished / rejected / cancelled / canceled / closed 这类已知终态才放行，本 build 没见过的审核状态、以及 DECC 根本没返回状态的工单都算命中。
   - 工单匹配走 `endpoint_id`（draft id 或已批准 baseline id），或者展示名同时带上 HTTP method 和路由。已观测到 `<path> method:<METHOD>` 和 `<METHOD> <path>` 两种写法，路径参数按占位符归一后比较，大小写也会折叠，DECC 的 `channel_name`、`endpoint_name`、`schema_name` 和 `name` 展示名字段都会试，不是只看第一个有值的；工单的 `title` 刻意不算，它是人类可读描述，恰好写了 method 和路由就会误拦别的 endpoint 的工单。其他写法只能靠 `endpoint_id` 命中，而且只有本次提交已知的 `endpoint_id` 才算数。既没有已知 `endpoint_id`、展示名也读不出 method + 路由的未结束工单会计入 `unreadable_endpoint_identity_count`，计数非零时整次扫描返回 `DECC_GATEWAY_SUBMIT_PENDING_TICKET_UNVERIFIED`——因为「没匹配到」已经不足以证明该端点没有在途工单。
   - 扫描必须能证明自己看完了整个列表，而且只有服务端真的回传的分页标记才算证据。页预算耗尽、返回的页号与请求不符、返回的页比请求的更大、重复返回同一页、没到 total 就返回空页、去重后的工单数超过 total、短页与更早某页报过的 total 相矛盾、page size 报成 0、或者既没有 total 又没有自己的 page size 时，都返回 `DECC_GATEWAY_SUBMIT_PENDING_TICKET_UNVERIFIED`，同样不发写请求。total 一旦报过就必须被满足：后一页把 total 报小、或者干脆不报，都不会提前结束遍历。完成度按 ticket ID + version 去重计数，不按返回行数计；重提可能复用 ticket ID 并递增 version，旧版本已结束不代表新版本已结束。

5. 真实写入会回读 `version=0` 并校验完整 schema、description、entity 和 assurance paths。DECC 没有已建模的 revision/CAS token，只能串行同一 bytedcli 进程内的修改并做即时回读；无法确保没有其他 CLI/Web 编辑者并发覆盖。不能建立独占编辑窗口时禁止使用 `--yes`。HTTP 408/425/429 属于 ambiguous outcome，会进入 readback/unknown 处理；遇到 verification 或 outcome unknown 错误时按 hint 查询 draft，禁止盲目重试。

## Agent Guidance：ticket 查询与撤回

1. 优先使用 `ticket list/get` 和 `ticket comment list` 核验状态和驳回原因，不要先打开 Chrome。已有 ticket URL 时直接传 `--url`；不要同时传 `--url` 和 `--ticket-id`。
2. `ticket get` 省略 `--surface` 时会在明确可回退错误后按 `unified-v2`、`unified-v1`、`portal` 顺序尝试；显式 `--surface` 会关闭回退。指定 version 时，返回结果必须证明是同一 version。`unified-v2` 会请求完整迭代历史；文本输出会列出 actions、当前/总迭代数、未解决驳回字段、两个 schema digest、一致性和生效 source。JSON 的 `schema_summary` 只承载当前迭代、驳回字段、digest/一致性/source；actions 与 `iteration_summary` 保持在同级。字段级驳回原因优先读取 `full_iteration_history[].review_comments[]`。
3. `ticket list` 的 `total` 只在 DECC 返回权威总数时出现；否则使用 `current_count` 表示当前页数量。未知响应结构会报错，不能据此得出“没有工单”。列表行带 Interface 列（JSON 为 `channel_name`，来自 `channel_data.name`，缺失时回退 `endpoint_name`），用于直接判断工单对应哪个接口，不需要为每张单再跑一次 `ticket get`；两者都缺时该列为空，不会用服务名冒充接口。
4. 非数字短 ID（形如 `demo-short-ticket-id`）通常必须带 `--version` 才能查到；省略 `--surface` 时回退链上的每个 surface 都会回 “not found”，这不代表工单不存在。先用 `decc ticket list --id <id>` 读出 version 再 `ticket get --ticket-id <id> --version <version>`；只有 list 返回空才能判定工单不存在。纯数字 ID 通常不带 version 也能查，查不到时 CLI 只提示用 list 确认是否存在，不会误导去找 version。
5. 评论只有在上游记录可关联到目标 ticket 时才返回；`filtered: false` 表示共享评论池无法安全归属，CLI 会返回空列表，不能把 raw 中的其他评论当成本工单证据。
6. 驳回的 endpoint 工单需要新迭代时，使用 `ticket iteration create`，不要用 Chrome 的 Create Iteration。命令只支持 `unified-v2` rejected ticket，要求 exact version、`create_iteration` action、同一 entity/method/path/region/assurance path，并从指定 draft 只复制 `--expect-field` 声明的 description-only 修正；未列出的 draft 差异会被忽略。必须把 `rejected_fields` 与所有预期修正逐项核对。默认 dry-run；若用户未明确授权真实创建，展示完整 diff、`would_create_iteration` 和 `snapshot_digest` 后暂停。真实写入必须带相同 selector、reason、intended fields、snapshot 和 `--yes`，POST 后回读新 iteration snapshot。

   写前有两条各自独立的预检，都不发 POST：请求的 version 必须等于 `version_history[].version_num` 的最大值（结果里回报为 `latest_version`），能证明不是最新时返回 `DECC_TICKET_ITERATION_NOT_LATEST`（最新版本即使已 cancelled 也仍算最新，服务端同样只接受最新版本）；`version_history` 缺失、为空、或条目本 build 读不出来时，属于「证明不了哪个是最新」，另有错误码 `DECC_TICKET_ITERATION_LATEST_UNVERIFIED`，不会当成「就是最新版本」。请求的版本本身是 cancelled 时返回 `DECC_TICKET_ITERATION_CANCELLED`。这几个错误码的 `details.refused_by` 都是 `cli`，用来和服务端拒绝（`refused_by: "server"`）区分。dry-run 对 `NOT_LATEST` 和 `CANCELLED` 同样直接报错，因为这两条是已证实的阻塞；`LATEST_UNVERIFIED` 说的是「证明不了哪个最新」，dry-run 把它降级进 `warnings` 让 reviewer 仍能读到 diff，此时 `latest_version` 是 `"unverified"` 而不是把请求的 version 原样回填，真实写入路径仍然直接拒绝，所以 live 结果的 `warnings` 恒为空。`--version` 本身不是正整数属于调用方入参错误，更早返回 `DECC_INPUT_ERROR`。

   写入结果按五个独立字段读，不要互相推断：`iteration_snapshot_persisted`（新 iteration 的 `schema_snapshot` 已按 digest 回读验证，是这项检查跑过的显式记录；回读失败会直接抛错，所以真实写入的结果只会是 `true`）、`main_schema_matches_snapshot`（顶层 `ticket.schema` 是否与该 snapshot 一致，两份 schema 有一份读不出来时为 `unverified`；它转述的是同一次回读里的 `schema_consistent`，不是又量了一次，所以两者不会互相矛盾。dry-run 结果里这五个字段同样存在，取值是 dry-run 语义：`iteration_snapshot_persisted` 为 `false`，`iteration_diff_entry_count` 为 `"unverified"`，`main_schema_matches_snapshot` 描述的是写入前读到的工单）、`status_after`、`iteration_diff_entry_count`（`ticket/diff` 在上一个迭代与本次迭代之间报了多少条目；它只数条目、不看内容，所以证明的是服务端看得到差异、不是差异具体是什么，`0` 也不代表写失败，取不到时为 `unverified`，包括第 1 个迭代）、以及 `change_categories`（把同一批改动按属性种类重新分组：`description` 是字段描述，`tag` 是合规标签，`structure` 是类型/取值/键集合以及新增或删除的路径，`metadata` 是字段快照上其余属性；owners、assurance path 这类 endpoint 级改动根本不在这份 diff 里。只带路径，一条路径可能落进多个分组，逐属性明细仍在 `changed_fields`，那里才是完整 diff）。

   结果还会带 `reviewer_visibility`（审核页面看到什么的固定陈述）和 `ticket_url_form`：`versioned`、`id_only`，或者 region 与 surface 都给不出结论时的 `unverified`（包括本该带 version 却没拿到 version）；`unverified` 时给出的是不带 version 的 URL，可能打不开那个确切版本。`ticket cancel` 和 `gateway endpoint submit` 同样输出这个字段并打同一行提示。事实是：`create_iteration` 写 iteration 的 `schema_snapshot`，不改写顶层 `ticket.schema`；审核页面当前迭代渲染的是 `ticket.schema`，reviewer 需要把 Base 选择器切到上一个迭代才能看到本次改动。撤销某个版本不会把该版本上的加急申请带到新版本。

7. `ticket iteration submit` 只用于把 rejected ticket 的现有 iteration 执行 `reset to pending`，不改 schema。先 dry-run 复核 exact version、action 和 snapshot，再用同一 `--expect-snapshot --yes`。命令写后回读 pending 状态，并强制比较顶层 `ticket.schema` 与当前 iteration snapshot；不一致、缺失或无法解析时返回 `DECC_TICKET_SCHEMA_DIVERGENCE`。同一个错误码同时覆盖「真的不一致」和「读不出来」，所以它只陈述两者无法被证明一致，此时 pending 状态本身不代表 schema 已被修正。写前那次检查带 `details.refused_by: "cli"`；写后回读那次不带，改用 `phase: "readback"` 与 `write_attempted: true`，因为那条路径确实已经发过写请求。结果同样带 `reviewer_visibility` 与 `ticket_url_form`。若 exact ticket 已 pending 且两份 schema 一致，`--yes` 幂等返回、不要求 snapshot、也不发 POST；pending 但 schema 不一致或不可验证仍失败。
8. 撤回必须先运行默认 dry-run 或显式 `--dry-run`，检查 ticket/version/status/actions。若用户原始请求没有明确授权真实撤回，必须展示 dry-run 结果、暂停并等待用户肯定答复；只有收到授权后，才能对同一 selector/version/reason 加 `--yes`。不得把 agent 自己的检查结论视为用户确认。若返回 `DECC_TICKET_CANCEL_OUTCOME_UNKNOWN`，先按输出 URL 核验状态，禁止盲目重试。

## Agent Guidance：DES-MQ 字段变更

1. 顺序固定：`data-version create` → `field create` / `field update` → `data-version submit` → 等 Geo Review 通过（状态 5 → 8 → 12）→ `transfer-config version create --data-version <n>` → `submit` → `apply`。DES-MQ 的数据版本自己不 apply（对 gateway 5 调 `data_version/apply` 会返回 `400000`），通道只有在传输配置版本 apply 之后才会用上新字段。
2. submit 之后用 `data-version status` 看审批进度，Geo Review 节点后面带审批单链接。`decc ticket get` 和 `ticket list --id` 查不到这类 DES-MQ 数据版本审批单，不要据此判断审批单不存在。实测一次提交由 DECC-Robot 在一分钟左右自动通过，变成 12 之后才能被传输配置版本引用。
3. 每条写命令都默认 dry-run。先跑一遍给用户看 diff，用户明确同意后才加 `--yes`。`field create/update` 的 `--yes` 还必须带同一次 dry-run 打印的 `--confirmation-token`。token 绑定整条版本记录和这次的字段，控制台上有人保存过、或者字段参数变了，token 就失效，要重新 dry-run。
4. 只有 Draft（5）能写字段和 submit。dry-run 提示 "not a Draft" 时不要硬加 `--yes`，按提示从该版本开一个新草稿。`data-version create` 会列出已有草稿和它们各自的 upstream（如 `3 (from 2)`），upstream 落后于最新 Approved 版本的旧草稿不要接着改。
5. 多个字段用 `--fields-file`（JSON 数组，每项 `path` / `type` / `description` / `tag`，可选 `sync`、`sample`），一次 dry-run、一次写入，避免多次整条覆盖。
6. `transfer-config version apply` 的 dry-run 若出现 rollback 警告，说明目标版本比当前 Applied 版本旧，apply 会把通道退回旧的数据版本，要先和用户确认。
7. `channel get` 只读。豁免开关和过滤模式在 DES-MQ 控制台上改，本 CLI 不提供写命令。

## 枚举值参考

### DECC Region

- **Registration (`hdfs-data create`, `hdfs-channel create`):** `China-North`, `Singapore-Central`, `EU-TTP2`, `US-EastRed`, `EU-Compliance2`, `US-TTP`, `Asia-SouthEastBD`, `Asia_Saas`, `Singapore_Saas`, `Asia_CIS`
- **Data transfer / Dorado HSQL (`data-transfer-config create`):** `China-North`, `EU-Compliance2`, `EU-TTP2`, `Singapore-Central`, `US-East`, `US-EastRed`, `US-TTP` only. **Both** `--source-region` and `--target-region` must be in this list; unmapped values (e.g. `Asia_Saas`) fail with `DECC_INPUT_ERROR` before create or `--dry-run`.
- **`--partition-value` default:** literal `${date}` (Dorado schedule placeholder — not shell-expanded).

### vGeo Region

`ROW-TT`, `NonTT`, `US`, `EU`, `CN`

### Scenario

| 值  | 名称                    | 说明                       |
| --- | ----------------------- | -------------------------- |
| 0   | UNKNOWN_SCENARIO        | 未知场景                   |
| 1   | ALL_SCENARIO            | 全部场景                   |
| 2   | TEXAS                   | Texas 数据主权场景         |
| 3   | CLOVER                  | Clover 数据主权场景        |
| 4   | CN_CROSS_BORDER         | CN 跨境传输场景            |
| 5   | TT_NONTT                | TT&NonTT 数据隔离场景      |
| 6   | EU_US_DIRECT_CONNECTION | EU-US 专线场景             |
| 7   | ROW_HDFS_BOE            | row-hdfs/boe 网关场景      |
| 8   | ROW_HDFS_PRODUCTION     | row-hdfs/prod 网关场景     |
| 9   | RPC_TEXAS_CLOVER_MIXED  | RPC-Texas/Clover 混合场景  |
| 10  | HDFS_TEXAS_CLOVER_MIXED | HDFS-Texas/Clover 混合场景 |

### Object Type（apply 命令）

| 值  | 类型    | 自动分配角色  |
| --- | ------- | ------------- |
| 1   | channel | Channel Owner |
| 2   | data    | Data Owner    |

### Gateway Service Source Type

`Web`, `Log`, `Metric`, `CommonHeader`

## Notes

- `gateway endpoint list` 的 stage 仅支持 `approved` 和 `draft`
- `gateway endpoint list` 可通过 `--path <path>` 按 HTTP path 过滤；DECC 服务端按前缀匹配，带花括号的路径由 CLI 改成静态前缀查询并对当前页本地精确过滤（JSON 输出 `path_filter`，含 `requested_path`、`templated`、`server_path_filter`、`match`、`scanned_count`、`matched_count`），本页无命中会报 `DECC_GATEWAY_ENDPOINT_NOT_FOUND`
- `gateway endpoint list` JSON 输出带 `page`、`page_size`、`current_count`、`has_more`、`scanned_all` 与 `truncated`；`page_size` 是本次实际生效的页大小（请求值与 DECC 回传值取小）。只有 `scanned_all: true` 才代表这一次响应覆盖了全部匹配行；`truncated: true`（含 `--page > 1` 的任何一页）都不能用来判断某接口不存在，需要继续翻页或改用 `gateway tagging get`
- `gateway endpoint get` 的 stage 仅支持 `approved` 和 `draft`
- `gateway endpoint create` 必填 `--entity-id`、`--path`、`--method`、`--description`；`--owners` 可选，省略时使用 operator
- `gateway endpoint update` 自动使用当前登录用户作为 operator；命令不需要也不支持手动传 operator
- `gateway endpoint update` 会先查询 draft detail，并沿用 detail 中的 `attributes.assurance_paths`
- `gateway endpoint update` 的 schema 字段只支持从文件读取：`--query-file`、`--path-file`、`--req-headers-file`、`--req-body-file`、`--resp-headers-file`、`--resp-body-file`
- `ticket list` 默认 `--surface unified-v2`，可选 `unified-v1` / `portal`；过滤项都是可选的，常用过滤包括 `--id`、`--entity-id`、`--schema-id`、`--type`、`--status`、`--applicant`、`--region`
- `ticket get` 接受 `--ticket-id` 或 ticket detail `--url`（二选一）；省略 `--surface` 时只对明确可回退错误依次尝试 `unified-v2`、`unified-v1`、`portal`
- `ticket iteration create` 仅用于 unified-v2 rejected endpoint ticket；它写 iteration 的 `schema_snapshot`，不改写顶层 `ticket.schema`。请求的 version 必须是 `version_history` 里的最大值（cancelled 的最新版本同样算最新），否则返回 `DECC_TICKET_ITERATION_NOT_LATEST`；最新版本本身已 cancelled 时另外返回 `DECC_TICKET_ITERATION_CANCELLED`；证明不了哪个是最新版本时返回 `DECC_TICKET_ITERATION_LATEST_UNVERIFIED`
- `ticket iteration submit` 仅 reset 当前 iteration 为 pending；真实写入后必须通过顶层 schema 与当前 snapshot 的 digest 一致性检查
- 工单详情 URL 的形态按 region 决定，surface 只在 region 未知时替它作数（两条实测证据里 region 与 surface 是一起变的）：`US` 工单、或 region 未知的 `portal` 工单用 `/ticket/detail/<id>`（加 version 段会渲染成 "cannot find an item"）；`EU` 工单、或 region 未知的 `unified-v2` 工单用 `/ticket/detail/<id>/<version>`。region 不在已知取值里等同于 region 未知，仍然退回 surface 判断，所以未知 region 的 `portal` 工单照样是 id-only。两者都给不出结论时（surface 缺失或为 `unified-v1`，同时 region 未知或不在已知取值里；或者该带 version 却没拿到 version），返回不带 version 的形态并把 `ticket_url_form` 标成 `unverified`，不会去猜
- `ticket comment list` 接受 `--ticket-id` 或 ticket detail `--url`（二选一）；无法安全关联的全局评论池不会放入结果
- `ticket cancel` 接受 exact ticket/version，默认 dry-run；只有 `--yes` 才写入，写前检查 pending/cancel action 与 priority，必要时还需 `--discard-priority`；写后回读
- `hdfs-data create` 和 `hdfs-channel create` 的 gateway 固定为 HDFS（6）
- `apply` 命令的 role 根据 `--object-type` 自动推断：1 → Channel Owner，2 → Data Owner
- Gateway 服务权限是 Kani 权限，不是 HDFS 的 `object_user_role/apply`；改 endpoint 草稿、提 OG 工单需要 `edit`。`gateway permission apply` 为当前登录用户申请，默认预览只读 Kani 元数据、不发写请求，`--yes` 才提交；审批进度用 `kani openapi workflow list --region va --namespace <预览里的 resource.ns>` 查。详见 `references/decc.md` 的 Gateway permission 章节
- `hdfs-data create` 默认 scenario 为 3（CLOVER）
- `hdfs-channel create` 默认 scenario 为 4（CN_CROSS_BORDER）
- `hdfs-data create` 只注册表本身，不能改字段；已有表的字段增删改必须走 `hdfs-data data-version`（建草稿 → column create / column update / column delete → submit）
- `hdfs-data simplified create` 在注册时写入 type、description、reason、IDL 和第一版。必填 `--channel-id`、`--name`、`--owners`。带 `--idl` 或 `--idl-file` 时还要 `--idl-type`；方向要同时给 `--source-vgeo` 和 `--target-vgeo`。默认 dry-run，只打印 `POST /openapi/simplified/data/create` 的 body；`--yes` 才发送。`--need-all-recommendation` 只打开 OpenAPI 的推荐开关，不会启动页面 AI Generate
- `hdfs-data simplified update` 从已有版本开新版本。必填 `--data-id`、`--upstream-version`。默认 dry-run，`--yes` 才 `POST /openapi/simplified/data/update`。列级增删改仍走 `data-version column`
- `hdfs-data ai` 复现页面 AI Generate，打门户 `checker_center/automation_task`，不走 OpenAPI，也不读 `--need-all-recommendation`。`check` 只读，必填 `--body-file`（JSON，含 `endpoint` 和 `data`）。`submit` 用同一份 body，默认 dry-run，`--yes` 才提交。`status` 读最新任务，`--task-id` 或 `--data-id` 至少一个，可加 `--data-version`。`adopt` 记录采纳，必填 `--task-id` 和 `--records-file`（JSON 数组），默认 dry-run，`--yes` 才写
- `hdfs-data create` 不带 `--dry-run` 时立即注册；`--dry-run` 只打印请求体并只读核对：channel 是否存在、`--scenario` 是否在 channel 自己的 scenario 里（默认 3=CLOVER 对 ROW-TT channel 基本是错的，这类 channel 多为 4=CN_CROSS_BORDER）、同 channel 下是否已有同名 data
- 新注册的表自带**空草稿 version 1**（无 IDL / Basic Info，也没有 applied 版本可供 `data-version create`），应原地编辑：`idl import` → `column update --description` → `update`（`--description` / `--sync-reason` / `--direction`）→ `submit` → 审批通过后 `apply`。细节见 `references/decc.md` 的 "Registering a new table"
- `data-version idl import` 默认读 Hive 元数据里本表的 DDL；DDL 含中文会被拒绝，用 `--strip-comments` 或 `--idl-file`（英文注释会成为列描述）；`--tag` 给未打标的列统一打标。`idl import` / `update` 是整条记录覆盖写，token 绑定整条记录，且只写 Draft
- `hdfs-data data-version` 的 scenario 按表自动探测（走 `data/detail`），输出会打印来源，如 `Scenario: 2=TEXAS (detected)`；真实 channel 基本不是 ALL_SCENARIO——US-TTP 用 2=TEXAS，EU 用 3=CLOVER，所以不要手写 `--scenario 1`。探测失败会退回 1 并告警 `(fallback)`，此时应显式传 `--scenario`——它收名字（`--scenario TEXAS`）也收 DECC 载荷里的数字码（`--scenario 2`）
- `--tag` 的 category 码表用 `hdfs-data category list` 实时拉，不要照抄本地副本：线上码表和 datapilot 里硬编码的那份已经对不上（线上多 5 个码、15 个已被灰掉、4 个文案有更新）。取值本身仍应来自合规需求，也可以用 `--json ... data-version get` 读同表其它列的 `json_schema.properties.<column>.des.tag`（CN_CROSS_BORDER / TT_NONTT 表看 `des.dt_tag`）对齐
- category 写到哪个字段由表的 scenario 决定：US/EU 场景（TEXAS / CLOVER 等）写 `des.tag` 并带 `des.sync`；4=CN_CROSS_BORDER、5=TT_NONTT 用 ROW Data Catalog，写 `des.dt_tag`，没有 `sync`。CLI 按探测到的 scenario 自动选字段，这类表传 `--sync` 会被拒；`category list` 对这两个 scenario 读的是 `dt_tag` 码表（输出 `Written to: des.dt_tag`），`--with-descriptions` 对应 `catalog_type=6`
- `column create` / `column update` / `column delete` 都同时改写 `idl.content`（Hive DDL）和 `json_schema`（含 `des.tag` / `des.dt_tag` category 标签），两者必须一致，所以只能由同一条命令一起写
- DECC 拒绝 data version 里出现任何中文（错误码 `101002`）；`column create` / `column update` 会在写入前校验 `--column-name` / `--column-type` / `--description` / `--tag` 并指出具体是哪个参数
- `data_version/update` 是整条记录覆盖写且没有 compare-and-set，因此三条改列命令的 `--yes` 都必须带上同一份草稿 dry-run 产出的 `--confirmation-token`；草稿变了 token 即失效，且 token 还绑定了具体这一处改动，不能跨列复用
- `column update` 至少要传 `--column-type` / `--description` / `--tag` / `--sync` 之一，只改传入的字段。它对 schema 节点是逐字段合并而不是重建，因为列过审后 DECC 会挂上自己的 `asset_id` / `entity` / `reason` / `uneditable`，重建会把这些静默丢掉
- 改类型会同时写两套类型词汇：`des.original_type` 存 Hive 类型，`type` 存 DECC 推导的 JSON Schema 类型。除 `string` 外两者并不相同——`bigint` → `integer`、`array<string>` → `array`、`decimal(10,2)` → `number`
- `column delete` 在草稿上能删掉，但**能删不等于能过审**：删掉已生效版本里的字段属于 schema 回退，审批方是否接受由业务决定，提交前先确认。dry-run 会打印被删声明和它带的 tag，便于回滚
- `hdfs-data data-version` 的 `list` / scenario 探测 / `cancel` / `load-schema` 走 V3 BFF（`decc.tiktok-row.net`），`detail` / `create` / `update` / `submit` / `apply` 走 OpenAPI（`bc-maliva-gw.tiktok-row.net`）；V3 的"forbidden"是按端点而非按方法判的——`create`/`update`/`submit` 在 V3 被拒，而 `cancel` 虽然在 OpenAPI 上有路由（BAM `tiktok.decc.openapiv3` 里有注册），但个人账号会被 403，只能走 V3。`apply` 同样先走 OpenAPI，个人账号 403 时同一份 body 改打门户 BFF
- `load-schema` 复现页面 Load：`GET /v3/data/hive_table_ddl` 的 `region` 必须是 DECC 机房名（EU-TTP 表写 `US-EastRed`；`EU` 与 `gcp` 都拿不到 DDL），再 `POST /v3/schema/gateway/load_json_schema`。写回只在 `--yes` 发生，并且要带上 dry-run 打印的 `--confirmation-token`（`data_version/update` 是整记录覆盖，没有 compare-and-set）。根 `json_schema.type` 必须是 `object`，同时把 `gateway` 写成 6。缺 `object` 时 Annotation 树是空的；缺 gateway 时版本列表被页面滤掉
- `data-transfer-config create` 先走 OpenAPI。个人账号被 403 时，同一份 body（`gateway` 在外层和 `data` 里各一份）改打门户 BFF `POST /decc-next-api/v3/data_transfer_config/create`。只放外层 gateway 时，Transfer Job 列表会滤掉这条记录
- `hdfs-data category list` 读的是 DES-HDFS 列打标的 category 码表（写入 `json_schema` 的 `des.tag`，ROW-TT 场景为 `des.dt_tag`）。码表从 V3 `schema/gateway/attributes` 拉，`--with-descriptions` 会额外读 OpenAPI `catalog/details` 补每个码的说明。TEXAS(2) 与 CLOVER(3) 的树完全一致，ALL_SCENARIO(1) 返回空树，所以不给 `--data-id` / `--scenario` 时默认按 TEXAS 读。`data_center/rule/query` 返回的是方向（VGEO / region）规则而不是 category 码表
- `column create` / `column update` 传 `--tag` 时会拿码表核对，但**只告警不拦截**：DECC 的 `data_version/update` 不校验 tag，填错要到人工审批才被驳回，所以提前说出来；码表拉不到时报 `not_checked` 并照常继续
- `hdfs-data data-version cancel` 只对**审批中**的版本生效：DECC 一律返回 `{"msg":"success"}`，但 `Draft` / `Suspended` 版本实测原地不动。命令按回读结果判定，未生效时打印 `cancel had no effect` 并给出未变的状态。API 无法删除 `Draft`，`cancel` 也删不掉
- `hdfs-data data-version submit` 才会真正开出审批工单，`create`、`idl import`、`update` 与三条改列命令只动草稿
- 审批通过后版本停在 `Suspended`，要 `data-version apply --yes`（OpenAPI `data_version/apply`；个人账号 403 时改打门户 BFF）才变 `Applied`；只对 Suspended 区域生效，已 Applied 报 `no_change`，未审批通过报 `DECC_HDFS_DATA_VERSION_NOT_APPLICABLE`，结果按回读状态判定
- `data-transfer-config create` 的 schema 解析顺序：OpenAPI `data/field/list`（个人账号常 403）→ Dorado DECC schema → 最新 **applied** data version 的 Hive IDL（`schema_source: decc_data_version`，与 `data-version get` 同源，含分区键）→ 源 Hive 列（需 DataLeap session）。新注册的表通常落在 applied data version 这一步；`schema.compare_source_hive` 失败不影响 ready。`--dry-run` 只需 `--data-id` / `--source-region` / `--source-data-name` / `--target-region`
- `data-transfer-config create` 后总会检查目标 global_hsql 任务的 `sourceRegionInfos[].yarnQueue`（结果 `hsql_source_yarn_queue`）：DECC 可能建出空队列，Dorado 上线会报 1003 NullPointerException。传 `--source-yarn-region` / `--source-yarn-dc` / `--source-yarn-cluster` / `--source-yarn-queue`（四者同时）在创建时补齐本 data 的空队列并逐字段回读；不传时只告警。已创建后报 `missing` 时去改该任务，不要重跑 create（会多建一个 transfer config）
- data version 的区域状态码不止平台文档里那几个：实测一次真实提交会在几分钟内经过 `Draft → 6 → 13 → 8 → Suspended`，其中 6/13/8 没有公开命名。CLI 对未命名的码原样打印为 `code <n>`，这不是报错；要看权威阶段请去 DECC 控制台
- `states` 只列出该版本传输方向（`extra.hdfs.list`）实际覆盖的区域，所以草稿上显示三个区、提交后收敛成一个区是正常的
- DES-RPC V3 channel 类型：`--role callee` 对应后端 type 2，`--role caller` 对应后端 type 3。后端把 type 1 视为 ALL_CHANNEL_TYPE 并拒绝，因此 `channel create --role caller` 和 `channel list --role caller` 都必须落到 type 3。
- DES-RPC topology 的 `--source-channel` 取 caller（type 3）的 PSM 名（例如 `example.demo.caller`），`--target-channel` 取 callee（type 2）的 channel id（数字）。两侧形态不对称：source 是 PSM 名、target 是数字 id。若给 `--source-channel` 传了 caller 的数字 channel id，CLI 会自动用 `channel get` 解析出对应 PSM 名后再提交，避免后端返回 301003 "no permission"（此报错是字段值不对，不是权限门）。若某个 PSM 只登记过 callee，需要先 `channel create --role caller` 建出对应 caller channel 再建 topology。
- DES-RPC topology 的方向对应 method 归属：`--methods` 里的方法必须能在 `topology search-data`（对 caller channel 查目标方向）里作为受支持的目标出现；方法归属在 callee channel 上，用 callee channel 查 `topology search-data` 可确认该方向是否受支持。
- `des-mq` 全部走 V3 BFF（`decc.tiktok-row.net`，`gateway=5`），个人账号即可写；`channel get` 读 DES-MQ 控制台（`des-mq-va.tiktok-row.org`）。控制台响应里带监控账号密码，CLI 只输出白名单字段，不打印也不记录原始响应
- DES-MQ 数据版本 = JSON 消息样例（`idl.content`）+ 带标签的字段树（`json_schema`）。`field create/update` 同时改这两处：字段节点写 `type` / `description` / `des.sync` / category，样例里写入 `--sample`（新字段缺省为该类型的空值）。category 写到哪个字段由 scenario 决定：4=CN_CROSS_BORDER、5=TT_NONTT 写 `des.dt_tag`，其他写 `des.tag`
- 字段路径用点分隔，`[]` 表示进入数组元素，如 `Msg.Containers[].Host`；父节点必须已存在，路径不能以 `[]` 结尾。`--sample` 按字段类型解析（number 字段上 `--sample 42` 是数字），穿过数组时写进每个元素
- `field create` 遇到已存在且完全一致的字段报 unchanged，不写；已存在但不一致时报错并指向 `field update`。`field update` 只改传入的属性，保留 DECC 自己挂上的 `uneditable` 等属性，不允许 object 和标量之间互改类型
- 样例或字段树里有超出 JS 安全整数范围的整数时，CLI 拒绝改写（`DECC_DES_MQ_UNSAFE_INTEGER`），因为 JSON 往返会改掉这些数
- 写后都会回读：字段写入按类型、标签、描述和样例逐项核对，不一致报 `DECC_DES_MQ_READBACK_MISMATCH`；submit / apply 按回读的区域状态判定
- DES-MQ 数据版本状态：5=Draft，8=In Review（submit 后 Geo Review 进行中），12=Approved（Geo Review 通过），4=Pending（与 HDFS 共用的标签）；其他码原样显示为 `code <n>`。写入、提交、引用的状态要求对版本的每个区域都成立，例如一个区域是 Draft、另一个区域在审时不允许整条覆盖写。传输配置版本状态：7=Draft（新建），1=Suspended（已提交待 apply，或被新版本替换下来的旧版本），3=Applied（当前生效）；0/2/4–6 的名字按控制台标签顺序推断，线上没见过
- `transfer-config version create` 默认以当前 Applied 版本为 upstream；引用的数据版本不是 Approved 时 `--yes` 被拒（`DECC_DES_MQ_DATA_VERSION_NOT_APPROVED`）。`submit` 只接受 Draft（7），`apply` 只接受 Suspended，已 Applied 报 `no_change`
- 物理通道 ID 就是传输配置的 `channel_transfer_config_id`（`transfer-config list` 的 Physical Channel 列）
- `des-mq` 的 scenario 从 data 上读；`--scenario` 只在 DECC 没报 scenario 时用来补，和 data 自己的 scenario 不一致时直接拒绝，避免标签写进错误的 `des` 字段
- 需要结构化输出加 `--json`（全局选项，放在子命令之前）

## PSM Common Parameters and Common-Error Approval

`gateway common-param` 使用独立的 `/unified_api/v2/common_param` API，鉴权固定走 i18n-tt；`--region US|EU` 指审批区域。此资源不是普通 endpoint。草稿由 PSM 共享，approved 版本按区域读取；approved 条目必须同时提供匹配的 OG 区域和 `Office_Net` → 本区 VPC 路径，证据缺失或不匹配会拒绝读取及提审。`get --version` 只接受精确的正整数版本；省略时读取所选 stage 的当前 schema，不接受 `0`。`get` 和 `update` 支持只有公共 query/header、没有 `res_schema` 的草稿。

```bash
# Read the approved regional schema or shared draft; data:null means absent.
bytedcli --json decc gateway common-param get --psm example.api.service --region US --stage approved
bytedcli --json decc gateway common-param get --psm example.api.service --region EU --stage draft

# Preview replacement of the complete content.http.http_schema object.
bytedcli --json decc gateway common-param update --psm example.api.service --region EU --draft-id demo-draft --entity-id demo-entity --http-schema-file /tmp/common-schema.json
# Only if every listed deletion is intentional, execute that reviewed snapshot.
bytedcli --json decc gateway common-param update --psm example.api.service --region EU --draft-id demo-draft --entity-id demo-entity --http-schema-file /tmp/common-schema.json --allow-delete --yes --expect-snapshot <snapshot_digest>

# Preview a common-error approval, then execute the exact reviewed snapshot.
bytedcli --json decc gateway common-param submit --psm example.api.service --region EU --draft-id demo-draft --entity-id demo-entity
bytedcli --json decc gateway common-param submit --psm example.api.service --region EU --draft-id demo-draft --entity-id demo-entity --yes --expect-snapshot <snapshot_digest>
```

`update` 与 `submit` 默认只预览；真实执行均需 `--yes --expect-snapshot`，指纹绑定当前身份、区域、草稿和请求，submit 还绑定 approved baseline。`--expect-snapshot` 不能单独使用，漏传 `--yes` 会报错。`update --http-schema-file` 接收完整的 `http_schema` 对象（只含一个 `""` entry），执行整份替换；预览的 `diff` 覆盖 path/query/cookie、请求和响应全部 section，列出新增、修改、删除路径及数量。保留不打算删除的公共字段和 wildcard。存在删除时，执行必须额外带 `--allow-delete`；删除列表被截断时，即使带此参数也拒绝执行，需要缩小变更。此命令组目前更新已有草稿，不创建新草稿。

`update` 的 `write_outcome` 区分 `not_sent`（预览）、`no_change`（执行时内容相同、未发 POST）和 `verified_by_readback`（写入后读回一致）；只有最后一种返回 `verified: true`。写请求在预览及发送前均按实际序列化 JSON 校验 7,340,032 字节上限，包含字符串转义开销；超限属于本地输入错误，不会发送 POST。

`submit` 专门提交显式 HTTP 400–599 公共错误响应，每项必须包含 body；保留这些响应的全部结构和标签，不提交 `*` wildcard 或公共 query/header。只有 wildcard 的草稿可以读写，但提审前需要用 `update` 添加显式错误码和 body，CLI 不会把 wildcard 自动展开成错误码。目标路径固定为 `Office_Net` → `US_VPC1` / `EU_VPC1`；EU 自动附加 `common_error method:get` / `PSM_BODY_DIFF`，这是当前公共错误审批流程的固定协议标识，不从 endpoint 的 HTTP method 推导。其余公共参数或其他 method 对应的提审流程不在该命令范围内。

每轮先比较本区 baseline、共享 draft 和预期错误码，查 regional ticket list 中的 `common_error method:get` 以避免重复工单；工单 schema ID 可能与 shared common-param ID 不同。提交输出的 `ticket_id`、`ticket_version`、`ticket_url` 是创建证据；继续用 `decc ticket get --url ...` 核验 region、OG、PSM、错误码 schema 和审批状态。确定性 HTTP 拒绝（如 400/403）保留状态码、request ID 和可用的脱敏限长 `upstream_message`；原始响应体不进入错误输出、HTTP trace 或临时错误文件。超时、限流、5xx 或无法验证的响应保留可用诊断字段。`DECC_COMMON_PARAM_OUTCOME_UNKNOWN` 表示需要先核对工单/草稿再决定是否重试，不能据此自动重复 POST。

## References

- [Gateway 目标选择与诊断](references/gateway-targets.md)
- `references/decc.md`
- `../../invocation.md`
