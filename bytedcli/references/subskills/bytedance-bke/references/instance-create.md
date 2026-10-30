# 新建实例（I18N / US / EU-TTP）

I18N / US（`--site i18n-tt`，US 加 `--env us`）和 EU-TTP（`--site eu-ttp`），与控制台「创建应用实例」表单提交同一个请求：BKE 建出一张 RO 工单（状态 created，不会自动开始），到控制台开始执行。

```bash
# 集群外部署可选的部署集群（应用部署集群）
bytedcli --site i18n-tt bke app deployed-cluster list --app demo-app --cluster demo-cluster-a,demo-cluster-b
# 表单列出的镜像版本（online + test，默认选第一个）
bytedcli --site i18n-tt bke version image list --app demo-app --type all --page-size 5
# 默认只预览：读取所需的全部信息，打印将要发送的请求，不发写请求
bytedcli --site i18n-tt bke instance create --app demo-app --name demo --cluster demo-cluster-a,demo-cluster-b \
  --deployed-cluster demo-core --chart-version 1.0.0.2 --repo-version 1.0.0.21 --set replicaCount=2 \
  --title "新建 demo 实例" --scene TEST --change-level L2 --end 2026-01-02T18:00 \
  --content "新建 demo 实例" --rollback-plan "删除新实例" --impact "仅新实例"
# 用户确认预览后才加 --yes（写在子命令之后）
```

- 只支持 templateCustomized（按 chart 问题渲染 values）、镜像全部由 SCM 构建、恰好标记一个主仓库的应用；其他应用返回 `BKE_INPUT_ERROR`，到控制台新建。
- 实例名是 `<--name>-<集群>-<随机后缀>`，`--name` 至多 20 个字符（小写字母、数字、`-`，首尾不能是 `-`）。
- 镜像：主仓库版本必须用 `--repo-version <版本>` 指定，须是 build_ok 的 online 或 test 包（表单默认选最新一个，常是 test 包，所以不提供默认）；选了 test 包会给出 warning。其他镜像仓库默认取最新 online 包，`--repo-version <仓库>=<版本>` 覆盖。`--repo-version` 与 `instance list --repo-version` 同义，都是主仓库的 SCM 版本，不是构建出的镜像版本。
- 部署：不带 `--deployed-cluster` 是集群内部署；带一个目标表示全部集群外部署到它，或按 `<成员集群>=<目标>` 逐个指定。目标必须在 `app deployed-cluster list` 的候选里，候选为空的集群不能集群外部署；应用未开启集群外部署时直接报错。集群定义标记暂停的集群，新实例的 rollout 也暂停（`Paused` 列）；集群定义不存在时按不暂停处理并给出 warning，读取集群定义出错（权限、5xx 等）时直接报错。
- `--set <问题>=<值>` 只接受 chart `questions.yaml` 中的问题（含 subquestions），按问题类型校验 int / bool，enum 问题的值必须是 chart 列出的选项；`canaryPercent`、`maxUnavailable`、`partition` 是发布字段，不能用 `--set`。新实例按 `canaryPercent 100%` 和应用默认的 `maxUnavailable` 发布。
- 变更管控字段与表单一一对应：`--title`、`--scene`（`TEST` 即「新机房建设/测试集群变更」）、`--change-level`、`--start` / `--end`（变更窗口；带时分的本地时间、RFC 3339 或 10 位 epoch 秒，`--start` 默认现在）、`--content`、`--precheck-result`、`--metrics`、`--rollback-plan`、`--impact`、`--receiver`（默认自己）；`--concurrency` 改创建阶段的批次并发，默认用模板的。
- EU-TTP 不要传 `--description`：EU 网关没有登记这个字段，留空时请求里不带它（与控制台一致），传了会被网关 403（`result.state` 为 `not_created`，`message` 是网关原文，工单不会建出）。CLI 还没在 EU 真实提交过。
- 预览的 `request` 就是 `--yes` 发出的请求；`file_content` 是实例 values，默认打码，`--nomask` 显示原文。`fileContentSha256` 是未打码内容的 sha256。
- `--yes` 只发一次，不重试，结果看 `result.state`：
  - `created`：`ticketId` / `ticketUrl` 是新工单，退出码 0。
  - `not_created`：BKE 明确拒绝（HTTP 4xx，或请求没有发出），退出码 1；与运行中工单冲突时 `conflicts` 列出冲突记录。
  - `unknown`：超时、网络错误、HTTP 5xx，或 HTTP 2xx 却不是预期的应答（信封异常、没有工单 ID）。工单可能已经建出，退出码 1；按 `check` 先查工单（I18N 用 `ticket list --mine`，US 到控制台），再决定是否重跑。
- `--raw` 是读取的上游响应：应用、集群外部署开关、模板、`bke` 平台条目、chart 文件名（不含内容）、成员集群与集群定义、部署集群候选、SCM 版本，以及 `--yes` 时的创建响应（`response`）；其中 values 类字段默认打码，`--nomask` 显示原文。

## 输出字段

JSON `data`：`application`、`env`、`template`（`id/name`）、`dry_run`、`instances`（`cluster/zone/generateName/deployMode/deployedCluster/nodeLevel/paused`）、`images`（`psm/repo/version/type/main`）、`parameter`、`fileContentSha256`、`warnings`、`request`（`method/url/body`，与 `--yes` 发出的一致，`body.file_content` 默认打码）、`result`（预览时为 `null`；`{state: "created", ticketId, ticketUrl}`、`{state: "not_created", code, message, conflicts}` 或 `{state: "unknown", code, message, check}`）、`raw`。

## Agent 流程

1. 用户给出应用、集群和版本后，先查候选：集群外部署用 `app deployed-cluster list`，镜像版本用 `version image list --type all`。主镜像版本按用户给定的或核对后的版本填，不要替用户挑。
2. 不带 `--yes` 预览，把集群、部署集群、chart 与镜像版本（特别是 test 包 warning）、变更窗口和管控字段展示给用户。
3. 用户明确同意这一次后才带 `--yes`。其他镜像仓库默认取最新 online 包，两次运行之间可能变化；提交时用预览里 `images` 的版本给每个仓库写上 `--repo-version <仓库>=<版本>`，保证发出的就是用户确认的请求。
4. `result.state` 为 `unknown` 时先查工单，不要直接重跑；为 `not_created` 时按 `message` 修正后再预览一次。
