# FTF v3 智能接入工作流

## 导航

- [用途](#用途)
- [纯 PSM 输入的最短决策路径](#纯-psm-输入的最短决策路径)
- [SCM 生效前标准预览（强制）](#scm-生效前标准预览强制)
- [正式命令入口](#正式命令入口)
- [安全职责边界](#安全职责边界)
- [标准工作流](#标准工作流)
- [低打扰交互策略](#低打扰交互策略)
- [上传、发布与回滚安全](#上传发布与回滚安全)
- [人工恢复证据包](#人工恢复证据包)

## 用途

本文件定义 FTF v3 SDK Agent 智能接入的 Agent 编排流程。核心边界是：

- 正式入口统一使用 `bytedcli ftf access create/update`、`access admission execute`、`access artifact create/publish/deploy`、`access compile execute/status`、`access record open/close/status` 与 `access status`。
- `bytedcli ftf psm access --type sdk_agent` 仅保留兼容，不作为新流程推荐入口；确认使用旧版 SDK 接入时统一使用 `bytedcli ftf access legacy create --psm <psm>`。
- 用户只说“帮我给 `<psm>` 接入 FTF”时，默认表示新版 SDK 智能接入；只有明确指定 ByteCopy 才走 ByteCopy。识别到 Atum 时读取有效配置，按原生 FTF 阶段生成、验证；只有实际不支持或编译失败时才报告具体原因。
- AI 沙箱只在受控工作副本中执行真实文件改造与安全模拟，不运行项目 build、boot 或其它本地编译/启动基线。真实编译验证统一由 SCM 完成；普通 CLI 与 Manager 只处理安全文件快照、生成结果和流程状态，不在本地替代 SCM 编译。
- 构建用途范围按用户明确意图选择：只接测试/线下用 `test`，只接线上用 `online`，两者都接用 `both`，两者都关闭用 `none`；后续切换使用 `access update --build-scope <scope>`。未指定 `--build-scope` 时维持当前配置。
- 默认低打扰推进。仅在缺少必要输入、需要申请权限、需要确认高风险操作或进入人工恢复时打断用户。

接入完成后的线上 `source_hash_mismatch` 后台闭环与追踪方式见 `online-source-refresh.md`；不要把它与本文件的接入期 Agent 调优流程混用。

## 纯 PSM 输入的最短决策路径

用户只提供 PSM 并要求“接入 FTF 录制/mock”时，严格按以下顺序推进，不先执行通用 `auth status`，也不要求用户补充仓库、工单或 SCM 上下文：

1. 以当前登录用户身份读取实时状态。用户未指定面板时，串行执行 `bytedcli --json --site cn ftf access record status --psm <psm> --region cn` 和 `bytedcli --json --site cn --vregion China-Pay ftf access record status --psm <psm> --region china-pay`；用户明确指定面板时只查询目标面板。`--region` 选择业务面板，请求网关则由 `ftf` 前的全局 `--site/--vregion` 决定，两者必须按以上映射保持一致。CN 查询保持 TeslaX v1 gateway，China-Pay 查询路由到追光 Manager，禁止用 CN Manager 响应代替。CN、China-Pay 均查询各自区域的全部环境心跳，分别展示线上 prod/canary 和其他有效环境；缺失标签不作为录制证据，查询失败记 unknown。未指定面板时，无关面板失败不覆盖已有可靠证据；指定面板失败则报告该面板状态未知。每个结果记录接入标记及 `data.recording_by_environment.online`、`data.recording_by_environment.other` 和 `data.recording_found_anywhere`；任一分组实际 `recording=true` 表示已有录制基础，缺字段或 `unknown` 且无正证据时不得判为无基础。旧后端没有新字段时继续按原 `data.record_detail.record_status` 兼容判断。历史工单只能作为参考，不能替代实时状态。
2. 未指定面板时先展示 CN、China-Pay 的分面板证据，再给综合结论；线上与 PPE/BOE 分组分别判断，已有 PPE/BOE 录制不能阻止用户明确要求的 online 接入。任一目标用途已录制时不创建该用途的新工单；仅当目标面板的 SDK、prebuild、深度录制标记均有效且录制已关闭时，先按目标面板执行不带 `--yes` 的 `access record open --psm <psm> --region <region>` 预览，其中 CN 使用全局 `--site cn`，China-Pay 使用全局 `--site cn --vregion China-Pay`。预览一致且用户已明确要求开启该面板时追加 `--yes` 写入，不重复询问；否则只询问这一项。后续写操作与回读始终复用同一组全局站点参数和面板参数。未观察到心跳不替代 SDK 接入标记。已有 order id 或 session id 时先执行 `access status`，按已有产物继续；用户已要求新版接入且目标面板的接入标记缺失时，直接进入创建预览，不再询问“确认重建”。接入标记均有效时报告部署或心跳现状，只在用户另行要求重新接入时创建。录制异常或未知状态时停止并报告恢复动作，不盲目 create。
3. 在实时接入标记缺失且用户已要求接入，或用户另行明确要求重新接入时，先执行不带 `--yes` 的 `access create --psm <psm>`，核对自动发现的 PSM、仓库、SCM 和创建人。只透传用户明确提供的运行范围参数；用户未显式指定时不要传 `--canary-name`，不得把接口查询到的小流量机房自动转换为接入限制。若业务没有 canary 部署，先说明将不限定小流量机房，并明确询问是否继续；普通“帮我接入”不等于同意忽略该部署条件。用户明确同意忽略该 warning，或本会话已授权自动确认同类 warning 后，使用 `cluster=default`、空 `canary_name` 的语义继续，并在准入阶段正常追加 `--confirm-warnings`。不得建议用户先修改业务部署来满足接入。结果一致且用户已明确要求执行接入或重建时，直接追加 `--yes` 创建，不重复询问。保存响应中实际存在的 selector；存在 order id 时优先复用，缺少 session id 时使用 `access status --order-id <id>` 获取。若响应不含 order id 或 session id，按不确定写结果停止并报告恢复动作，禁止因此重复 create。
4. 若 readiness 结构化结果明确包含 `sdk_record_mq_permission=need_permission`，自动追加 `--apply-mq-permission` 重试一次，不再要求用户手动申请或单独确认；旧后端没有结构化结果时，仅把精确错误 `sdk record mq permission is required` 作为兼容识别。返回 `permission_submitted` 或有效工单链接时，表示工单创建成功后继续准入，`mq_permission_ready` 仍保持真实权限状态；如需确认权限已生效，可约 20 秒后自动复查一次，但不得因此打断用户。申请失败、其他权限错误、模糊报错或重试后仍为 `need_permission` 时停止，并报告唯一所需动作。
5. 创建成功后按 `access admission execute` → `access artifact create` → `access compile execute/status` → `access artifact publish` 推进。每一步依据已有产物继续；失败后可单独重做生成或编译，不因显示状态拒绝重试。识别到 Atum 时继续新版流程，不按名称切换旧版；命令已解析后保持 YAML 和原生命令，使用两种用途各自的草稿。若文件定位失败，读取 `details.files[].summary`：存在多个候选时才请用户确认路径，不反复猜路径；`candidates` 为空且兼容字段 `oncall_recommended=true` 时说明已读文件为何不适合，但不发起 FTF oncall，直接提供本文末尾的陈思源单聊入口。`recovery_action=restore_codebase_read` 时，先从错误中的仓库 URL 或工单仓库解析精确 `<namespace>/<repo>`，推荐 Reporter 权限，并运行 `bytedcli --json codebase permission repository apply -R "<namespace>/<repo>" --action reporter` 获取真实 `manual_apply_url`。若尚未授权，主动询问“是否帮你申请该仓库的 Reporter 读权限”，不要只给链接后结束；用户确认申请或本会话已授权后，以相同参数追加 `--yes` 自动提交，向用户提供返回的真实 `approval_url`；不得只给手动指引、拼接申请链接或声称已批准。申请后等待用户确认权限生效，再重试被阻塞的读取分支。
6. 验证编译必须同时具备 `verification_path=v3_online` 与 `verification_path=legacy_test` 两条成功证据：前者使用线上草稿，后者使用独立测试草稿，分别验证实际 prebuild 和编译结果。默认仅 SCM 使用历史成功构建人作为编译身份；按后台构建历史或普通 compile 流程返回的历史成功人顺序轮换。依赖权限导致构建失败时，最多使用 3 个不同的历史成功人重试；不 fallback 到接入人，不因权限失败重新生成 draft，也不让 Agent 在本地编译。Manager 会并行发起两条构建，只完成一条时继续等待另一条，不发布 artifact。两条均成功后 Manager 才会把 session 推进到 `awaiting_confirmation`，`next_action` 变为 `publish_artifact`；Agent 以 `access status` 返回的 `stage` 与 `next_action` 判断是否具备发布条件，不自行解释 `changePreview.tracks` 的完整性。随后先预览 `access artifact publish --version <version>`，按“SCM 镜像 → 环境变量 → Pre-Build → 线上草稿 diff/结果 → 测试草稿 diff/结果”的顺序向用户展示。用户消费并确认后追加 `--yes`。该命令连续完成首次正式发布、SCM FTF 配置及回读、PSM 注册、`is_register_sdk_agent/is_register_sdk/is_register_sdk_prebuild/is_register_smartq_advanced` 持久化和工单完成。结果进入 `registered` 才能描述为“平台侧接入已完成”。同一工单已处于 `awaiting_confirmation` 时可直接确认发布，不重新走编译验证。
7. 注册完成后，按目标面板和对应全局站点参数预览 `access record open --psm <psm> --region <region>`，确认后追加 `--yes`；随后用相同路由执行 `access record status`，分别回读注册状态和录制状态。`is_register_sdk=true` 表示接入已完成，`record_status=3` 表示仍等待业务重新编译、部署或心跳，不得把它改写成接入失败，也不得把已注册描述为正在录制。最后明确提示业务执行新的编译上线。

面向用户的阶段输出固定为三项：当前结论、关键证据、唯一下一步。正常推进不展开脚本迭代、内部状态图、完整 JSON 或重复命令；只有出现阻塞时才补充必要原因和恢复动作。SCM 生效前的高风险确认必须按下方专用模板展开关键证据。

### SCM 生效前预览

编译两种用途都成功后，运行不带 `--yes` 的 `access artifact publish --version <version>`。以响应的 `confirmation_ready` 和 `missing_evidence` 判断下一步；显示状态不额外限制生成、编译重试。

向用户依次展示 SCM 镜像、环境变量、Pre-Build 变化，两用途的实际编译结果，以及 CLI 已渲染的受控文件 diff。JSON 模式直接使用 `rendered_diff`：`changed` 是有改动，`unchanged` 是前后一致，其余状态说明具体读取问题；缺少文件快照只作提示，不把它当成编译失败或新的发布门禁。截断内容如实说明，不自行解码、拼 diff 或补写证据。

明确本次确认会发布草稿、应用 SCM 配置、注册 PSM 和完成工单；业务合码、重新编译部署和开启录制由用户另行决定。具备发布条件且用户明确授权后才执行 `--yes`；用户要求发布前停下时，只展示预览。风险为空只表示没有已上报风险。

标准呈现示例（下列内容即 CLI 文本模式的真实输出形态：`当前结论` 与各轨道均为「项目 / 内容」两列表格，不带 `键：值` 前缀；轨道说明行是表格之后的缩进正文，不是表格里的字段。复述时不要臆造 `说明` 之类不存在的字段名）：

```text
FTF 智能接入生效前确认

当前结论
 项目       内容
 确认状态   可确认
 工单 ID    1234
 会话 ID    sample-session-id
 目标版本   sample-artifact-version
 缺失证据   无

关键证据

SCM 配置变更
 配置项                 当前值       目标值      变化
 镜像                   demo-old     demo-new    更新
 环境变量 FTF_EXAMPLE   接口未返回   <UPDATED>   新增或覆盖
 Pre-Build              [8,23]       [8,17,23]   新增 17

AI Draft 代码变更：v3_online
 项目       内容
 验证状态   verified
 风险       未发现已上报风险
build.sh diff
  --- a/build.sh
  +++ b/build.sh
  @@ -1,2 +1,3 @@
   set -e
  +source ./ftf_nova_build.sh
   make build
script/bootstrap.sh diff
  --- a/script/bootstrap.sh
  +++ b/script/bootstrap.sh
  @@ -1,2 +1,3 @@
   #!/usr/bin/env bash
  +export TCE_STAGE=canary
   exec ./bin/demo-service

AI Draft 代码变更：legacy_test
 项目       内容
 验证状态   verified
 风险       未发现已上报风险
  测试草稿保留原程序名及启动参数，分别展示实际改动。

影响与边界
即将执行：发布已验证 draft；应用并回读 SCM 配置；注册 PSM；完成接入工单。
不会自动执行：业务代码合入；业务重新编译；线上部署；开启流量录制。

唯一下一步
等待用户明确确认后，重新执行同一命令并增加 --yes。
```

## 正式命令入口

`--json` 与 `--site` 是全局参数，需要放在 `ftf` 前面。下列 ID-only 示例固定为 cn；zg 使用
`--site cn --vregion China-Pay`。裸 order id 或 session id 未附站点时先索取，不得猜测。普通
access 命令的 order id 与 session id 至少提供一个；同时提供时必须指向同一会话。验证编译命令必须二选一，只传 `--order-id` 或 `--session-id`。

```bash
# 创建：普通用户只需要 PSM；CLI 自动发现仓库、SCM 和原始镜像，分支默认 master。
# 默认只预览；确认请求后增加 --yes。
bytedcli ftf access create \
  --psm example.psm

bytedcli ftf access create \
  --psm example.psm \
  --yes

# 仅在用户明确指定用途时增加 --build-scope；未指定时维持当前配置。
bytedcli ftf access create --psm example.psm --build-scope test

# 已有工单后切换用途范围：默认预览，确认后增加 --yes；不会重开工单或重新生成产物。
bytedcli --site cn ftf access update --session-id sample-session --build-scope online
bytedcli --site cn ftf access update --session-id sample-session --build-scope online --yes

# 用户明确选择旧版 SDK 接入时，先预览，再创建 MR 与 BPM 工单。
bytedcli ftf access legacy create --psm example.psm
bytedcli ftf access legacy create --psm example.psm --yes

# 非默认仓库布局必须显式覆盖，并确认预览中的最终路径。
bytedcli ftf access legacy create \
  --psm example.psm \
  --source-branch develop \
  --build-file build/service.sh \
  --boot-file script/start.sh

# 准入检查：先预览受控文件范围，再提交
bytedcli --site cn ftf access admission execute \
  --order-id 10001

bytedcli --site cn ftf access admission execute \
  --order-id 10001 \
  --yes

# 生成：先预览，再确认创建线上与测试草稿。默认流程不传 common/previous attempt。
bytedcli --site cn ftf access artifact create \
  --session-id sample-session

bytedcli --site cn ftf access artifact create \
  --session-id sample-session \
  --yes

# 验证编译：先预览真实四文件范围，再触发；默认请求携带受控 file_snapshot
bytedcli --site cn ftf access compile execute \
  --session-id sample-session \
  --artifact-version sample-artifact-version \
  --source-hash sample-source-hash

bytedcli --site cn ftf access compile execute \
  --session-id sample-session \
  --artifact-version sample-artifact-version \
  --source-hash sample-source-hash \
  --yes

# 验证编译状态：默认单次查询；仅按需有限轮询
bytedcli --site cn ftf access compile status --session-id sample-session
bytedcli --json --site cn ftf access compile status \
  --session-id sample-session \
  --wait \
  --poll-interval-ms 3000 \
  --timeout-ms 600000

# 首次正式发布并完成平台侧收尾：先预览确认变更，再增加 --yes 执行
# 仅当用户明确指定或修改用途时传 --build-scope；预览与 --yes 必须使用同一值。
bytedcli --site cn ftf access artifact publish \
  --session-id sample-session \
  --version sample-artifact-version \
  --build-scope test

bytedcli --site cn ftf access artifact publish \
  --session-id sample-session \
  --version sample-artifact-version \
  --build-scope test \
  --yes

# SDK 线上录制开关：以下为 CN；默认预览，确认后增加 --yes
bytedcli --site cn ftf access record open --psm example.psm --region cn
bytedcli --site cn ftf access record open --psm example.psm --region cn --yes
bytedcli --site cn ftf access record close --psm example.psm --region cn
bytedcli --site cn ftf access record close --psm example.psm --region cn --yes

# China-Pay 同时切换网关和业务面板，不能只传 --region china-pay
bytedcli --site cn --vregion China-Pay ftf access record open --psm example.psm --region china-pay

# 单独查询 SDK 接入与线上录制状态；不会查询录制流量
bytedcli --site cn ftf access record status --psm example.psm --region cn
bytedcli --site cn --vregion China-Pay ftf access record status --psm example.psm --region china-pay

# 状态与固定进度图
bytedcli --json --site cn ftf access status --session-id sample-session --with-versions
bytedcli --site cn ftf access status --session-id sample-session --format graph
bytedcli --site cn ftf access status --session-id sample-session --format mermaid

# 回滚：先预览，用户明确确认后增加 --yes
bytedcli --site cn ftf access artifact deploy \
  --session-id sample-session \
  --version sample-verified-version

bytedcli --site cn ftf access artifact deploy \
  --session-id sample-session \
  --version sample-verified-version \
  --yes
```

复杂 JSON 和多行 Markdown 不要内联到命令参数。需要把已确认的 SCM 编译问题作为下一轮生成上下文时，写入受控临时文件并通过 `--compile-knowledge-file` 传入；任务结束后删除临时文件或交由临时目录回收。默认接入流程不生成 common attempt 或 previous attempts 文件。

## 安全职责边界

| 层级          | 可以做                                                                                                                                         | 不可以做                                                                                                                                                                        |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Skill / Agent | 在 AI 沙箱的受控业务工作副本安全读取四文件；审查并执行改造脚本；采集真实 diff；做语法、幂等性和受控文件范围模拟                                | 运行项目 build/boot、本地编译或启动基线；把凭证注入脚本；在业务工作副本之外写入；自动执行高风险发布或恢复                                                                       |
| bytedcli      | 安全读取四文件并生成快照；触发 SCM 验证编译；首次发布后编排平台收尾；有限轮询状态；预览并调用 SDK 录制开关；渲染状态、图和回滚预览             | 在本地替代 SCM 编译；执行 `script_content`；除 artifact create 或生成任务查询成功结果中的 `generation.script_content` 外，输出完整脚本、base64 文件内容、`file_snapshot` 或凭证 |
| Manager       | 执行准入、状态机、Fornax 生成、artifact 校验、历史成功构建人选择、SCM 编译编排、受门禁保护的发布、SCM 配置回读、PSM 注册和工单完成；审计操作人 | 在 Manager 主机或普通 CLI 进程中执行本地业务构建；把接入人作为依赖权限失败的 fallback；发布危险、failed 或 blocked 产物                                                         |

审查的是改造脚本在 AI 沙箱中实际发生的操作。改造脚本编辑 build/bootstrap 时，若实际下载并执行远程内容、提权、读取或外传凭证、破坏性删除、越出工作副本写入或修改宿主机服务，停止执行并记录 `blocked` issue。仅作为文本写入 build.sh、随后由 SCM 构建执行的既有 FTF 编译命令（如 ftf_nova_build.sh 的调用及构建结束后的 git checkout）不属于沙箱改造阶段执行，不能只凭字符串出现就阻断；仍需检查实际修改范围，真实编译结果只认 SCM。脚本还必须能在 SCM prebuild 环境独立运行，不得依赖 `apply_patch` 等 Agent/Worker 专用命令；AI 沙箱存在该命令不能作为 SCM 可用性的证据。不要尝试通过改写命令绕过门禁。

## 标准工作流

### 1. 获取或创建会话

1. 已有 order id 或 session id 时，先用 `access status` 获取当前阶段、阻塞原因和下一步。
2. 没有会话时，使用 `access create --psm <psm>`。CLI 使用当前登录用户，并自动发现仓库、SCM、原始镜像和运行范围；源码分支默认 `master`。只有自动发现失败或用户明确要求覆盖时才补充高级参数。用户未显式指定时不要传 `--canary-name`，不得猜小流量机房。业务无 canary 部署且 warning 只表达这一事实时，说明影响后由用户确认，或消费本会话已有授权，以 `cluster=default`、空 `canary_name` 的语义正常 `--confirm-warnings` 继续；不要要求业务先新增 canary 部署。先检查预览中的 PSM、仓库、SCM 和创建人；请求本身没有新增风险且用户已要求执行接入时，可以继续使用 `--yes`，不重复询问。
3. 不再为新流程生成 `psm access --type sdk_agent` 命令。Atum 沿用新版双用途流程，不按构建工具名称切换旧版；只有用户明确选择旧版接入时使用 `access legacy create --psm <psm>`。

### 2. 确认代码基线与文件路径

准入、AI draft 和验证编译默认不要求把业务仓库 clone 到本地。CLI 使用当前登录用户的 Codebase 身份，按工单仓库与 `source_branch` 远程遍历目录并读取 raw 文件；分支未指定时使用 `master`。

必须记录以下事实：

- 远程 Codebase 仓库和目标 branch；用户未覆盖时为 `master`。
- build、boot、main、go.mod 四文件的仓库内相对路径。

默认先检查 `build.sh`、`script/bootstrap.sh`、`main.go`、`go.mod`。默认文件不存在或内容明显不承担对应职责时，CLI 会有界遍历仓库目录，查找 build/compile、bootstrap/start、Go main 和 go.mod 候选。只有一个合理候选时自动采用；存在多个合理候选时返回 `FTF_ACCESS_FILE_CONFIRMATION_REQUIRED`，向用户展示候选及判断依据，再使用 `--build-file`、`--boot-file`、`--main-file`、`--go-mod-file` 重试。若配置文件可读但缺少 `go build`、`atum`、`ftf_nova_build.sh` 等当前支持的改造入口，且其它候选也均不适合，保持阻塞是正确行为；面向用户必须说明“找到了哪些文件、为什么不适合”，然后直接提供陈思源单聊入口，不发起 FTF oncall，也不主动代发消息。

只有用户明确提供 `--repo-dir`，或需要在调用方控制的 AI 沙箱工作副本采集改造 diff 时，才走本地读取。此时必须使用独立、可复核的工作副本，不得在含用户改动的目录中自动 reset、clean、stash、覆盖文件或切换分支；也不得在该工作副本运行项目 build/boot、编译或启动命令。

### 3. 安全读取四文件并执行准入检查

四文件是：

| 类型   | 默认来源                                                    | 约束                                               |
| ------ | ----------------------------------------------------------- | -------------------------------------------------- |
| build  | 工单 `build_file`、`--build-file`，否则 `build.sh`          | 远程文件非空、可读且不超限；不适合时扫描候选并确认 |
| boot   | 工单 `boot_file`、`--boot-file`，否则 `script/bootstrap.sh` | 同上                                               |
| main   | 工单 `main_file`、`--main-file`，否则 `main.go`             | 同上                                               |
| go.mod | 工单 `go_mod_file`、`--go-mod-file`，否则 `go.mod`          | 同上                                               |

远程读取时拒绝绝对路径和 `..` 穿越，限制目录深度、文件数量、候选数量和单文件大小。文件内容只在请求内转换为 base64；不写入项目文件，不在日志或报告中展示原文或 base64。AI 沙箱的 `--repo-dir` 模式额外拒绝符号链接逃逸、非普通文件和读取期间发生变化的文件。

先运行不带 `--yes` 的 `access admission execute` 检查选择器、文件范围和权限/警告开关。明确缺少 MQ 权限时自动追加 `--apply-mq-permission`，工单创建成功后继续准入，不要求用户手动申请。无 canary 部署时，用户已同意或已授权忽略后，保持 `cluster=default`、`canary_name` 为空并使用 `--confirm-warnings` 正常继续；其它 warning 仅在业务语义已确认可接受时使用 `--confirm-warnings`。申请失败、warning 业务语义不明确或检查要求高风险动作时暂停；普通通过项和已提交的 MQ 权限工单不打断。

### 4. 生成并验证改造脚本

调用 `access artifact create` 生成线上与测试两用途草稿，默认不传 common/previous attempt 或轮次参数。Manager 负责保存脚本、在独立沙箱执行改造及模拟、收集结果，并把具体失败交给生成器修正；接入 Agent 消费结果，不重复保存、执行脚本或制作本地 diff。

生成等待超时后按响应提示查询同一 job，任务仍运行时继续等待，不重复提交。沙箱通过只代表文件改造与模拟通过；真实依赖、插桩、编译和打包仍由 SCM 验证。只重生成失败用途，保留另一用途已有结果。

危险脚本、越界写入或无法可靠判断的行为立即停止。普通生成脚本的语法、文件定位和启动校验失败，由 Agent 继续重生成失败用途；`blocked` 或历史 `manual_recover` 显示不禁止这个操作，不需要用户修脚本。先从本轮响应提炼实际失败检查，不维护 common attempt / previous attempts 记录。

把实际错误写成 JSON 数组，通过 `--compile-knowledge-file` 交给下一轮。例如 `[{"category":"script_patch","signature":"校验返回的错误原文","cause":"已确认的原因；未确认则说明未知","remediation":"依据错误可执行的修正建议","source":"本轮草稿版本及失败检查名"}]`。先执行 `access artifact create --session-id <session-id> --purpose online --compile-knowledge-file <file>` 取得预览的 `compile_knowledge_hash`，再使用同一文件并追加 `--compile-knowledge-hash <hash> --yes`；测试侧失败时将用途改为 `--purpose test`，保留另一用途的产物。同用途最多进行3次有新证据的重生成，仍失败时联系陈思源；不要重复相同请求，不因依赖权限错误重新生成草稿。

### 5. 在 SCM 完成真实双轨编译

1. `access compile execute` 提交生成当前 draft 时的原始 build、boot、main、go.mod 快照；SCM 分别执行 `v3_online` 与 `legacy_test` 草稿。Agent 不在本地复现或替代这一步。
2. 编译身份默认从后台构建历史或普通 compile 流程的历史成功构建人中选择，不使用接入人作为默认或 fallback。
3. 若失败明确属于依赖权限，按历史成功人顺序轮换，每个身份最多尝试一次，总上限 3 个不同身份。身份耗尽后停止；不 fallback 接入人，不扩大权限，不重新生成 draft。
4. 若失败属于脚本补丁、业务编译或其它可改造问题，下钻 SCM 日志提炼实际错误，按上一节 JSON 格式通过 `--compile-knowledge-file` 交给下一轮 AI draft。只有改造内容变化后才重新触发编译。
5. 两条轨道均 `verified` 后才能进入发布确认；只成功一条时继续等待或修复失败轨道，不发布 artifact。

### 6. 权限、warning 与人工恢复

- 生成阶段的“读取验证输入失败：HTTP 403”指沙箱/TOS 输入读取，不等于 Codebase 仓库无权限。准入刚完成且源码已读到时，不申请该业务仓 Reporter，也不让用户审批；先复用同一生成任务查询结果，无有效产物且任务明确失败时仅重试失败用途。原地址签名或工具调用问题交生成器修正，仍失败联系陈思源。只有实际仓库文件读取返回 AccessDenied 或明确 restore_codebase_read，才进入仓库申请。
- 后台 Fornax 请求超时与 CLI 等待超时分开：增加 CLI --timeout-ms 不会改变后台 Fornax 的请求时限。先按返回的 job/session 查询同一任务，明确失败且有新证据后才重生成，不用延长等待代替修复。
- Codebase 仓库读权限失败：推荐 Reporter，先运行 `bytedcli --json codebase permission repository apply -R "<namespace>/<repo>" --action reporter` 取得真实 `manual_apply_url`。用户确认或已授权后追加 `--yes` 自动发起申请，并返回真实 `approval_url`。这条命令申请目标仓库自身权限；不要误用依赖仓批量 `permission apply --repos`，也不要使用需要 Owner 权限的 `permission repository create`。
- 无 canary 部署：说明将使用 `cluster=default` 且 `canary_name` 为空；用户同意或已有授权后用 `--confirm-warnings` 继续。不要建议先修改业务部署。
- FTF 自身无法解决的文件识别、编译证据矛盾、平台状态机或基础设施故障：停止自动化并联系陈思源。单聊入口：`https://applink.feishu.cn/client/chat/open?openId=ou_cc558af8a96811680ab31f430188b5a1`。只向用户提供链接，不主动代发 IM，也不创建 FTF oncall。

### 7. 跟踪状态与进度

- `access status` 用于读取 stage、status、block reason、recovery actions 和 next action；需要版本信息时增加 `--with-versions`。
- `access status` 的文本输出使用中文阶段、处理状态和下一步语义；JSON 同时保留原始枚举和 `stageLabel`、`statusLabel`、`nextActionLabel`，Agent 面向用户时优先使用中文标签。
- `access status --format graph|mermaid` 只渲染 Manager 返回的固定 nodes/edges。文本、Mermaid 和 JSON 必须表达同一组阶段，不临时增加“看起来合理”的节点。
- `access compile execute` 提交生成当前 draft 时的原始 build、boot、main、go.mod 快照；SCM 构建中会执行该 draft，不能再提交本地已应用 draft 的文件。生成时未传 `--repo-dir`，编译也省略它，直接读取同一远程分支；生成时使用本地工作副本，则保留生成前原始快照用于编译，不对用户已有改动执行清理或回退。四文件 override 规则与 `access admission execute` / `access artifact create` 一致；预览确认后增加 `--yes`，不要通过 JSON 手工注入 `file_snapshot`。
- `access compile status` 默认只查询一次。自动化需要等待时增加 `--wait`；轮询仅在 `compile_status=pending|running` 或 `auto_retrying=true` 时继续，其他状态立即停止。`--poll-interval-ms` 范围为 1000～60000，默认 3000；`--timeout-ms` 范围为 1000～1800000，默认 600000。
- 验证编译失败时，不能把 SCM commit 描述当作真实错误。历史 attempt 未返回或返回空白 `verification_path` 时按 `v3_online` 兼容解释。若 current attempt 同时提供 `scm_repo_id` 与 `scm_version`，继续执行 `bytedcli scm repo build-log --repo-id <scm_repo_id> <scm_version> --status failed`；历史响应缺少 `scm_repo_id` 时，只允许从可信 `compile_url` 的 `/scm/detail/<id>/` 路径提取一次，不猜仓库。FTF 返回的 `build_id` 是 SCM version id，不得直接作为 ByteBuild `--record-id` 使用。
- SCM 下钻时先获取真实失败 step、exit code 和最小脱敏错误摘要，不向用户展示完整 `detail`、`user_envs`、`scm_envs` 或整段日志。出现 v3 script、patch、hash、注入命令缺失等证据时归为脚本补丁问题；业务 Go 编译错误归为业务基线；权限错误归为权限；无明确证据才保留基础设施分类。下钻只用于诊断，不改变 Manager 的 `next_action`；Agent 不自动重试或切换 builder，依赖权限身份轮换只消费 Manager 返回的历史成功人策略。匹配《FTF 编译问题汇总》后，将命中项整理为 `signature/category/cause/remediation/source` JSON 数组，通过 `--compile-knowledge-file` 传给下一轮 artifact create；只传已确认知识，不附完整日志，不把未知原因补写成确定结论。
- 对 hash mismatch、权限、基础设施等平台策略之外的编译问题，参考 [FTF 编译问题汇总](https://bytedance.larkoffice.com/wiki/VRm1wE6kIiytzKkTyOUcggQQnQh) 查找同类错误。命中已知问题后，把“错误、原因、对策”整理为结构化条目写入 `evaluation.issues`，与真实 SCM 失败证据和四文件快照一起作为下一轮 AI draft 的输入；未命中时也要把已确认的真实错误和可执行建议写入 issues，不用猜测补足原因。依赖权限错误只触发最多 3 个历史成功构建人的轮换，不进入下一轮 AI draft。最终 AI draft 只允许修改 build 和 bootstrap；main.go、go.mod 与其它业务源码只能作为分析输入，不得写入改造结果。
- Manager 为线上与测试用途分别创建构建，携带各自 manifest、artifact、source hash、script hash 及 purpose。历史 `legacy_test` 名称继续兼容，但新测试编译必须实际消费独立测试稿；失败反馈和重新生成只作用于对应的一侧。
- 两条验证均通过后执行 `access artifact publish`，不得使用 `artifact deploy` 代替首次发布。首次发布成功后继续完成 SCM 配置、PSM 注册和工单收尾；中途失败时先重新执行不带 `--yes` 的 publish 预览，消费最新 SCM 状态后再确认恢复，由 current 指针和后端回读幂等续跑，不改选其它版本。
- `access record open|close` 只要求 `--psm example.psm`；`--env`、`--region` 可选，未显式传入时由 Manager 使用 `prod/cn`。显式选择面板时必须同步选择请求网关：CN 使用全局 `--site cn` 配合 `--region cn`，China-Pay 使用全局 `--site cn --vregion China-Pay` 配合 `--region china-pay`，不得只改业务 `--region`。命令默认预览并要求 `--yes`，预览必须明确只修改 `is_open_record`，保留采样策略且不创建、关闭或切换 ByteCopy。操作人由 JWT 解析，不提供 `--trigger-user`。
- `access record status --psm example.psm` 查询 SDK Agent、SDK、prebuild、ByteCopy、普通/深度录制接入标记及线上录制状态。`is_register_sdk_agent` 是接入来源的规范性标记；核心用户结论仍优先展示 `is_register_sdk` 和 `record_status`。它不查询 recorded flow；用户说“有没有录制流量”时仍使用 `ftf flow ...`。
- 文本输出先看 compile status、last error category、recovery action 和 next action，再看 attempt 表与 current attempt 详情。JSON 保留后端扩展字段和完整 attempt 证据，但删除所有 `file_snapshot` 与 `failure_evidence.user_envs`，并继续脱敏脚本、base64、凭证和 URL userinfo；唯一例外是 artifact create 或显式生成任务查询成功结果中的 `generation.script_content`，用于 Agent 审查和受控执行。
- 正常推进时不向用户逐轮展开脚本调优细节，只报告关键阶段变化。只有需要用户动作时才展示阻塞原因、影响和建议动作。

## 低打扰交互策略

| 场景                                                                                         | 是否打断用户 | 处理                                                                                       |
| -------------------------------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------ |
| 已有完整 selector、branch/commit 和四文件                                                    | 否           | 自动完成只读检查、AI 沙箱改造模拟、SCM 编译和状态查询                                      |
| 缺少目标 branch/commit、关键文件路径或必要业务参数                                           | 是           | 只询问缺失且无法安全推断的输入                                                             |
| 需要申请权限或确认 warning 的业务语义                                                        | 是           | 展示具体检查项、影响和拟执行动作                                                           |
| 普通 draft 生成与静态验证通过后的 immutable 自动上传                                         | 否           | 由一次 `artifact create --yes` 连续完成，不等同正式发布                                    |
| 首次 `artifact publish`、显式 `--upload-to-tos`、历史版本 `artifact deploy` 或其它高风险写入 | 是           | 先展示预览，获得明确确认后执行；用户已前置授权自动推进时仍展示变更，随后直接执行并简要通报 |
| 危险脚本、不可恢复 blocked、历史成功构建人 3 次权限轮换耗尽                                  | 是           | 停止自动化，提供 manual recovery 证据包和陈思源单聊入口                                    |

## 上传、发布与回滚安全

- 静态验证通过的 draft 由 Manager 自动上传 immutable manifest/script，并在回读校验成功后返回 `compile_ready=true`；上传失败不得写入可编译状态。
- dangerous script、`evaluation.status=failed`、`evaluation.status=blocked` 时不得进入 compile-ready，更不能发布。
- 不把“生成了脚本候选”或“沙箱模拟通过”描述为“业务改造完成”；只有真实 diff 与 SCM 双轨编译验证通过后才能进入发布确认。
- 首次发布必须使用 `access artifact publish`。它只接受等待首次发布的 compile-verified draft；成功后必须同时确认 current 指针、SCM 配置回读、`is_register_sdk_agent` 及关联 SDK 状态、工单完成和 `registered` 阶段。
- 历史版本回滚通过 `access artifact deploy` 执行，只允许显式选择历史 `verified` artifact version。目标不存在、blocked、failed 或验证状态不明确时拒绝。
- `artifact deploy` 未传 `--yes` 时只展示 current、目标版本和影响；用户明确确认后才能重新发布。目标已经是 current 时按幂等结果返回，不重复发布。
- 发布后必须读回 current version；读回与目标不一致时报告不确定写结果，不能宣称成功。
- Phase 5 的 `artifact deploy` 仅重新发布历史已验证 artifact，不关闭 prebuild。关闭 prebuild 延后到 Phase 6，不在本工作流中通过其它命令替代。

## 人工恢复证据包

进入 manual recovery 或联系陈思源时，提供最小脱敏证据：

- order id、session id、PSM。
- 业务工作副本标识、目标 branch、基线 commit 和当前 HEAD commit。
- 四文件的仓库内相对路径和大小，不包含文件原文或 base64。
- AI 沙箱改造脚本的安全审查结论、真实 diff 摘要和 issues；不包含本地 build/boot 结果，因为默认流程不运行它们。
- 当前 stage/status、block reason、recovery actions、next action。
- 验证编译的 compile status、current attempt、attempt 顺序、使用过的历史成功构建人数量、last error category、recovery message、next action 和脱敏 compile URL；不包含 `file_snapshot` 或 `failure_evidence.user_envs`。
- 是否曾请求上传或回滚，以及最终 current version 读回结果。

不得附带真实脚本全文、仓库凭证、Cookie、JWT、环境变量值或其它敏感信息。

## 测试与线上分别生成、验证

`access artifact create` 默认读取一次源码并准备线上和测试两份草稿。普通测试编译保留原程序名和启动参数，设置录制能力；线上用途保留普通程序及已确认录制范围。Atum读取直接配置，保留已解析的build/test命令和原生FTF阶段。

显式 `--upload-to-tos` 只上传当前用途已评测通过的草稿，未指定 `--purpose` 时为线上用途，不自动生成另一用途；两用途的验证证据不混用。

两份草稿分别真实编译；测试侧失败不会丢掉线上产物。使用 `access artifact create --purpose test|online` 或 `access compile execute --purpose test|online --artifact-version <version>` 只重做对应用途。错误和历史尝试应来自该用途，不把另一侧的错误传给模型。缺少测试草稿时先补测试草稿，不以旧固定插桩的编译成功替代。

发布前预览分别展示两侧实际改动。默认缺省请求仍兼容线上用途；工单和状态只描述产物与当前进度，不要求整段节点从头执行。
