---
name: bytedance-megatron
description: "Operate Megatron (Spark/Flink app management) via bytedcli: get/search/locate Spark app metadata (resolve an application id to its Dorado task/instance and Spark UI roots), discover Spark AppMaster and Flink JobManager/TaskManager log links, list/tail/head Megatron proxy container logs for Flink JM/TM and Spark AppMaster/executors, get queue usage, inspect queue quota, apply to join a queue as a regular user (加入队列 BPM ticket), list/get your Megatron console tickets (我发起的), and read a Spark app's Spark UI run detail (jobs/stages/task-summary quantiles/slowest tasks/executors/sql/explain) from a live YARN proxy or the Spark History Server REST API. Use when tasks mention Megatron, Spark apps, Flink apps, application logs, executor logs, driver syslog head, queue usage, user queue quota, joining a queue, 申请加入队列, Megatron tickets/工单, Spark UI, Spark jobs/stages/tasks/executors, task duration percentiles, data skew, Spark explain plans, Flink JM/TM proxy logs, or analyzing how a Spark/Flink task ran."
---

# bytedcli Megatron

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

- Megatron Spark/Flink 应用管理
- 查询或搜索 Spark 应用元数据；从 application id 反查 Dorado task / instance / project、Spark UI 入口与 AppMaster 日志目录
- 发现 Spark AppMaster 日志、Flink JobManager / TaskManager 日志链接
- 查询队列使用情况
- 查询队列默认配额、用户配额，或计算单个用户在队列中的资源上限
- 向 Megatron 队列添加 User（默认 dry-run，`--yes` 提交；自动预检已存在则 no-op）
- 普通用户申请加入队列（`queue apply`，创建「加入队列」BPM 工单；默认 dry-run，`--yes` 提交；仅 CN）
- 查看我发起的 Megatron 工单（`ticket list` / `ticket get`）
- 读取单个 Spark 应用的 Spark UI 运行详情（jobs / stages / task-summary / tasks / executors / sql / explain），分析任务运行情况（慢 stage、task 耗时分位与数据倾斜、executor 异常、failed task、Spark explain 执行计划）
- 列出、tail 或 head Megatron proxy 容器日志：Flink JM/TM、Spark AppMaster（driver）以及按 executor id 定位的 Spark executor 容器；从 JM 的 `taskmanager_url.list` 反查可用 TM URL
- 按全局 `--site` 路由，按 `--region` / 全局 `--vregion` 选择站点内虚拟区域

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# CN 站点：查询 Spark 应用元数据
bytedcli megatron app get --app-ids application_1234567890000_000001

# i18n-tt 站点：按虚拟区域查询多个应用
bytedcli --site i18n-tt megatron app get --app-ids application_1234567890000_000001,application-abc-123 -r sg

# EU-TTP 生产网络：使用生产网 API 网关和 EU-TTP JWT 入口
BYTEDCLI_NETWORK_PROFILE=prod bytedcli --site eu-ttp megatron app get --app-ids application-demo -r i18n_gcp

# us-ttp-usts 站点（USTS 控制台直供 API，需本地 tiktok SSO session；不接受 -r）
bytedcli -j --site us-ttp-usts megatron app get --app-ids application_1234567890000_000001

# 搜索应用
bytedcli --site i18n-tt megatron app search --app-name demo-app --state RUNNING -r va
bytedcli --site i18n-tt megatron app search --me -r sg

# 排查第一站：从 application id 反查 Dorado task/instance/project、TQS id、live/history Spark UI 根地址与 AM 日志目录
bytedcli --site i18n-tt megatron app locate --app-id application_1234567890000_000001 -r sg

# 查看队列使用情况 + 用户配额（合并的命令）
bytedcli --site i18n-tt megatron queue usage --queue-name root.demo_queue --user-name demo-user -r sg
bytedcli --site i18n-tt megatron queue usage -r sg

# i18n-bd 站点 my-bd 机房（独立 Megatron 实例，CLI 直连服务主机）
bytedcli --site i18n-bd megatron queue usage --queue-name root.demo_queue -r mybd

# 列出队列（默认按当前 SSO 用户过滤；--all-users 列全部）
bytedcli --site i18n-tt megatron queue list -r sg
bytedcli --site i18n-tt megatron queue list --all-users -r sg
# 按队列名搜索（跨所有用户；--fuzzy false 精确匹配）
bytedcli --site i18n-tt megatron queue list --queue-name demo_queue -r sg

# 配置层面的用户配额（默认 ratio / 已配置的 per-user ratio）
bytedcli --site i18n-tt megatron queue quota list-users --queue-name root.demo_queue -r sg
bytedcli --site i18n-tt megatron queue quota get-default --queue-name root.demo_queue -r sg

# 向队列添加用户（默认 dry-run 预览请求；加 --yes 真正提交）
bytedcli --site i18n-tt megatron queue add-user --queue-name root.demo_queue --user demo.user -r sg
bytedcli --site i18n-tt megatron queue add-user --queue-name root.demo_queue --user demo.user -r sg --yes

# 普通用户申请加入队列：创建「加入队列」BPM 工单，由队列 owner 审批（默认 dry-run，--yes 提交；目前仅 CN）
bytedcli megatron queue apply --queue-name root.demo_queue --reason "运行示例离线任务"
bytedcli megatron queue apply --queue-name root.demo_queue --reason "运行示例离线任务" --yes

# 我发起的 Megatron 工单（ID / 流程名字 / 状态 / 队列 / 集群 / 申请人 / 审批人）
bytedcli megatron ticket list
bytedcli megatron ticket list --workflow-key join_queue --finished progress
bytedcli megatron ticket get --id 123456

# 读取 Spark UI 运行详情：运行中自动走 live UI，结束后自动回退 History Server
bytedcli --site i18n-tt megatron spark-ui summary get --app-id application_1234567890000_000001 -r sg
bytedcli --site i18n-tt megatron spark-ui jobs list --app-id application_1234567890000_000001 -r sg
bytedcli --site i18n-tt megatron spark-ui stages get --app-id application_1234567890000_000001 --stage-id 8 -r sg
# 看一个 stage 的 task 耗时 / GC / spill 分位（p50/p95/max）：几 KB 就能判断倾斜，不用拉整张 task 表
bytedcli --site i18n-tt megatron spark-ui task-summary get --app-id application_1234567890000_000001 --stage-id 8 -r sg
# 最慢的 N 个 task（服务端排序），定位倾斜 task 所在 executor / host
bytedcli --site i18n-tt megatron spark-ui tasks list --app-id application_1234567890000_000001 --stage-id 8 --limit 10 -r sg
bytedcli -j --site i18n-tt megatron spark-ui sql get --app-id application_1234567890000_000001 --sql-id 29 -r sg
bytedcli --site i18n-tt megatron spark-ui explain get --app-id application_1234567890000_000001 -r sg
bytedcli --site i18n-tt megatron spark-ui explain get --app-id application_1234567890000_000001 --sql-id 29 -r sg
bytedcli --site i18n-tt megatron spark-ui executors list --app-id application_1234567890000_000001 --all -r sg
bytedcli -j --site i18n-tt megatron spark-ui history-info download \
  --app-id application_1234567890000_000001 \
  --output-dir /tmp/demo-spark-evidence -r sg

# 也可显式传 live 或 history 页面 URL；不要手工传浏览器 Cookie
bytedcli --site i18n-tt megatron spark-ui jobs list \
  --app-id application_1234567890000_000001 \
  --spark-ui-url https://spark-ui.example/proxy/application_1234567890000_000001/jobs/ -r sg

# 获取日志链接：Spark AppMaster / Flink JobManager + TaskManager
bytedcli -j --site i18n-tt megatron spark log-link list --app-id application_1234567890000_000001 -r sg
bytedcli -j --site i18n-tt megatron flink log-link list --app-id application_1234567890000_000001 -r sg \
  --taskmanager-keyword container_123 --resolve-taskmanager-downloads

# Megatron proxy 容器日志：列文件、tail / head 日志；--app-id 解析 AppMaster（Flink JM / Spark driver）容器
bytedcli megatron log list --url 'https://megatron-log.example/yodel-logs/proxy/demo-host/demo-jm/demo-user?pod_name=demo-jm'
bytedcli megatron log list --app-id application-demo --attempt latest
# Spark driver syslog 的开头（启动期配置判定都在这里）；代理只能整档下载，本地截前 N 字节
bytedcli megatron log get --app-id application_1234567890000_000001 --file syslog --head-bytes 4000000
# 按 executor id 定位 Spark executor 容器日志（id 来自 spark-ui executors list；driver 用 `driver`）
bytedcli --site i18n-tt megatron log list --app-id application_1234567890000_000001 --executor-id 12 -r sg
bytedcli --site i18n-tt megatron log get --app-id application_1234567890000_000001 --executor-id 12 --file stderr --tail-bytes 65536 -r sg
# Flink：从 JM 反查 TM URL 后 tail TM 日志
bytedcli megatron log list --host demo-host:8092 --pod-id application-demo-attempt-1-master-1
bytedcli megatron log get --url 'https://megatron-log.example/yodel-logs/proxy/demo-host/demo-jm/demo-user?pod_name=demo-jm' --file jobmanager.log --tail-bytes 4096
bytedcli megatron log get --app-id application-demo --attempt 1 --file jobmanager.log --tail-bytes 4096
bytedcli megatron log get --host demo-host:8092 --pod-id application-demo-taskmanager-1-252 --file taskmanager.log --tail-bytes 4096
bytedcli megatron log taskmanager list --jm-url 'https://megatron-log.example/yodel-logs/proxy/demo-host/demo-jm/demo-user?pod_name=demo-jm'
bytedcli megatron log taskmanager list --app-id application-demo --attempt latest
bytedcli megatron log get --jm-url 'https://megatron-log.example/yodel-logs/proxy/demo-host/demo-jm/demo-user?pod_name=demo-jm' --tm-pod demo-tm-1 --file taskmanager.log --tail-bytes 4096
bytedcli megatron log get --app-id application-demo --tm-pod demo-tm-1 --file taskmanager.log --tail-bytes 4096

# 离线聚合已采集 Spark UI JSON，生成治理 proposal-signals（不访问 Spark History 网络）
bytedcli -j --site i18n-tt megatron spark-ui proposal-signals build \
  --app-id application_1234567890000_000001 \
  --stages-file /tmp/stages.json \
  --stage-file /tmp/stage_15.json \
  --sql-file /tmp/sql.json \
  --environment-file /tmp/environment.json

# 诊断任务（失败原因 / 慢任务 / 资源利用率）——按方法论决策树判断该取哪些证据
# 见 references/spark-ui-diagnose/GUIDE.md（方法论；scripts/compute_metrics.py 仅做派生指标计算）
```

## Site and region

- 站点使用全局 `--site`：`cn`、`i18n-tt`、`i18n-bd`、`eu-ttp`、`us-ttp`、`us-ttp-bdee`、`us-ttp-usts`、`boe`。
- `--region` 表示 Megatron 的虚拟区域，会作为 `x-bcgw-vregion` 请求头发送；也可用全局 `--vregion` 提供默认值。
- `cn`、`us-ttp`、`us-ttp-bdee`、`us-ttp-usts` 不需要 `--region`。
- `us-ttp` / `us-ttp-bdee` 走 `bc-useastdt-gw.tiktok-row.net` 网关；`us-ttp-usts` 走 USTS 控制台
  `cloud.tiktok-usts.net`，除 ByteCloud JWT 外还要本地 tiktok SSO session（控制台登录 Cookie）。
  报 `MEGATRON_SESSION_REQUIRED` 时先 `bytedcli --auth-site tiktok auth login --session` 再重跑。
- `i18n-tt` 默认 `sg`，常用值包括 `sg`、`va`、`us-west`、`us_south_west`、`eu`、`id`、`mygp`。
- `i18n-bd` 默认 `mycis`，支持 `mycis`、`mybd`。`mybd` 是 my-bd 机房的独立 Megatron 实例：
  CLI 直连其服务主机（不经过 `cloud.byteintl.net` 网关，路径无 `/api/v1/megatron_platform` 平台前缀），
  鉴权仍使用 i18n-bd ByteCloud JWT。
- `eu-ttp` 默认 `i18n_gcp`，常用值包括 `eu_ttp`、`i18n_gcp_gp`、`i18n_gcp`、`eu_ttp_no`。
- `boe` 默认 `boe`，常用值包括 `boe`、`boei18n`。

## Agent 排障最短链（不要先跑 `--help`）

拿到 Spark application ID 后，先用 summary 判断应用级状态，再按失败对象下钻。以下命令均为只读，参数形态稳定：

```bash
bytedcli --site <site> --json megatron spark-ui summary get --app-id <applicationId> -r <region>
bytedcli --site <site> --json megatron spark-ui jobs list --app-id <applicationId> -r <region>
bytedcli --site <site> --json megatron spark-ui executors list --app-id <applicationId> --all -r <region>
bytedcli --site <site> --json megatron spark-ui stages get --app-id <applicationId> --stage-id <stageId> -r <region>
```

- 失败任务：`summary -> jobs list -> stages get`。从 failed job 找 stage ID，再从 task `errorMessage` 区分首发异常与级联异常。
- OOM：同时检查 task 错误和 summary 的 `oomKilled`；错误文本出现 OOM 但 `oomKilled=0` 时，不能称为容器 OOM-kill。
- 慢任务/倾斜：从 summary 的 input/shuffle/spill 总量开始，再用 stage task 分布验证，不要只凭应用总耗时下结论。
- 输出过大时把完整 JSON 落到 `/tmp`，用 `node` 或 `jq` 做只读统计；不要假设运行环境一定安装 Python。

## Notes

- 需要结构化输出加全局 `--json`
- 加入队列：普通用户用 `queue apply`（控制台「申请加入队列」，只填申请原因），`queue add-user` 是队列 owner / 管理员直接加人的接口。`queue apply` 先查队列成员，已是成员或已有同队列未结束的加入队列工单时不会再建单；`--yes` 只提交一次，返回 `MEGATRON_QUEUE_APPLY_UNKNOWN` 时不要重试，先用 `megatron ticket list --queue-name <queue> --finished progress` 确认是否已建单。
- `ticket list` 默认列当前登录用户发起的工单，`--finished` 可重复：`progress`（进行中）、`done`（已完成）、`closed`（已关闭/撤回）；审批人只对进行中的工单显示。
- `--app-ids` 支持逗号分隔或空格分隔的 application ID
- Spark/Flink 日志链接 discovery 用 `megatron spark log-link list` / `megatron flink log-link list`；默认不要加 `--parse-download-page`，只有派生下载 URL 失败、页面模板变化，或必须读取页面真实下载锚点时才开启
- 若在生产网络访问 `i18n-tt` 或 `eu-ttp` 的 Megatron 平台 API，设置 `BYTEDCLI_NETWORK_PROFILE=prod`；
  EU-TTP 的应用、队列等平台 API 会切换到生产网网关，JWT 使用 EU-TTP 生产网入口。
  返回 `error_type: production_network` 时检查运行命令是否带该环境变量；该配置不改写返回的 Spark UI 或容器日志链接。
- `megatron spark-ui` 自动发现时优先读取运行中的 live YARN proxy，live 不可用时回退 Spark History Server；CLI 直接请求内部 REST 接口，不要从浏览器复制 Cookie
- `megatron spark-ui sql list` 会用 `offset` / `length` 自动翻页读取全部 SQL execution；Spark REST 默认页大小只有 20，不要把单页条数当成 execution 总数
- `megatron log get` 默认 `--tail-bytes 4096`，text 模式 stdout 只输出日志正文；metadata 使用 `--json` 获取
- `megatron log` 支持 `--app-id --attempt latest|<id>` 从 application attempts 的 `logsLink` 自动解析 JM URL；JSON 会带 attempt metadata
- `--host --pod-id` 会直接构造 JM/TM proxy log URL。裸 IPv6 可直接写，CLI 自动补端口 8092（如 `2001:db8::1`）；显式端口写 `ipv6:port`（如 `2001:db8::1:8092`）；不带端口且要避免最后一个数字被当成端口时用 `[2001:db8::1]`。CLI 会补上方括号。`--pod-id` 只接受完整 JM/TM pod id，不猜短 id
- TM proxy log 若返回 404 `no log found` 或 308 跳 Argos，不爬 Argos 前端；回到 `megatron log taskmanager list --jm-url <jm-url>` 重新选择可用 TM

## References

- `references/megatron.md`
- `../../invocation.md`
- `../../troubleshooting.md`
- `references/spark-ui-diagnose/GUIDE.md` — 诊断方法论：假设驱动地用 spark-ui 原子命令定位失败原因/慢因/资源问题；`scripts/compute_metrics.py` 仅做派生指标计算
