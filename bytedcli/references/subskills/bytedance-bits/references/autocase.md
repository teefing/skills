# AutoCase 运行与报告

使用 `bytedcli bits autocase` 查询 AutoCase / Verse / BITS scenario plan 的运行，或更新既有 manualTask 中一条精确叶的状态、测试备注与截图。

## 对象 ID

- `planDetail/{scenarioPlanId}` 标识 scenario plan。
- `manualTask/{runId}` 标识可执行的 BITS run；其 ID 是后端 `TestPlanId`。
- URL 查询参数 `devops_space_old_id` 是 BITS/OneSite 的路由项目 ID；ID 模式的 `--project-id` 也必须传这个路由 ID。
- `run get` 返回的 `projectId` 是服务端业务 `ProductId`，不能直接复制为 `run pass --project-id`。需要写入时优先复用同一个完整 URL，或从 URL 的 `devops_space_old_id` 取得路由 ID。
- `--case-id` 是 `LeafInfo` 中的源 `CaseId`，不是列表序号；它必须与同一叶的 `--minder-id` 成对使用。

请保持 scenario plan、manualTask、路由项目、业务 ProductId 和叶 ID 的语义独立。优先传入完整的 BITS `manualTask` URL，因为 URL 同时携带 scenario plan、路由项目与 OneSite space 上下文。

## 命令

```bash
# 推荐：URL 携带 scenario plan、run、space 与 project routing（devops_space_old_id）。
bytedcli bits autocase run get \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>"

# 仅传 run ID 时，--project-id 必须是 URL 的路由项目 ID，不是 run get 返回的 ProductId。
bytedcli bits autocase run get --id <run-id> --project-id <routing-project-id> --space-id <space-id>

# 使用统一 deadline 轮询。
bytedcli bits autocase run get --wait \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>" \
  --timeout-ms 1800000 --poll-interval-ms 15000

# 原子写入 report.json；路由仍来自 URL。
bytedcli bits autocase run report \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>" \
  --out ./autocase-report

# 预览一条精确的源 CaseId + MinderId 叶（默认也是预览）。
bytedcli bits autocase run pass \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>" \
  --case-id <source-case-id> --minder-id <minder-id> --dry-run

# 明确提交一次，写入测试备注，并回读同一叶确认 Status=1 与 Note。
bytedcli bits autocase run pass \
  --id <run-id> --project-id <routing-project-id> --space-id <space-id> \
  --case-id <source-case-id> --minder-id <minder-id> \
  --note "Regression verified" --yes
```

## 字段复制与精确叶查找

`run get --json` 的 `data.projectId` 是业务 ProductId，不能用它替代写入路由。若使用 URL，直接把同一个 URL 传给 `run pass`；若使用 ID 模式，从原 URL 的 `devops_space_old_id` 复制路由项目值到 `--project-id`，不要从 `data.projectId` 猜测。

要取得精确的源 `CaseId` 与叶 `MinderId`，对同一 URL 使用只读 `test-plan get`，遍历实际返回的 `data.LeafInfo`，不要取第一条或把数组位置当作 `CaseId`。`LeafInfo` 外层 map key 是 `TestCaseId` 分组键，不能替代叶对象中的源 `CaseId`；以叶对象的 `CaseId + MinderId` 为准：

```bash
bytedcli --json test-plan get \
  --url "https://bits.bytedance.net/devops/<space-id>/quality/plan/scenarios/planDetail/<scenario-plan-id>/manualTask/<run-id>?devops_space_old_id=<routing-project-id>" > ./autocase-leaf.json
```

核对叶对象的 `CaseId` / `MinderId` 后，再把同一对值传给 `run pass`；外层 `TestCaseId` 只用于分组定位，不要把它当作 `CaseId`。`run report` 的旧 `projectId` 同样是报告侧业务项目字段，不是可供 `run pass` 猜测的路由来源。

## 单叶通过

`run pass` 先读取当前 manualTask 的 `LeafInfo[TestCaseId][MinderId]`，再按叶对象中的源 `CaseId` 精确匹配目标，只允许未执行、失败、阻塞或跳过叶目标通过。可选 `--note <text>` 会写入同一叶的测试备注；已经通过的叶仍可单独更新备注。若状态已经通过且备注内容也相同，则返回 `noOp`，不会重复写入。空白备注会被拒绝；省略 `--note` 不会清空已有备注。

默认与 `--dry-run` 都是预览，文本会明确显示 `Not executed`；JSON 中 `dryRun:true` 或 `noOp:true` 且 `write:"not-run"` 表示命令业务成功但没有执行平台写入。只有 `--yes` 才执行状态或备注写入，`--dry-run` 与 `--yes` 不能同时使用。

状态通过与测试备注是两条已验证的 BITS 写入契约：状态走 `ExecuteTestPlan`，备注走 `RemarkTestPlan`（`/caseApi/addPlanRemark`）。需要更新状态时，CLI 先写状态再写备注；叶已经通过时只写备注。CLI 会将纯文本备注封装为 BITS 富文本 JSON，再重新读取同一 CaseId + MinderId；只有状态确认为通过，且指定的备注也回读一致时，才报告 `verification: confirmed`。成功 JSON 结果中的 `statusWrite` 与 `noteWrite` 为 `not-run`、`submitted` 或 `reconciled`；`rejected` / `unknown` 只出现在未收敛错误详情的 `status_write` / `note_write`。

两条写入都不会自动重放。若响应未知，CLI 会先回读同一叶进行一次收敛：目标状态与备注均已落盘时可确认成功，否则通过错误详情中的 `status_write`、`note_write` 与 `stage` 区分拒绝、未知和部分成功，提示先核对再决定是否重试。Operator 从当前登录身份取得，不接受手填凭据或认证头；该命令不批量执行、不改变其他叶或整个计划状态。

## 单叶状态、备注和截图同步

`run update` 支持 `--status unexecuted|passed|failed|blocked|skipped`、`--note <text>` / `--note-file <UTF-8文件>` 及可重复的 `--image <本地路径>`。至少提供其中一项；省略状态会保留当前状态，省略备注会保留当前文本。备注输入替换文本，已有截图与富文本扩展字段始终保留；不提供删除图片操作。`run pass --note` 同样保留原有图片。

```bash
# 先预览：没有上传、状态或备注写入。
bytedcli bits autocase run update \
  --url "<完整BITS-manualTask-URL>" --case-id <源CaseId> --minder-id <MinderId> \
  --status blocked --note-file ./result.txt --image ./screenshot.png --dry-run

# 确认执行：只补说明和截图，保留当前结果。
bytedcli --json bits autocase run update \
  --url "<完整BITS-manualTask-URL>" --case-id <源CaseId> --minder-id <MinderId> \
  --note-file ./result.txt --image ./screenshot.png --image ./another.png --yes
```

测试备注应记录实际测试账号（脱敏）、包版本、设备、测试环境与泳道、观察到的结果和阻塞原因；不要写密码、验证码、Cookie 或 Token。`--note` 与 `--note-file` 互斥，空白文本被拒绝，两者均限制为 1 MB UTF-8 字节。文件读取也有上限，读取期间增大超过限制会拒绝。API/SDK 入口为 `services.bytest.updateAutoCaseLeaf`；CLI 命令的命名参数同时生成 MCP schema（`image` 接受路径数组）。

截图按文件签名验证 PNG/JPEG/GIF/WebP，单张不超过 20 MB、每次最多 30 张，输入文件总计不超过 50 MB（包括重复路径或内容），更大的批次分次同步。预览只读取和验证本地文件；`--yes` 才调用 `UploadCommonFile2Tos`。上传名含内容 SHA-256，相同叶上再次同步同一内容会复用已有图片，不重复上传或写备注。此去重适用于 CLI 已上传、仍保留原名的图片；历史 UI 上传的图片没有此内容标识。

组合操作依次执行需要的状态写入、图片上传、备注写入，然后回读同一叶。备注写入前会重新检查原备注与目标状态，有并发修改时停止覆盖；平台未提供原子 compare-and-set，无法完全消除检查后的并发窗口。上传与备注没有跨接口事务，失败时图片可能已上传但尚未挂到备注。所有写接口禁用自动重试并拒绝跳转。上传响应未知时不盲目重传；错误详情包含 `stage`、`status_write`、`note_write`、`partial_success`、`images` 和可用的上传 URL，先核对再恢复操作。成功回读才返回 `verification: confirmed`；预览和 no-op 不代表新写入。

平台权限、计划状态和缺陷关联约束以接口实际返回为准；拒绝更新时返回错误，不擅自改为其他测试结果。该命令只更新单叶测试结果，不修改整体计划生命周期，也不代替真实测试执行。

## 运行状态

`run get --wait` 将 BITS 平台状态映射为 `succeeded`、`failed`、`blocked`、`exception` 和 `canceled`。失败的 run 退出码为 `2`；blocked 或 exception run 退出码为 `3`；canceled run 与超时退出码为 `4`。

## Plan 执行限制

经验证，BITS `CreateTestPlan` 操作接收完整的创建模板，包括基础信息、测试配置、case 选择、路由上下文与操作人；它会创建 scenario plan，并通过 `GetTestPlanTaskList` 暴露生成的 `manualTask`。该操作不支持仅凭现有 `planDetail/{scenarioPlanId}` 发起执行。`ExecuteTestPlan` 只更新现有 `manualTask` 内的 minder results；测试备注由独立的 `RemarkTestPlan` 更新。

请先在 BITS 中启动现有 scenario plan，再将生成的 `manualTask` URL 传给 run 命令。

## 报告与 Evidence

`run report` 通过同目录临时文件与原子 rename 写入 `report.json`。报告包含 run 摘要字段、业务项目字段、可用的聚合报告数据，以及稳定的 AI / report evidence URL。

经验证的 API 会返回 evidence link，但没有稳定的鉴权附件下载 contract。因此该命令只记录元数据，不跟随 redirect 或下载文件，避免不安全跳转、错误 MIME 处理和凭据泄漏。
