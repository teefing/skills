# TCE

## 站点

```bash
# 列出支持的站点
bytedcli tce list-sites
```

在 ByteDance 生产网络内使用 `--site i18n-tt` 时，设置 `BYTEDCLI_NETWORK_PROFILE=prod`，TCE OpenAPI 与 ByteCloud JWT host 会自动切到生产网可达的 `cloud-i18n.bytedance.net`。

## 服务查询

```bash
# 收藏的服务
bytedcli tce service list --page 1 --page-size 10

# 搜索服务
bytedcli tce service search --keyword "keyword" --env "ppe_xxx" --page 1 --page-size 10

# 获取服务详情（也支持 --psm + 可选 --env）
bytedcli --site cn tce service get <service_id>
bytedcli --site cn tce service get --psm example.service.api --env prod

# 列出服务集群（支持 --service-id 或 --psm）
bytedcli --site cn tce cluster list --service-id <service_id> --page 1 --page-size 10
# 集群列表两种视图（默认聚合 vs. IDC 明细）

# 1）默认视图（聚合，加权汇总，每个集群一行；IDC 列隐藏）
bytedcli --site cn tce cluster list --psm example.service.api --env prod --page 1 --page-size 10
bytedcli --site boe tce cluster list --service-id 234558 --cluster-name tls_mix_proxy_boe --page 1 --page-size 10

# 2）IDC 明细视图（每个集群 × IDC 一行）
bytedcli --site cn tce cluster list --psm example.service.api --env prod --with-idc --page 1 --page-size 10
# 列出 PPE 集群（--env ppe_* 自动推断 PPE 环境，无需显式传 --ppe）
bytedcli --site ttp-us-limited tce cluster list --psm example.service.api --env ppe_rd_test_env --page-size 100
```

### 服务负责人字段

查询服务负责人读 `data.auth.iam_info.owners[]`（每项含 `username`、`email`，保留完整列表）；`auth.owner_name` 是 GDPR/ZTI 鉴权用户名、`auth.owner` 为已废弃 ID，均非负责人。`owners` 缺失或为空时如实说明未返回 IAM owner，不要用这两个字段兜底。

## 集群预检使用方法

`cluster create/reset/update/upgrade/scale --preflight` 分别调用独立的预检接口。Agent 应将用户已经明确提供的业务值带入对应命令，使用全局 `--json` 读取结果；允许空请求或部分请求，不为缺失字段猜测服务、集群、版本、容量或模板。各命令支持的输入和示例见下方对应 Preflight 小节。

预检不会创建工单、锁定资源或保留配额。CLI 不生成 `client_token`，不向预检接口发送 `dry_run`，也不套用正式提交的业务默认值；没有前置阻断项时，**后端在预检内部执行正式提交路径的 DryRun**，将实际计划放入 `preview`。CLI 的 `--dry-run` 只用于查看本地构造的正式请求，不能提供动态候选或后端计划；完成同一请求的预检后，无需为后端校验再单独调用 `--dry-run`。

按以下顺序处理标准 JSON 信封中的 `data`：

1. `status=success` 且 `data.can_submit=false`、`block_reason=request_invalid`：根据 `constraints[]` 中 `blocking=true` 的 `code/field/message` 补充或修正输入，再运行同一命令的预检。`blocking=false` 的非阻断项也要展示，它可能说明默认行为、被忽略字段或风险。
2. `status=error` 且 `data.block_reason=submission_rejected`：结合后端错误与保留的预检报告修正请求，再次预检。`permission_denied` 或 `policy_blocked` 时停止提交并说明拒绝原因；401、取消、超时等未形成报告的错误不能当作空报告，更不能改用正式写接口试错。
3. 用 `options` 选择当前条件下的动态候选，由用户决定有业务影响的值；候选为空不代表没有合法值，`recommended` 也不表示已替用户选择。Reset 响应没有 `options`。`current_state` 是已查询到的配置和能力，不是补全后的请求或执行结果；例如扩容按配置容量 `count` 计算，不按实时 Running Pod 数计算。
4. `data.can_submit=true` 后核对 `preview` 中的实际目标、版本、容量、模板和发布策略，并展示非阻断提示。`preview=null` 或缺少关键计划时，明确说明哪些内容无法核对，展示已知请求与 `current_state`，由用户决定是否接受信息不足；目标或影响范围仍不清楚时不提交。`preview=null` 不能解释为没有变更。
5. 用户确认本次计划后，保留已确认的业务参数，移除 `--preflight`，按正式命令要求显式加 `--yes` 提交。正式接口会重新校验；`can_submit=true` 不是授权，也不保证提交成功。提交后读取工单终态说明结果，不能把预检计划当作执行结果。

`--preflight` 与 `--dry-run`、`--yes` 互斥；Update、Upgrade、Scale 还不能与 `--wait` 同用。输入格式或参数类型错误由 CLI 直接返回，不会形成后端报告。

## 服务与集群创建

`service create/update/delete` 与 `cluster create/reset/update/upgrade/scale/restart` 的 `--dry-run` 预览本地构建的正式请求；必要的只读查询仍可能发生。真实提交须经用户确认并显式传 `--yes`。各集群命令的预检用法见下方对应章节。

**工单幂等 Token：**`service create/update/delete` 与 `cluster create/reset/update/upgrade/scale/restart` 在内部生成 UUIDv4 `client_token`，并仅为这些已有 Token 契约的工单提交启用 HTTP 重试。同一条命令的所有重试复用同一个请求体和 Token。Token 不作为 CLI 参数或用户输出，也不支持跨进程复用。`deployment action/cancel/execute-step`、`instance delete`、`instance force-delete`、`service check-repos`、`deploy-lane` 不自动重试。

```bash
# 创建服务：service_info 建议来自平台推荐模板或控制台导出的 payload
bytedcli tce service create --service-info-file service-info.json --dry-run
bytedcli tce service create --service-info-file service-info.json --yes

# 更新 / 删除服务
bytedcli tce service update --service-id <service_id> --update-info-file update-info.json --dry-run
bytedcli tce service delete --service-id <service_id> --request-file delete-request.json --dry-run

# 查询和校验服务可用 SCM 包
bytedcli tce service repo-info-list --service-id <service_id>
bytedcli tce service check-repos --service-id <service_id> --request-file check-repos.json --dry-run
bytedcli tce service check-repos --psm example.service.api --env prod --request-file check-repos.json --dry-run

# 正式创建 / 删除集群：cluster_info 建议来自预检候选、平台推荐模板或控制台导出的 payload
bytedcli tce cluster create --service-id <service_id> --cluster-info-file cluster-info.json --dry-run
bytedcli tce cluster create --psm example.service.api --env prod --cluster-info-file cluster-info.json --yes
bytedcli tce cluster reset --service-id <service_id> --cluster-id <cluster_id> --dry-run
bytedcli tce cluster reset --service-id <service_id> --cluster-name default --dry-run
bytedcli tce cluster reset --psm example.service.api --env prod --cluster-name default --dry-run
bytedcli tce cluster reset --service-id <service_id> --cluster-id <cluster_id> --yes
```

`check-repos.json` 只包含 `repos` 和 `cluster_ids`；服务选择器写入 URL path，不要在 JSON body 中添加 `service_id`。`service create/update/delete/check-repos` 的正式 `--request-file` 不接受顶层 `dry_run`（即使值为 `false` 或 `null`），应使用 CLI `--dry-run`；`service_info` / `update_info` 等嵌套业务对象中的同名字段原样保留。`service check-repos` 使用 `--psm` 且省略 `--env` 时，bytedcli 按 `prod` 发送；正式 `cluster reset/update` 使用 PSM selector 且省略环境时也会补 `env=prod`，对应 preflight 不补默认环境。`cluster reset/update` 的服务选择器和集群选择器彼此独立，名称由 TCE 后端解析；名称不唯一时会原样返回候选集群信息。

### 服务输入文件与字段治理

服务 create/update/delete/check-repos 没有后端 preflight。`--dry-run` 只显示 CLI 在本地组装的正式请求，不检查 PSM、ByteTree、IAM、镜像、仓库权限或业务必填项；真实提交仍由后端校验。create/update 的 JSON 文件继续 raw pass-through，delete 不增加业务字段约束；check-repos 在本地校验 `cluster_ids` 为整数数组、`repos` 为对象数组，以及已提供且非 `null` 的 `repos[].name/version` 为字符串；两个数组可省略或为 `null`。未知扩展字段保持原样，已知字段保留符合类型约定的值，包括允许的 `null`、`0` 和空数组；BAM schema 的 optional 只表示传输层字段可省略，不代表创建业务一定允许缺失。

#### 文件模式与覆盖关系

| 命令                  | 局部文件模式                                                                    | 完整请求模式                                                               | 覆盖关系                                                                                                     |
| --------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `service create`      | `--service-info-file` 的根对象就是 `service_info`                               | `--request-file` 根对象含 `service_info`，也可含 `note/purpose/source_url` | 两者同时提供时只读 `--request-file`；显式工单 option 覆盖完整请求同名字段，不做深度合并                      |
| `service update`      | `--update-info-file` 的根对象就是 `update_info`，服务 ID 由 `--service-id` 注入 | `--request-file` 根对象含 `service`、`update_info` 和可选工单元数据        | 两者同时提供时只读 `--request-file`；`--service-id` 总是覆盖文件 `service`，显式工单 option 覆盖文件同名字段 |
| `service delete`      | 无局部文件模式                                                                  | `--request-file` 根对象是完整删除请求，不包 `service_info/update_info`     | `--service-id` 总是覆盖文件 `service`；非空工单 option 覆盖文件同名字段；`client_token` 由 bytedcli 生成     |
| `service check-repos` | 无局部文件模式                                                                  | `--request-file` 根对象是 `{cluster_ids, repos}`                           | `--service-id` 或 `--psm [--env]` 写入 URL path；文件中的顶层 `service_id` 会被删除，不参与请求              |

create/update 只有非空的 `--note`、`--purpose`、`--source-url` 才覆盖完整请求中的同名元数据；未传或传空值时保留文件值。

create 的完整请求包装示例：

```json
{
  "service_info": {
    "meta": { "psm": "example.service.api", "env": "prod" }
  },
  "note": "demo service create"
}
```

update 的完整请求包装示例：

```json
{
  "service": 123456,
  "update_info": { "runtime": { "period_seconds": 10 } },
  "note": "demo service update"
}
```

#### 最小 create 结构起点

以下是 SCM/default 模式的最小结构起点，不是后端业务必填项的替代品。`example.*`、`demo-*`、`sample-*` 均为占位值，必须替换为用户确认的实际目标：

```json
{
  "meta": { "psm": "example.service.api", "env": "prod" },
  "build": {
    "base_image": "sample-base-image",
    "dependency_mode": "default",
    "framework_support": "none",
    "scm_repo_info": [
      {
        "name": "demo-repo",
        "path": "demo-org/demo-repo",
        "main_repo": true
      }
    ]
  },
  "runtime": {
    "app_path": "bin/start.sh",
    "new_ports": [{ "intent": "primary", "is_primary": true, "port": 8080 }]
  }
}
```

保存为 `service-info.json` 后先本地预览，再由用户确认是否提交：

```bash
bytedcli tce service create --service-info-file service-info.json --dry-run
bytedcli tce service create --service-info-file service-info.json --yes
```

依赖模式条件：

- `build.base_image` 是基础镜像字符串，BAM 注释要求非空；bytedcli 没有基础镜像候选查询命令，应由用户按 TCE 镜像能力或已确认配置提供。
- `build.dependency_mode=default` 是 SCM 模式。按业务提供 `build.scm_repo_info[]`，并用 `runtime.app_path` 指定启动脚本路径；路径填写时去掉 `/opt/tiger/` 前缀。`framework_support` 可按业务选 `none` 或 `script`，不能猜测。
- `build.dependency_mode=manifest` 是 manifest/image 模式。`build.scm_repo_info` 不参与该模式，`runtime.app_path` 可省略；`build.framework_support` 必须为 `none`。镜像或 manifest 的目标值来自 TCE 镜像/manifest 平台能力或用户已确认配置，当前没有 service create preflight 或 CLI 候选命令，禁止根据历史值猜测。
- `runtime.new_ports[]` 的 primary 端口放第一项；`port` 是整数端口号，`intent` 可表达 `primary/debug/other/health`。BAM 仅声明当前协议为 TCP，`type` 是 read-only，不写入请求。

#### 单字段 update

先用 JSON 模式读取目标服务，确认 `.data.service_id` 和 `.data.meta/.auth/.build/.runtime/.upgrade/.extra_features` 当前值：

```bash
bytedcli --json tce service get --psm example.service.api --env prod
```

只更新健康检查周期时，`update-info.json` 可仅包含：

```json
{ "runtime": { "period_seconds": 10 } }
```

`period_seconds` 单位为秒；不要把它写成 `"10s"`。然后使用上一步返回的数字 service ID：

```bash
bytedcli tce service update --service-id <service_id> --update-info-file update-info.json --dry-run
bytedcli tce service update --service-id <service_id> --update-info-file update-info.json --yes
```

update 只提交用户明确要改的字段；不要把 `service get` 的整个响应回写成 `update_info`。当前值只用于核对和选择写入值。

#### delete 完整请求

`delete-request.json` 是完整删除请求，不要再包 `service_info` 或 `update_info`。最小文件如下：

```json
{
  "service": 123456
}
```

先通过必填的 CLI service ID 预览文件；该 ID 始终覆盖文件中的 `service`：

```bash
bytedcli tce service delete --service-id <service_id> --request-file delete-request.json --dry-run
```

文件还可包含 `note`、`purpose`、`source_url` 等工单元数据。非空 `--note`、`--purpose`、`--source-url` 会覆盖文件同名字段；未传这些 option 时保留文件值。`client_token` 由 bytedcli 为本次命令生成，文件中的值不会被使用，也不需要用户管理。文件顶层不得包含 `dry_run`（包括 `false` 或 `null`），本地预览统一使用 CLI `--dry-run`。不传 `--request-file` 时仍按 `--service-id` 构造原有最小删除请求。

#### check-repos 请求与取值来源

`check-repos.json` 的完整 body 示例：

```json
{
  "cluster_ids": [123456],
  "repos": [{ "name": "demo-repo", "version": "demo-version" }]
}
```

按以下实际 CLI 输出路径取值，不要凭名称猜测：

1. 运行 `bytedcli --json tce service repo-info-list --service-id <service_id>`。标准输出的 `.data` 是 `{service_id, repos, total}`；仓库候选在 `.data.repos[]`，从每项返回的 `repo_name`（兼容站点可能返回 `name`）和 `versions[].version` 中选择，再映射为 check-repos 的 `{name, version}`。如果某站点返回不同 raw 行结构，展示原始 `.data.repos[]` 并让用户明确选择，不自行变换或虚构版本。
2. 运行 `bytedcli --json tce cluster list --service-id <service_id>`，从 `.data.clusters[].meta.id` 取得数字 cluster ID。只发送用户要校验的目标集群，不把服务详情里的 read-only `runtime.cluster_ids` 整体复制进去。
3. `--service-id` 来自 `service get` 的 `.data.service_id`；也可直接使用用户给定的 PSM 与环境。使用 `--psm` 且省略 `--env` 时按 `prod` 发送。

`repos[].name` 与 `repos[].version` 的非 `null` 值是字符串；`cluster_ids` 提供且非 `null` 时必须是整数数组。bytedcli 在 `--dry-run` 预览和 `--yes` 提交前校验这些已知字段的基础类型，错误会指出 JSON 字段/数组索引路径；不会新增业务必填、正数范围或自动转换。`--dry-run` 仍只是本地预览，不代表仓库权限检查成功；真实检查必须经用户确认并显式使用 `--yes`。

#### 值来源与禁止猜测

| 字段或目标                                                 | 取值来源                                                                                                                           |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 新建 `meta.psm`                                            | 用户的服务唯一标识目标；需符合 TCE/ByteTree 业务约束。bytedcli 无“发现未创建 PSM”命令，不能从相似服务猜测                          |
| `meta.env`、服务名称、端口、启动脚本、健康检查、服务等级等 | 用户业务目标；若需验证平台能力，在 TCE 对应服务/运行时能力中确认。没有 CLI 候选时明确要求用户提供                                  |
| `auth.galaxy_info.parent_id`                               | ByteTree 父节点能力；省略时平台会尝试自动解析。显式填写时由用户从 ByteTree 获取，当前没有 TCE CLI 查询命令                         |
| IAM owners/operators/groups、鉴权与合规字段                | 用户从 ByteCloud IAM、GDPR/ZTI 或服务合规配置中确认；更新时可先看 `service get` 当前值，但不能自动推断新负责人、敏感级别或数据区域 |
| `build.base_image`、manifest/image、依赖模式               | TCE 镜像/manifest 与构建能力或用户已确认配置；当前 service 命令不提供候选发现                                                      |
| 更新目标 service ID 与当前配置                             | `service get` 的 `.data.service_id` 和对应配置对象                                                                                 |
| check-repos 的 repo name/version                           | `service repo-info-list` 的 `.data.repos[]`                                                                                        |
| check-repos 的 cluster ID                                  | `cluster list` 的 `.data.clusters[].meta.id`                                                                                       |

#### writable、read-only 与 deprecated 字段

已知可写字段仍需以后端业务规则为准：

- `meta`: `psm`（创建目标）、`name`、`env`、`host_type`、`tags`、`template`、`tlb_url`。
- `auth`: `approval_controls`、`authorization_type`、`owner_name`、`product_group/product_group_name`、`risk_control`、`galaxy_info.parent_id`，以及 IAM 的 `owners/operators/pocs/authorized_groups` 标识。
- `build`: `base_image`、`dependency_mode`、`enable_forbidden_pyc`、`framework_support`、`install_package_info[].name/type`、`scm_repo_info[].main_repo/name/path`。
- `runtime`: `app_path`、`enable_iast`、`enable_same_cluster`、`failure_threshold`、`health_check_path`、`is_runtime`、`mount_info`、`new_ports[].intent/is_primary/port`、`period_seconds`、`umount_ss_conf`。
- `upgrade`: `rollback_surge_percent`。
- `extra_features.service_token`: `contain_user_personal_info`、`data_sensitivity_level`、`level`、`personal_info_creation_region`、`purpose`、`deploy.type`、`deploy.scale/descale.enable/reason`、`tech_stack.framework/language/platform_types_v_2`。

read-only 字段只用于读取当前状态，不应复制进 create/update：

- `meta.create_time/update_time/is_subscribe/last_deploy_ticket/service_url/service_cloud_url/status/status_display/tags_display`；`meta.id` 作为服务标识由 request-level `service` / `--service-id` 选择。`meta.is_sensitive` 还是已下线字段。
- `auth.galaxy_info.node_id/path_display/path_url`、`auth.iam_info.edit_url`、IAM user 的 `email`、authorized group 的 `display/name`。
- `build.service_inline_role`、`build.scm_repo_info[].remote_id`。
- `runtime.cluster_ids/image_version/latest_repo_info/new_ports[].type`。
- `upgrade.upgrade_url`。

不要在新请求中新增 deprecated 字段：

- `auth.owner`、`auth.iam_info.authorized_groups[].id`。
- `build.language/tech_stack`、`build.install_package_info[].id`，以及 `build.scm_repo_info[]` 的 `description/disable_notify/id/need_compile/need_notify/runtime_type/scm_branch/scm_repo_id/version/version_id`。
- `extra_features.enable_sidecar`、`extra_features.service_token.tech_stack.type`。
- `runtime.allowed_host_types/enforce_ha/host_type/is_service_hostuniq/service_hostuniq_num/splits_param`。
- `upgrade.update_rely`。

单位与取值提示：

- `runtime.period_seconds` 是秒；`runtime.failure_threshold` 是连续失败次数，BAM 标注默认值 `0`、业务范围 `1~100`，不要自行修正矛盾值，交由用户与后端确认。
- `upgrade.rollback_surge_percent` 是百分比整数；`runtime.new_ports[].port` 是整数端口号。
- `build.install_package_info[].type` 支持 BAM 声明的 `apt-ge`、`pip`、`pip3`；`authorization_type` 可用 `user` 或 `service`（默认/推荐为 `service`）；`service_token.data_sensitivity_level` 为 `L1~L4`，`level` 为 `P0~P3`。CLI 不在运行时增加枚举或范围校验。

### Create Preflight（只读发现）

`cluster create --preflight` 调用独立的 Create Preflight 接口，不创建工单、不生成 `client_token`、不发送 `dry_run`，也不会执行版本查询、提交或轮询。请求可以为空，也可以只提供服务 selector、`env`、`cluster_info` 或创建开关；`can_submit: false` 在 HTTP 与业务 envelope 成功时仍是成功报告。HTTP / 业务失败保持非零退出码，响应内若含有效报告则保留在错误输出的 `data` 中。

以下使用 PSM 的示例均显式传 `--env prod`；目标不是 prod 时，替换为用户指定的实际环境，避免预检环境与正式创建的默认环境不一致。

```bash
# 空请求、仅提供服务与环境、或提供完整请求文件，逐步发现创建条件
bytedcli --json tce cluster create --preflight
bytedcli --json tce cluster create --psm example.service.api --env prod --preflight
bytedcli --json tce cluster create --request-file create-request.json --preflight
```

- 服务 selector 最多一个（`--service-id` / `--psm`）。预检允许 `--env` 单独作为部分输入，且不会自动补 `prod`；正式创建要求合并后的请求恰好包含一个 `service` 或 `psm`、包含 object 类型的 `cluster_info`，使用 PSM 且未提供环境时才补 `env=prod`。
- `--request-file` 优先于 `--cluster-info-file`，两者同时提供时不会读取后者，也不会深度合并。显式 `--service-id` 或 `--psm` 会整体替换文件中的 `service` / `psm` / `env`，随后再应用显式 `--env`；`--note`、`--purpose`、`--source-url`、`--quick-create`、`--sync-slots`、`--need-sast-check` 等显式值覆盖文件字段，并保留 `false`、`0` 与未知扩展字段。预检会剥离文件顶层的 `client_token` 和 `dry_run`。
- Create Preflight、正式 `--dry-run` 与提交共用同一宽松输入类型检查。CLI 只校验已填写的已知字段，类型错误返回 `TCE_INPUT_ERROR` 及完整 JSON 字段路径；同时定点拒绝会被后端静默忽略的 `cluster_info.name`、`runtime.env_lst` 和环境变量条目 `name` / `value`，hint 会给出正确字段与 JSON 示例。各层对象仍允许未知扩展，已建模的可选嵌套字段可显式为 `null`，`0`、`false`、空数组和扩展值不会被清空或规范化。该检查不增加必填项、默认值、枚举、配额或动态业务约束，最终仍以后端 constraints / `can_submit` 为准。
- `current_state.quick_create_supported` 表示 Quick Create 是否可用；`current_state.placement_quotas` 是服务端配额快照。`balances: null` 表示未知，`available: 0` 表示已知为零，负值也原样保留；VDC 聚合 `balances` 与 `unit_quotas[].balances` 是不同层级，不做相加、推断或过滤。
- `options.vregions`、`placements[].idcs[].resource_profiles`、`packages[].details`、`image_versions` 与 `repo_versions` 都是候选项，只供展示和显式选择。CLI 不做配额或调度判断，也不自动选取候选。
- `preview.cluster_info`、`preview.repo_info`、`preview.package_info` 保留服务端复杂配置和扩展字段；成功报告也可能没有 `preview` 或返回 `preview: null`。非阻断 `PREVIEW_UNAVAILABLE` 只表示无法生成预览，不等于没有变更。
- Quick Create 可能用最新历史镜像覆盖显式依赖；没有历史镜像时保留调用方提供的依赖。以服务端 `constraints` / `preview` 提示为准，不要根据候选自动提交。
- `--preflight` 与 `--dry-run` / `--yes` 互斥。预检后可由用户选择是否再执行正式 create `--dry-run`；真实提交仍必须经用户确认并显式传 `--yes`。

#### 创建文件结构与最小配置

`--cluster-info-file` 读取的文件根对象就是 `cluster_info`，不要再包一层 `cluster_info`。`--request-file` 读取完整请求，外层放 `service`，或 `psm` / `env`，以及 `cluster_info`。两者同时提供时 `--request-file` 优先，不读取 `--cluster-info-file`；显式 `--service-id` / `--psm` 按现有覆盖规则替换文件 selector，其他显式创建开关覆盖同名文件字段。预检可从部分请求开始，并根据后端约束逐步补充字段。

可作为 `cluster-info.json` 结构起点的最小对象如下。`sample-*` 位置值仅用于说明结构；实际运行前必须从目标服务本次预检的 `options` 取得候选并由用户显式选择，禁止直接运行占位值：

```json
{
  "meta": { "name": "demo-cluster" },
  "resource": {
    "zone": "sample-zone",
    "physical_cluster": "sample-physical-cluster",
    "logical_cluster": "sample-logical-cluster",
    "cpu": 1,
    "mem": 1
  },
  "runtime": {
    "replicas": {
      "dc_info": [{ "idc": "sample-idc", "count": 1 }],
      "canary_dc_info": []
    }
  }
}
```

完整 `create-request.json` 使用同一个 `cluster_info`，只在外层增加服务 selector；例如：

```json
{
  "psm": "example.service.api",
  "env": "prod",
  "cluster_info": {
    "meta": { "name": "demo-cluster" },
    "resource": {
      "zone": "sample-zone",
      "physical_cluster": "sample-physical-cluster",
      "logical_cluster": "sample-logical-cluster",
      "cpu": 1,
      "mem": 1
    },
    "runtime": {
      "replicas": {
        "dc_info": [{ "idc": "sample-idc", "count": 1 }],
        "canary_dc_info": []
      }
    }
  }
}
```

字段类型与单位：

- 集群名必须写在 `meta.name`；不要写顶层 `cluster_info.name`，即使同时存在 `meta.name` 也会按错位字段报错。名称由字母、数字、中划线 `-`、下划线 `_` 组成，首尾必须是字母或数字；BAM schema 中的 optional 只表示传输层可省略，不代表创建业务一定接受缺失。
- `resource.cpu` 是 CPU 核数，`resource.mem` 单位是 GiB；两者均为 number。`resource.zone`、`physical_cluster`、`logical_cluster` 与 CPU / mem 是创建接口注释要求的基础字段，但 CLI 仍允许部分预检请求。
- `runtime.replicas` 是对象，不是副本数字；`dc_info[]` / `canary_dc_info[]` / `env_info[]` 的 `count` 是整数，IDC 副本使用字符串 `idc`。不要使用 `runtime.count` 或把 `replicas` 写成 number。
- `runtime.repo_info[]` 的 `remote_id`、`name`、`version`，`image_version` / `image_tag` 及 `env_list[]` 的 `env_name` / `env_value` 都是字符串；环境变量列表字段是 `env_list`，不是 `env_lst`，条目键也不要缩写成 `name` / `value`。`extra_features.feature_gates` 是 string map。
- `resource.provider` 是字符串，`runtime.vdc_agnostic` 是 boolean；副本项的 `quota_op.type` / `to_psm` 是字符串，`runtime.repo_info[].merge_build[]` 的 `down_repo_id` 是整数、其余已声明字段是字符串。BAM 的 int / i64 字段只接受整数，但 CLI 不增加正数、范围或枚举约束。只有 runtime schema 已覆盖的核心字段会在本地报告类型路径；高级字段必须通过 Create Preflight 验证。
- 按候选需要补充 `resource.vregion`、`resource.resource_quality` 与 `resource.sale_mode`；不要在没有后端候选的情况下猜值。

#### Sidecar、卷、调度与只读字段

本地 runtime schema 只检查上面的核心字段。`sidecar`、卷、自动扩缩容/调度等高级对象会原样传给后端，字段名和静态类型可帮助构造 JSON，但不代表 CLI 已验证平台能力、枚举、配额或引用 ID。每次修改后都必须重新运行 Create Preflight。

先用 `cluster list` 读取当前集群；当前没有 `cluster get` 命令。JSON 信封中的来源路径是 `.data.clusters[]`：

```bash
bytedcli --jq '.data.clusters[] | {meta, resource, runtime: {local_volumes: .runtime.local_volumes, bytedrive_volumes: .runtime.bytedrive_volumes, bytenas_volumes: .runtime.bytenas_volumes, hostuniq_affinity: .runtime.hostuniq_affinity, auto_scale_conf: .runtime.auto_scale_conf}, sidecar, traits: .extra_features.traits}' \
  tce cluster list --psm example.service.api --env prod --cluster-name default
```

该响应用于核对当前值，不是可直接回写的 payload：`meta.id/status`、资源 usage、`runtime.slot_info`、`extra_features.traits` 等是只读状态，废弃字段也不应复制到 create/update。高级输入来源如下：

- `runtime.local_volumes[]` 使用字符串 `mount_point` / `mount_type` 与整数 `size`（GiB）；`bytenas_volumes[]` 使用字符串 `idc` / `mount_path` / `volume`；ByteDrive map value 与卷 `size` 是整数。卷名、集群和挂载能力来自目标平台的卷配置或用户明确提供的已批准值，当前 CLI 没有卷候选发现命令。
- `runtime.hostuniq_affinity` 是用户选择的平台调度策略（`affinity`、`anti-affinity`、`shard-anti-affinity`）；`auto_scale_conf` 的 IDC key、窗口、阈值和上下限来自目标集群支持的自动扩缩容能力。不要从其他集群猜测或默认复制。
- `sidecar.service_mesh*` 的开关是 boolean；`sidecar_instances_data[]` 的 sidecar/spec ID 和参数必须来自目标平台的 Sidecar 能力或用户明确输入。当前 Create Preflight 不返回独立 Sidecar 候选列表。
- `quota_op.type` 与 `to_psm` 来自用户明确选择的资源预留/释放操作和目标 PSM；当前 CLI 没有 quota operation 候选命令。`repo_info[].merge_build[]` 来自目标 SCM/构建平台提供的合并编译元数据，Create Preflight 的 `options.repo_versions[]` 不等于完整 `merge_build`，不得自行拼接。
- `extra_features.traits`、副本 `all_dc_info` / `vdc`、资源 usage 和 slot 信息是只读回显，不写入请求；带 `@deprecated` 语义的字段仅用于兼容读取。

最小高级对象示例只展示 wire shape；占位值必须替换为目标平台确认的值：

```json
{
  "runtime": {
    "local_volumes": [{ "mount_point": "/data", "size": 20 }],
    "bytenas_volumes": [
      { "idc": "sample-idc", "mount_path": "/mnt/shared", "volume": "sample-volume" }
    ],
    "hostuniq_affinity": "anti-affinity"
  },
  "sidecar": {
    "service_mesh": {
      "enable_sidecar_percent": 100,
      "sidecar_http_ingress_enable": true
    },
    "service_mesh_switch": { "enable_mesh_redis_egress_switch": true }
  }
}
```

用户选定候选后，将值填入请求文件中的 `cluster_info`，或直接填入 `--cluster-info-file` 对象：

| 预检候选                                                                  | `cluster_info` 中的目标字段                                                                                                |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `options.vregions[]`                                                      | `resource.vregion`                                                                                                         |
| `options.placements[]` 的 `vregion/zone/physical_cluster/logical_cluster` | `resource` 下的同名字段                                                                                                    |
| `placements[].idcs[].idc`                                                 | `runtime.replicas.dc_info[].idc` 或 `canary_dc_info[].idc`；普通/自定义调度为 IDC，默认智能调度为 VDC，使用返回的 `idc` 值 |
| `idcs[].resource_profiles[]`                                              | `resource.resource_quality` 与 `resource.sale_mode`，保持返回的组合                                                        |
| `options.packages[].name`                                                 | `resource.package`                                                                                                         |
| `options.image_versions[].version`                                        | `runtime.image_version`                                                                                                    |
| `options.repo_versions[]` 的 `repo_id/repo_name/versions[].version`       | `runtime.repo_info[]` 的 `remote_id`（字符串）、`name`、`version`                                                          |

配额未知不能当作零，不同资源池或 `quota_scene` 的余额不能相加。候选的 `vdc` 用于识别位置，不作为替代 `idc` 的请求字段。Create Preview 是尚未持久化的配置，不代表已创建集群或实时运行状态。

#### 用 `--jq` 分步读取候选与预览

`--jq` 是全局参数，放在 `tce` 前面并自动启用 JSON 输出。它用于有针对性地投影完整信封，不应使用数组切片或 `head` 强制截断候选；需要保存全部原始字段时去掉 `--jq`，使用 `--json` 读取完整响应。以下示例以 `env=prod` 为例，目标是其他环境时必须替换。

1. 先用服务与环境读取 `vregions`，向用户展示全部候选并选择 `resource.vregion`：

```bash
bytedcli --jq '.data | {can_submit, constraints, vregions: .options.vregions}' \
  tce cluster create --psm example.service.api --env prod --preflight
```

2. 把选定的 vregion 写入部分请求文件；`sample-vregion` 必须替换为上一步的真实候选：

```json
{
  "psm": "example.service.api",
  "env": "prod",
  "cluster_info": {
    "resource": { "vregion": "sample-vregion" }
  }
}
```

再用该文件获取 `placements`。这里只投影三项定位值，避免提前展开所有 IDC 与资源规格，但不截断 placement 候选：

```bash
bytedcli --jq '.data | {can_submit, constraints, placements: [.options.placements[]? | {zone, physical_cluster, logical_cluster}]}' \
  tce cluster create --request-file create-request.json --preflight
```

3. 用户选择 placement 后，把 `zone`、`physical_cluster`、`logical_cluster` 与已有 `vregion` 一起写入 `cluster_info.resource`，再次预检对应的 IDC 与资源规格：

```bash
bytedcli --jq '.data | {can_submit, constraints, idcs: [.options.placements[]?.idcs[]? | {idc, resource_profiles}]}' \
  tce cluster create --request-file create-request.json --preflight
```

4. 将用户选定的 `idc`、`resource_quality`、`sale_mode` 与所需 `cpu` / `mem` / `count` 写入请求，并按创建模式读取全部依赖候选；不自动采用第一个候选或 `recommended`：

```bash
bytedcli --jq '.data.options | {packages, image_versions, repo_versions}' \
  tce cluster create --request-file create-request.json --preflight
```

5. 填好普通、镜像或 Quick Create 所需依赖后，再核对阻断项和最终计划；`preview` 为 `null` 时仍如实保留：

```bash
bytedcli --jq '.data | {can_submit, block_reason, constraints, preview}' \
  tce cluster create --request-file create-request.json --preflight

# 完整原始信封始终可获取
bytedcli --json tce cluster create --request-file create-request.json --preflight
```

#### 普通、镜像与 Quick Create 预检流程

1. **普通流程**：按上述五步填入位置、CPU / mem、副本和当前服务要求的包或 SCM 依赖。只有本次报告返回 `can_submit=true`，且 `preview.cluster_info/repo_info/package_info` 足以核对服务端补齐的依赖时，才可接受本次请求中未显式填写的依赖；不能据此推断其他服务也可省略。
2. **镜像流程**：从 `options.image_versions[]` 选择版本并写入 `runtime.image_version`，重新预检。`image_tag` 依服务端 preview 与实际契约决定，禁止从 `image_version` 字符串拼接；若报告要求额外镜像字段，按 constraint 或后端候选补充。
3. **Quick Create**：仍需提供可预检的 `cluster_info` 并显式加 `--quick-create`。历史镜像存在时，后端可能补齐或覆盖依赖；没有历史镜像时不能保证自动生成依赖。始终核对 `current_state.quick_create_supported`、constraints 和完整 preview。

```bash
# 普通流程；create-request.json 显式包含 psm、env=prod 与完整 cluster_info
bytedcli --json tce cluster create --request-file create-request.json --preflight

# 镜像流程：image-create-request.json 增加后端候选的 runtime.image_version
bytedcli --json tce cluster create --request-file image-create-request.json --preflight

# Quick Create 流程
bytedcli --json tce cluster create --request-file create-request.json --quick-create --preflight
```

三种流程都以 `can_submit`、blocking / non-blocking constraints 和 preview 为准。候选 `recommended` 只表示后端推荐，不代表用户授权自动选择；配额候选未知不等于零；`preview=null` 时不能假造配置模板或解释为没有变更。达到 `can_submit=true` 后仍只完成只读预检，不创建工单或集群。

### Reset Preflight（只读删除检查）

`cluster reset --preflight` 调用独立的 Reset Preflight 接口，不创建删除工单、不生成 `client_token`、不发送 `dry_run`，CLI 也不额外发起服务或集群目标查询、提交或轮询；TCE 后端仍会解析请求中提供的 selector。请求可以为空，也可以只提供部分服务、环境、集群 selector 或工单字段。Reset Preflight 报告不提供 `options` 候选项；`can_submit: false` 在 HTTP 与业务 envelope 成功时仍是成功报告。HTTP / 业务失败保持非零退出码，响应内若含有效报告则保留在错误输出的 `data` 中。

```bash
# 空请求：先发现后端要求的 selector 与约束
bytedcli --json tce cluster reset --preflight

# 部分请求：逐步确认实际删除目标
bytedcli --json tce cluster reset --psm example.service.api --cluster-name default --preflight
bytedcli --json tce cluster reset --service-id <service_id> --cluster-id <cluster_id> --preflight
```

- 服务 selector 最多一个（`--service-id` / `--psm`），集群 selector 最多一个（`--cluster-id` / `--cluster-name`）。`--env` 可以作为非空的部分输入单独发送，预检不会自动补 `prod`。
- `current_state.cluster` 是当前目标快照；`preview.cluster_list` 是后端判定的删除目标，可包含逻辑/物理集群、区域、机房和 serverless 配置。`preview` 缺失、为 `null` 或 `cluster_list: null` 都不能解释为“没有删除目标”。
- Reset 会先将集群缩容到零，再永久删除集群。`can_submit: true` 只表示当前预检允许继续，不代表已授权、不保证正式提交成功，也不会自动触发删除。
- `--preflight` 与 `--dry-run` / `--yes` 互斥，且 Reset Preflight 不提供 `--wait`。正式 reset 仍要求恰好一个服务 selector 和一个集群 selector；使用 PSM 且省略环境时才补 `env=prod`，真实提交仍必须显式传 `--yes`。

### PPE 环境操作流程

PPE 服务的 service ID 与 prod 不同。当 `--env` 值匹配 `ppe` 或 `ppe_*` 时，bytedcli 自动按 PPE 环境查询，无需显式传 `--ppe`。
获取到 PPE service ID 后，其他所有命令（`cluster update`、`deployment list`、`instance list` 等）直接使用 `--service-id` 即可。

```bash
# 第 1 步：用 --env ppe_* 查到 PPE 服务和集群（自动推断 PPE，假设返回 service_id=100343）
bytedcli --site ttp-us-limited tce cluster list --psm example.service.api --env ppe_rd_test_env

# 第 2 步：后续命令直接用 --service-id
bytedcli --site ttp-us-limited tce deployment list --service-id 100343
bytedcli --site ttp-us-limited tce cluster update --cluster-id 305999 --service-id 100343 --update-info-file payload.json --yes
bytedcli --site ttp-us-limited tce instance list --service-id 100343
```

## 集群更新

### Update Preflight（只读发现）

`--preflight` 调用独立的 Update Preflight 接口，不创建工单、不轮询、不生成 `client_token`，也不发送 `dry_run`。本节适用于 `cluster update` 及其隐藏兼容别名 `cluster edit`；`cluster upgrade` 也支持独立预检，详见下方「Upgrade Preflight」。预检请求可以为空，也可以只提供部分 selector、`update_info` 或工单字段，用于逐步发现约束、当前状态和可用流水线模板。

```bash
# 空请求：先发现服务端当前要求的字段
bytedcli --json tce cluster update --preflight

# 部分请求：逐步补充目标和 update_info
bytedcli --json tce cluster update --psm example.service.api --cluster-name default --preflight
bytedcli --json tce cluster update --service-id <service_id> --cluster-id <cluster_id> --update-info-file payload.json --preflight
```

成功结果以 `can_submit`、`constraints`、`current_state`、`options`、`preview` 为核心：

- 只有 HTTP 成功且业务 `code` 未失败的 envelope 中，`can_submit: false` 才是成功的预检报告；根据 `constraints[].blocking/code/field/message` 修正输入，`block_tickets` 列出阻止提交的工单 ID。HTTP 或业务失败仍返回非零退出码，响应内若含有效报告则保留在错误输出的 `data` 中。
- `block_reason` 只会是 `request_invalid`、`submission_rejected`、`permission_denied`、`policy_blocked` 之一，用于区分请求无效、提交被拒、权限不足和策略阻断。
- `options.pipeline_templates` 用于发现当前请求可选或推荐的模板；模板 ID 可能为 `0`。候选项必须交由用户选择，不自动采用推荐值。
- `preview` 由服务端 DryRun 生成时，`cluster_list` 是实际更新的集群列表，每项的 `diff_info` 是对应差异；`pipeline_template` 是实际采用的模板，临时或内置模板的 `id` 可以为 `null`；`delay_release` 只表示 DryRun 工单配置了延迟上线，不是实际执行时间。`preview` 缺失或为 `null` 不能解释为“没有变更”。
- `can_submit: true` 不是授权结果，也不保证正式提交成功；正式 update 仍会执行权限和业务校验。
- `--preflight` 不能与 `--dry-run`、`--yes`、`--wait` 或 `--change-single-dc` 同用。正式 `--dry-run` 只预览本地请求；后端约束与实际计划以 Preflight 报告为准。
- Update Preflight、正式 `--dry-run` 与提交共用核心输入校验：提供的 `update_info.resource` 字段复用 create 类型，`cpu` / `mem` 等资源值必须是 number；提供的 `update_info.runtime.env_list` 条目复用 `env_name` / `env_value` 类型，`env_value` 为字符串或 `null`。集群名写在 `update_info.meta.name`，顶层 `update_info.name`、`runtime.env_lst` 及条目内 `name` / `value` 会在调用 API 前返回完整路径和修正示例。
- 该校验不把 update 整树改为 strict：空对象、缺失块、显式 `null`、部分环境变量条目以及 `resource` / `runtime` 中未建模的高级扩展仍原样透传，其他动态约束继续由 Update Preflight 判断。

#### Resource 更新示例

先用 `cluster list` 读取 `.data.clusters[].resource`，确认当前规格和目标集群；不要把 usage、`package_info`、`vregion` 等只读回显整体复制进 `update_info`：

```bash
bytedcli --jq '.data.clusters[] | {name: .meta.name, resource}' \
  tce cluster list --service-id <service_id> --cluster-name default
```

下面的 `update-resource.json` 只展示 CPU / 内存规格 wire shape；CPU 单位为核，内存单位为 GiB。是否还需保留 package、资源质量或其他同级字段，以当前配置和 Update Preflight constraints 为准：

```json
{
  "resource": {
    "cpu": 2,
    "mem": 4,
    "limit_cpu": 2,
    "limit_mem": 4
  }
}
```

```bash
bytedcli --json tce cluster update --service-id <service_id> --cluster-id <cluster_id> \
  --update-info-file update-resource.json --preflight
```

> **更新配置的安全规则：**
>
> 1. **ALWAYS ask the user for explicit confirmation** before running the real update. Candidate pipeline templates and other options discovered by preflight must be selected by the user.
> 2. CLI 按文件原样提交 `update_info`，不会回查并与当前集群配置合并。省略字段在后端的处理可能因字段而异，不能一概宣称必然保留或清除；先读取当前配置，并通过 Update Preflight 核对目标差异和同级字段要求。
> 3. **Before modifying `env_list`**, first retrieve the current environment variables (from TCE console or the cluster detail API), then submit the complete desired `env_list` array. The backend replaces this array, so omitted entries are removed.
> 4. **`--yes` 必须显式带上才会提交。** 不传 `--yes`（且不传 `--dry-run`）时命令会直接报 `TCE_CONFIRMATION_REQUIRED` 并提示加 `--yes` / `--dry-run`，不会进入交互等待。
> 5. `--dry-run` 可查看本地构建的正式请求体；后端约束和实际计划以本节 Update Preflight 报告为准。

```bash
# 可选：单独执行一次 dry-run，查看本地构建的正式请求
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --dry-run

# 用户明确确认目标、完整 update_info 与候选项后，使用 --yes 提交
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --yes --note "description of change"

# 可选：提交后等待完成
bytedcli tce cluster update --cluster-id <cluster_id> --service-id <service_id> --update-info-file payload.json --yes --wait --note "description of change"

# 服务和集群选择器可交叉组合；省略 --env 时正式请求按 prod 发送
bytedcli tce cluster update --service-id <service_id> --cluster-name default --update-info-file payload.json --dry-run
bytedcli tce cluster update --psm example.service.api --env prod --cluster-id <cluster_id> --update-info-file payload.json --dry-run
bytedcli tce cluster update --psm example.service.api --env prod --cluster-name default --update-info-file payload.json --dry-run
# 可选参数：--purpose、--delay-online、--pipeline-template、--change-single-dc、--block-delay-config
# 等待参数：--wait-timeout-sec（默认 600）、--poll-interval-sec（默认 5）
```

**update_info JSON 示例**（修改环境变量 — 注意包含全部已有变量）：

```json
{
  "runtime": {
    "env_list": [
      { "env_name": "DEPLOY_PATH", "env_value": "/opt/tiger/example_bin" },
      { "env_name": "RUNTIME_IDC_NAME", "env_value": "useast5" },
      { "env_name": "SCM_NAME", "env_value": "data.search.example_us" },
      { "env_name": "SCM_VERSION", "env_value": "2.0.3.1752" },
      { "env_name": "SEC_KV_AUTH", "env_value": "1" },
      { "env_name": "START_SCRIPT", "env_value": "bash /opt/tiger/example_bin/runs/tce_run" },
      { "env_name": "TCE_PRELOAD_SCRIPT", "env_value": "preload.sh" }
    ]
  }
}
```

> **WARNING**: When `update_info.runtime.env_list` is present, the backend replaces the `env_list` array. Submit the complete desired set of environment variables; omitted entries are removed. Always retrieve the current cluster configuration first, then make the user-requested changes on top of that list.

## 集群升级

### Upgrade Preflight（只读发现）

`cluster upgrade --preflight` 调用独立的 Upgrade Preflight 接口，不创建工单、不轮询、不生成 `client_token`、不发送 `dry_run`，也不查询镜像元数据。请求可以为空，或仅提供部分服务、集群、SCM / 镜像、模板及工单字段。

```bash
# 空请求：发现服务端要求的字段和可选升级模式
bytedcli --json tce cluster upgrade --preflight

# 部分镜像请求：image-version 与 image-tag 在预检时均可单独提供
bytedcli --json tce cluster upgrade --service-id <service_id> --image-version 1.0.0.86 --preflight

# 多集群 SCM 请求：显式策略应用到全部目标
bytedcli --json tce cluster upgrade --cluster-ids 12345,67890 \
  --repo-info-file repos.json --rollout-strategy default --pipeline-template 0 --preflight
```

- 服务 selector 最多一个（`--service-id` / `--psm`），集群 selector 最多一个（`--cluster-id` / `--cluster-name` / `--cluster-ids` / `--cluster-names`）；`--env` 可以作为非空的部分输入单独发送，不会补成 `prod`。
- `--repo-info-file` 仍按 1 MiB 上限与 SCM 数组 schema 校验，并与 `--image-version`、`--image-tag` 互斥。预检不会自动补 image tag，也不会调用 image lookup。
- `--rollout-strategy` 仅接受 `default`（Strict）或 `eager`（Quick），必须同时提供集群目标，并应用到全部目标。Preflight 不会补默认策略；即使 `can_submit: true`，也必须以响应 `preview.cluster_list[].rollout_strategy` 为实际策略，服务端可能把请求的 `eager` 回退为 `default`。
- `options` 可返回按集群划分的 rollout strategy、升级模式、流水线模板、镜像版本、SCM 版本及目标镜像仓库。候选项必须展示给用户并由用户选择，不自动采用推荐值。
- `constraints[].cluster_id` 标识多集群请求中受约束的目标；`can_submit: false` 仍是成功报告。HTTP / 业务错误中若包含有效报告，会保留在错误输出的 `data` 中。
- `preview` 缺失或为 `null` 不表示“没有变更”；预检结果不会自动提交。`--preflight` 不能与 `--dry-run`、`--yes` 或 `--wait` 同用。

`cluster upgrade` 支持 SCM 版本和镜像版本升级。SCM 升级使用 `--repo-info-file`，文件最大为 1 MiB，内容是非空仓库数组，每项必须包含非空字符串 `name` 和 `version`；`scm_repo_id` 为可选字符串。

```bash
# 预览 SCM 版本升级
bytedcli tce cluster upgrade --cluster-id <cluster_id> --service-id <service_id> --repo-info-file repos.json --dry-run

# 用户确认后提交；正式升级默认 rollout strategy 为 eager，也可显式选择 default
bytedcli tce cluster upgrade --cluster-id <cluster_id> --service-id <service_id> --repo-info-file repos.json --rollout-strategy default --yes
# 可选参数：--note、--purpose、--pipeline-template（允许 0）、--rollout-strategy default|eager、--block-delay-config
```

> **升级的 pipeline_template**：省略 `--pipeline-template` 时
> bytedcli 不发送 `pipeline_template`，TCE 服务端按 service 自身配置解析升级管线。
> 若某 service 没有可解析的默认升级管线，会报 `get pipeline_template error: ... no documents in
result`——此时显式传 `--pipeline-template <id>`，或改用 `tce deploy-lane` / 控制台。

### 一单多集群（multi-cluster ticket）

`cluster upgrade` 支持用 `--cluster-ids id1,id2,...` 或 `--cluster-names name1,name2,...` 将多个集群放进**一张**升级工单，支持 SCM 和镜像升级。`--cluster-id`、`--cluster-name`、`--cluster-ids`、`--cluster-names` 四选一；列表不允许空项或重复目标。

```bash
# 多集群纯版本升级；先从预检 preview.cluster_list 核对目标与策略
bytedcli tce cluster upgrade --cluster-ids 12345,67890 --service-id <service_id> \
  --repo-info-file repos.json --dry-run

# 也可用 --cluster-names + psm/env；pipeline upgrade 端点会编码为 cluster_list[].name
bytedcli tce cluster upgrade --cluster-names canary,default --psm example.service.api --env prod \
  --repo-info-file repos.json --dry-run

# 用户确认后提交一张覆盖两集群的升级单
bytedcli tce cluster upgrade --cluster-names canary,default --psm example.service.api --env prod \
  --repo-info-file repos.json --yes

# 多集群镜像模式
bytedcli tce cluster upgrade --cluster-ids 12345,67890 --service-id <service_id> \
  --image-version 1.0.0.86 --psm <psm> --yes
```

> **灰度建议**：逐集群一单（`--cluster-id X` 每集群一单，可独立观察/回滚）与一单多集群（`--cluster-ids` 一次覆盖多集群）按需选择；一单多集群等价于控制台「批量升级」，回滚以单为粒度。

### 镜像模式（image-mode / manifest-mode）服务升级

`image_mode=false`（console 升级页 "基于 SCM 配置" radio disabled）的服务**不接受 SCM-mode 升级**，必须按 image_version + image_tag 提交，否则 server 返回：

```
HTTP 400 image_version is not provided for upgrading service in manifest mode
```

`cluster upgrade` 用 `--image-version`（与 `--repo-info-file` 互斥）走 image-mode 路径：

```bash
# 本地请求预览；image_tag 可由 image_versions_info 解析
bytedcli --site i18n-tt tce cluster upgrade \
  --cluster-id <cluster_id> --service-id <service_id> \
  --image-version 1.0.0.86 --pipeline-template <template_id> --dry-run

# 用户确认后提交
bytedcli --site i18n-tt tce cluster upgrade \
  --cluster-id <cluster_id> --service-id <service_id> \
  --image-version 1.0.0.86 --pipeline-template <template_id> --yes

# 直接指定 image-tag（跳过 image_versions_info 查询）
bytedcli --site i18n-tt tce cluster upgrade \
  --cluster-id <cluster_id> --service-id <service_id> \
  --image-version 1.0.0.86 \
  --image-tag tce/example.image.service:abcdef0123456789 \
  --pipeline-template <template_id> --yes
```

提交前按本节 Upgrade Preflight 核对实际目标和策略，并取得用户确认；正式升级用 `--yes`。`--dry-run` 只用于本地复核正式请求。

互斥关系：

- `--repo-info-file` 与 `--image-version` 二选一，必须有一个
- `--image-version` + `--image-tag` 直接发；只传 `--image-version` 时按目标版本查询 `/services/<id>/image_versions_info/?image_version=<version>`，使用返回的 `image_name` 作为 `image_tag`
- 按版本查询未取得 tag 时，传 `--psm` 触发 manifest_info 兜底（但 i18n-tt 等站点 manifest_info 通常不带 image_tag，命中率不高）
- image 模式允许兼容调用 `--service-id <id> --psm <psm>`：`--service-id` 仍是升级请求的服务 selector，`--psm` 只用于 image_tag 查询，最终请求只发送 `service`。该组合不能再带 `--env`
- 仅使用 `--psm [--env]` 时，PSM/env 是服务 selector，最终请求发送 `psm` 和 `env`，不发送 `service`；此模式必须显式传 `--image-tag`

请求体差异（与 SCM 模式对比）：

- `cluster_info.runtime.repo_info`: 镜像模式不发送该字段
- `cluster_info.runtime.image_tag` / `image_version`: 必填
- `pipeline_template`: 可省略；镜像模式服务若需要具体模板，从 console 升级页"流水线模板" 下拉或 `/pipeline_template?...&type=upgrade` 拿 ID 后用 `--pipeline-template` 显式传入

什么时候用哪个：

- 服务有 SCM 配置（升级页能选 "基于 SCM 配置"）→ `--repo-info-file` 传仓库数组
- 服务只能选 image_version → `--image-version`

其中 `repos.json`：

```json
[
  {
    "name": "example/demo-repo",
    "version": "1.0.0.1",
    "scm_repo_id": "123",
    "main_repo": true
  }
]
```

真实提交使用 `--wait` 时，更新、升级、扩缩容和重启会等待工单结束：完成时返回 `data.final_status`；失败或取消时返回非零退出码及 `TCE_DEPLOYMENT_FAILED`／`TCE_DEPLOYMENT_CANCELED`，工单 ID 和终态保存在 `error.details`。`--dry-run` 即使与 `--wait` 同传也只返回本地请求预览，不调用 mutation API、不创建工单且不轮询。

## 集群扩缩容

### Scale Preflight（只读发现）

`cluster scale --preflight` 调用独立的 Scale Preflight 接口，不查询服务、集群或 IDC，不生成 `client_token`、不发送 `dry_run`，也不提交或轮询工单。空请求、部分 selector、只传 `--idc`、只传副本数和部分嵌套 JSON 都可用于逐步发现约束；CLI 不补 `env=prod`、小流量副本数、`quota_op` 或 `pipeline_mode`。

```bash
# 空请求：先发现服务端要求的字段
bytedcli --json tce cluster scale --preflight

# 部分请求：单 IDC 或 count-only 都不会触发元数据查询
bytedcli --json tce cluster scale --idc sample-idc --preflight
bytedcli --json tce cluster scale --replicas 2 --preflight
bytedcli --json tce cluster scale --psm example.service.api --cluster-name default \
  --idc sample-idc --replicas 2 --canary-replicas 0 --pipeline-template 0 --preflight

# 完整业务输入与平滑参数
bytedcli --json tce cluster scale --service-id <service_id> --cluster-id <cluster_id> \
  --scale-info-file scale.json --smooth-file smooth.json \
  --ignore-pipeline-template --skip-rolling-granularity-check --preflight
```

- 服务和集群 selector 在预检中各自最多一个；正式提交各自恰好一个。`--preflight` 与 `--dry-run`、`--yes`、`--wait` 互斥。
- `--scale-info-file` 接受 legacy `{dc_info, canary_dc_info}`，或完整 `{runtime:{replicas, serverless_conf, shard_num, shard_params}}`；两种格式不能混合，也不能与 `--idc`、`--replicas`、`--canary-replicas` 组合。未知、拼错、只读字段（例如 `all_dc_info`、`vdc` in `dc_info`、`pipeline_mode`）会被拒绝，不会静默剥离。
- `current_state.cluster.replicas.prod/canary` 返回当前 IDC/VDC/count，`shard_num` 可为 `null`；`reservation_supported`、`serverless_supported`、`sharding_supported`、`smooth_supported` 是能力提示。`options.pipeline_templates` 只是候选项，必须展示给用户并由用户选择，不得自动使用 `recommended`。
- `preview.cluster_list[].diff_info` 和 `pipeline_template` 是后端实际预览；`preview.resource_operations` 给出 `idc/scale_op/resource_op/reserve_to`。`reserve_to: ""` 不能推断为当前用户，`preview: null` 也不能解释为没有变更。
- `constraints[].field` 可直接映射到 CLI/JSON：selector 对应 `--service-id|--psm`、`--cluster-id|--cluster-name`；`update_info.runtime.replicas.*` 对应 `--idc/--replicas/--canary-replicas` 或 `--scale-info-file`；`serverless_conf`、分片字段只通过完整文件提供；`smooth` 对应 `--smooth-file`；`pipeline_template` 对应 `--pipeline-template`。后端限制和模板适用性以报告为准，不由 CLI 推断。
- `can_submit: true` 只表示满足预检阶段发现的条件，不代表授权或用户确认。HTTP/业务错误仍为非零退出；响应中若有有效报告，会保留在错误结果 `data`。

真实提交必须获得用户明确确认并显式加 `--yes`；不传 `--yes` / `--dry-run` 时命令报 `TCE_CONFIRMATION_REQUIRED`。先按本节 Scale Preflight 核对当前容量和实际变更计划。

```bash
# 可选：本地预览正式请求（PSM 模式省略 env 时才默认 prod）
bytedcli tce cluster scale --psm example.service.api --env prod --cluster-name demo-prod --replicas 2 --dry-run

# 用户确认目标、输入和候选项后提交
bytedcli tce cluster scale --psm example.service.api --env prod --cluster-name demo-prod --replicas 2 --yes

# 显式单 IDC 只修改该 IDC；不会把 canary 自动补为 0
bytedcli tce cluster scale --cluster-id <cluster_id> --service-id <service_id> \
  --idc sample-idc --replicas 3 --dry-run

# 完整文件可单独执行 serverless 或分片扩缩容，不要求 dc_info
bytedcli tce cluster scale --cluster-id <cluster_id> --service-id <service_id> \
  --scale-info-file scale.json --smooth-file smooth.json --dry-run

# 用户确认后可等待工单完成
bytedcli tce cluster scale --cluster-id <cluster_id> --service-id <service_id> \
  --scale-info-file scale.json --yes --wait --pipeline-template 0
```

未指定 `--idc` 的 `--replicas` 保持既有正式请求默认：按集群 IDC 展开，未显式提供小流量数量时将 canary 设为 0。Legacy 文件直接使用文件内的 IDC，省略 `canary_dc_info` 时补空数组；这两种旧输入模式均保留 `quota_op/pipeline_mode` 默认值。显式 `--idc` 和完整 `{runtime:{...}}` 文件不应用这些默认值。正式文件中的副本条目须提供必要字段；serverless 或 shard-only 请求不会被 legacy `dc_info` 要求误拦截。

**Legacy scale_info JSON 示例**（正式模式保留既有默认）：

```json
{
  "dc_info": [{ "idc": "sample-idc", "count": 5, "quota_op": { "type": "no-process" } }],
  "canary_dc_info": [{ "idc": "sample-idc", "count": 1 }]
}
```

**完整 scale_info JSON 示例**（显式透传，不添加 legacy 默认；可单独使用 serverless/分片字段）：

```json
{
  "runtime": {
    "replicas": {
      "dc_info": [
        {
          "idc": "sample-idc",
          "count": 3,
          "deleted": false,
          "env": "prod",
          "stage": "all_dc",
          "quota_op": { "type": "reserve", "to_psm": "example.service.target" }
        }
      ],
      "canary_dc_info": [{ "idc": "sample-idc", "count": 0, "env": "canary" }],
      "env_info": [{ "env": "prod", "count": 3 }]
    },
    "serverless_conf": {
      "free_replicas": [{ "idc": "sample-idc", "vdc": "sample-vdc", "count": 1, "frozen_cpu": 0 }],
      "min_replicas": [{ "vdc": "sample-vdc", "count": 0 }]
    },
    "shard_num": 2,
    "shard_params": { "canary_shard_num": 1 }
  }
}
```

**smooth.json 示例**：

```json
{
  "smooth_stages": 2,
  "smooth_percentage": 50,
  "smooth_proportions": [5000, 5000],
  "time_interval": "10s",
  "interval_by_detect": false,
  "confirm_webhooks": [
    { "hook_url": "https://example.com/tce-confirm", "async": true, "can_skip": true }
  ]
}
```

`smooth_percentage` 使用百分数单位；`smooth_proportions[]` 每项使用万分比（basis points，1/10,000），数组长度必须与后端计算出的 SmoothStage 数量一致。上例两阶段各为 `5000`。不要仅凭本地猜测阶段数；先用 Scale Preflight 核对 constraints、preview 和 `smooth_supported`。

当后端返回 `InvalidParameter.Ambiguous` 时，Agent 必须展示 error message 中的候选 ID 并让用户选择，再使用 `--cluster-id` 重试；不得自行选择第一个候选。

## 集群滚动重启

调用 TCE 正式「操作实例 → 重建实例」接口（`POST /deployment/cluster/pod_exec/`，请求体包含 `service`、`cluster`、`exec_type=rebuild`、`exec_params`，可选 `pipeline_template` / `note`），由 TCE 自身按并发粒度滚动重建整集群实例，不是逐个删 Pod。

> **SAFETY RULES — `cluster restart` MUST follow ALL steps in order:**
>
> 1. **ALWAYS `--dry-run` first.** 先展示将要提交的重建请求体。
> 2. **Wait for explicit user confirmation before the real run.** 真正执行前再加 `--yes`。
> 3. **不要把「重启」与 `instance delete` 混用。** 本命令是显式的滚动重建工单，不需要手工删 Pod。
> 4. **Do not overlap with cluster update / scale / deployment changes.** 避免与其它发布或变更并发执行。

参数：`--surge-percent`（并发粒度 %，默认 10）、`--interval-sec`（操作间隔秒，默认 30）、`--pipeline-template`（可选流水线模板 id）、`--note`、`--wait` 及 `--wait-timeout-sec`（默认 600）/`--poll-interval-sec`（默认 5）。

```bash
bytedcli tce cluster restart --psm example.service.api --env prod --cluster-name demo-prod --dry-run
bytedcli tce cluster restart --cluster-id <cluster_id> --service-id <service_id> --surge-percent 25 --interval-sec 10 --yes --wait
```

## 发布工单

```bash
# 查询发布工单
bytedcli tce deployment list --service-id <service_id> --type upgrade
bytedcli --json tce deployment get <deployment_id>

# 取消发布工单：dry-run 只解析 deployment 并展示 {action: cancel}
bytedcli tce deployment cancel <deployment_id> --dry-run
bytedcli tce deployment cancel <deployment_id>

# 最小工单级 action：先预览，再核对 pipeline.allow_actions 后提交
bytedcli tce deployment action --deployment-id <deployment_id> --action start --dry-run
bytedcli tce deployment action --deployment-id <deployment_id> --action start --yes

# rollback 附加字段
bytedcli tce deployment action --deployment-id <deployment_id> --action rollback \
  --extra-json '{"rollback_reason":{"index":1,"info":"sample-context","reason":"demo rollback"},"upgrade_min_ready_second":10,"upgrade_surge_percent":25}' \
  --dry-run

# 最小步骤级 action：先预览，再核对步骤 allow_actions 后提交
bytedcli tce deployment execute-step --step-id <step_id> --action start --dry-run
bytedcli tce deployment execute-step --step-id <step_id> --action start --yes

# 选择审批人附加字段
bytedcli tce deployment execute-step --step-id <step_id> --action choose_ttops_approver \
  --extra-json '{"approver_type":"organization_account","is_noc":true}' --dry-run

# 检测规则反馈对象
bytedcli tce deployment execute-step --step-id <step_id> --action skip \
  --extra-json '{"ignore_reason":"demo reason","ignore_rules_feedback":[{"id":123,"reason":"demo reason"},{"id_str":"sample-rule","reason":"demo reason"}]}' \
  --dry-run
```

动作与 ID 必须来自下方详细章节所列的 `deployment get` 输出路径；`--dry-run` 只做本地请求预览，不代表后端接受。

## 服务实例

```bash
# 推荐方式：使用 --psm + --env
bytedcli --site cn tce instance list --psm example.service.api --env prod --ordering -cpu

# 兼容方式：使用 --service-id
bytedcli tce instance list --service-id <service_id> --ordering cpu --page 1 --page-size 10

# 按 node IP 过滤服务实例
bytedcli tce instance list --service-id 234558 --node-ip 10.35.142.21 --force-update --page 1 --page-size 10 --tce-site boe

# 强制刷新缓存
bytedcli tce instance list --psm example.service.api --env prod --force-update

# 获取全部实例（不分页）
bytedcli tce instance list --psm example.service.api --env prod --no-pagination

# 迁移指定实例，推荐先 dry-run
bytedcli tce instance delete --cluster-id 123456 --idc sample-idc --pod-name sample-pod-1 --dry-run
bytedcli tce instance delete --cluster-id 123456 --idc sample-idc --pod-name sample-pod-1 --yes --tce-site boe

# 强制删除实例（绕过 PDB 并上报故障机），默认预览，提交加 --yes
bytedcli --site cn tce instance force-delete --pod-name demo-pod --dry-run
bytedcli --site cn tce instance force-delete --pod-name demo-pod --yes
```

> **CRITICAL SAFETY RULES — `instance delete` MUST follow ALL steps in order:**
>
> 1. **Do not propose or run instance deletion unless the user explicitly asks to delete a specific instance, or the context is clearly an instance/node migration where deleting the instance is part of the migration workflow.** Do not infer delete from broader intents like restart, recover, or troubleshoot.
> 2. **Never delete more than one instance at a time.** If the user wants multiple instances removed, handle them strictly one-by-one, with a fresh checkpoint between each deletion.
> 3. **ALWAYS `--dry-run` first** and show the exact `cluster-id`, `idc`, and `pod-name` that would be deleted.
> 4. **ALWAYS get a second explicit confirmation before the real delete.** One confirmation is for target identity; a second confirmation is for executing the deletion now.
> 5. **Before deleting, re-check that the target pod still exists and is unique** via `instance list` or `instance search`. Never delete based on stale output alone.
> 6. **Before deleting, check remaining capacity and health.** If you cannot confirm that enough healthy replicas remain after deletion, especially in prod or low-replica services, stop and surface the risk first.
> 7. **After deleting, re-list instances and inspect status before taking any further action.** If the service does not recover as expected, do not continue with any second deletion.
> 8. **Do not overlap instance deletion with cluster update / scale / deployment changes.** If another change is in flight, warn about compounded risk before proceeding.

### 从实例下载文件（CN）

`tce instance download` 通过 TCE 文件 relay 把实例内文件直接流式写到本地，不经过 WebShell 输出通道，因此不受终端输出截断影响。当前仅支持经过验证的 `--site cn` 链路。

```bash
# 推荐：执行前先用 instance list 确认目标，再用 PSM/env + 精确 Pod/容器名解析 container id
bytedcli --site cn tce instance download \
  --psm example.service.api \
  --env ppe_demo \
  --pod-name demo-pod \
  --container-name main \
  --remote-path /opt/tiger/toutiao/log/result.log.gz \
  --output ./result.log.gz

# 调大下载上限和超时；只有明确需要覆盖本地文件时才加 --force
bytedcli --site cn tce instance download \
  --pod-name demo-pod \
  --container-name main \
  --container-id containerd://demo \
  --remote-path /var/log/tiger/result.log.gz \
  --output ./result.log.gz \
  --max-bytes 52428800 \
  --timeout-ms 180000 \
  --force
```

- TCE 允许的远端目录：`/opt/tiger/cores/`、`/opt/tiger/toutiao/log/`、`/opt/tiger/data/log/`、`/var/log/tiger/`。
- 执行前先用 `instance list` 确认唯一 Pod/容器和远端路径；命令不提供 `--dry-run`。
- 默认 `--max-bytes 10485760`（10 MiB）、`--timeout-ms 120000`。真实下载会同时检查 `Content-Length` 和实际流式字节数；超限、超时、中断或校验失败时清理临时文件。
- 默认拒绝覆盖已有本地文件；`--force` 仅覆盖已有普通文件。下载在目标目录内先写私有临时文件，成功后原子提交。
- 成功结果包含 `output_path`、`bytes`、`sha256`、Pod/容器标识和远端路径；一次性签名 URL 不会进入输出。
- 需要先存在浏览器态 SSO session；收到 `AUTH_SESSION_REQUIRED` 时执行 `bytedcli auth login --session` 后重试。

## Relay WebShell

```bash
# 先生成浏览器态 SSO session，再直接从 PSM/env 建连
bytedcli --json auth login --begin --session --session-method qr --no-terminal-qr
bytedcli --json auth login --complete <complete_token>
bytedcli tce webshell open --psm example.service.api --env prod --first
# 服务实例很多时用 --node-ip 先在服务端按节点过滤，open / interactive 均支持
bytedcli tce webshell open --psm example.service.api --env prod --node-ip 10.35.142.21 --first
bytedcli tce webshell exec --session-id ws_xxx --command 'hostname; date'
# 仅当上一步返回 TCE_WEBSHELL_OTP_REQUIRED 时使用；TTY 会隐藏输入，Agent 应通过子进程 stdin pipe 注入一行
bytedcli tce webshell exec --session-id ws_xxx --command 'hostname; date' --otp-stdin
bytedcli tce webshell interactive --psm example.service.api --env prod --first
# interactive 同样支持 --node-ip 与 --otp-stdin
bytedcli tce webshell interactive --psm example.service.api --env prod --node-ip 10.35.142.21 --first
# interactive 同样支持 --otp-stdin：TTY 下先隐藏输入，看到 OTP 提示时自动提交一次
bytedcli tce webshell interactive --psm example.service.api --env prod --first --otp-stdin

# 保存输出到本地文件
bytedcli tce webshell exec --session-id ws_xxx --command-file /tmp/diag.sh --output-file /tmp/diag.out
# relay 拒绝握手时自动重试（默认 5 次）；脚本里频繁建连时可调大
bytedcli tce webshell exec --session-id ws_xxx --command 'hostname' --handshake-retries 8
bytedcli tce webshell close --session-id ws_xxx
```

### 握手失败与重试

- relay 偶发拒绝 websocket 握手：不返回 101，而是返回 HTTP 200 + `token expires, maybe attack!`。此时连接没有打开，命令一定没有发出。
- bytedcli 在连接打开前失败时重新获取 websocket URL，退避 1–3 秒后重试，默认最多 5 次，`--handshake-retries <n>` 可调（0–20，0 表示不重试）。连接打开后的错误不重试，避免重复执行非幂等命令。
- 成功输出的 `data.handshake_attempts` 记录实际握手次数；全部被拒时返回 `TCE_WEBSHELL_HANDSHAKE_REJECTED`，`error.details` 带 `attempts`、`handshake_retries`、`status`、`body`、`logid`（`body` 尽力捕获，可能缺失）。持续失败时重新 `tce webshell open`，并把 `logid` 反馈给 relay 维护方。
- 握手返回 401/403 视为会话被拒，不重试；先 `bytedcli auth login --session` 再重新 `tce webshell open`。连接超时（`TCE_WEBSHELL_CONNECT_TIMEOUT`）也不重试。

### OTP 编排

1. Agent 先正常调用 `tce webshell exec`。若目标无需 OTP，命令直接执行。
2. 收到 `TCE_WEBSHELL_OTP_REQUIRED` 后，保留相同 `session-id` 与命令，通过模型对话之外的 secret input 获取当前 Seal/飞连 OTP。OTP 提示文案可能是 `please input otp code`、`please input seal/feilian OTP code` 或 `请输入Google Authenticator OTP码（输入q退出）`，bytedcli 均能识别。
3. exec 模式以 stdin pipe 启动带 `--otp-stdin` 的同一命令，写入一行 OTP 后关闭 stdin；interactive 模式 TTY 下先隐藏输入、连上后自动提交。非 TTY 管道不要配 interactive：stdin EOF 会立即关闭会话，只喂一行 OTP 会在门禁提示出现前结束——管道场景统一用 exec。不要通过 argv、环境变量、文件、日志或普通对话传递 OTP。
4. OTP 只在连接后 30 秒的门禁窗口内自动提交一次。收到 `TCE_WEBSHELL_OTP_INVALID` 时丢弃该值并请求新 OTP，禁止自动重放；interactive 下服务端再次提示需手工输入或重进。收到 `TCE_WEBSHELL_OTP_TIMEOUT` 时重新连接同一持久化会话再试。

bytedcli 会在 WebSocket 内先等待 OTP 提示，单独提交 OTP，并在认证后终端输出出现后才发送业务命令。OTP 缺失、无效或超时时不会发送业务命令。

## 发布工单

```bash
# 查询发布工单列表（按服务 ID + 类型筛选）
bytedcli tce deployment list --service-id <service_id> --type upgrade
bytedcli tce deployment list --psm example.service.api --env prod --type upgrade

# 按状态筛选
bytedcli tce deployment list --service-id <service_id> --status finished --page 2

# 获取发布工单详情（返回 meta + pipeline stages + runtime）
bytedcli --json tce deployment get <deployment_id>

# 获取全局发布工单详情（返回 global ticket + service_info/cluster_info）
bytedcli tce deployment get <global_ticket_id> --global

# 跨站点查询工单
bytedcli --site boe tce deployment list --service-id <service_id>
bytedcli --site byteintl tce deployment get <deployment_id>

# us-ttp 专用：先解析 USTS Review step 并预览固定 approver 请求，不提交
bytedcli --site us-ttp tce deployment select-ttops-approver <deployment_id> --dry-run
# 用户确认后，在 USTS Review 步骤选择 USTS-NOC 作为 TTP 审批人并确认
# 对应 UI "操作 → 选择TTP审批人 → 弹窗选 USTS-NOC → 确定"，仅 us-ttp 租户下的部署会有该动作
# 不传 --step-id 时，会自动根据 deployment 详情定位含 choose_ttops_approver 的 ConfirmStep
bytedcli --site us-ttp tce deployment select-ttops-approver "https://cloud-ttp-us.bytedance.net/tce/deployment_new/<deployment_id>?service_id=<service_id>"
bytedcli --site us-ttp tce deployment select-ttops-approver <deployment_id> --step-id <step_id>

# 最小工单级 action：先预览，再核对 pipeline.allow_actions 后提交
bytedcli tce deployment action --deployment-id <deployment_id> --action start --dry-run
bytedcli tce deployment action --deployment-id <deployment_id> --action start --yes

# rollback 附加字段写入 body 顶层
bytedcli tce deployment action --deployment-id <deployment_id> --action rollback \
  --extra-json '{"rollback_reason":{"index":1,"info":"sample-context","reason":"demo rollback"},"upgrade_min_ready_second":10,"upgrade_surge_percent":25}' \
  --dry-run

# 最小步骤级 action：先预览，再核对步骤 allow_actions 后提交
bytedcli tce deployment execute-step --step-id <step_id> --action start --dry-run
bytedcli tce deployment execute-step --step-id <step_id> --action start --yes

# 选择审批人附加字段
bytedcli tce deployment execute-step --step-id <step_id> --action choose_ttops_approver \
  --extra-json '{"approver_type":"organization_account","is_noc":true}' --dry-run

# 检测规则反馈对象；数字规则使用 id，非数字规则使用 id_str
bytedcli tce deployment execute-step --step-id <step_id> --action skip \
  --extra-json '{"ignore_reason":"demo reason","ignore_rules_feedback":[{"id":123,"reason":"demo reason"},{"id_str":"sample-rule","reason":"demo reason"}]}' \
  --dry-run
```

### Action 请求映射与静态字段契约

| CLI 输入 | 请求映射 |
| --- | --- |
| `deployment action --deployment-id <id>` | `<id>` 只进入 `/deployment/:id/pipeline/actions/` 的 path，不进入 body |
| `deployment execute-step --step-id <id>` | `<id>` 只进入 `/deployment_steps/:id/actions/` 的 path，不进入 body |
| `--action <name>` | 写入 body 的 `action`；动作名是动态字符串，不增加本地枚举 |
| `--extra-json <object>` | 合并到 body 顶层；与 `action` 冲突时显式 `--action` 优先，未知扩展、`null`、`0`、`false` 原样保留 |

工单级 body 的已知字段：

| 字段 | 静态类型与含义 |
| --- | --- |
| `action` | string；当前动作名 |
| `pause_reason` | string；暂停原因 |
| `rollback_reason` | object；可含整数 `index`、字符串 `info`、字符串 `reason` |
| `skip_rolling_granularity_check` | boolean；是否跳过滚动粒度检查，只能按目标平台提示与用户决定 |
| `update_mode` | string；更新模式 |
| `upgrade_min_ready_second` | integer；滚动间隔，单位秒 |
| `upgrade_surge_percent` | integer；滚动粒度，单位百分比 |

步骤级 body 的已知字段：

| 字段 | 静态类型与含义 |
| --- | --- |
| `action` | string；当前步骤动作名 |
| `approver` / `approver_type` | string；审批人与审批人类型 |
| `is_noc` | boolean；是否为 NOC 人员 |
| `pause_reason` / `reason` / `ignore_reason` | string；对应动作或忽略检测规则的原因 |
| `ignore_rules_feedback` | array；每项为 `{id?: number, id_str?: string, reason?: string}`，数字规则 ID 用 `id`，非数字规则或字符串表示用 `id_str` |

这些 schema 只提供静态类型和文档，不接入 `--extra-json` 的运行时解析；BAM 标记 optional 也不表示某个具体动作一定接受缺失字段。真实必填条件、动作与组合仍由目标工单状态和后端决定。

### ID、动作和附加值来源

1. 先运行 `bytedcli --json tce deployment get <deployment_id>`。标准信封中，工单 ID 在 `.data.meta.id`，工单级当前动作在 `.data.pipeline.allow_actions`，步骤 ID 在 `.data.pipeline.stages[].steps[].id`，步骤级当前动作在 `.data.pipeline.stages[].steps[].allow_actions`。
2. `allow_actions` 项可能直接是字符串，也可能是含 `name` / `type` / `display` 的对象。字符串直接作为 `--action`；对象优先使用目标项的 `name`，仅当平台明确把 `type` 作为动作 token 且 `name` 缺失时才使用 `type`。`display` 只用于展示，不应反推动作名；不要自动选择第一项。
3. `pause_reason`、`rollback_reason.index/info/reason`、`update_mode` 与是否跳过滚动粒度检查，来自目标 TCE 工单操作/回滚表单或用户明确选择。bytedcli 当前没有这些候选的独立查询命令。
4. `approver`、`approver_type`、`is_noc` 来自目标 TCE/USTS 审批人选择能力和用户选择；检测规则 `id` / `id_str` 及反馈原因来自目标 TCE Detector 结果和用户选择。当前 CLI 没有独立的审批人或检测规则候选命令，不能虚构命令、猜值或自动采用历史值。
5. `--dry-run` 只打印本地组装的请求，不调用 action 接口，也不证明后端会接受。用户确认目标 ID、当前允许动作和附加字段后，才把同一请求改为 `--yes` 提交。

### 流水线整步驱动示例（部署不自动推进时）

直连 `tce cluster update --yes` 创建的部署会以 `auto_start: false` 卡在 deploy stage。
传统做法是去 TCE console 点 "开始" / "跳过"，纯命令行链路用循环 + execute-step 替代：

```bash
TICKET_ID=<from cluster update>
while true; do
  DEP=$(bytedcli --json tce deployment get "$TICKET_ID")
  STATUS=$(echo "$DEP" | jq -r '.data.meta.status')
  case "$STATUS" in
    finished|success) break ;;
    failed|cancelled|canceled) echo "deploy failed: $STATUS"; exit 1 ;;
  esac

  NEXT=$(echo "$DEP" | jq -r '
    .data.pipeline.stages[].steps[]
    | select(.status == "pending")
    | .id as $id
    | (.allow_actions // [])[]?
    | (if type == "string" then . elif type == "object" then (.name // .type // empty) else empty end) as $action
    | select($action == "start" or $action == "skip")
    | ($id|tostring) + " " + $action
  ' | head -1)
  [[ -z "$NEXT" ]] && { sleep 10; continue; }

  bytedcli tce deployment execute-step \
    --step-id $(echo "$NEXT" | awk '{print $1}') \
    --action  $(echo "$NEXT" | awk '{print $2}') \
    --yes
done
```

## 环境级联查询

```bash
# 查询 PSM 的环境级联信息
bytedcli tce env-cascader --psm example.service.api

# 指定分区
bytedcli tce env-cascader --psm example.service.api --partition CN

# 指定环境
bytedcli tce env-cascader --psm example.service.api --env prod

# 排除分区
bytedcli tce env-cascader --psm example.service.api --excluded-partitions SG,VA
```

## 泳道部署

`tce deploy-lane` 会直接创建部署，命令本身既没有 `--dry-run` 也没有 `--yes`；执行前先用
`env-cascader` 和只读查询核对泳道、集群及 SCM 版本。`--action create --cluster-spec-file`
使用的是 **ENV 显式 cluster spec**，不是本 reference 前文 `tce cluster create` 的
`cluster_info`。ENV spec 的字段表与最小 JSON 由 bytedance-env `references/env.md` 维护：
`bytedcli self skill get bytedance-env/references/env.md`。

```bash
# 部署泳道
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

# 先用安全 ENV 链导出并复验 cluster.json（全部都是只读 dry-run）
bytedcli --jq '.data.cluster_spec' env service deploy-tce \
  --env ppe_demo --standard-env online_cn --psm example.service.api --dry-run > cluster.json
bytedcli --json env service deploy-tce \
  --env ppe_demo --standard-env online_cn --psm example.service.api \
  --cluster-spec-file cluster.json --dry-run

# 仅在用户确认后使用已经验证的完整 ENV spec；这一条会立即执行真实部署
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

# 创建时注入自定义环境变量（逗号分隔 key=value）
bytedcli tce deploy-lane \
  --env boe_demo \
  --standard-env boe \
  --psm example.service.api \
  --action create \
  --cluster-names default \
  --env-vars "scmVersion=1.0.0.100"

# 升级时设置自定义环境变量；执行模式必须二选一传 --dry-run（预览）或 --yes（提交）
bytedcli env service upgrade-tce \
  --psm example.service.api \
  --env boe_demo \
  --standard-env boe \
  --cluster-id 12345 \
  --env-vars "scmVersion=1.0.0.100" \
  --yes
```

`--cluster-spec-file` 只用于 `--action create`，并与 `--cluster-names` / `--specify-dcs` /
`--zone` / `--virtual-cluster` 互斥。导出后必须按 bytedance-env reference 检查 `cluster_spec`
非 null 且 `name` / `zone` / `virtual_cluster` / `base_cluster_id` / 非空 `dc_infos` 完整；
多集群 preview 的 `cluster_spec=null` 不能固定成一个 spec 对象。`tce deploy-lane` 的 branch /
SCM-version 参数与 `env service deploy-tce` 不完全相同，不要把 ENV 只读复验描述成所有模式都等价。

`--env-vars` 支持逗号分隔的多个键值对，如 `--env-vars "key1=val1,key2=val2"`。值会合并到集群的 `new_env_vars` 中，不会覆盖未指定的已有环境变量。

## 精确 SCM 制品到 PPE 泳道

当 PPE 测试需要证明某个 Git/MR commit（而不是可漂移的分支或仓库 latest version）已经运行时，使用以下证据门禁。该流程包含真实远端写入：写前必须冻结目标并获得明确授权；提交结果不明时禁止盲重试。

### 只读写前门禁

1. 冻结本地与远端 source SHA，确认 worktree clean、远端 source branch 与本地 `HEAD` 一致。
2. 通过 `tce env-cascader` 和 ENV/TCE 查询解析 `PSM -> partition -> standard_env -> PPE lane -> lane service/RID -> cluster`。PPE service ID 与 prod service ID 不同，禁止按约定推导。
3. 读取目标泳道当前主仓版本、目标 cluster 的**顶层**实例列表、running/pending 发布工单。递归遍历或聚合得到的实例数不能作为写入前置条件；后续直接读取发生漂移时，必须生成新计划并重新确认。
4. 构建精确 commit 的 SCM test 制品，并按返回 version 回读 `data.versions[]`：只接受唯一一条同时满足 `version=<exact_version>`、`base_commit_hash=<source_sha>`、`status=build_ok` 的记录。请求 filter、filter echo、`data.repo.version` 或列表第一项都不是制品身份证据。
5. 把 source SHA、SCM version、泳道/cluster、expected-before 版本与实例数、唯一一次 upgrade、验收条件和回滚边界绑定到不可变计划。用户确认的是这个计划，不是后续漂移后的新状态。

```bash
# 构建精确 commit 的 test 制品
bytedcli --json scm repo build example/service/api \
  --commit <source_sha> --type test --arch x86_64

# 按返回 version 回读并从 data.versions[] 做唯一精确匹配
bytedcli --json scm repo version list example/service/api \
  --version <exact_version> --page-size 100

# 解析 PPE lane、确认目标集群与直接实例状态
bytedcli --json tce env-cascader --psm example.service.api --partition CN
bytedcli --json tce cluster list --psm example.service.api --env ppe_demo --with-idc --page-size 50
bytedcli --json tce instance list --cluster-id <cluster_id> --page 1 --page-size 50

# 确认没有并发发布者
bytedcli --json tce deployment list --psm example.service.api --env ppe_demo --status running
bytedcli --json tce deployment list --psm example.service.api --env ppe_demo --status pending
```

### 单次受控写入

第二次只读核对仍满足不可变计划后，使用明确 SCM repo/version 只提交一次 upgrade；不要用 mutable branch 代替精确版本。

```bash
bytedcli --json tce deploy-lane \
  --env ppe_demo \
  --standard-env online_cn \
  --psm example.service.api \
  --env-type ppe \
  --flow-base prod \
  --scm-repo-name example/service/api \
  --scm-repo-version <exact_version> \
  --action upgrade
```

保存返回的 ENV ticket 和关联 TCE deployment。若命令超时、退出结果不明确或本地进程句柄丢失，先查询同一 ticket、同一泳道与同一 cluster；不得创建第二张工单“再试一次”。

### 只读部署后验收

必须同时证明：

- 原 ENV/TCE 工单进入成功终态，且绑定预期泳道与 cluster；
- 泳道 service/cluster 报告预期 SCM version；
- 目标 cluster 的顶层实例列表达到 expected healthy state；
- 不再有 running/pending 发布工单；
- 共享域名 smoke 携带完整 PPE 路由身份；CN TCE 常见形态为 `x-use-ppe: 1` 与 `x-tt-env: <lane>` 同时存在；
- 返回的公开业务字段证明目标行为，而不只是 HTTP 200。

仅带 `x-tt-env` 的请求可能回落到 online，可作为路由对照，但禁止作为 PPE 验证证据。若新 SCM version 已生效、Pod 健康而响应仍像旧版本，先补齐完整 PPE headers 并重读泳道身份，再判断代码或运行配置问题。主 selector 建议重复请求多次；存在等价 ID selector 时也应同时验证。

smoke 失败时不要自动回滚。保留原工单与现场状态，基于当前 observed state 生成独立 rollback plan，并为回到 prior exact SCM version 单独获取授权。

## 跨站点示例

```bash
bytedcli --site boe tce service search --keyword "my-service"
bytedcli --site byteintl tce service search --keyword "my-service"
bytedcli --site ttp-us-limited tce service search --keyword "my-service"
bytedcli --site ttp-eu tce service search --keyword "my-service"
```

## Notes

- 站点别名：`prod=cn`、`i18n=byteintl`、`tx-ttp=ttp-us-limited`、`eu-ttp=ttp-eu`
- `cluster update` 按原样提交 `--update-info-file`，不会回查合并当前配置；文件包含 `runtime.env_list` 时后端会替换该数组，必须提交完整期望数组；`tce cluster edit` 为隐藏别名
- `service get`、`cluster list`、`deployment list` 都支持 `--psm`；如果同一 PSM 在多个 env 下都有服务，可加 `--env` 做唯一定位
- `service check-repos` 与正式 `cluster reset/update` 也支持 `--psm [--env]`；正式请求省略 `--env` 时按 `prod` 发送，对应 preflight 不补默认环境。`cluster reset/update` 的服务选择器和集群选择器彼此独立，可以组合 `--service-id + --cluster-name` 或 `--psm [--env] + --cluster-id/--cluster-name`
- `cluster list --cluster-name` 可按集群名过滤结果；当同一 vregion 下存在多个同名集群时，建议和 `--service-id` 或 `--psm --env` 一起使用
- `instance list` 推荐使用 `--psm + --env`；兼容方式也支持 `--service-id`
- `instance list --node-ip` 可按 node IP 过滤服务实例；仅支持和 `--service-id` 或 `--psm --env` 一起使用，不支持 `--cluster-id`
- `instance list` 的文本表格会展示 `IDC` 列；按 `--node-ip` 排查时可直接看到实例所在机房
- 实例迁移沿用 `instance delete` 命令，调用 `DELETE /open-apis/v1/pods/`；需要同时传 `--cluster-id`、`--idc`、`--pod-name`；推荐先 `--dry-run` 输出请求，再决定是否执行。默认要求交互确认，非交互场景可显式加 `--yes`
- `--ordering` 可选值：`cpu/-cpu/mem/-mem/idc/-idc/createtime/-createtime/podstatus/-podstatus`；`-` 前缀表示倒序，不带 `-` 表示升序
- `tce webshell` 提供 `open/exec/close/interactive` 四个子命令。执行前需要先通过 `auth login --begin --session --session-method qr --no-terminal-qr` 和 `auth login --complete <token>` 准备本地浏览器态 SSO session；interactive 仍不支持 `--json`。
- `tce webshell open` / `interactive` 从 `--psm --env` 解析目标时会先拉取该服务返回的实例列表，再在本地按 `--pod-name` / `--container-name` / `--container-type` 过滤；服务实例很多（上万个 pod）时这一步较慢，可用 `--node-ip <ip>` 让服务端先按节点过滤（与 `instance list --node-ip` 是同一个 `node_ip` 查询参数），或放大全局 `--http-timeout-ms`（写在子命令之前）。
- `tce webshell exec` 每次会重新建立 websocket，因此不会保留上一次命令的 cwd / export / alias；如果需要完整交互态，仍然使用 `tce webshell interactive`
- `tce webshell exec --otp-stdin` 只从 stdin 读取一行 Seal/飞连 OTP；无 OTP 提示时不会提交该值。Agent 应按 `OTP_REQUIRED → secret input → 同 session 重试` 编排，且不得让 OTP 进入 argv、环境变量、文件、日志或模型对话。`tce webshell interactive --otp-stdin` 仅适用于 TTY：连接前隐藏输入 OTP，连上后 30 秒门禁窗口内看到提示自动提交一次；管道场景用 exec，不要用 interactive。

## Pod readiness 检查

```bash
bytedcli --json tce instance diagnose --pod-names demo-pod-a,demo-pod-b
bytedcli --site i18n-tt --vregion Singapore-Central --json tce instance diagnose --pod-names demo-pod-a
```

`--pod-names` 是必填的精确名称列表，取自当前实例查询。命令只读，GET `/api/v1/tce/open-apis/v1/pod_readiness_msg` 使用 `pod_names` 查询参数，不执行部署或 Pod 操作。身份由当前 CLI 环境变量/配置决定，`--site` 与可选 `--vregion` 沿用目标路由。

结果 `data.pods[]` 保留 `podName/format/msg/checkList`，每项检查保留 `name/stage/status/msg/oncall/docLink/docTitle`；状态保留平台原值，包括 passed、failed、pending 及未知值。`missingPodNames` 列出未返回证据的请求 Pod；非结构化消息或空检查列表都不推断为就绪。缺省消息和文档字段稳定输出 `null`。标准信封 `status=success` 表示查询完成，不代表所有 Pod 就绪；Running 也不能替代这些检查证据。
