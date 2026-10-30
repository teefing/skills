---
name: bytedance-tce
description: "Use when tasks mention TCE services/clusters/instances, deployments/lanes, environment queries/preflight checks or instance file/log/core downloads. Use bytedcli: service list/search/get/create/update/delete; cluster list/create/update/upgrade/scale/reset; instance list/search/diagnose readiness, migrate via delete, force-delete only on explicit request; allowed CN file/log/core downloads; deployment list/get/cancel/actions; env cascader; lane deploy."
---

# bytedcli TCE

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

- 服务列表/搜索/详情/创建/更新/删除
- 集群信息查询、创建/删除/更新/升级/扩缩容预检、创建/更新/扩缩容/删除/滚动重启
- 实例列表/搜索/详细 readiness 检查（`instance diagnose`）/迁移（`instance delete`）/强制删除（`instance force-delete`）
- CN 实例文件下载（日志、core 等 TCE 允许目录）
- 发布工单查询与操作（列表/详情/取消/工单级 action/步骤级 action）
- 环境级联查询
- 泳道部署

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 执行任一 `cluster ... --preflight` 前，先读 `references/tce.md` 的「集群预检使用方法」及该命令的 Preflight 小节。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `tce service`, `tce cluster`, `tce instance`, and `tce deployment`. Old flat names (e.g. `tce list-starred-service`, `tce search-service`, `tce get-service`, `tce list-service-clusters`, `tce list-instance`, `tce list-deployment`, `tce get-deployment`) still work as hidden aliases.

> 在 ByteDance 生产网络内使用 `--site i18n-tt` 时，设置 `BYTEDCLI_NETWORK_PROFILE=prod`，TCE OpenAPI 与 ByteCloud JWT host 会自动切到生产网可达的 `cloud-i18n.bytedance.net`。

```bash
# 列出支持的站点
bytedcli tce list-sites

# 列出我订阅/收藏的服务（默认；加 --recent 可改列最近访问的服务）
bytedcli tce service list --page 1 --page-size 10

# 搜索服务
bytedcli tce service search --keyword "keyword" --env "ppe_xxx" --page 1 --page-size 10

# 获取服务详情（也支持 --psm + 可选 --env）
bytedcli --site cn tce service get <service_id>
bytedcli --site cn tce service get --psm example.service.api --env prod

# 查询 PSM 运行时治理状态（对应控制台微服务治理状态，如 running / stopped）
bytedcli tce service governance get --psm example.service.api

# 查询服务健康档案（健康分、各维度得分与风险项计数；需要数字 service id）
bytedcli tce service health get --service-id 123456

# 列出服务集群（支持 --service-id 或 --psm）
bytedcli --site cn tce cluster list --service-id <service_id> --page 1 --page-size 10
bytedcli --site cn tce cluster list --psm example.service.api --env prod --page 1 --page-size 10
bytedcli --site boe tce cluster list --service-id 234558 --cluster-name tls_mix_proxy_boe --page 1 --page-size 10
# 其它命令里 <cluster_id> 的取值就是本命令返回的 data.clusters[].meta.id

# 查询精确 Pod 的 readiness 检查项（只读；Running 不等于 ready）
bytedcli --json tce instance diagnose --pod-names demo-pod-a,demo-pod-b
bytedcli --site i18n-tt --vregion Singapore-Central --json tce instance diagnose --pod-names demo-pod-a

# 创建/更新/删除服务
bytedcli tce service create --service-info-file service-info.json --dry-run
bytedcli tce service create --service-info-file service-info.json --yes
bytedcli tce service update --service-id <service_id> --update-info-file update-info.json --dry-run
bytedcli tce service delete --service-id <service_id> --request-file delete-request.json --dry-run

# 查询和校验服务可用 SCM 包
bytedcli tce service repo-info-list --service-id <service_id>
bytedcli tce service check-repos --service-id <service_id> --request-file check-repos.json --dry-run
bytedcli tce service check-repos --psm example.service.api --env prod --request-file check-repos.json --dry-run

# 创建集群预检：空请求或逐步补充服务和 cluster_info
bytedcli --json tce cluster create --preflight
bytedcli --json tce cluster create --psm example.service.api --env prod --cluster-info-file cluster-info.json --preflight

# 删除集群预检：逐步核对实际删除目标
bytedcli --json tce cluster reset --preflight
bytedcli --json tce cluster reset --psm example.service.api --cluster-name default --preflight

# 创建/删除集群（cluster_info 建议来自预检候选、平台推荐模板或控制台导出的 payload）
bytedcli tce cluster create --service-id <service_id> --cluster-info-file cluster-info.json --dry-run
bytedcli tce cluster create --psm example.service.api --env prod --cluster-info-file cluster-info.json --yes
bytedcli tce cluster reset --service-id <service_id> --cluster-id <cluster_id> --dry-run
bytedcli tce cluster reset --psm example.service.api --env prod --cluster-name default --dry-run

# 更新集群预检：逐步补充 selector / update_info
bytedcli --json tce cluster update --preflight
bytedcli --json tce cluster update --cluster-name default --psm example.service.api --update-info-file payload.json --preflight

# 更新集群配置（通过 JSON 文件提交 update_info）
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --yes
bytedcli tce cluster update --cluster-name default --psm example.service.api --env prod --update-info-file payload.json --dry-run
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --yes --wait --note "demo update"

# 升级预检：逐步补充目标、版本与 rollout strategy
bytedcli --json tce cluster upgrade --preflight
bytedcli --json tce cluster upgrade --cluster-ids 100,101 --rollout-strategy default --repo-info-file repos.json --preflight

# SCM 版本升级
bytedcli tce cluster upgrade --cluster-id <cluster_id> --service-id <service_id> --repo-info-file repos.json --dry-run

# 镜像升级：--psm 与 --service-id 同用时仅用于 image_tag 查询，不会作为服务 selector 发送
bytedcli tce cluster upgrade --cluster-id <cluster_id> --service-id <service_id> \
  --image-version 1.0.0.86 --psm example.image.service --dry-run

# 扩缩容预检：可仅提供 IDC、副本数或完整输入
bytedcli --json tce cluster scale --preflight
bytedcli --json tce cluster scale --psm example.service.api --cluster-name demo-prod --idc sample-idc --replicas 2 --preflight
bytedcli --json tce cluster scale --service-id <service_id> --cluster-id <cluster_id> --scale-info-file scale.json --smooth-file smooth.json --preflight

# 集群扩缩容（调整各 IDC 副本数）
bytedcli tce cluster scale --psm example.service.api --env prod --cluster-name demo-prod --replicas 2 --dry-run
bytedcli tce cluster scale --psm example.service.api --env prod --cluster-name demo-prod --replicas 2 --yes
bytedcli tce cluster scale --cluster-id <cluster_id> --service-id <service_id> --scale-info-file scale.json --yes --wait --pipeline-template 400013643

# 集群滚动重启（TCE 原生「操作实例 → 重建实例」，由 TCE 按并发粒度滚动重建）
bytedcli tce cluster restart --psm example.service.api --env prod --cluster-name demo-prod --dry-run
bytedcli tce cluster restart --cluster-id <cluster_id> --service-id <service_id> --surge-percent 25 --interval-sec 10 --yes --wait

# 列出服务实例（推荐使用 --psm + --env）
bytedcli --site cn tce instance list --psm example.service.api --env prod --ordering -cpu

# 搜索服务实例（兼容方式：使用 service_id）
bytedcli --site cn tce instance search --service-id <service_id> --ordering cpu --page 1 --page-size 10

# 按 node IP 过滤服务实例
bytedcli tce instance list --service-id 234558 --node-ip 10.35.142.21 --force-update --page 1 --page-size 10 --tce-site boe

# 下载文件；执行前先用 instance list 确认目标，默认上限 10 MiB，失败不保留半文件
bytedcli --site cn tce instance download \
  --psm example.service.api \
  --env ppe_demo \
  --pod-name demo-pod \
  --container-name main \
  --remote-path /opt/tiger/toutiao/log/result.log.gz \
  --output ./result.log.gz

# 直接复用本地浏览器态 SSO session，自动从 PSM/env 建立 webshell 会话
bytedcli --json auth login --begin --session --session-method qr --no-terminal-qr
bytedcli --json auth login --complete <complete_token>
bytedcli tce webshell open --psm example.service.api --env prod --first
# 服务实例很多时用 --node-ip 先在服务端按节点过滤，open / interactive 均支持
bytedcli tce webshell open --psm example.service.api --env prod --node-ip 10.35.142.21 --first
bytedcli tce webshell exec --session-id ws_demo --command 'hostname; date'
# 仅当上一步返回 TCE_WEBSHELL_OTP_REQUIRED 时使用；TTY 会隐藏输入，Agent 应通过子进程 stdin pipe 注入一行
bytedcli tce webshell exec --session-id ws_demo --command 'hostname; date' --otp-stdin
bytedcli tce webshell interactive --psm example.service.api --env prod --first
# 同样支持 --node-ip 在服务端按节点过滤实例
bytedcli tce webshell interactive --psm example.service.api --env prod --node-ip 10.35.142.21 --first
# 交互模式同样支持自动输入 OTP：TTY 下先隐藏输入，连上后看到提示只自动提交一次
bytedcli tce webshell interactive --psm example.service.api --env prod --first --otp-stdin
bytedcli tce webshell close --session-id ws_demo
```

### 服务创建、更新、删除与仓库校验（Agent Guidance）

执行 `service create/update/delete/check-repos` 前先读 `bytedcli self skill get bytedance-tce/references/tce.md` 的「服务输入文件与字段治理」。服务没有 preflight；`--dry-run` 只预览本地将要提交的请求，不调用后端校验。

- create 的 `--service-info-file` 根对象就是 `service_info`；`--request-file` 是含 `service_info` 的完整请求，且两者同时存在时后者优先。非空 `--note` / `--purpose` / `--source-url` 覆盖文件元数据。
- update 的 `--update-info-file` 根对象就是 `update_info`；`--request-file` 是完整请求，且两者同时存在时后者优先。`--service-id` 始终覆盖文件中的 `service`，非空 `--note` / `--purpose` / `--source-url` 覆盖文件元数据。
- create/update 的 JSON 文件保持 raw pass-through：未知扩展、`null`、`0`、`false` 原样保留，CLI 不新增字段级运行时校验。BAM 的 optional 只表示传输层可省略，不等于创建业务允许缺失。
- delete 的 `--request-file` 根对象是完整删除请求，不包 `service_info` / `update_info`；必填 `--service-id` 覆盖文件中的 `service`，非空 `--note` / `--purpose` / `--source-url` 覆盖同名元数据。`client_token` 由 bytedcli 生成，不在文件中管理；顶层不要写 `dry_run`，应使用 CLI `--dry-run`。
- check-repos 会在预览和提交前校验非空 `cluster_ids` 的元素为整数，以及非 `null` 的 `repos[].name/version` 为字符串，不增加业务必填、正数范围或权限约束；未知扩展字段及符合类型约定的值保持原样。`--dry-run` 不检查后端仓库权限。

SCM/default 模式的最小结构起点如下；占位值必须替换为用户确认的真实目标，不能直接提交：

```json
{
  "meta": { "psm": "example.service.api", "env": "prod" },
  "build": {
    "base_image": "sample-base-image",
    "dependency_mode": "default",
    "framework_support": "none",
    "scm_repo_info": [{ "name": "demo-repo", "path": "demo-org/demo-repo", "main_repo": true }]
  },
  "runtime": {
    "app_path": "bin/start.sh",
    "new_ports": [{ "intent": "primary", "is_primary": true, "port": 8080 }]
  }
}
```

单字段更新可从以下 `update-info.json` 开始；`period_seconds` 单位为秒：

```json
{ "runtime": { "period_seconds": 10 } }
```

`check-repos.json` 的根对象是请求 body，服务 selector 不写入文件：

```json
{
  "cluster_ids": [123456],
  "repos": [{ "name": "demo-repo", "version": "demo-version" }]
}
```

- 新建 PSM 是用户业务目标；bytedcli 没有“猜测未创建 PSM”的查询命令。更新所需 `service_id` 与当前可写值来自 `service get`；repo name/version 来自 `service repo-info-list` 返回的 `.data.repos[]`；cluster ID 来自 `cluster list` 的 `.data.clusters[].meta.id`。
- `dependency_mode=default` 使用 SCM 配置，需按业务提供 `scm_repo_info` 与启动脚本；`dependency_mode=manifest` 不使用 SCM 配置，`framework_support` 必须为 `none`，`app_path` 可空。镜像/manifest、ByteTree parent、IAM 与合规值没有对应 CLI 候选时，必须由用户根据对应平台能力提供，禁止猜测。
- 不要回写 read-only 字段，例如 URL/状态/时间、`runtime.cluster_ids/image_version/latest_repo_info`、`upgrade.upgrade_url`；不要新增 deprecated 字段。完整 writable/read-only/deprecated 清单与单位见 reference。

### 创建集群配置与预检（Agent Guidance）

创建前先读取完整说明：`bytedcli self skill get bytedance-tce/references/tce.md`，按「Create Preflight（只读发现）」逐步获取候选，不运行正式 create 试错。

- `--cluster-info-file` 的根对象是 `cluster_info`；`--request-file` 是完整请求，外层包含 `service`，或 `psm` / `env`，以及 `cluster_info`。
- 集群名只写在 `cluster_info.meta.name`；顶层 `cluster_info.name` 会报错，即使同时提供了 `meta.name` 也不会静默忽略。
- 使用 PSM 预检时显式传 `--env`；示例的 `prod` 应替换为用户目标环境。
- `runtime.replicas` 是对象，不是数字；副本写在 `dc_info[]` / `canary_dc_info[]`，每项使用字符串 `idc` 和整数 `count`。
- 环境变量字段固定为 `runtime.env_list[].env_name` / `env_value`；不要写 `env_lst` 或条目内的 `name` / `value`，`env_value` 使用字符串或 `null`。
- Create Preflight、正式 `--dry-run` 与提交共用宽松输入类型检查：只校验已填写的已知字段，错误返回完整 JSON 字段路径；未知扩展、显式 `null`、`0`、`false` 和空数组原样透传。
- 位置、IDC、资源规格与依赖均从当前请求的后端候选逐步取得，由用户显式选择；不截断候选，也不自动采用第一个或 `recommended`。
- 普通、镜像与 Quick Create 的最小文件、候选映射和核对流程统一见 `references/tce.md`，最终以 `can_submit`、constraints 和 preview 为准。

### 更新集群输入校验（Agent Guidance）

- Update Preflight、正式 `--dry-run` 与提交共用核心校验：提供的 `resource` 字段复用 create 类型，`cpu` / `mem` 等资源值使用 number；提供的 `runtime.env_list` 条目使用 `env_name` / `env_value`，其中值为字符串或 `null`。集群名写在 `meta.name`，不要写顶层 `name`。
- 校验保持 partial：省略块、显式 `null`、部分环境变量条目和未知高级扩展继续透传；不要写 `runtime.env_lst` 或条目内的 `name` / `value`。
- CLI 按原样提交 `update_info`，不会回查并与当前集群配置合并；不能一概宣称省略字段必然保留或清除。明确修改 `runtime.env_list` 时，后端会替换该数组，必须提交完整期望数组，并用 Update Preflight 核对其他同级字段要求。

### 工单幂等与重试

`service create/update/delete` 与 `cluster create/reset/update/upgrade/scale/restart` 会在内部自动生成一次性 `client_token`；同一命令进程内的网络重试会复用完全相同的 Token 和请求体。该机制不提供用户输入、输出或跨进程复用入口。Create / Reset / Update / Upgrade / Scale Preflight 均不生成 Token。`deployment action/cancel/execute-step`、`instance delete`、`instance force-delete`、`service check-repos` 和 `deploy-lane` 不启用这项自动写重试。

### WebShell 目标解析（Agent Guidance）

- `tce webshell open` / `interactive` 从 `--psm --env` 解析目标时，会先拉取该服务返回的实例列表，再在本地按 `--pod-name` / `--container-name` / `--container-type` 过滤；服务实例很多（上万个 pod）时这一步很慢，默认 HTTP 超时可能不够，需要用全局 `--http-timeout-ms` 放大（全局参数写在子命令之前）。
- `--node-ip <ip>` 把 `node_ip` 透传给实例查询，由服务端先按节点过滤再返回，是缩小 `open` / `interactive` 解析范围的推荐方式；它只缩小服务端返回范围，不改变 `--pod-name` 的本地精确匹配语义。

### WebShell OTP（Agent Guidance）

- 首次调用 `tce webshell exec` 时不要预先索要 OTP。若目标无需 OTP，命令会按原流程执行。
- WebShell 的 OTP 提示有三种文案，bytedcli 均能识别：`please input otp code`、`please input seal/feilian OTP code`、`请输入Google Authenticator OTP码（输入q退出）`。
- 返回 `TCE_WEBSHELL_OTP_REQUIRED` 时，保留原 `session-id` 与命令，通过模型对话之外的 secret input 获取一个当前 Seal/飞连 OTP，再用 `--otp-stdin` 重试同一命令。
- exec 模式：Agent 以 stdin pipe 启动子进程，写入一行 OTP 后关闭 stdin 即可（exec 不占用进程 stdin）。
- interactive 模式：TTY 下会先显示隐藏输入提示，OTP 在 WebShell 打印提示时自动提交，然后正常进入 shell；非 TTY 管道中 OTP 行之后的字节会回留给会话使用，但 stdin 一旦 EOF 会话立即关闭——只喂一行 OTP 就关 stdin 会在门禁提示出现前结束，OTP 无法提交。因此非 TTY 场景不要用 interactive，改用 `tce webshell exec --otp-stdin`（exec 不占用 stdin）。
- 不要把 OTP 拼进 shell 命令，也不要通过 argv、环境变量、文件、日志或普通对话传递。
- OTP 只在连接后 30 秒的门禁窗口内自动提交一次。`TCE_WEBSHELL_OTP_INVALID` 表示 OTP 无效或已过期：丢弃该值并重新请求，禁止自动重放；interactive 模式下服务端再次提示时由用户手工输入或退出重进。
- `TCE_WEBSHELL_OTP_TIMEOUT` 表示认证后未在时限内进入 shell：重新连接同一持久化会话并使用当前 OTP 重试。
- bytedcli 会在看到 OTP 提示后先单独提交 OTP，确认出现认证后终端输出才发送业务命令；错误分支不会把业务命令当作 OTP。

### WebShell 握手重试（Agent Guidance）

- `tce webshell exec` 每次都会新建 websocket。relay 会间歇性拒绝握手（例如返回 HTTP 200 + `token expires, maybe attack!`），此时连接尚未打开、命令一定没有发出，bytedcli 会重新获取 websocket URL，退避 1–3 秒后重试，默认最多 5 次，可用 `--handshake-retries <n>` 调整（0–20，0 表示不重试）。
- 连接打开之后的错误（`TCE_WEBSHELL_ERROR`、`TCE_WEBSHELL_TIMEOUT` 等）不会自动重试，因为命令可能已经发出且不一定幂等。
- 成功时 JSON 的 `data.handshake_attempts` 是实际握手次数（1 表示没有重试）。
- 全部尝试都被拒时返回 `TCE_WEBSHELL_HANDSHAKE_REJECTED`，`error.details` 包含 `attempts`、`handshake_retries` 以及 relay 响应的 `status`、`body`、`logid`（`body` 为尽力捕获，可能缺失；没有收到 HTTP 响应时只有 `attempts`）。命令没有发出，可以直接重跑同一命令；持续失败时重新 `tce webshell open`，并把 `logid` 反馈给 relay 维护方。
- 握手返回 401/403 时不重试，直接返回 `TCE_WEBSHELL_HANDSHAKE_REJECTED`：先 `bytedcli auth login --session` 刷新 SSO 会话，再重新 `tce webshell open`。

## 发布工单

```bash
# 查询发布工单列表与详情
bytedcli tce deployment list --service-id <service_id> --type upgrade
bytedcli tce deployment list --psm example.service.api --env prod --type upgrade
bytedcli --json tce deployment get <deployment_id>

# 取消发布工单：先本地预览精确 cancel 请求，再执行
bytedcli tce deployment cancel <deployment_id> --dry-run
bytedcli tce deployment cancel <deployment_id>

# 选择 TTP 审批人：dry-run 可只读解析 step 并预览固定请求
bytedcli --site us-ttp tce deployment select-ttops-approver <deployment_id> --dry-run

# 最小工单级 action：先预览，再核对 pipeline.allow_actions 后提交
bytedcli tce deployment action --deployment-id <deployment_id> --action start --dry-run
bytedcli tce deployment action --deployment-id <deployment_id> --action start --yes

# rollback 的附加字段写入请求体顶层
bytedcli tce deployment action --deployment-id <deployment_id> --action rollback \
  --extra-json '{"rollback_reason":{"index":1,"info":"sample-context","reason":"demo rollback"},"upgrade_min_ready_second":10,"upgrade_surge_percent":25}' \
  --dry-run

# 最小步骤级 action：先预览，再核对步骤 allow_actions 后提交
bytedcli tce deployment execute-step --step-id <step_id> --action start --dry-run
bytedcli tce deployment execute-step --step-id <step_id> --action start --yes

# 选择审批人所需的附加字段
bytedcli tce deployment execute-step --step-id <step_id> --action choose_ttops_approver \
  --extra-json '{"approver_type":"organization_account","is_noc":true}' --dry-run

# 检测规则反馈对象同时支持数字 id 与字符串 id_str
bytedcli tce deployment execute-step --step-id <step_id> --action skip \
  --extra-json '{"ignore_reason":"demo reason","ignore_rules_feedback":[{"id":123,"reason":"demo reason"},{"id_str":"sample-rule","reason":"demo reason"}]}' \
  --dry-run

# 跨站点查询
bytedcli --site boe tce deployment list --service-id <service_id>
bytedcli --site byteintl tce deployment get <deployment_id>
```

### Deployment action 入参与取值来源（Agent Guidance）

两个通用 action 命令都把 `--action` 写入 body 的 `action`，把 `--extra-json` 对象合并到 body 顶层；发生同名冲突时显式 `--action` 始终优先。动作名保持动态字符串，未知扩展、`null`、`0`、`false` 原样透传，不新增字段级运行时校验。

- `deployment action`：`--deployment-id` 只用于 URL path。已知附加字段为 `pause_reason`、`rollback_reason{index,info,reason}`、`skip_rolling_granularity_check`、`update_mode`、`upgrade_min_ready_second`（整数秒）和 `upgrade_surge_percent`（整数百分比）。
- `deployment execute-step`：`--step-id` 只用于 URL path。已知附加字段为 `approver`、`approver_type`、`is_noc`、`pause_reason`、`reason`、`ignore_reason` 与 `ignore_rules_feedback[]`；反馈项形状为 `{id?: number, id_str?: string, reason?: string}`。
- 先运行 `bytedcli --json tce deployment get <deployment_id>`：工单 ID 在 `.data.meta.id`，工单级当前动作在 `.data.pipeline.allow_actions`，步骤 ID 在 `.data.pipeline.stages[].steps[].id`，步骤级当前动作在 `.data.pipeline.stages[].steps[].allow_actions`。`allow_actions` 项可能是字符串或对象；字符串直接作为动作名，对象优先读取 `name`，仅当平台明确把 `type` 作为动作 token 且 `name` 缺失时才使用 `type`，不要根据 `display` 猜测。
- 暂停/回滚原因、回滚原因序号和更新模式来自目标 TCE 工单操作/回滚表单或用户明确选择；审批人与类型来自目标 TCE/USTS 审批人选择能力；检测规则 `id` / `id_str` 和原因来自目标 TCE Detector 结果及用户选择。bytedcli 当前没有这些候选的独立查询命令，不能虚构命令、猜值或自动选第一项。
- `--dry-run` 只预览本地组装的请求，不调用 action 接口，也不代表后端会接受。用户确认目标、当前允许动作及附加字段后，才把同一命令改为 `--yes` 提交。

## 环境级联查询

```bash
# 查询 PSM 的环境级联信息（partition -> env -> lane）
bytedcli tce env-cascader --psm example.service.api

# 指定分区
bytedcli tce env-cascader --psm example.service.api --partition CN

# 指定环境
bytedcli tce env-cascader --psm example.service.api --env prod
```

## 泳道部署

`tce deploy-lane` 会直接创建部署，命令本身既没有 `--dry-run` 也没有 `--yes`；执行前先用
`env-cascader` 和只读查询核对泳道、集群及 SCM 版本。`--action create --cluster-spec-file`
接收的也是 **ENV 显式 cluster spec**，不是 TCE `cluster_info`。先用
`env service deploy-tce --dry-run` 获取 `.data.cluster_spec`，确认它非 null 且必填字段完整，
再用同一 ENV 命令配合 `--cluster-spec-file ... --dry-run` 复验固定后的 preview / pre-check。
字段表、最小 JSON 与完整只读链见 bytedance-env 的 `references/env.md`（通过
`bytedcli self skill get bytedance-env/references/env.md` 读取）。

```bash
# 部署泳道（需要指定 env、standard-env、psm、flow-base、branch）
bytedcli tce deploy-lane \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --flow-base prod \
  --branch master

# 部署指定 SCM 版本（仅提交指定仓库，不携带完整 SCM 列表）
bytedcli tce deploy-lane \
  --env prod \
  --standard-env boe \
  --psm example.service.api \
  --flow-base boe \
  --scm-repo-name example/service/api \
  --scm-repo-version 1.0.0.8 \
  --action upgrade

# 创建时注入自定义环境变量（逗号分隔 key=value）
bytedcli tce deploy-lane \
  --env boe_demo \
  --standard-env boe \
  --psm example.service.api \
  --action create \
  --cluster-names default \
  --env-vars "scmVersion=1.0.0.100"

# 使用已由 ENV --dry-run 完整验证的 spec 创建；以下命令会立即执行真实部署
bytedcli tce deploy-lane \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --action create \
  --cluster-spec-file cluster.json

# 开启热部署
bytedcli tce deploy-lane \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --flow-base prod \
  --branch master \
  --action create \
  --hot-deploy
```

`--cluster-spec-file` 只用于 `--action create`，并与 `--cluster-names` / `--specify-dcs` /
`--zone` / `--virtual-cluster` 互斥。`tce deploy-lane` 的 branch 与 SCM version 参数不等同于
`env service deploy-tce` 的全部模式；ENV 预检只负责验证同一 env / standard-env / PSM 和 spec，
不要声称两个入口所有参数完全等价。

### 精确 SCM 制品部署到 PPE

当 PPE 验证必须证明某个 Git/MR commit 已实际运行时，不要直接按可漂移的 branch 部署。先构建该 commit 的 SCM test 制品并从 `data.versions[]` 精确核对 `version`、`base_commit_hash`、`status=build_ok`，再使用 `--scm-repo-name + --scm-repo-version` 只提交一次泳道升级。完整的写前漂移门禁、不明结果恢复、ENV/TCE 工单回读、实例健康和共享域名 PPE 路由验证见 `references/tce.md` 的「精确 SCM 制品到 PPE 泳道」章节。

## 环境变量注入（upgrade-tce）

```bash
# 升级时设置自定义环境变量；执行模式必须二选一传 --dry-run（预览）或 --yes（提交）
bytedcli env service upgrade-tce \
  --psm example.service.api \
  --env boe_demo \
  --standard-env boe \
  --cluster-id 12345 \
  --env-vars "scmVersion=1.0.0.100" \
  --yes
```

`--env-vars` 支持逗号分隔的多个键值对，如 `--env-vars "key1=val1,key2=val2"`。值会合并到集群的 `new_env_vars` 中，不会覆盖未指定的已有环境变量。

## 跨站点示例

```bash
bytedcli --site boe tce service search --keyword "my-service"
bytedcli --site byteintl tce service search --keyword "my-service"
bytedcli --site ttp-us-limited tce service search --keyword "my-service"
bytedcli --site ttp-eu tce service search --keyword "my-service"
```

## 输出结构（--json）

加 `--json`（全局选项，放在子命令之前）时，列表类命令返回统一信封结构：

- 顶层：`{ status, data, error, context }`；成功时 `status="success"`、`error=null`。
- 列表数据位于 `data.<资源复数>[]`：收藏/搜索服务在 `data.services[]`，集群在 `data.clusters[]`，工单在 `data.deployments[]`。**例外：实例列表在 `data.pods[]`（不是 `data.instances`）。**
- 分页信息位于 `data.page_info{ total_count, page_num, page_size }`；另有冗余字段 `data.total`。**实例（`instance list`）按「是否走服务实例分页接口」分两类：含 `data.page_info`（`--page-size` 生效）——`--psm [--env]`，或 `--service-id` 搭配 `--ordering` / `--node-ip`；无 `data.page_info`、只有 `data.total`、一次返回全量——裸 `--service-id` 或裸 `--cluster-id`（二者互斥，不能同传）。**
- 执行上下文位于 `context{ execution_time_ms, timestamp, api_endpoint }`。
- `cluster update/upgrade/scale/restart --wait`：完成时返回 `data.final_status`；失败或取消时返回非零退出码，工单 ID 与终态位于 `error.details`。

下游脚本/Agent 解析时，统一按「成功看 `status`、取列表读 `data.<资源复数>`、取分页读 `data.page_info`」处理；`instance list` 的列表始终读 `data.pods[]`，分页则按上一条区分：走服务实例分页接口的形态（`--psm [--env]`、或 `--service-id` 加 `--ordering`/`--node-ip`）有 `page_info`，裸 `--service-id`、裸 `--cluster-id` 仅有 `data.total`。

## Notes

### 服务负责人字段

查询服务负责人读 `data.auth.iam_info.owners[]`（每项含 `username`、`email`，保留完整列表）；`auth.owner_name` 是 GDPR/ZTI 鉴权用户名、`auth.owner` 为已废弃 ID，均非负责人。`owners` 缺失或为空时如实说明未返回 IAM owner，不要用这两个字段兜底。

### 安全规则

**服务与集群变更。** 创建、更新、升级、扩缩容、删除和重启都可能生成真实工单。先确认站点、服务、集群和变更内容；用户明确确认后才执行正式命令，并显式传 `--yes`。`--preflight` 是只读发现，`can_submit=true` 不是授权；`--dry-run` 只预览本地构造的正式请求，必要时仍会做只读查询，不提供后端预检报告。两者都不能替代用户确认。创建服务或集群时优先使用平台推荐模板或控制台导出的配置，不要凭空拼接复杂 `service_info` / `cluster_info`。

- **配置更新与版本升级**：`cluster update` 修改配置，`cluster upgrade` 修改 SCM 或镜像版本。CLI 按原样提交 `update_info`，不会回查合并当前配置；明确提交 `runtime.env_list` 时，后端会替换该数组，必须基于当前列表构造完整期望数组，避免遗漏变量被删除。预检里的模板、版本、升级模式和发布策略仅是候选；尤其请求 `eager` 时还要核对 `preview.cluster_list[].rollout_strategy`，不能自动选择或只凭请求判断最终策略。
- **集群删除（Reset）**：Reset 会先缩容到零再永久删除集群。预检或只读查询必须定位唯一的实际目标，向用户展示目标和删除影响，得到明确确认后才用 `--yes` 提交；不要把 Reset 当作重启。
- **扩缩容**：先从预检的 `current_state` 读取配置容量，按 IDC/VDC 计算目标值，再核对 `preview.cluster_list[].diff_info` 和 `resource_operations`。IDC、流水线模板及预留目标由用户选择，`reserve_to: ""` 不能推断为当前用户。遇到 `InvalidParameter.Ambiguous` 时展示候选 ID，让用户选择，不自动取第一项。`--scale-info-file` 的 legacy 副本格式与完整 `runtime` 格式不能混用，也不能与 `--idc` / `--replicas` / `--canary-replicas` 同传。
- **滚动重启**：`cluster restart` 调用 TCE 的 `pod_exec` 重建工单，默认并发粒度 10%、间隔 30 秒。必须先用 `--dry-run` 展示重建请求，用户确认后再加 `--yes`；可用 `--wait` 等待工单终态。重启整集群不等同于逐个执行 `instance delete`。

- **`instance force-delete` 稳定性规则（MUST follow）**：
  (1) 仅在用户明确要求强制删除时使用；必须告知其会绕过 PDB 并上报故障宿主机。
  (2) 删除前先用 `instance list` / `instance search` 确认目标站点及实例当前仍存在且唯一，避免用过期 pod 名或模糊匹配结果直接删。
  (3) 执行 `--pod-name <name> --dry-run` 展示请求；再次确认后才加 `--yes`，`--dry-run` 优先。
  (4) 每次仅处理一个实例，执行前检查健康副本，执行后重新查询实例状态；状态异常时停止，不与其他实例或部署变更并发执行。
- **`instance delete` 稳定性规则（MUST follow）**：
  (1) 除非用户明确要求“删除实例 / 删除 pod”，或上下文明确是在做“实例迁移 / 节点迁移”并且删除实例是迁移动作的一部分，否则不要主动建议或执行 `tce instance delete`；不要把“重启”“排障”“恢复”“摘流量”自动等同为删除实例。
  (2) 禁止一次性删除 2 个或以上实例；任何多实例场景都只能单个串行执行，每删一个都要重新观察，再决定下一个。
  (3) 任何真实删除前都必须先执行 `--dry-run`，并向用户展示精确的 `cluster-id / idc / pod-name`。
  (4) 任何真实删除都必须二次确认：第一次确认目标实例是否正确，第二次确认是否现在执行删除；不要复用历史确认。
  (5) 删除前先用 `instance list` / `instance search` 确认目标实例当前仍存在且唯一，避免用过期 pod 名或模糊匹配结果直接删。
  (6) 删除前先检查剩余实例数量与状态；如果无法确认删除后仍有足够健康副本，尤其是 prod / 单副本 / 低副本场景，先提示风险并暂停，等待用户明确继续。
  (7) 删除后必须重新执行实例查询，确认 replacement / remaining pods 状态，再继续任何下一步操作；如果删除后状态异常，不要继续串行删第二个。
  (8) 不要把实例删除和 `cluster update`、扩缩容、deployment 操作并发混用；有正在进行的发布或变更时，优先提醒用户存在叠加风险。
- **`instance download` 下载规则**：当前只支持 `--site cn`，远端文件必须位于 TCE 官方允许目录；执行前先用 `instance list` 确认唯一 Pod/容器和远端路径。下载默认最多 10 MiB，可用 `--max-bytes` 调大；命令流式写入输出目录中的本地临时文件，校验响应长度并计算本地 SHA-256，成功后才原子落盘。默认不覆盖已有本地文件，明确需要覆盖时才传 `--force`。一次性 relay 签名 URL 不会出现在成功输出中。

### 资源定位参数

- `service get`、`cluster list`、`deployment list` 都支持 `--psm`；如果同一 PSM 在多个 env 下都有服务，可加 `--env` 做唯一定位
- `service check-repos`、`cluster reset/update` 也支持 `--psm [--env]`；正式请求省略 `--env` 时按 `prod` 发送，`cluster reset/update --preflight` 则不补默认环境。`cluster reset/update` 的服务选择器和集群选择器彼此独立，可以组合 `--service-id + --cluster-name` 或 `--psm [--env] + --cluster-id/--cluster-name`
- `cluster list --cluster-name` 可按集群名过滤结果；当同一 vregion 下存在多个同名集群时，建议和 `--service-id` 或 `--psm --env` 一起使用
- **PPE 环境**：当 `--env` 值匹配 `ppe` 或 `ppe_*` 时，bytedcli 自动按 PPE 环境查询，无需显式传 `--ppe`。拿到 PPE service ID 后，`deployment list`、`cluster update`、`instance list` 等命令直接用 `--service-id`
- 实例迁移沿用 `instance delete` 命令，调用 `DELETE /open-apis/v1/pods/`；需要同时传 `--cluster-id`、`--idc`、`--pod-name`；推荐先 `--dry-run` 检查 DELETE 请求，默认会要求交互确认，非交互场景可显式加 `--yes`

### 分页与输出

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json tce instance list --psm example.service.api --env prod ...`）；返回信封结构见上方「输出结构（--json）」
- `instance list` 推荐使用 `--psm + --env` 组合；兼容方式也支持 `--service-id`
- `instance list --node-ip` 可按 node IP 过滤服务实例；仅支持和 `--service-id` 或 `--psm --env` 一起使用，不支持 `--cluster-id`
- `instance list` 的文本表格会展示 `IDC` 列；按 `--node-ip` 排查时可直接看到实例所在机房
- `instance list --ordering` 支持 `cpu/mem/idc/createtime/podstatus`，带 `-` 前缀表示倒序

### 站点与别名

- Flag renames: `--page-num` is now `--page`; old name still works as a hidden alias
- 使用全局 `--site` 选择站点（`cn|boe|byteintl|ttp-us-limited|ttp-eu`），不传则默认跟随 `BYTEDCLI_CLOUD_SITE`。Per-service `--tce-site` is a hidden alias for backward compatibility.
- 常用别名：`prod=cn`、`i18n=byteintl`、`tx-ttp=ttp-us-limited`、`eu-ttp=ttp-eu`

### WebShell

- `tce webshell` 适合在 `instance list` / `deployment get` 已经定位到目标 pod 之后做补充排障；agent 优先使用 `auth login --begin --session --session-method qr --no-terminal-qr` + `auth login --complete <token>` 准备浏览器态 SSO session，再使用 `tce webshell open/exec/close`，人用交互场景再使用 `tce webshell interactive --psm --env`。BOE webshell 若返回 SSO HTML 或 `invalid JSON response`，通常需要额外补一次 `--site cn` 的 session。

## References

- `references/tce.md`

## Pod readiness 诊断

用实时实例列表中的精确 Pod 名调用 `tce instance diagnose --pod-names <comma-separated-names>`；沿用当前 CLI 身份配置与目标 site/vregion，不更换身份或扩大查询范围。该命令只读取检查证据，不重启、迁移或发布 Pod。

JSON 的 `data.pods[]` 保留 `podName`、`format`、`msg` 和 `checkList[]`；检查项包含 `name/stage/status/msg/oncall/docLink/docTitle`。`format=false` 或空检查列表表示缺少结构化证据，应保留原始消息。`missingPodNames` 明确标记请求但未返回的 Pod。缺省消息和文档字段稳定输出 `null`。查询 `status=success` 只表示接口读取成功；failed、pending、未知状态或缺失证据均不能据此宣称 Pod 已就绪。
