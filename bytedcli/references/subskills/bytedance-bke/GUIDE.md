---
name: bytedance-bke
description: "通过 bytedcli 查询 BKE 发布控制台，在 CN 推进已有发布计划，在 I18N / US / EU-TTP 按控制台表单新建应用实例（指定镜像版本与集群外部署集群）。用于应用与管理员、两个应用的部署覆盖对比（按集群列出缺口）、发布实例（ReleaseInstance）的状态与版本、灰度/锁/离线标记、values 与实例对比、发版后实例批量体检（按 Pod 状态分类、致命日志签名、日志模式匹配）、成员集群，以及 CN Pod 命令执行、容器内文件读取 / 下载，Pod 列表、重启次数、事件、YAML、容器日志、镜像与 chart 构建版本（含新建表单列出的 online + test 版本）、集群外部署可选的部署集群，CN / I18N / EU-TTP 发布计划、人工关卡与启动前的变更管控预检（审批窗口、命中策略），CN / I18N / EU-TTP 历史 RO 工单与发布计划（按应用或按人查，含复制计划）及工单详情（模板、审批、批次策略、新旧版本），以及发版 / 新建实例前的权限与前置条件自检（RO 权限、应用管理员、集群与源实例可读）、账号的发版权限与持有的 SpaceX 角色、BKE 的 SpaceX 角色及成员；CN 计划可确认关卡、开始 / 暂停 / 继续 / 取消，对已调度对象重试 / 跳过 / 取消；I18N / US / EU-TTP 可提交新建实例工单（写命令默认预览，`--yes` 才提交）。支持 CN、I18N、US、I18N-BD、EU-TTP。用户提到 BKE 应用、某应用还缺哪些集群 / 和某个组件对比部署覆盖、发布实例、发版后体检 / 健康检查、成员集群、Pod 排障、日志、镜像 / chart 版本、发布计划跟踪、发布窗口 / 变更管控能否启动、RO 工单 / 发版历史 / 复制计划、有没有发版权限、有哪些 SpaceX 角色 / 谁有某个角色、能不能新建实例、新建实例 / 指定镜像版本或部署集群建实例、人工关卡确认、计划暂停 / 继续、对象重试或从未发布的实例时使用。TCE 服务与部署请使用 bytedance-tce。"
---

# bytedcli BKE

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

## 覆盖范围

- 应用：管理员、chart 仓库、镜像 SCM 仓库、默认发布配置；与基准应用对比部署覆盖（基准应用有实例、本应用没有的集群，及反向）
- 发布实例（ReleaseInstance，每个应用在每个成员集群上一个）：状态、chart / 镜像版本、灰度 / 锁 / 离线标记、渲染后的 values、两个实例的差异
- 已下线集群上的实例、已创建但从未发布过的实例
- 实例体检：按 Pod 状态把每个匹配实例归入健康分类，可选扫描致命日志签名、匹配自定义日志模式、判断旧 Pod 是否仍在服务
- 成员集群：zone / DC / VDC、业务场景、集群组、架构、phase，以及某个集群上部署了哪些应用的实例
- Pod：按 workload 列表、就绪容器、重启次数、事件、打码 YAML、一次性容器日志；CN 支持执行命令和读取 / 下载容器内文件
- 镜像 / chart 版本：应用镜像仓库和 chart 仓库在 SCM 中构建成功的版本；`--type all` 与新建表单一样列 online + test
- 新建实例（I18N / US / EU-TTP）：按控制台「创建应用实例」表单提交工单，主镜像版本必须指定，可选集群外部署集群、chart 问题答案和变更管控字段；集群外部署可选的部署集群用 `app deployed-cluster list` 查
- 发布计划（CN / I18N / EU-TTP；EU-TTP 没有对象级关卡和变更管控预检）：列表与按应用筛选、节点与对象进度、跟踪、人工关卡、变更管控预检（只读）
- 计划写操作（仅 CN）：确认计划级关卡或灰度对象的 CONFIRM；计划开始 / 暂停 / 继续 / 取消；已调度对象重试 / 跳过 / 取消
- 工单（CN / I18N / EU-TTP，只读）：应用的 RO 工单与发布计划（按应用名查，或扫描某人的工单，含复制计划）；单个 RO 工单的模板、审批、所属计划、对象的新旧版本、阶段与批次策略、操作记录
- 权限与前置条件（只读）：当前用户的 RO 发版权限、应用管理员身份、集群定义与 platform 项目可读、集群外部署开关，以及目标集群、复制源实例的可读性；不指定应用时看账号的发版权限与持有的 SpaceX 角色，以及 BKE 的 SpaceX 角色及成员（CN / I18N / EU-TTP）
- 不适用：TCE 服务、集群、部署单（用 `bytedance-tce`）；CN 上新建实例、更新实例、新建计划、操作 RO 工单、加锁、灰度标记、加管理员等其他 BKE 写操作

## 认证与控制面

`--site` 选择 ByteCloud 登录站点，`--env` 选择该站点下的 BKE 控制面。不同控制面之间的应用、实例和集群互不共享，CLI 不跨站点或控制面 fallback。

| 控制面  | 参数                                   | 登录                                 | 发布计划 / 工单 / SpaceX 角色  | 新建实例 |
| ------- | -------------------------------------- | ------------------------------------ | ------------------------------ | -------- |
| CN      | `--site cn`（默认）                    | `bytedcli --site cn auth login`      | 支持                           | 不支持   |
| I18N    | `--site i18n-tt`（默认 `--env i18n`）  | `bytedcli --site i18n-tt auth login` | 支持                           | 支持     |
| US      | `--site i18n-tt --env us`              | 与 I18N 共用 `i18n-tt` 登录          | 不支持                         | 支持     |
| I18N-BD | `--site i18n-bd`（`--site i18n` 等价） | `bytedcli --site i18n-bd auth login` | 不支持                         | 不支持   |
| EU-TTP  | `--site eu-ttp`                        | `bytedcli --site eu-ttp auth login`  | 支持（无对象级关卡、计划预检） | 支持     |

- 只有 `--site i18n-tt` 下有多个控制面；其他站点不需要传 `--env`。
- 其他站点（如 `boe`、`us-ttp`）返回 `BKE_INPUT_ERROR`。
- 只支持个人用户身份：`--as app` 或 `BYTECLOUD_AUTH_AS=app` 会返回 `BKE_INPUT_ERROR`。
- 在生产网先 `export BYTEDCLI_NETWORK_PROFILE=prod`，CLI 会改用对应控制面的生产网 host；发布计划、工单和 SpaceX 角色仍走办公网 host，生产网未验证。
- BKE API 使用个人 JWT；CN `pod execute` / `pod file get` 的 relay 阶段复用 `bytedcli auth login --session` 保存的个人 SSO 会话。登录只证明身份，后端仍校验访问权限。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## 命令速查

所有参数都是 option，没有位置参数；每个叶子命令都支持 `--env`；除 `pod execute` / `pod file get` 外均支持 `--raw`。`app`、`instance`、`pod`、`version`、`perm precheck`、`ticket list` 命令还支持 `--project`，默认 `<app>-application`（`app compare` 的基准用 `--baseline-project`）；`cluster instance list --app` 只按应用名过滤，不接受 `--project`。

| 目的                                             | 命令                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 应用详情                                         | `bke app get --app <app>`                                                                                                                                                                                                                                                            |
| 应用管理员                                       | `bke app admin list --app <app>`                                                                                                                                                                                                                                                     |
| 集群外部署可选的部署集群                         | `bke app deployed-cluster list --app <app> --cluster <a,b>`                                                                                                                                                                                                                          |
| 部署覆盖对比                                     | `bke app compare --app <app> --baseline <app> [--region <zone>] [--vdc <vdc>] [--scenario <s>] [--show missing\|extra\|both]`                                                                                                                                                        |
| 列应用的发布实例                                 | `bke instance list --app <app> [筛选]`                                                                                                                                                                                                                                               |
| 单个实例详情 / values / 对比                     | `bke instance get --app <app> --name <instance>`                                                                                                                                                                                                                                     |
| 新建实例（I18N / US / EU-TTP）                   | `bke instance create --app <app> --name <前缀> --cluster <a,b> [--deployed-cluster <目标>] --chart-version <v> --repo-version <主仓库版本> [--set <问题>=<值>] --title <t> --change-level L0..L3 [--scene TEST] --end <time> --content <c> --rollback-plan <r> --impact <i> [--yes]` |
| 实例批量体检                                     | `bke instance diagnose --app <app> [筛选] [--instance <a,b>] [--logs] [--warn-pattern <regex>] [--master-pattern <regex>]`                                                                                                                                                           |
| 列成员集群                                       | `bke cluster list [--name] [标签筛选]`                                                                                                                                                                                                                                               |
| 单个成员集群                                     | `bke cluster get --name <cluster>`                                                                                                                                                                                                                                                   |
| 某集群上所有应用的实例                           | `bke cluster instance list --cluster <cluster> [--app]`                                                                                                                                                                                                                              |
| Pod 列表 / 重启次数                              | `bke pod list --app <app> --instance <ri> [--workload <name>] [--restarts]`                                                                                                                                                                                                          |
| Pod 事件                                         | `bke pod events --app <app> --instance <ri> --pod <pod>`                                                                                                                                                                                                                             |
| Pod YAML                                         | `bke pod yaml --app <app> --instance <ri> --pod <pod>`                                                                                                                                                                                                                               |
| 容器日志                                         | `bke pod logs --app <app> --instance <ri> --pod <pod>\|--all-pods [--container <name>] [--grep <regex>] [--master-pattern <regex>]`                                                                                                                                                  |
| CN 容器执行 / 文件                               | `bke pod execute --command <cmd> [--yes]` / `bke pod file get --path <path> [--tail <n>] [--output <file>]`（均需 `--app --instance --pod`）                                                                                                                                         |
| 镜像 / chart 版本                                | `bke version image list --app <app> [--repo <name\|path\|remoteId>] [--type online\|test\|all]` / `bke version chart list --app <app>`                                                                                                                                               |
| 发布计划列表                                     | `bke plan list [--creator <user>] [--status created\|ready\|running\|paused\|success\|failed\|canceled] [--keyword <text>] [--app <app>] [--scan <n>]`                                                                                                                               |
| 计划详情 / 对象进度                              | `bke plan get --plan-id <id> [--objects]`                                                                                                                                                                                                                                            |
| 跟踪计划                                         | `bke plan follow --plan-id <id> [--until gate\|done] [--interval <sec>] [--timeout <sec>]`                                                                                                                                                                                           |
| 人工关卡                                         | `bke plan gate list --plan-id <id> [--active] [--page <n>] [--page-size <n>]`                                                                                                                                                                                                        |
| 变更管控预检（只读）                             | `bke plan precheck --plan-id <id> [--at <time>]`                                                                                                                                                                                                                                     |
| 确认关卡（CN）                                   | `bke plan gate confirm --plan-id <id> --app <app> [--node-id <id> \| --objects <a,b>] [--yes]`                                                                                                                                                                                       |
| 计划开始 / 暂停 / 继续 / 取消（CN）              | `bke plan start\|pause\|resume\|cancel --plan-id <id> --app <app> [--yes]`                                                                                                                                                                                                           |
| 对象重试 / 跳过 / 取消（CN）                     | `bke plan object retry\|skip\|cancel --plan-id <id> --app <app> --objects <a,b> [--node-id <id>] [--yes]`                                                                                                                                                                            |
| 应用的 RO 工单与计划（CN / I18N / EU-TTP）       | `bke ticket list --app <app> [--creator <user> \| --mine] [--op <op>] [--status <status>] [--since <time>] [--limit <n>] [--plan-steps]`                                                                                                                                             |
| RO 工单详情（CN / I18N / EU-TTP）                | `bke ticket get --ticket-id <id>`                                                                                                                                                                                                                                                    |
| 发版 / 新建实例前置检查（只读）                  | `bke perm precheck --app <app> [--cluster <cluster>] [--template-ri <instance>]`                                                                                                                                                                                                     |
| 我的发版权限与 SpaceX 角色（CN / I18N / EU-TTP） | `bke perm status`                                                                                                                                                                                                                                                                    |
| BKE 的 SpaceX 角色与成员（CN / I18N / EU-TTP）   | `bke perm role list [--scope product\|site] [--role <name>]`                                                                                                                                                                                                                         |

## 应用

```bash
bytedcli bke app get --app demo-app
bytedcli --json --site i18n-tt bke app get --app demo-app
bytedcli bke app admin list --app demo-app

# 应用不在默认 project（<app>-application）下时显式指定
bytedcli bke app get --app demo-app --project demo-project

# 部署覆盖：基准应用（--baseline，必填）有实例、demo-app 没有的集群
bytedcli bke app compare --app demo-app --baseline demo-baseline-app
# 两边都按 zone / VDC / 业务场景过滤；--show extra 列反向（demo-app 有、基准没有），both 两者都列
bytedcli --json bke app compare --app demo-app --baseline demo-baseline-app --region China-North --show both
# 基准应用不在默认 project 时
bytedcli bke app compare --app demo-app --baseline demo-baseline-app --baseline-project demo-base-project
```

- `app compare` 按每个发布实例所属的集群比较：集群外部署的实例算在目标集群上，`Deploy` 列（JSON `deployedCluster`）是 Pod 实际运行的集群。只用 BKE 的实例查询，两边各读一次。
- 已下线集群上的实例两边都不计入。实例不论状态都算覆盖；`covered_by_status` 按状态统计已覆盖集群上本应用的实例（`unreleased` 从未发布，`unknown` 没有状态）。文本模式有非 `succeed` 时给出带同一 `--site` / `--project` / `--env` 的 `bke instance list --status` 命令；该命令列的是全部集群，不受 compare 的过滤条件限制，`unknown` 没有对应的 `--status`，要看不带 `--status` 时的 Status 列。
- `--region` 决定两边各列出哪些集群；某个集群是否算已覆盖，按另一个应用的全部在线实例判断，同一集群上两个应用的 zone 标签写法不同也不会误报缺口。`--vdc`、`--scenario` 由 BKE 按同一条件过滤两边。
- 计数（`baseline_clusters`、`covered`、`coverage_ratio`、`missing_count`、`extra_count`、`by_zone`）总是两个方向都算；`--show` 只决定文本和 JSON 列出哪些集群行，未列出的一侧在 JSON 里为 `null`。
- 缺口行描述的是基准应用在该集群上的实例（实例名、部署方式）；`Arch`（`architecture`）来自对列出的集群做的集群查询（每 100 个集群一次）。查询失败时全部为 `null`，并写进 `errors`，其余结果照常输出；查询成功但集群没有返回或没有架构标签时也为 `null`，此时 `errors` 为空。

## 发布实例

```bash
# 默认每页 20 条，由 BKE 服务端分页
bytedcli bke instance list --app demo-app
bytedcli bke instance list --app demo-app --page 2 --page-size 50

# --status: all|succeed|deploying|init|failed|unreleased；--all 返回全部匹配
bytedcli --json bke instance list --app demo-app --status failed --all

# --keyword 匹配实例名或集群名，可重复或逗号分隔；多个值默认 or，--match and 要求全部命中
bytedcli bke instance list --app demo-app --keyword demo-cluster
bytedcli bke instance list --app demo-app --keyword demo-app --keyword demo-cluster --match and

# 集群、业务场景、VDC、版本、灰度筛选
bytedcli bke instance list --app demo-app --cluster demo-cluster
bytedcli bke instance list --app demo-app --scenario demo-scenario --vdc demo-vdc
bytedcli bke instance list --app demo-app --chart-version 1.0.0.1 --image-version 1.0.0.12
bytedcli bke instance list --app demo-app --gray true

# 按 zone（region）和主仓库版本（文本输出的 Version 列）筛选：BKE 不支持，读取全部匹配后本地过滤
bytedcli bke instance list --app demo-app --region China-North --repo-version 1.0.0.21

# 已下线集群上的实例：exclude（默认，与 BKE 控制台一致）| include | only
bytedcli bke instance list --app demo-app --offline include
bytedcli bke instance list --app demo-app --offline only

# 已创建但从未发布过的实例（没有状态、也没有发布工单）
bytedcli bke instance list --app demo-app --status unreleased --all

bytedcli bke instance get --app demo-app --name demo-app-demo-cluster
bytedcli bke instance get --app demo-app --name demo-app-demo-cluster --values
bytedcli bke instance get --app demo-app --name demo-app-demo-cluster --diff demo-app-other-cluster
bytedcli --site i18n-tt bke instance get --env us --app demo-app --name demo-app-demo-cluster
```

- `--image-version` 是构建镜像版本，由 BKE 服务端过滤；`--repo-version` 是主镜像仓库版本（`mainRepoVersion`），区分大小写精确匹配；`--region` 是实例的 zone 标签（如 `China-North`），不区分大小写，因为同一 zone 的标签大小写并不统一。两者都在本地过滤。
- 文本输出的 `Flags` 列：`gray`（实例所在集群带 BKE 灰度 / test canary 标记）、`locked(<owner>)`（集群锁）、`offline`（集群已下线）、`unreleased`（从未发布）。
- `instance get` 展示集群、zone / VDC、状态与原因、chart 与主仓库版本、in-cluster / out-cluster 部署、canary 与 max unavailable、最近工单、创建人与复制来源、镜像仓库版本。
- `--diff <other>` 比较同一应用的两个实例：规格字段（集群、zone、VDC、状态、chart 版本、rollout 配置、部署方式、灰度 / 锁 / 离线标记、各镜像仓库与镜像版本）加 values 的 unified diff；`--diff` 与 `--values` 不能同时使用。

## 实例体检

```bash
# 应用的全部匹配实例（不分页）：读 rollout status、各 workload 的 Pod 和每个 Pod 的详情，给出健康分类
bytedcli bke instance diagnose --app demo-app

# 与 instance list 相同的筛选参数；--instance 收窄到指定实例（可重复或逗号分隔，必须在筛选结果里）
bytedcli bke instance diagnose --app demo-app --region China-North --repo-version 1.0.0.21
bytedcli bke instance diagnose --app demo-app --instance demo-app-demo-cluster

# --logs：ready_with_restarts / partial_ready / not_ready_or_crash 三类实例各挑一个当前 Pod，读主容器日志尾部找致命行
# （klog F、panic:、fatal error:，以及行首或 E/F 级 klog 行里的 OOMKilled / out of memory）
bytedcli --json bke instance diagnose --app demo-app --logs --category not_ready_or_crash,ready_with_restarts

# --warn-pattern：在服务中的实例里各读一个 ready 新 Pod 的日志尾部（--warn-tail，默认 2000 行），统计匹配行；可重复，不按逗号拆分
# --master-pattern：先找日志命中它的新 Pod（master）来读；旧 Pod 残留时也用它判断旧 Pod 是否仍是 master
bytedcli bke instance diagnose --app demo-app --warn-pattern 'snapshot unavailable' --master-pattern 'role=master'
```

| 分类                         | 含义                                                                                                                                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ok`                         | workload 全部就绪，当前 Pod 都 ready；读不到 Pod 详情时 detail 注明 `restarts not checked`。期望副本为 0 且没有 Pod 时也是 `ok`                                                                   |
| `ready_with_warnings`        | 同 `ok`，但 `--warn-pattern` 在读到的 Pod 日志里命中（只在传了 `--warn-pattern` 时出现）                                                                                                          |
| `ready_with_restarts`        | 全部就绪，但当前 Pod 有重启；detail 带最近一次退出原因                                                                                                                                            |
| `partial_ready`              | 部分当前 Pod 就绪，其余的原因写在 detail                                                                                                                                                          |
| `pending_sched_old_pod_left` | 新 Pod 没跑起来，旧 ReplicaSet 的 Pod 还在服务；看 `oldPod` 与 `newVersionEffective`：`false` 表示旧 Pod 的镜像已不在当前 spec 中，新版本未生效；`null` 表示仅凭镜像无法判断（例如只改了 values） |
| `pending_before_upgrade`     | 当前 Pod 都在 Pending，且有 Pod 已 Pending 超过 1 天                                                                                                                                              |
| `pending_sched_no_pod`       | 当前 Pod 都在 Pending（等待调度、拉镜像等），没有 Pod 在跑                                                                                                                                        |
| `not_released`               | 实例只有 CR，从未发布；这类实例读不到 Pod 时仍归 `not_released`，原因在 `error`，不计入 `pod_query_failed`，也不影响退出码                                                                        |
| `not_ready_or_crash`         | 没有就绪的当前 Pod（CrashLoopBackOff、没有 Pod、没有 workload 等）；有在跑但未就绪的当前 Pod 时归入这一类，即使另有 Pending 的 Pod                                                                |
| `pod_query_failed`           | 读不到 rollout 或 Pod（如成员集群不可达，已按 GET 重试），原因在 `error`                                                                                                                          |

- 新旧 Pod 按 ReplicaSet 区分：BKE 标为 stale 的、或不属于最新 ReplicaSet 的 Deployment Pod 记为 `old`；分类只看当前（新 ReplicaSet）的 Pod，旧 Pod 只用来判断是否仍在服务。准入失败（如 `UnexpectedAdmissionError`、`OutOfcpu`）的 Pod 会被控制器替换，不算当前 Pod，只在 detail 里注明。
- `--concurrency`（默认 8，1–16）是同时体检的实例数，每个实例内并发读 4 个 Pod 详情。参考耗时（只读实测，默认并发）：CN 约 970 个实例约 100 秒，I18N（`--site i18n-tt`）50 个实例约 75 秒；`--logs`、`--warn-pattern`、`--master-pattern` 会逐个读日志，跨地域控制面更慢，先用筛选或 `--instance` 缩小范围。
- 文本输出默认列出非 `ok` 的分类，`--category` 指定要列的分类；只有一个实例时打印它的 Pod 表（含 NOTE）和结论。JSON 的 `summary` 始终统计全部实例，`--category` 只过滤 `items`。
- `--logs` 先读当前容器，Pod 重启过再读 previous；previous 有致命行，或当前容器读不到时，采用 previous。两份日志互不影响，都读不到时 detail 注明 `log scan failed`。`log` 的 `lines`、`fatalLines`、`signature`、`sample` 都来自 `source` 指明的那份日志，`previousSignature` 是 previous 的签名（没读或没有时为空）。
- `--master-pattern` 只在每个 Pod 最近 200 行里找，要用 master 周期性打印的标记；只在选举时打印一次的行（如 `became leader`）多半已经不在这 200 行里。日志读不到、又没有其他 Pod 命中时，`masterFound` 为 `null`。
- 有实例为 `pod_query_failed` 时退出码为 1，其余实例照常输出；不健康的分类本身不影响退出码。

## 成员集群

```bash
# 标签筛选（--group / --scenario / --region / --dc）在服务端执行；--region 对应 BKE 的 zone 标签
bytedcli bke cluster list --region China-North --scenario demo-scenario
bytedcli bke cluster list --name demo-cluster-a,demo-cluster-b
# --phase 与 --keyword（匹配集群名或描述）在本地过滤
bytedcli bke cluster list --group demo-group --phase running --page-size 50

bytedcli bke cluster get --name demo-cluster

# 一个集群上所有应用的实例；--app 只保留某个应用
bytedcli bke cluster instance list --cluster demo-cluster
bytedcli --json bke cluster instance list --cluster demo-cluster --app demo-app
```

- 不带 `--name` 或标签筛选时 `cluster list` 会拉全量（CN 约 20 MB），优先带筛选条件。
- 标签值只允许字母、数字、`.`、`_`、`-`，每个标签参数只接受一个值。

## Pod

```bash
bytedcli bke pod list --app demo-app --instance demo-instance
bytedcli --json bke pod list --app demo-app --instance demo-instance --workload demo-workload --restarts --page 2 --page-size 20
bytedcli bke pod events --app demo-app --instance demo-instance --pod demo-pod
bytedcli bke pod yaml --app demo-app --instance demo-instance --pod demo-pod --raw
bytedcli --nomask bke pod yaml --app demo-app --instance demo-instance --pod demo-pod
bytedcli bke pod logs --app demo-app --instance demo-instance --pod demo-pod --container demo-container --tail 20
bytedcli bke pod logs --app demo-app --instance demo-instance --pod demo-pod --container demo-container --since 30m
bytedcli bke pod logs --app demo-app --instance demo-instance --pod demo-pod --container demo-container --previous --timestamps
bytedcli bke pod logs --app demo-app --instance demo-instance --pod demo-pod --since 1h --grep 'panic|fatal'

# 实例的全部 Pod（所有 workload、任何阶段），并发 4；--master-pattern 标出日志里出现主节点标志的 Pod
bytedcli bke pod logs --app demo-app --instance demo-instance --all-pods --container demo-container --tail 500 --master-pattern 'became leader'
bytedcli --json bke pod logs --app demo-app --instance demo-instance --all-pods --grep 'OOM|panic'
```

- `pod list` 从 rollout status 读取 workload 名称，再逐个列 Pod，排序后本地分页；`--workload` 必须是 status 中的名称，不要自己拼。`ready` 是就绪容器数 / 容器总数。
- 默认只发 `1 + workload 数` 次请求；`--restarts` 再为每个 Pod 发一次详情 GET（并发 8），`restarts` 是各容器 `restartCount` 之和，未查询或未上报时为 `null`。
- `pod events` 按 `lastTimestamp`（为空时用 `eventTime`）由早到晚排序。
- `pod yaml`（含 `--raw`）默认按 values 的规则打码，`--nomask` 显示原文。
- `pod logs` 只读一次 tail（`--tail` 默认 200），不跟随、不打码。省略 `--container` 时，Pod 只有一个容器才自动选取，否则报错并列出容器名。
- `--since 30m|2h|1d` 会请求 `timestamps=true`，在本次 tail 内按本机时间过滤；不加 `--timestamps` 时去掉时间前缀。`truncated_by_tail: true` 表示读满了 `--tail`，时间窗口可能不完整，应增大 `--tail`。
- `--grep` 是 JavaScript 正则（非 Unicode 模式），区分大小写；在 `--since` 之后、对去掉时间前缀的正文匹配，非法时返回 `BKE_INPUT_ERROR`。
- `--master-pattern` 没有默认值，对本次读到的每一行（`--since` / `--grep` 之前）匹配，有一行命中就记 `master: true`；不传时 `master` 为 `null`。
- `--pod` 与 `--all-pods` 必须且只能传一个，否则返回 `CLI_ARGS_*`（退出码 2）。`--all-pods` 从 rollout status 读出全部 Pod 再逐个读日志；没传 `--container` 时只能自动选取单容器 Pod（rollout 列表没有容器信息时读一次 Pod 详情），多容器 Pod 记为该 Pod 的 `BKE_INPUT_ERROR`。某个 Pod 读取失败只记在它的 `error` 里，其余照常输出；有失败时信封仍是 `success`，`failed` 大于 0、退出码 1。
- 文本模式 stdout 只打印日志行，`--raw` 打印未过滤的原文；带 `--master-pattern` 时 `Master: …` 汇总行打印到 stderr，`--all-pods` 有失败时还会在 stderr 打印 `<失败数> of <Pod 数> pod(s) failed.`。`--all-pods` 每个 Pod 先在 stdout 打印 `==> <pod> [<workload>, master] <保留行数>/<读到行数> lines <==`，失败时打印 `ERROR <code>: <message>`；实例没有 Pod 时打印 `No pods in <instance>.`。JSON 的 `lines` 是过滤结果，`fetched_lines` 是本次读到的行数，`matched_lines` 是 `--grep` 保留的行数（不传时为 `null`）。

## CN 容器内执行与文件

```bash
# 先预览；--yes 执行，--dry-run 优先于 --yes
bytedcli --site cn bke pod execute --app demo-app --instance demo-instance --pod demo-pod --command 'ls /opt/tiger'
bytedcli --site cn bke pod execute --app demo-app --instance demo-instance --pod demo-pod --command 'ls /opt/tiger' --yes
# 只读文件无需 --yes；默认输出文本，二进制输出 base64
bytedcli --site cn bke pod file get --app demo-app --instance demo-instance --pod demo-pod --path /opt/tiger/log/demo.log --tail 100
bytedcli --site cn bke pod file get --app demo-app --instance demo-instance --pod demo-pod --path /opt/tiger/log/demo.log --output ./demo.log
```

- 仅 CN；其他控制面在登录 / 请求前报错。ROW 诊断需使用获准的 SDP 流程，本命令不支持 ROW BKE Pod。
- 两个命令都接受 `--container`；只有一个容器时可省略。`execute` 传由 `sh -c` 执行的 shell 字符串，stdout / stderr 合并为一个终端流并移除 ANSI。
- `--timeout-ms` 默认 30000，范围 1–300000，限制命令 / socket 等待；relay HTTP 使用全局 HTTP 超时。超时不证明远端进程已经结束，确认结果后再决定是否重试。
- 需要个人 JWT 和已保存的 SSO 会话；会话过期执行 `bytedcli auth login --session`。需要 OTP 时使用控制台，本命令不接收 OTP。
- 文件须为绝对路径的普通文件；容器须有 bash、head、tail、base64。`--max-bytes` 默认 1048576、最大 10485760；超限报错，可缩小 `--tail` 或提高限制。读取失败不保存部分结果。
- `--output` 保存原始字节到新文件，不覆盖已有文件。JSON 返回 `encoding`（utf8/base64）和 `content`；保存时 `content=null`，返回 `outputFile`。文件内容不打码。
- 两个命令均无 `--raw`。`execute` JSON 包含 `dryRun`、`pod`、`container`、`command`、`timeoutMs`、`exitCode`、`output`、`durationMs`；完整结果的远端非零或未知退出码时信封为 success，CLI 退出 1；超时、断线或输出边界不完整时为 error，执行结果未知。

## Version

仅列 SCM `build_ok` 版本；`--type online|test|all` 默认 `online`，`all` 是 online + test（不含 offline），由新到旧，与新建实例表单的版本下拉一致（表单默认选第一个，常是 test 包）；`--page` 默认 1，`--page-size` 默认 20，由 SCM 分页。镜像默认选应用标记的主仓库（标记了多个时必须传 `--repo`），`--repo` 可按 name / path / remoteId 选择；chart 使用应用的 `chartRepo`，SCM 中必须有同名仓库（不区分大小写）。

SCM 站点由 BKE 控制面决定：CN 用 `cn`，I18N、US 和 EU-TTP 都用 `i18n-tt`（EU-TTP 应用引用的是同一批 SCM 仓库），I18N-BD 用 `i18n-bd`。

```bash
bytedcli bke version image list --app demo-app --repo demo-repo --page-size 3
bytedcli --json bke version chart list --app demo-app --type test
```

## Plan

读命令支持 CN、I18N（`--site i18n-tt` 默认 `--env i18n`）和 EU-TTP（`--site eu-ttp`）；写命令只在 CN，见下文「Plan 写操作」。EU-TTP 没有 Athena，计划里有运行中的灰度对象时 `plan get` / `plan gate list` 直接报错（读不了对象级关卡），到 BKE 控制台看；EU 网关没登记变更管控的 `checkRule`，`plan precheck` 会返回 OG 403。

```bash
bytedcli bke plan list --app demo-app --scan 50
bytedcli bke plan get --plan-id "$demo_plan_id" --objects
bytedcli --json bke plan follow --plan-id "$demo_plan_id" --until gate --timeout 600
bytedcli bke plan precheck --plan-id "$demo_plan_id" --at 2026-01-02T14:00
```

- `plan list` 默认由服务端分页（page 1、size 20）。计划查询不支持按应用过滤，所以 `--app` 会读取最新 `--scan` 个计划（默认 200，上限 1000）的 base-info（并发 8），匹配后本地分页：`total` 是扫描范围内的匹配数，`unresolved` 是 base-info 返回 not found 的计划数，其他错误（认证、解析、网络）直接报错。`truncated: true` 表示扫描停在 `--scan`、服务端还有更早的计划，文本模式此时提示调大 `--scan`。不加 `--app` 时 `items[].application`、`scanned`、`unresolved`、`truncated` 为 `null`。
- `plan get` 列出节点和关卡，口径同 `plan gate list --active`：计划级关卡是每个运行中的 flow 节点的全部 manualConfirm 条件（`uuid`、`pipelineId`、`taskRunId`、`status`），对象级关卡是 running / paused / waiting / failed 灰度对象的 Athena CONFIRM 活动。`waiting` 标记仍在等待的关卡；条件还是 `ready` 时（关卡刚开始几秒，控制台还没给出确认动作）不算等待。计划的 base-info 返回 not found 时 `application` 为 `null`，其他错误直接报错（`plan follow`、`plan gate list` 相同）。不加 `--objects` 时只为查关卡遍历未结束节点（不是 success / skipped / canceled）的对象，`objects` 为 `null`；`--objects` 逐页遍历全部节点 ticket → stage → batch 的对象。pipeline ID 为 0 的对象尚未调度，记为 `pending`，不读详情。
- `plan gate list` 在计划级关卡之外，再列出灰度对象的 Athena CONFIRM 活动；灰度对象来自 `batch_type` 为 gray 的批次，或所在节点分组名带 BKE 灰度标签（`灰度`）的批次。`--active` 仍遍历全部 ticket / stage / batch 页，只对 running / paused / waiting / failed 的对象查询 CONFIRM 活动。计划级关卡的 `waiting` 判断同 `plan get`（条件还是 `ready` 时不算等待）。关卡全部读取后本地分页（默认 page 1、size 20）：`total` 是全部关卡数，`waiting` 是全部等待中的关卡数。
- `plan precheck` 用计划保存的变更管控参数调用 ByteChange 的规则校验接口（`gateway/checkRule`），回答「在 `--at`（默认现在）启动会不会被拦」。该接口只校验规则，不上报变更事件、不发起审批。`--at` 必须带时分，接受本地时间（如 `2026-01-02T14:00`）、RFC 3339 或 10 位 epoch 秒；只给日期会报 `BKE_INPUT_ERROR`。只看顶层 `checkStatus`：`pass` 放行，`hold` / `refuse` 会拦下。`policies[]` 里大多数命中策略即使整体通过也显示 `status: hold`，不要据此判断；按时段拒绝的策略显示 `refuse`（`hint` 会点名）；policyId 0 是内置的「需要已通过的申请单」规则，显示 `pass` 或 `hold`。`inAllowedHours` 表示该时间是否落在这条策略允许的时段内（禁止类策略也一样，`false` 表示落在禁止时段）。`approvers` 是窗口内的审批步骤和窗口外追加的审批人；policyId 0 没有审批人，策略读取失败时 `approvers` 为 `null`、原因在 `approversError`。启动时间按计划自己的审批窗口（`applyTickets[].windows`，epoch 秒）校验，早于窗口开始也会 `hold`（`reason: INVALID_APPLY_PLAN`）；`hint` 据此给出下一步：等窗口开始、补窗口或重提计划、等审批通过，或换到策略允许的时段。无论结果如何退出码都是 0。
- `plan follow` 默认 `--until done --interval 30 --timeout 600`（秒；`--interval` 5–3600，`--timeout` 至多 86400）。`done` 指 success / failed / canceled；`gate` 在出现等待中的关卡（计划级关卡，或灰度对象的 Athena CONFIRM，口径同 `plan get`）或计划结束时停止，计划级条件还是 `ready` 时继续等。`gate` 每次轮询都按 `plan get` 的口径读取关卡；`done` 只读计划级关卡，结果的 `gates` / `waiting` 不含对象级关卡。超时返回当前状态并带 `timedOut: true`，不报错。文本模式逐行打印状态变化，停在关卡时列出等待中的关卡；JSON 只输出最终状态和 `changes[]`。

`--raw` 只包含组成视图的响应，其中 `run`、`gates`、`objectGates` 是 bytedcli 裁剪后的视图，不是上游对象（节点动作只保留 opKey，不含对象运行参数和 Athena 上下文）：

- `plan list`：`{pages, applications}`。`pages` 按页序列出每次计划查询的 `{data, page}`（RO 响应的 `data` 与分页信息）；`applications` 以计划 ID 为 key，值是 base-info 的上游 `data`，只含读取成功的计划。不加 `--app` 时 `pages` 只有一页，`applications` 为 `null`。
- `plan get` / `plan follow`：`{plan, run, application, gates, objects}`。`plan`、`application` 是计划详情和 base-info 的上游 `data`（base-info not found 时 `application` 为 `null`）；`run` 是 `{status, nodes}`；`gates` 按运行中的 flow 节点各列一组 manualConfirm 条件（`uuid/pipelineId/taskRunId/status`）；`objects` 只在 `--objects` 时有值，按遍历顺序列出 ticket 详情和 stage 详情的上游 `data`、batch 每页的 `{data, page}`，否则为 `null`。对象级关卡只在视图的 `gates` 里，`raw` 不含 Athena 响应。`plan follow` 是最后一次读取的 `raw`。
- `plan gate list`：`{plan, objects, objectGates}`。`plan` 同 `plan get` 的 `raw`（其中 `objects` 为 `null`）；`objects` 是上面的遍历响应，不受 `--active` 影响；`objectGates` 是全部对象级关卡，不受本地分页影响。
- `plan precheck`：`{plan, request, check, policies}`。`plan` 是计划详情的上游 `data`，`request` 是实际发送的校验请求体，`check` 是校验接口的上游 `data`，`policies` 以策略 ID 为 key，值是策略详情的上游 `data`（读取失败为 `null`）。

## Plan 写操作

仅 CN（`--site cn`），只推进已有计划，不新建计划。每个写命令都要求 `--plan-id` 和 `--app`：`--app` 必须与计划 base-info 中的应用一致，否则返回 `BKE_INPUT_ERROR`，不发写请求。

```bash
# 默认只预览：读取计划、解析目标，打印将要发送的每个 POST（URL + body），不发写请求
bytedcli bke plan gate confirm --plan-id "$demo_plan_id" --app demo-app
# 用户同意这一次操作后才加 --yes（写在子命令之后），并带上预览中的 --node-id；同时带 --dry-run 时仍只预览
bytedcli bke plan gate confirm --plan-id "$demo_plan_id" --app demo-app --node-id "$demo_node_id" --yes

# 灰度对象的 Athena CONFIRM：逐个点名对象，没有 --all
bytedcli bke plan gate confirm --plan-id "$demo_plan_id" --app demo-app --objects demo-instance-a,demo-instance-b

bytedcli bke plan pause --plan-id "$demo_plan_id" --app demo-app
bytedcli --json bke plan object retry --plan-id "$demo_plan_id" --app demo-app --objects demo-instance-a --node-id "$demo_node_id"
```

- `gate confirm` 不带 `--objects` 时确认计划级关卡：只看 `special/flow` 节点，不带 `--node-id` 时只取运行中的节点，`--node-id` 限定到一个节点。确认参数取自控制台在节点或仍在等待的 manualConfirm 条件上提供的 `flowManualConfirmNodeRun` 动作，CLI 不自己拼；没有该动作的节点记入 `skipped`。关卡刚开始的几秒内条件还是 `ready`，控制台还没给出这个动作：这类关卡记入 `skipped`（原因里带节点 ID）并计入 `notReady`，不发请求，预览和 `--yes` 都以退出码 1 结束；几秒后重新预览，再带预览给出的 `--node-id` 确认，不要原样重跑 `--yes`。条件已是 running 但没有确认动作的关卡只记入 `skipped`。带 `--yes` 时目标会重新解析，计划在预览后推进的话可能换成下一个关卡，所以提交时带上预览中的 `--node-id`（文本预览会给出重跑命令）。
- 带 `--objects` 时只确认这些灰度对象仍在等待的 CONFIRM 活动；`--objects` 与 `--node-id` 不能同时使用；`--objects` 解析为空（如 `--objects ""`）时返回 `BKE_INPUT_ERROR`，不会改为确认计划级关卡。
- 发送用的 `--yes` 写在子命令之后；写在 `bke` 前面的全局 `--yes` 只批准安全策略确认，命令仍只预览。
- `start` 预览（不带 `--yes`，或带 `--dry-run`）会顺带跑一次只读的 `plan precheck`（按现在启动），结果在 `precheck`；预检失败不影响预览，原因在 `precheckError`。带 `--yes` 时不再预检；其他写命令这两个字段都是 `null`。
- `start` 被变更管控拦下（响应 `checkStatus` 为 hold / refuse）时计划不会开始：`result.response` 原样保留响应，文本模式打印 `checkStatus` / `checkResults`，`held: true`，退出码 1。用 `bytedcli --site cn bke plan precheck` 看原因，常见是启动时间早于计划自己的审批窗口。
- 计划 `cancel` 不可逆，文本预览会提示。
- `object retry` 重试对象第一个失败的 task，没有失败 task 的对象跳过；`object skip` 让对象不再参与本次执行；`object cancel` 取消对象的流水线。尚未调度（pipeline ID 为 0）的对象不能操作，记入 `skipped`。同名对象出现在多个节点时返回 `BKE_INPUT_ERROR`，用 `--node-id` 指定节点。
- 多个目标逐个发送，写请求不自动重试。某个目标失败时记在它的 `result` 里，其余照发；有失败时信封仍是 `success`，但 `failed` 大于 0、退出码 1。超时或网络错误记为 `BKE_ERROR`，`message` 注明结果未知：写可能已生效，先用 `plan get` 核实，不要直接重跑。没有可操作目标时只返回 `skipped`，退出码 0；`notReady` 大于 0 时退出码 1。
- 发送后回读一次状态填入 `after`；回读失败时写请求已经发出，`readBackError` 记录原因，`after` 为 `null`。
- `--raw` 是 `[计划详情, base-info, …]`：依次为解析目标时读取的上游响应（计划运行、条件、对象或关卡遍历），不含写响应；写响应在各目标的 `result.response` 中。`start` 预览末尾再追加一项预检的 raw（同 `plan precheck --raw`，预检失败时为 `null`）。

## 新建实例

I18N / US（`--site i18n-tt`，US 加 `--env us`）和 EU-TTP（`--site eu-ttp`）：`instance create` 按控制台「创建应用实例」表单建出一张 RO 工单（状态 created，不会自动开始），可指定 chart 版本、主仓库镜像版本和集群外部署的部署集群。默认只预览，`--yes` 才提交。参数规则、输出字段、结果判断和 Agent 流程见 `references/instance-create.md`（`bytedcli self skill get bytedance-bke/references/instance-create.md`），使用前先读。

## 工单

CN、I18N（`--site i18n-tt` 默认 `--env i18n`）和 EU-TTP（`--site eu-ttp`），只读。

```bash
# 按应用名查 RO 工单和应用的发布计划，按创建时间倒序，默认 50 条
bytedcli bke ticket list --app demo-app

# 扫描某人的工单并保留本应用的（含复制计划）；--mine 用 bytedcli auth login 保存的用户名
bytedcli --json bke ticket list --app demo-app --mine --op copy --since 2026-01-01
bytedcli bke ticket list --app demo-app --creator demo-user --status failed --limit 200

bytedcli bke ticket get --ticket-id "$demo_ticket_id"
bytedcli --json --site i18n-tt bke ticket get --ticket-id "$demo_ticket_id" --raw
```

- 行分两类：`kind: ro` 是 RO 工单，`kind: plan` 是发布计划。`op`：`create` 新建实例、`update` 更新（RO 更新工单和批量更新计划）、`rollback` 回滚、`delete` 删除、`copy` 复制实例的计划、`baseline` 基线计划、`plan-step` 计划派生的 RO 工单、`other` 其他。回滚与更新是同一种 RO 工单类型，按 RO 模板区分（CN 模板 35，I18N 模板 41）。
- 不带 `--creator` / `--mine` 时按应用名查工单中心：RO 工单按对象名（`<app>.<cluster>.<instance>`），计划按应用标签。这种方式查不到复制计划和部分 RO 工单，`notes` 会提示。
- 带 `--creator` / `--mine` 时扫描这个人的全部工单，保留本应用的：RO 工单看对象名，计划看应用标签，计划派生的 RO 工单在其计划（含下面认定的复制计划）属于本应用时保留。复制计划不带应用名：读出它要复制的源实例（`templateInstance`），该实例在本应用的 project（`--project`，默认 `<app>-application`）中且其所属应用就是本应用时列入 `items`，`objects` 是目标集群数，集群外复制的部署集群在 `deployedCluster`；源实例不在 project 中（已删除）、属于同 project 的其他应用或读不出所属应用，或计划里读不出源实例（`templateInstance` 为 `null`）时列在 `unverified_copy_plans`。只检查满足 `--op`、`--status`、`--since` 的复制计划，且最多检查最新的 200 个（每个要读两次），`copy_plans_checked` 是检查数，`copy_plans_unchecked` 是超出上限未检查的数量（`notes` 会提示用 `--since` 收窄）；读取失败的列在 `copy_plan_errors`（`id/code/message`），`notes` 给出数量。
- 每次搜索最多读 2000 条记录，超出时 `scan_truncated: true`，更早的记录没有读到。`--op`、`--status`（不区分大小写）、`--since` 在本地过滤；`--since` 接受日期（本地零点，如 `2026-01-02`）、本地时间（如 `2026-01-02T14:00`）、RFC 3339 或 10 位 epoch 秒。过滤后按创建时间倒序取前 `--limit` 条（默认 50，上限 2000）：`total` 是匹配数，`returned` 是返回数，`truncated: true` 表示还有更多匹配。
- 计划派生的 RO 工单（`op: plan-step`）默认隐藏，加 `--plan-steps` 或 `--op plan-step` 才列出。
- 只为返回的行再读一次详情：RO 工单读模板名，计划读标题、变更等级与场景（`changeScenes` / `strategyScenes`）；读取失败写进该行的 `error`，其余照常输出。
- 参考耗时（只读实测）：CN 按应用名约 2 秒；I18N 扫描一个人的工单约 9 秒。
- `ticket get` 只接受 RO 工单 ID；发布计划用 `bke plan get --plan-id`。工单本身（base data 与 detail）必须读到，进度、对象、操作记录、审批（变更管控申请）和所属计划读取失败时写进 `errors`（`part/code/message`），退出码仍为 0。
- `ticket get` 展示模板（名称、模板 ID、工单类型）与 `op`、状态与起止时间、所属计划、回滚关系（`rollbackFrom` 是本工单回滚的工单，`rollbackTicketId` 是回滚本工单的工单）、审批（变更等级 / 类型 / 场景、BPM 单号与审批人、审批页）、对象（集群、集群组、场景、zone，chart 与主仓库版本的旧 -> 新）、各阶段及其批次策略（`ratio` 百分比或 `count` 个数、并发、容忍度、暂停策略）、操作记录。
- 策略场景（`strategyScenes`，如 `TEST` 表示新集群或测试集群）只在发布计划和 BPM 审批单上：工单属于计划时取自计划；不属于计划时文本模式提示用 `bytedcli --json --site <同一站点> bpm ticket get --ticket-id <BPM 单号>` 查看 `data.config.strategyScenes`（`bpm ticket get` 的文本视图不显示该字段）。BPM 单号在 CN 和 I18N 之间会重复，必须带同一个 `--site`，否则会读到另一个站点的单子。
- `ticket list` 的 `createdAt` 是 epoch 秒；`ticket get` 的时间是 RO 返回的 RFC 3339 字符串，未开始或未结束时为 `null`。文本模式时间都显示为本地时间，精确到秒。
- `--raw`：`ticket list` 是 `{records}`，与 `items` 同序的工单中心原始记录；`ticket get` 是 `{base, detail, progress, objects, events, approval, plan}`，各部分的上游 `data`，读取失败或不存在时为 `null`。values 的打码与省略见下文「values 打码」。

## 权限预检

```bash
bytedcli bke perm precheck --app demo-app
bytedcli --json bke perm precheck --app demo-app --cluster demo-cluster --template-ri demo-app-demo-cluster-abcde
```

- 只读：逐项检查当前用户发版和新建实例的前置条件，不申请权限、不改任何对象。各项并发读取。某项读取被拒（403）、对象不存在或上游出错时只让这一项失败，`detail` 是 HTTP 状态和上游消息，`remedy` 跟着失败原因走：403 给权限类建议，不存在给核对名称或 `--site` / `--env` 的建议，其他错误提示重试。登录失效（401）、`--as app`、名称非法等会让每一项都失败的错误直接让整条命令报错，按错误的 `hint` 处理。
- 必过项，失败时 `ready: false`：
  - `ro_permission`：RO 权限 `release_plan_operate`，新建和操作发布计划都需要，由 BKE 的 SpaceX 角色 `release_plan_operator` 授予。`detail` 带 RO 返回的 `hasPermission` / `canApply`。
  - `app_admin`：当前用户在应用管理员列表中，`detail` 列出现有管理员。比对的是 `bytedcli auth login` 保存的用户名，不展开用户组。
  - `cluster`（带 `--cluster`）：成员集群可读，`detail` 附 phase、zone、VDC、场景、集群组、架构。phase 只作参考：不是 `running` 时 `remedy` 会提示，但这一项不算失败，因为这类集群上的实例也可能正常运行。
  - `template_instance`（带 `--template-ri`）：要复制的源实例可读，`detail` 附所在集群、部署方式（如 `out-cluster -> <目标集群>`）和 chart 版本。
- 可选项，失败不影响 `ready`：
  - `cluster_definitions`：集群定义可读。控制台的新建实例表单靠它列出集群；读不到时改为复制已有实例来建。只读一条，不拉全量列表。
  - `platform_project`：`platform` 项目可见，成员集群都属于这个项目。
  - `out_cluster`：应用允许集群外部署（实例部署到另一个集群）；带 `--template-ri` 时以该实例的身份询问。
  - `cluster_free`（带 `--cluster`）：该集群上还没有本应用的实例，在线和离线集群都会查。已有实例时 `detail` 列出实例名，这时应更新已有实例，不要再建一个。
- `ok: null` 表示未检查，不影响 `ready`：RO 只在 CN / I18N / EU-TTP 提供，US、I18N-BD 上 `ro_permission` 为 `null`；`app_admin` 依赖 `bytedcli auth login` 保存的用户名，读不到时为 `null`，`remedy` 提示先登录；RO 或 BKE 的响应缺少 `hasPermission` / `enabled` 时对应项也为 `null`。
- 无论结果如何退出码都是 0，结论看 `ready` 和 `items[].ok`。文本模式逐项列出 `Result`（`yes` / `NO` / `no (optional)` / `not checked`），末行汇总：有必过项失败时列出它们；否则写 `Ready: no required check failed.`，再列出未检查项和可选项缺口。
- `--raw` 以检查项 `id` 为 key 列出上游响应，读取失败或未执行的项为 `null`；`cluster_free` 和 `template_instance` 中的 values 与其他实例视图一样打码。
- `ro_permission` 失败时 `remedy` 末尾提示用 `bytedcli --site <同一站点> bke perm status` 查看持有的 SpaceX 角色。

## 发版权限与 SpaceX 角色

```bash
bytedcli bke perm status
bytedcli --json --site i18n-tt bke perm status
bytedcli bke perm role list
bytedcli --json bke perm role list --scope site --role release_plan_operator
```

- 只读，支持 CN、I18N 和 EU-TTP；US、I18N-BD 在取 JWT 前报 `BKE_INPUT_ERROR`。不需要 `--app`，看的是账号在当前控制面的权限；某个应用能不能发版、能不能新建实例用 `perm precheck`。
- `perm status` 并发读取三次：RO 权限，以及 SpaceX 的产品级（BKE）和站点级（`bke_cn` / `bke_i18n` / `bke_euttp`）角色。
  - `ro_permission`：必过项，同 `perm precheck`，决定 `ready`。RO 没给 `hasPermission` 时为 `ok: null`，`ready` 仍为 `true`，不要当成有权限。
  - `spacex_role`：可选项，不影响 `ready`。只要产品级或站点级任一级持有 `release_plan_operator` 就为 `true`，`detail` 写两级各自的结果（`yes` / `no` / `role not listed`，读取失败时为 HTTP 状态和上游消息）。两级都没有时：RO 权限已通过则 `remedy` 为 `null`，`detail` 说明能否发版以 RO 权限为准（角色可能在其他资源范围授予）；RO 权限未通过则提示在 SpaceX 上申请该角色，再在同一站点重跑 `perm status` 确认（它同时读两级；`perm role list` 一次只读一级）。有一级读取失败、另一级没有时：被拒（403）提示找 BKE SRE 确认能否查看角色，其他错误提示稍后重跑。
  - `roles`：两级各自持有的全部角色名，读取失败的一级为 `null`。
  - 单次读取被拒（403）或上游出错时只让对应项失败；登录失效（401）或 `--as app` 让整条命令报错。退出码始终为 0。
  - 文本模式：检查表、`Your SpaceX roles: product: …; site: …`、末行汇总（同 `perm precheck`）。
- `perm role list` 读一级角色：`--scope product`（默认，BKE 产品）或 `--scope site`（当前控制面的站点），按角色名排序。
  - `mine` 是 SpaceX 对当前用户的判断。通过部门或组授予的人不会单独出现在成员里，判断“我有没有”只看 `mine`。
  - `--role <name>` 按精确名称只看一个角色并列出成员（`userName`、`displayName`、`type`、`inherited`）。`type` 为 `person`、`department`（`displayName` 是部门名）、`group`、`service`，其他账号类型原样保留。角色名不存在时报 `BKE_NOT_FOUND`，`hint` 给出列出角色名的命令。
  - 文本模式：`Role | Mine | Members` 表和 `You hold: …`；带 `--role` 时另起一节列成员。
- `--raw`：`perm status` 是 `{ro_permission, roles_product, roles_site}`，各次读取的上游 `data`，失败为 `null`；`perm role list` 是该级的完整上游 `data`（带 `--role` 也不裁剪）。

## 输出

- 需要机器可读输出时把全局 `--json` 放在 `bke` 前面，例如 `bytedcli --json bke instance list --app demo-app`。
- 条目字段是规范化后的 camelCase（如 `chartVersion`、`mainRepoVersion`、`neverReleased`；实例的 `deployedCluster` 是集群外部署时 Pod 所在的集群，集群内部署为空）；分页元数据是 snake_case：`page`、`page_size`、`has_more`、`total`。
- 除 `pod execute` / `pod file get` 外，JSON 始终带 `raw` 字段：加 `--raw` 时是组成该视图的上游响应（`instance list` 是每次 BKE 调用的上游响应数组，发布计划的裁剪见上文 Plan 一节），否则为 `null`。文本模式加 `--raw` 会在普通视图后打印上游 JSON；`pod logs` 的文本规则见上文。

| 命令                                                                                          | JSON `data` 主要字段                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app get`                                                                                     | 应用对象：`name`、`admins`、`chartRepo`、`psmList`、`imageConfigs`、默认发布配置、`phase`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `app admin list`                                                                              | `application`、`admins`、`total`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `app deployed-cluster list`                                                                   | `application`、`outOfClusterEnabled`、`items`（`cluster/deployedClusters[{name,nodeLevel}]/error`，读取失败的集群只记 `error`）、`total`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `app compare`                                                                                 | `site`、`env`（读取的站点与控制面）、`application`、`project`、`baseline`、`baseline_project`、`filters`、`show`、`app_clusters`、`baseline_clusters`、`covered`、`coverage_ratio`（0~1，无基准集群时为 `null`）、`covered_by_status`、`by_zone`（`zone/baseline/covered/missing`）、`missing_count`、`extra_count`、`missing` / `extra`（`cluster/zone/vdc/scenario/clusterGroup/deployedCluster/architecture/instances`，未列出时为 `null`）、`errors`（`source/code/message`）、`raw`（两个应用的实例响应，再加集群查询响应）                                                                                                                                                                                  |
| `instance list`                                                                               | `items`、`total`、`page`、`page_size`、`has_more`、`offline`、`offline_hidden`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `instance get`                                                                                | 实例对象；`values` 只在带 `--values` 时有内容，否则为 `null`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `instance get --diff`                                                                         | `application`、`a`、`b`、`field_diffs`、`values_diff`、`values_identical`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `instance diagnose`                                                                           | `application`、`filters`、`total`、`offline_hidden`、`summary`（各分类计数）、`signatures`（`signature/count/instances`）、`warnings`（不传 `--warn-pattern` 时为 `null`）、`items`（`instance/cluster/zone/category/detail/ready/restarts/signature/oldPod/newVersionEffective/warningPod/masterFound/warnings/pods/log/error`）；`--raw` 是 `{instances, rollouts}`，不含 Pod 详情                                                                                                                                                                                                                                                                                                                              |
| `cluster list`                                                                                | `label_selector`、`items`、`total`、`page`、`page_size`、`has_more`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `cluster get`                                                                                 | 集群对象：`zone`、`dc`、`vdc`、`scenario`、`clusterGroup`、`phase`、`offlineByPlatform` 等                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `cluster instance list`                                                                       | `cluster`、`application`、`items`、`total`、`page`、`page_size`、`has_more`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `pod list`                                                                                    | `application`、`instance`、`phase`、`workloads`、`items`、`total`、`page`、`page_size`、`has_more`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `pod events`                                                                                  | `application`、`instance`、`pod`、`items`、`total`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `pod yaml`                                                                                    | `application`、`instance`、`pod`、`yaml`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `pod logs`                                                                                    | `application`、`instance`、`pod`、`container`、`lines`、`fetched_lines`、`matched_lines`、`truncated_by_tail`、`master`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `pod logs --all-pods`                                                                         | `application`、`instance`、`pods`（`pod/workload/container/lines/fetched_lines/matched_lines/truncated_by_tail/master/error`）、`master_pods`（不传 `--master-pattern` 时为 `null`）、`failed`；`--raw` 是 `[{pod, log}]`，读取失败的 `log` 为 `null`                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `version image list` / `version chart list`                                                   | `application`、`repo`、`repoId`、`type`、`items`（`version/type/status/branch/commit/creator/createdAt/description`）、`total`、`page`、`page_size`、`has_more`、`raw`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `plan list`                                                                                   | `items`（`id/name/status/creator/createdAt/application/changeApplyUrl`）、`total`、`page`、`page_size`、`has_more`、`scanned`、`unresolved`、`truncated`、`raw`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `plan get`                                                                                    | 计划字段、`nodes`、`gates`（字段同 `plan gate list` 的 `items`）、`waiting`、`objects`（不加 `--objects` 时为 `null`）、`raw`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `plan follow`                                                                                 | `plan get` 的字段、`timedOut`、`changes[]`（`time/status/nodes`）                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `plan gate list`                                                                              | `planId`、`items`（`level/name/status/waiting/nodeId/activityId/objectName/pipelineId/conditions`；计划级关卡填 `nodeId`、`conditions`，对象级 CONFIRM 活动填 `activityId`、`objectName`、`pipelineId`，其余为 `null`）、`total`、`page`、`page_size`、`has_more`、`waiting`、`raw`                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `plan precheck`                                                                               | `plan`（字段同 `plan list` 的 `items`，`application` 为 `null`）、`at`（epoch 秒）、`checkStatus`、`reason`、`hint`、`applyTickets`（`id/title/url/status/windows[{startTime,endTime}]`）、`policies`（`policyId/name/type/url/status/inAllowedHours/controlResult/suggestion/approvers{steps[{order,usernames,roles}],outsideWindow}/approversError`）、`raw`                                                                                                                                                                                                                                                                                                                                                    |
| `ticket list`                                                                                 | `application`、`creator`、`op`、`status`、`since`、`limit`、`total`、`returned`、`truncated`、`scan_truncated`、`copy_plans_checked`、`copy_plans_unchecked`、`unverified_copy_plans`（`id/createdAt/status/templateInstance/clusters/url`，`templateInstance` 可为 `null`）、`copy_plan_errors`（`id/code/message`）、`notes`、`items`（`kind/id/createdAt/creator/status/op/type/templateId/objects/planId/level/description/url/template/title/changeScenes/strategyScenes/templateInstance/deployedCluster/error`）、`raw`                                                                                                                                                                                    |
| `ticket get`                                                                                  | `site`（读取工单的站点）、`id`、`name`、`templateId`、`ticketType`、`op`、`creator`、`description`、`status`、`createdAt`、`startAt`、`endAt`、`planId`、`rollbackFrom`、`rollbackTicketId`、`url`、`approvalUrl`、`approval`（`changeType/changeLevel/changeScenes/changeTitle/urgent/window/tickets[{bpmTicketId,platform,status,reviewers,reviewedBy}]`）、`plan`（`name/status/templateKey/title/level/changeScenes/strategyScenes` 等）、`stages`（`name/status/startAt/endAt/strategy`）、`progress`（`total/counts`）、`objects`（`name/cluster/clusterGroup/scenario/zone/status/oldChartVersion/newChartVersion/oldMainRepoVersion/newMainRepoVersion`）、`events`（`at/operator/key`）、`errors`、`raw` |
| `perm precheck`                                                                               | `application`、`user`（登录时保存的用户名，读不到为 `null`）、`ready`、`items`（`id/check/ok/required/detail/remedy`，`ok` 为 `true` / `false` / `null`）、`raw`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `perm status`                                                                                 | `site`、`env`、`user`、`ready`、`roles`（`product` / `site`，持有的角色名，读取失败为 `null`）、`items`（同 `perm precheck`，`id` 为 `ro_permission` / `spacex_role`）、`raw`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `perm role list`                                                                              | `site`、`env`、`scope`、`total`、`items`（`role/mine/memberCount`，带 `--role` 时多 `members[{userName,displayName,type,inherited}]`）、`raw`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `plan gate confirm` / `plan start\|pause\|resume\|cancel` / `plan object retry\|skip\|cancel` | `plan`、`operation`、`dry_run`、`targets`（`kind`（`plan/plan_gate/object_gate/object`）、`name`、`status`、`nodeId`、`pipelineId`、`activityId`、`request`（`method/url/body`，与实际发送一致）、`result`（预览时为 `null`；成功 `{ok: true, response}`，失败 `{ok: false, code, message}`）、`after`）、`skipped`（`name/reason`）、`failed`、`held`、`notReady`（仅 `gate confirm`：刚开始、还不能确认的计划级关卡数）、`precheck`（仅 `start` 预览有值，同 `plan precheck` 去掉 `plan`、`raw`，其他为 `null`）、`precheckError`、`readBackError`、`raw`                                                                                                                                                       |

`version ... --raw` 是 `{application, versions}`：`application` 是应用原始对象，`versions` 是 bytedcli 从 SCM 响应中提取的列表结果（`versions`、`total`），不是 SCM 原始响应。

`pod list --raw` 是 `{status, pods}`：`status` 是 rollout status 原文，`pods` 是各 workload 的列表响应，与 `workloads` 同序；不附带重启查询的 Pod spec。所有命令的 JSON 均带 `raw`，未传 `--raw` 时为 `null`。

### values 打码

- `instance get` 的 `--values`、`--diff`，以及 `instance get` / `instance list` / `cluster instance list` / `app compare` / `perm precheck` 的 `--raw` 中的上游 `spec.fileContent` 默认打码：敏感 key（token、secret、password、access key 等）的值及其下所有更深缩进的行、`- name: <敏感名>` 列表项的 `value`、长 token 样式的值和 BKE 加密值 `v1:...`。
- `ticket get --raw` 的每个部分都按 key 打码：以 `value`、`values`、`fileContent`、`file_content` 结尾的字段（对象的旧实例、新配置、patch / rollback 配置，操作记录等），字符串按 values 规则打码，对象和列表整体替换为 `<masked>`；审批申请和所属计划的 `userChangeData`（变更内容，含 values）不读入输出，`--nomask` 也不输出。
- 只有全局 `--nomask` 才输出原文：`bytedcli --nomask bke instance get --app demo-app --name demo-app-demo-cluster --values`。
- `--diff` 先用原文比较再打码：一对 `-` / `+` 行打码后看起来相同，说明只有被隐藏的值不同。

## 分页与离线集群

- BKE 默认不展示已下线集群上的实例。`--offline exclude` 时文本输出末尾提示隐藏了多少个，JSON 为 `offline_hidden`；统计失败，或带 `--status unreleased` / `--region` / `--repo-version`（需要本地过滤，无法统计）时为 `null`，文本输出也不提示。
- BKE 的离线开关是二选一（只看在线或只看离线），`--offline include` 会分别查询两侧再合并。
- `--offline include`、`--status unreleased`、`--region`、`--repo-version` 会读取全部匹配后在本地分页，`--all` 直接返回全部（不能与 `--page` / `--page-size` 同用）；其他情况由 BKE 服务端分页，`total` 只统计所请求的在线或离线一侧。
- `cluster list` 与 `cluster instance list` 一次读取全部结果，再在本地过滤、按名称排序和分页。

## 错误与排障

| 错误码            | 常见原因                                                                                                                                                                                                                                                                                                | 处理                                                                                           |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `BKE_INPUT_ERROR` | 标签值非法、站点 / `--env` 不支持、使用了 `--as app`；写命令：非 CN 站点、`--app` 与计划不一致、同名对象跨节点；`instance create`：非 I18N / US / EU-TTP、应用不是 templateCustomized、版本或问题不存在、部署集群不在候选里、变更窗口不合法；工单命令：US / I18N-BD 控制面、`--mine` 但没有保存的用户名 | 按 `hint` 修正参数后重试                                                                       |
| `BKE_NOT_FOUND`   | 应用、实例或集群不在当前控制面                                                                                                                                                                                                                                                                          | 核对名称，再核对 `--site` / `--env`；对象不跨控制面共享，不要换站点盲试                        |
| `BKE_AUTH_FAILED` | HTTP 401：JWT 无效或过期；HTTP 403：没有该 project / 应用的权限                                                                                                                                                                                                                                         | 401 时 `bytedcli --site <同一站点> auth login` 后重试；403 时联系应用管理员或 BKE SRE 申请权限 |
| `BKE_ERROR`       | 其他上游错误或意外重定向；`details.reason` 为 `member_cluster_unavailable` 时是 BKE 连不上成员集群                                                                                                                                                                                                      | 重试；仍失败时在 BKE 控制台对照同一页面                                                        |
| `SCM_*`           | 仅 `version` 命令：SCM 层透传的错误，如 `SCM_NOT_FOUND`（SCM 中搜不到 chart 仓库）、`SCM_AMBIGUOUS`（搜到多个候选仓库）                                                                                                                                                                                 | 用 `bke app get` 核对仓库名，再核对 `--site` / `--env`                                         |

- 缺少必填 option（如 `--app`、`--name`、`--cluster`、`--instance`、`--pod`）时由 CLI 统一返回 `CLI_ARGS_MISSING`。
- `details.reason` 为 `member_cluster_unavailable`：BKE 的部分副本连不上实例所在的成员集群（ToB 集群、超大集群常见），多见于 `pod list` 和 `pod logs`。读请求已自动重试：HTTP 400 或失败信封最多共 5 次，HTTP 500 走通用重试（共 `--http-retry-count` + 1 次，默认 3 次），`--http-retry-count 0` 时都不重试；`details.attempts` 是实际次数，`details.cluster` 是集群名（上游未给出时为 `null`）。稍后重跑；持续失败时到 BKE 控制台看同一实例，或找 BKE oncall。
- 实例名不确定时，先用 `instance list --cluster <cluster>` 或 `--keyword` 查出准确名称，不要拼接猜测。
- 应用在当前控制面存在、但 `instance list` 为空时，先试 `--offline include` 和 `--status unreleased`。

## Agent guidance

- 计划写命令先不带 `--yes` 执行，把预览中的目标和请求展示给用户；用户明确同意这一次操作后才带 `--yes` 重跑，确认计划级关卡时带上预览中的 `--node-id`。同意只对这一次有效，不延续到下一个关卡、对象或计划，也不要自动连发。
- 用户问能不能发版、能不能在某集群新建实例时，先跑 `perm precheck`（建实例带上 `--cluster`，复制已有实例时带 `--template-ri`），按 `remedy` 告诉用户缺什么、找谁开；`ok: null` 是未检查，不要当成通过。没有具体应用、只问账号有没有发版权限或持有哪些 SpaceX 角色时用 `perm status`；问某个角色有哪些人时用 `perm role list --role`，并说明通过部门或组授予的人不在成员列表里。
- 启动计划或安排启动时间前先跑 `plan precheck`（或看 `plan start` 预览里的 `precheck`），按 `hint` 和审批窗口决定何时启动；不要凭记忆或策略的周时段表推算窗口。
- 确认灰度对象关卡、重试或跳过对象前，先检查对象健康（`plan get --objects`、`pod list --restarts`、`pod events`、`pod logs`）；有异常先报告给用户，不放行。
- 新建实例前先读 `references/instance-create.md`，按其中的流程预览、确认后才带 `--yes`；报结果未知时先查工单，不要直接重跑。
- 除 CN 计划写命令、`pod execute` 和 I18N / US 的 `instance create` 外，没有其他 BKE 写命令（新建计划、CN 上新建实例、更新实例、操作 RO 工单、加锁、灰度标记、加管理员）。不要借助 curl、`insearch get` 或浏览器调用 BKE / RO / Athena 写接口，计划写命令已覆盖的接口也一样；需要变更时说明要做的操作，由用户在 BKE 控制台完成。
- 先确定控制面再查询：CN、I18N、US、I18N-BD、EU-TTP 各自独立；查不到时先确认 `--site` / `--env`，不要据此断定对象不存在。
- 不要自己调用 BKE 的 `releaseinstances?limit=...`：BKE 会先扫描 limit 个对象再过滤，返回随机子集。某集群上的全部实例用 `cluster instance list`，某应用的全部实例用 `instance list --all`。
- `gray` 是 BKE 的灰度（test canary）集群标记，不等于测试集群。
- `member_cluster_unavailable` 说明 BKE 读不到成员集群，不代表实例或 Pod 异常；不要据此下健康结论，如实报告并稍后重跑。
- 默认不要加 `--values`；需要时只引用相关片段，不要把整段 values 或 `--nomask` 输出贴进消息、文档或 MR。
- 问某应用还缺哪些集群、和某个组件比部署覆盖时用 `app compare`。基准应用由用户指定或确认，不要自行假定（例如默认拿某个系统组件当基准）；结论里说明基准、过滤条件，以及缺口行是基准应用的实例。
- 查某应用的发版历史、谁做过回滚或复制、某张工单的批次策略和新旧版本时用 `ticket list` / `ticket get`。要完整历史或复制计划时带 `--creator` / `--mine`；不带时结果不全（看 `notes`）。`unverified_copy_plans` 不能确定属于本应用，不要当作本应用的变更。
- 命令面覆盖应用（含部署覆盖对比）、发布实例、成员集群、Pod、镜像 / chart 版本、发布计划与 RO 工单查询、CN 计划写操作与 Pod 执行 / 文件读取、I18N / US 新建实例；权限只有 `perm precheck`、`perm status`、`perm role list` 三个只读命令（不能申请角色或权限），不要猜测其他子命令。

## References

- `../../invocation.md`
- `../../troubleshooting.md`
- `references/instance-create.md`：用 `instance create` / `app deployed-cluster list` 新建实例前读
