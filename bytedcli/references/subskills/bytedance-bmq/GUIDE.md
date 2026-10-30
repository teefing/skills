---
name: bytedance-bmq
description: "Operate BMQ (ByteCloud Message Queue / Kafka) via bytedcli: list/get topics, preview and submit topic creation orders, list clusters, consumer groups and mirrors, preview and submit mirror requests, preview messages using current-user permissions, or produce one message through the native SDK after a current-user permission preflight. Use when tasks mention BMQ produce/consume, writing or reading message bodies, Kafka topics, consumers, or data mirrors."
---

# bytedcli BMQ

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

## 消息读取

```bash
bytedcli bmq consume --vregion China-North --cluster demo-cluster --topic demo-topic --position earliest
bytedcli bmq consume --vregion China-North --cluster demo-cluster --topic demo-topic --partition 0 --offset 12 --format base64
# ByteIntl SINF 泳道 Topic 预览
bytedcli --site i18n-bd bmq consume --vregion ap-southeast-1 --cluster demo-cluster --topic demo-topic__lane --position latest --json
```

使用执行人的 ByteCloud JWT，由服务端检查读权限；不借用 Topic PSM 身份、不自动申请权限。
消息读取强制使用直接登录的 user 身份，不继承 `--as app` 或通用注入 JWT；需要有效的用户登录态。
`consume` 是控制台数据预览，不是消费组客户端：单次请求，不 ack、不提交位点、不持续监听。
后端决定样本数量，不支持 `--count`；响应上限为 40 MiB，超限时指定 `--partition` 缩小范围。
`--offset` 为非负 int64 的十进制字符串，必须指定 partition，不能同时指定 position。
`--format` 支持 str、pb（须有平台 schema）和 base64。JSON 中大整数保留为字符串。
TTP US/EU 不支持数据预览，CLI 不绕过此限制。
`--site i18n-bd --vregion ap-southeast-1` 的消息预览自动使用 SINF 后端；Topic 元数据仍通过 ByteIntl 控制面查询。这与 `Singapore-Central` 的普通 ByteIntl 路由不同，不要互换区域值。若遇到 `no such logic cluster`，先核对控制台实际区域、Cluster 和 Topic；已创建的泳道 Topic 通常以 `__lane` 结尾，预览不按单个 `ppe_*` 泳道名筛选。

## 消息发送

```bash
# 默认仅预览，不认证、不编译、不发送
bytedcli bmq produce --vregion China-North --cluster demo-cluster --topic demo-topic --body 'demo-message'
# 显式确认后发送一条消息
bytedcli bmq produce --vregion China-North --cluster demo-cluster --topic demo-topic --body-file ./message.txt --yes
# 使用已授权的 SDK 注册身份；这些字段不会授予权限
bytedcli bmq produce --vregion China-North --cluster demo-cluster --topic demo-topic --body 'demo-message' --key demo-key --psm example.demo.producer --owner demo-user --team demo-team --yes
```

- `--body` / `--body-file` 必须且只能提供一个。UTF-8 文件整体作为一条消息，保留换行和 BOM；消息体不能为空，消息体与 key 合计最多 999974 字节（SDK 1000000 字节上限预留 26 字节协议开销）。
- `--yes` 先使用直接登录用户的 ByteCloud JWT 查询身份、执行 BMQ 权限预检，通过后才调用原生 Go SDK 发送。不继承 `--as app` 或通用注入 JWT，不申请额外权限。TTP US/EU 暂不支持消息发送。
- **控制面和数据面身份不同**：用户 JWT 只用于权限预检；实际发送还要求运行机器具备 BMQ 服务发现、网络访问和 SDK/PSM/SASL 授权。`--psm` / `--owner` / `--team` 仅配置 SDK 注册信息，不绕过授权。未提供 PSM 时，从精确匹配的 Topic 元数据获取预检 PSM，但不会自动把 Topic 所有者 PSM 用作发送身份；SDK 继续使用当前运行环境身份。
- macOS/Linux 上，bytedcli 随包分发可审计的原生发送源码（`runtime/`），首次发送自动本地编译并缓存。npm 与 standalone 安装都需保留随包 skills 资源、安装 **Go 1.22** 并可访问内部 Go 模块；Go 缺失或编译失败时不发送。`BYTEDCLI_BMQ_GO_PATH` 可选择 Go 1.22 可执行文件。
- `--timeout-ms` 控制发送进程总时限（默认 35000，范围 1000–120000）；首次编译独立限制为 180 秒。单次执行不自动重试，SDK producer retry 也为 0。失败或超时可能已经投递，先查询 Topic 再决定是否重试。
- 成功输出 `cluster`、`topic`、`partition`、`offset`（int64 十进制字符串）；只有收到 broker 确认才报告成功。dry-run 隐藏消息正文，只展示字节数。

## Markdown 多行换行（必读）

多行正文使用 `--body $'line one\nline two'`，或通过 `--body-file` 读取文件。不要使用 `--body "line one\nline two"`：bash/zsh 双引号内的 `\n` 是字面量，不是真实换行。

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `bmq topic`, `bmq cluster`, `bmq consumer`, and `bmq mirror`. Old flat names (e.g. `bmq topics`, `bmq topic <id>`, `bmq clusters`, `bmq consumers`, `bmq mirrors`) still work as hidden aliases.

```bash
# Topic 列表
bytedcli bmq topic list --vregion "US-BOE" --page 1 --page-size 20
bytedcli bmq topic list --vregion "Singapore-Central" --search "demo" --all

# Topic 详情
bytedcli bmq topic get --topic-id 12345 --vregion "US-BOE"

# Topic 官方流量监控链接（BMQ 平台同款 Grafana 监控 URL）
bytedcli --site us-ttp bmq topic metrics get --search "demo-topic"
bytedcli --site us-ttp bmq topic metrics get --topic-id 12345 --type iframe

# Cluster 列表
bytedcli bmq cluster list --vregion "US-BOE" --all
bytedcli bmq cluster list --vregion "Singapore-Central" --search "public"

# Consumer Group 列表
bytedcli bmq consumer list --vregion "US-BOE" --page 1 --page-size 20
bytedcli bmq consumer list --vregion "Singapore-Central" --search "demo_consumer" --all
bytedcli bmq consumer list --vregion "Singapore-Central" --cluster-name "demo-cluster" --all

# Mirror 列表
bytedcli bmq mirror list --vregion "Singapore-Central" --status RUNNING --all
bytedcli bmq mirror list --vregion "Singapore-Central" --search "demo_topic" --page-size 10
```

## Topic 创建工单

使用 `bmq topic create` 预览或提交创建审批。默认查询创建元数据并预览完整资源订单；`--yes` 提交工单，`--dry-run` 优先于 `--yes`。预览展示站点、区域、接口、表单和服务端计算的订单配置（含权限）。

`--priority`（S/P0/P1/P2/P3）必填：控制台表单要求 Topic 优先级，缺省时工作流在建单阶段报 `priority should be S/P0/P1/P2/P3`，CLI 在本地预览前直接拒绝。创建参数和审批后的核验步骤见 [Topic creation orders](references/bmq.md#topic-creation-orders)。指定 `--site` 与明确的 `--vregion`，CLI 从维护的映射选择创建工作流；不接受 `--workflow-config-id`。服务树支持数字节点 ID 或精确路径，路径会通过只读查询解析。未支持的站点或区域组合会在建单前报错。

## Mirror 创建工单

使用 `bmq mirror create` 预览或提交 Mirror 申请（BPM `apply_mirror`，提交后进入管理员审核）。默认只做只读预检并预览完整 `bpmApply` 请求；`--yes` 提交一次，`--dry-run` 优先于 `--yes`。`--vregion` 是 Mirror 的**目标区域**（控制台顶导 vregion），CLI 据此从维护的映射选择 CreateMirror 工作流，不接受 `--workflow-config-id`。

```bash
bytedcli --site i18n-tt bmq mirror create \
  --vregion Singapore-Central --target-cluster demo_target_cluster --target-topic demo_topic \
  --source-vregion US-East --source-cluster demo_source_cluster --source-topic demo_topic \
  --mirror-cluster mirror_demo --service-tree 12345 --owner demo-owner \
  --throughput-quota 5 --description 'demo mirror: US-East to Singapore-Central' --dry-run
```

预检、字段含义、去重规则和回读方式见 [Mirror requests](references/bmq.md#mirror-requests)。

## 多站点支持

BMQ 支持多个站点，通过 `--site` 切换：

- `boe`: BOE 环境 (`cloud-boe.bytedance.net`)
- `i18n-tt`: TikTok ROW (`cloud.tiktok-row.net`)；`Europe-Central` 同样走 ROW 网关，按 `x-bcgw-vregion` 选区（与控制台一致），区域名用 `Europe-Central`，不要写 `EU-Central`
- `i18n` / `i18n-bd`: ByteIntl (`cloud.byteintl.net`)
- `eu-ttp`: EU TTP 站点
- `cn`: 中国站 (`cloud.bytedance.net`)

```bash
# TikTok ROW
bytedcli --site i18n-tt bmq topic list --vregion "Singapore-Central" --all

# BOE
bytedcli --site boe bmq topic list --vregion "US-BOE" --all
```

## Notes

- 返回 HTML 页面（登录页或控制台壳页）时报 `BMQ_HTML_RESPONSE`，hint 给出同站点的 `auth status` / `auth login` 命令；先确认登录态与 `--site` / `--vregion`。
- 需要结构化输出加 `--json`
- `--vregion` 指定虚拟区域（如 `US-BOE`、`Singapore-Central`、`CN` 等）
- `--all` 扩大所有者范围（默认只看自己拥有的），不自动翻页；分页使用 `--page` / `--page-size`。
- `bmq cluster list` 保留服务端 `total`、`page`、`page_size` 和本页 `current_count`；上游未提供总数时 `total` 为 `null`，未提供页码或每页条数时使用请求值。JSON 同时保留 `applied`、`recommended`、`showTopicQuotaApply`、`topicPartitionQuotaMax`，缺失值为 `null`。
- `bmq consumer list` 支持 `--cluster-name` 按集群名过滤
- `bmq topic metrics get` 返回 BMQ 平台同款 Grafana 监控 URL，默认 `--type link`（嵌入页用 `--type iframe`）；为便于查任意 topic，默认 `--all`（与 `topic list` 默认不同），多结果可用 `--cluster-name` 消歧

## Mirror search and hash strategy

`bmq mirror list --search <topic>` filters by **target topic** in the selected
`--vregion` (the mirror's target region). `--all` includes mirrors not owned by you;
`--page` and `--page-size` select one page, not an automatic full scan.

JSON mirror records include `partitionAlign` and `kafkaHashPolicy`. Text output
shows `Partition Align` and `Kafka Hash Policy`. These are separate upstream
fields: `false` is preserved, missing/null values are JSON `null` (text `-`), and
policy strings such as `PARTITION_ALIGN` or `KAFKA_DEFAULT` are returned unchanged.
Do not infer a policy from partition counts or substitute one field for the other.

## References

- `references/bmq.md`
