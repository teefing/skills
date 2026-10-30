# 创建共享 namespace 和子表

`abase create` 创建 CN、ROW、BD、EU 站点的普通共享 RW_SPLIT namespace；`abase table create`
在已有共享 namespace 下创建子表。两条命令默认预览，不提交资源申请。

## 建库

先确定服务树文件夹、owner、服务等级、存储容量和读写 RU。通过 location 的
`replicas` 读取准确的地域名；副本模板由平台提供，不能手改副本数。
用 `--site cn|i18n-tt|i18n-bd|eu-ttp` 选择站点，查询模板、预览、提交和回读必须
使用同一站点。`--location` 是必填的资源部署选择，须由用户明确指定。

```bash
bytedcli --site cn --json abase location list
bytedcli --site cn --json abase create \
  --name demo_namespace --product-id 1001 --owner demo-user \
  --location demo-location --storage-gib 500 \
  --read-ru demo-region=5000 --write-ru demo-region=5000 \
  --personal-info no --sensitivity l2 --reason "Create demo namespace"

# 确认预览后，使用相同业务参数和返回的 plan_sha256 提交
bytedcli --site cn --json abase create \
  --name demo_namespace --product-id 1001 --owner demo-user \
  --location demo-location --storage-gib 500 \
  --read-ru demo-region=5000 --write-ru demo-region=5000 \
  --personal-info no --sensitivity l2 --reason "Create demo namespace" \
  --accept-defaults --yes --expected-plan-sha256 <preview-hash>

# 在返回的 workflow_url 跟进审批，随后核实 namespace 与平台分配的集群、部署和配额
bytedcli --site cn abase get --psm demo_namespace
bytedcli --site cn abase capacity get --psm demo_namespace

# ROW 示例：先查该站点模板，再使用用户选定的 location 与准确地域名
bytedcli --site i18n-tt --json abase location list
bytedcli --site i18n-tt --json abase create \
  --name demo_namespace --product-id 1001 --owner demo-user \
  --location demo-location --storage-gib 500 \
  --read-ru demo-region=5000 --write-ru demo-region=5000 \
  --personal-info no --sensitivity l2 --reason "Create demo namespace"
```

参数约束：

- `--name`：1–128 位小写字母、数字或下划线，字母开头，不使用 `abase_`
  前缀和 `_primary` 后缀。后端还会校验保留名、已删除同名资源及创建权限。
- `--product-id`：服务树文件夹 ID；已有同名 PSM 必须绑定在该文件夹下。
  `--owner` 为用户名，可重复。
- `--level`：`p0|p1|p2`，默认 `p2`；需要更高等级时显式传入。`--location`
  必须适用于所选服务树和等级。
- `--storage-gib`：正整数 GiB；`--read-ru`、`--write-ru` 为
  `region=integer`，对模板内每个地域各传一次。上下限使用当前平台配置。
- `--personal-info yes|no`、`--sensitivity l1|l2|l3|l4` 必填。
  有个人信息时必须为 `l3` 或 `l4`，并传可重复的
  `--personal-info-region cn|us|row|europe`；无个人信息时不传来源地域。
- `--reason`：非空创建说明。

预览读取运行时配置、服务树归属、部署模板、实例规格估算和配额预检。
JSON 返回 `requested.site`、`workflow`、`request`、`defaults`、`instance_configs`、`quota_check` 和
`plan_sha256`。配额拒绝或无法识别的预检状态会阻止提交。
`quota_check.enforced=false` 表示平台未启用该配额检查。
`workflow.kind=quota_approval` 表示外层配额审批，
`namespace_approval` 表示普通建库审批，`workflow.path` 为对应提交路径。
两者均执行 CommonBuy V2 实例估算和配额预检；具体审批路径由所选站点的
运行时开关决定，不能通过参数绕过。所有认证接口使用所选站点的登录态。

`defaults` 显示普通资源、ABase2 Thrift 协议、关闭 primary、开启读写 backup
request、关闭自动审批。提交时用 `--accept-defaults` 接受这些设置。
每次提交前重新预检；站点、审批路径、请求、模板、实例估算或配额结果变化会要求重新预览。
哈希校验不提供服务端原子锁，也不提供端到端幂等保证。

建库返回 `status=submitted` 与 `receipt.workflow_url` 表示对应建库审批申请
已受理，不代表库已创建或可用。识别 `/record/<id>` 路径时还返回字符串
`receipt.ticket_id`，其他合法回执链接该字段为 null。使用回执链接跟进；
`abase ticket list` 仅列 ABase 工单，不能据其空结果排除外层配额工单。
当前不提供自动关联外层审批与最终库状态的 creation status 命令。
审批后通过 `abase get`、`abase capacity get` 核对名称、ID、共享属性、
分配集群、部署和配额；集群由平台选择。

仅支持上述四站点的 CommonBuy V2 普通共享建库流程。US、BOE、独占、KVCache、活动配额、
紧急逃逸及旧建库流程返回不支持，不自动换用其他提交路径。

## 建表

```bash
# 共享库目标：--psm 或 --cluster 与 --namespace
bytedcli --json abase table create --psm demo.namespace --table demo_table
bytedcli --json abase table create \
  --cluster demo-cluster --namespace demo_namespace --table demo_table

# 确认预览后提交
bytedcli --json abase table create --psm demo.namespace --table demo_table \
  --yes --expected-plan-sha256 <preview-hash>
bytedcli abase table get --psm demo.namespace --table demo_table
```

表名为 1–128 位 ASCII 字母、数字或下划线，字母开头。建表复用现有 ABase
站点和 `--region` 路由；拒绝独占 namespace、跨集群同名库及已有同名表。
子表共享 namespace 的底层物理表和配额，不提供独立 TTL、schema 或配额设置。
DataLeap 的 KV schema 创建使用另一条命令 `abase logic-table create`。

提交后回读表列表和详情：`created` 只表示已确认表元数据，详情中的 `state`
另行展示；`submitted` 表示请求已接受但元数据尚未确认。不要据此推断数据面就绪。

两种创建的写请求都不自动重试。`status=outcome_unknown` 或
`ABASE_CREATE_OUTCOME_UNKNOWN` 表示提交后发生超时、错误或回执异常：
保留请求与哈希，先查控制台订单/工单或精确表元数据再决定是否重试。
后端可能已经完成部分写入；查询为空不等于提交失败。
