---
name: bytedance-maat
description: "通过 bytedcli 查询 Maat CN/i18n 项目和收藏，修改管理员，构建分支并经确认新增/修改/删除灰度、调整顺序及完整条件树（用户名、请求头、Cookie、Query、AND/OR）；也支持联调环境搜索、配置查看、单环境分支与配置修改及触发构建。不用于全量上线、删除项目/构建或回滚。"
---

# Maat

通过 `bytedcli maat` 操作。项目名来自用户或查询结果，不能写死样例项目。
构建和灰度流程优先使用本 skill 的 CLI，不切到旧版网页操作 skill。若本机 CLI 尚无对应命令，说明版本/安装缺口，不把浏览器代操作当成 CLI 能力已通过验证。
全局站点支持 `--site cn` 和 `--site i18n`，分别使用独立站点和对应 Titan Passport 登录链路；不要复制浏览器 Cookie、JWT，也不要要求用户粘贴凭据。`i18n-bd`、`i18n-tt` 不等于 `i18n`，不自动代换。

站点与发布区域不同：CN 的常规操作区域默认 `CN`；i18n 先用 `project get` 读取 `publishRegionList`，再为区域查询、管理员更新和灰度操作显式传 `--region` 的准确值，例如 `Singapore-Central`，不能猜成 `SG`、`I18N` 或沿用 `CN`。i18n 的 `project get` 不带区域时只返回元数据，不查询区域版本。

CN 项目的 `publishRegionList` 不含 `CN` 时，`project get` 不带区域也只返回元数据和区域提示，不报目标不匹配、不自动选择其他区域。项目版本摘要和灰度操作不使用固定区域白名单，应传该项目 `publishRegionList` 中的准确值，例如 `--region Volcengine`。灰度发布支持 `byte` 和使用 Maat 渲染链的 `volcengine` 普通前端单 SCM 项目；不支持 `volcengine` 渲染链或未知渲染链。构建、管理员修改及联调写入仍保持各自原有限制，不因灰度支持而扩展。

## 查询

```bash
bytedcli --site cn --json maat user get
bytedcli --site cn --json maat project list
bytedcli --site cn --json maat project list --favorites --page 1 --page-size 20
bytedcli --site cn --json maat project get --project demo-web
bytedcli --site cn --json maat project get --project demo-cloud --region Volcengine
bytedcli --site cn --json maat version list --project demo-web --search 1.0.0.42 --page 1 --page-size 20
bytedcli --site cn --json maat gray get --project demo-web
bytedcli --site i18n --json maat project list --favorites --page 1 --page-size 20
bytedcli --site i18n --json maat project get --project demo-web
bytedcli --site i18n --json maat gray get --project demo-web --region Singapore-Central
```

版本列表只包含成功构建，搜索可能是模糊匹配；发布必须使用准确版本号，不能自动选最新。列表返回 `page`、`page_size`、`current_count`、`truncated`，不把当前页条数当成总数。查询不会初始化灰度配置。

`project list` 默认列出可见项目；“我的收藏”必须加 `--favorites`，使用服务端当前登录用户的收藏筛选，不能把可见项目或常用项目冒充收藏。收藏列表返回真实 `total`、`page`、`page_size` 和 `has_more`；用户要列举全部收藏时应翻页到 `has_more=false`，明确说明只展示当前页的情况。

## 联调环境

用户说“联调环境”时使用 `maat dev`，不是生产 `maat build` 或 `maat gray`。先读 [联调环境操作](references/dev.md)，覆盖列表/配置查询、单环境更新、触发构建和状态日志。

- `dev list/get` 按项目和区域搜索/精确定位；`dev config get` 只读项目级公共设置，绝不初始化。i18n 的环境操作需要准确 `--region`。
- `dev update` 修改单个环境的分支、描述、订阅人、静态资源或 API 代理配置。默认只读预览，展示变化和副作用后单独确认，再加 `--yes --confirm-plan`；未指定字段保留。
- `dev build` 触发已配置环境的构建，单独预览和确认。联调 SCM 来自 `dev config get`，可能与生产 SCM 不同；不能用生产分支查询结果替代联调分支校验。
- 修改或构建可能触发联调环境自动部署、订阅通知，不宣称是生产构建的 `onlyBuild`。`accepted` 仅表示受理，`dev get/logs` 是环境状态/历史，不可把旧成功状态归因于本次触发；结果未知时不重复提交。
- 项目级域名、SSO、页面路由以及共享 API 代理目标只读；不创建/删除环境，不调用额外部署接口，不顺带修改生产或灰度。

## 分支构建及衔接灰度

构建支持普通前端单 SCM 项目，CN/i18n 共用命令，i18n 构建和等待需要准确 `--region`。详细参数、恢复方式及验证边界见 [构建流程](references/build.md)。

### 确认节奏

- 区分用户授权和 CLI 预检。用户明确要求“构建某分支”或“构建并灰度”，且当前上下文已唯一确定项目、站点、区域和分支时，该请求已授权这一次生产 `onlyBuild`。Agent 仍先运行只读预览并核对范围，再携带指纹提交，无需额外问“是否开始构建”。仅讨论方案、查询或要求“先预览/等确认”不授权构建；用户另有确认要求时遵从。
- 已明确的参数复用当前任务上下文，不逐项重复询问。缺少或冲突的必要信息集中澄清一次；不能用默认项目、相似分支、最新版本或猜测的条件补齐。请求 ID、指纹、查询、轮询和回读由 Agent 处理，不要求用户手填或确认这些机械步骤。
- “构建并灰度”的正常路径是：自动预检并构建 → 验证本次构建结果 → 准备一份完整灰度预览 → 等待一次上线确认 → 提交并回读。初始请求不授权跳过灰度预览后的确认；仅构建请求也不授权追加灰度。
- 同一条灰度的版本、流量、条件和顺序变更合并为一次 `gray deploy` 预览及一次上线确认，不按字段拆开问。确认提示说清目标、变化、不变项、风险及完整条件/顺序；不让用户再确认一遍相同参数。删除是独立操作，按删除预览确认一次，不能沿用 deploy 的确认。
- 用户在当前唯一待确认预览后回复“上线”“发吧”或“确认”，即可使用该预览指纹执行，不再问“是否确认执行”；存在多个待确认目标或回复含糊时先澄清。不要仅为确认流程重复生成相同预览，CLI 自身仍会提交前重查。`no_op` 直接报告无需变更，不索取上线确认。
- 目标/意图改变、预览出现未授权风险、冻结异常或 `MAAT_PLAN_STALE` 时停止并说明具体差异；需要新预览和新确认，不能自动替换指纹。结果未知只读核查，不把原授权当成重复写入授权。管理员和联调环境的独立确认规则不受本节影响。

1. 用 `branch list --search` 查找，再用 `branch get --branch` 确认准确分支及提交。无精确匹配时停止并请用户确认分支已推送到关联 SCM 仓库，绝不自动使用 `master` 或近似分支。
2. 为本次构建生成独立随机 UUID 作为 `--request-id`，预览和提交复用该值。运行 `build create` 默认只读预览，描述默认来自分支最后一次提交，项目 SCM 环境变量原样保留且不打印值。
3. 核对预览的项目、站点、区域、仓库、分支、提交哈希、描述、环境变量键和冻结信息符合本次授权，保留 request-id 和指纹用于提交及恢复。符合上文授权条件时简要告知构建目标，直接以原参数加 `--yes --confirm-plan <fingerprint> --wait`；否则仅澄清缺口或等待用户指定的确认。只允许 `onlyBuild`，不调用构建后自动灰度/全量上线模式。
4. `accepted` 仅为服务端受理，不是构建成功；`succeeded` 才可衔接灰度。失败、未知、超时、提交漂移或多条匹配时停止发布。恢复用 `build wait`，不得重复 create。不能把列表第一条、最大版本或成功历史记录当成本次结果。
5. 用户要求“有则修改、无则新建”时，在构建成功后读取 `gray get`，先精确匹配条目标识；若用户说的是环境值，再检查完整条件。命中多个或名称/条件冲突时澄清，不把 `ppe` 等前缀匹配视为同一条。
6. 存在目标条目时，`gray deploy --mode update --version <本次准确版本>`，未要求修改的流量与条件保持不变。不自动替换条件树。
7. 不存在时，复用用户已明确的新灰度标识、流量比例和条件，只询问缺失或冲突项，再 `--mode create` 预览。完整条件树使用 `--conditions-file`，简单请求头使用 `--header`；不能从 `ppe_*` 名称猜测请求头，未经用户要求不能从其他灰度复制条件。用户明确要求参照其他灰度时，先唯一定位参照项，将实际采用的流量和条件纳入同一份发布预览；多个候选不一致时先澄清。
8. 无论创建还是修改，展示完整灰度预览后**单独等待一次上线二次确认**。构建授权不授权灰度发布。收到该预览的确认后直接按下文提交和回读，不再追加执行确认。

```bash
bytedcli --site cn --json maat branch list --project demo-web --search feature/demo
bytedcli --site cn --json maat branch get --project demo-web --branch feature/demo
bytedcli --site cn --json maat build create --project demo-web --branch feature/demo --request-id sample-build-001
bytedcli --site cn --json maat build list --project demo-web --branch feature/demo --page 1 --page-size 20
bytedcli --site cn --json maat build get --project demo-web --version 1.0.0.42
```

## 修改项目管理员

对应控制台“基本信息 → 项目管理员”，不是值班人，也不是单个灰度的操作者。管理员拥有上线权限，变更作用于所选站点内整个项目，`--region` 只是表单上下文，不限制授权范围。

```bash
# 增补或移除，默认只预览，保留其他管理员
bytedcli --site cn --json maat project admins update --project demo-web --add demo-alice --remove demo-bob
# 整组替换，必须由用户明确提供完整名单，不与 add/remove 混用
bytedcli --site i18n --json maat project admins update --project demo-web --region Singapore-Central --admins demo-alice,demo-carol
```

展示 `site`、项目、区域上下文、执行身份、`before`、`after`、`added`、`removed`、自移除风险和指纹后，**单独等待用户二次确认这一权限变更**。确认后以相同参数加 `--yes --confirm-plan <fingerprint>` 提交。不能仅因用户要求“集成功能”就修改真实管理员。

姓名必须是准确 Maat 用户名；模糊人名先澄清，不猜测账号。不能删除最后一位管理员，不接受同时新增/删除同一人。只修改 `adminUsers`，保留关联 SCM、描述、值班、锁定、业务域和其他表单字段；不显示项目 token。`MAAT_PLAN_STALE` 需要新预览及新确认；`MAAT_ADMIN_UPDATE_UNKNOWN` 需停止并人工核对控制台，不自动重试。移除自己后可能无法回读，不能因此重复写入。`verified_after_error` 仅表示回读匹配，不证明该写请求成功。

## 新增或修改并上线

完整条件树编辑（含 `inner.username` 用户名单、Cookie、Query 和嵌套 AND/OR）先读 [条件编辑](references/conditions.md)。使用 `--conditions-file` 输入目标灰度的完整 `rootCondition`，不是整份灰度配置，也不是局部补丁。用户要求“增加一个人”时，先查询、精确定位对应节点、保留现有成员和其他条件，编辑后预览；不改用 `--header`，不自行猜测账号后缀或改变 AND/OR。

指定插入位置或移动已有灰度使用 `--before <准确灰度名>` / `--after <准确灰度名>`，先读 [灰度顺序](references/conditions.md#灰度顺序)。顺序变化可能影响优先级命中，必须展示 `order.before` / `order.after`；与同一条灰度的版本、条件变更合并确认上线，不把“只调整顺序”当成只读操作。

1. 确定准确项目、灰度标识、新增或修改模式、版本、流量比例和条件。新增必须显式提供版本及流量；修改未指定的字段保持不变。
2. 运行不带 `--yes` 的预览。新增不会申请 ID，也不会创建或发布灰度；修改不会保存草稿。
3. 向用户展示操作模式、项目、站点和发布区域、执行身份、灰度标识、前后版本、流量百分比、完整目标条件、冻结提示、影响其他灰度与否，以及 `fingerprint`。无条件 100% 必须显著说明可能影响全部用户。`--conditions-file` 和 `--header` 都会替换整个目标条件树，不是追加。
4. **展示预览后，单独等待一次用户明确二次确认。初始的“上线灰度”指令不算二次确认。Agent 不得自行批准。** `no_op` 则报告无需变更，不再请求上线确认。
5. 用户确认当前唯一预览后，用完全相同参数加 `--yes --confirm-plan <fingerprint>`，不重复确认执行。任何参数、身份或远端配置变化都必须重新预览并再次确认，说明变化原因；不能擅自换用新指纹。
6. 核对结果。`verified` 表示写后配置回读一致；`verified_after_error` 表示写请求报错但回读已匹配，不能归因于本次写入。两者都不证明真实线上流量命中。`MAAT_DEPLOY_UNKNOWN` 必须停止，读取配置并查控制台上线日志，不得盲目重试。

```bash
# 新增：只预览，显式使用 0% 随机流量和请求头条件
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode create --version 1.0.0.42 --flow 0 --header x-demo-env=demo-gray

# 修改：仅改变版本，保留原流量和条件
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode update --version 1.0.0.43

# 火山项目使用准确区域；仅修改版本，保留现有条件和流量
bytedcli --site cn --json maat gray deploy --project demo-cloud --region Volcengine --name demo-gray --mode update --version 1.0.0.43

# i18n 同样支持新增和修改，必须指定准确发布区域
bytedcli --site i18n --json maat gray deploy --project demo-web --region Singapore-Central --name demo-gray --mode create --version 1.0.0.42 --flow 0 --header x-demo-env=demo-gray

# 修改条件：多个请求头条件按 AND + Equals 组合，替换整个原条件树
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode update --flow 1 --header x-demo-env=demo-gray --header x-demo-group=sample

# 自由编辑完整条件树：仅预览，保留未指定的版本和流量
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode update --conditions-file ./conditions.json
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode update --after demo-first --before demo-last

# 仅在用户看过相同预览并二次确认后，使用该次真实 fingerprint 提交
bytedcli --site cn --json maat gray deploy --project demo-web --name demo-gray --mode update --version 1.0.0.43 --yes --confirm-plan <fingerprint>
```

`--flow` 单位为 0-100 百分比；查询 JSON 中 `flow` 是 0-1 ratio，向用户解释时乘 100。`--conditions-file`、`--header`、`--clear-conditions` 三者互斥；省略三者则保留原条件。`--clear-conditions` 或文件中的空根条件组会清空全部目标条件。新增同名灰度报错，不会隐式修改；修改不存在的灰度也报错。不传 `--before/--after` 时，新建默认追加末尾、修改保留原位置；传入时只插入或移动目标，其他条目的内容及相对顺序不变。

## 删除灰度

用户要求删除或移除一条灰度时，使用 `maat gray delete`，先读 [删除流程](references/gray-delete.md)。按准确项目、站点、区域和灰度名称定位，只删除一个条目；这是发布配置变更，不是只删页面草稿，不等同于将流量设为 0 或清空条件。

先不带 `--yes` 预览，展示被删条目的版本、条件、流量、完整前后顺序及冻结提示，单独取得一次上线二次确认后，直接带相同 `--confirm-plan` 提交，不再重复核对目标。删除最后一条时，在这次确认中显著提示列表将为空；不能保证流量仍落到相同版本。未确认前不写入，不执行批量删除。

```bash
bytedcli --site cn --json maat gray delete --project demo-web --name demo-gray
bytedcli --site i18n --json maat gray delete --project demo-web --region Singapore-Central --name demo-gray
# 仅在用户审阅相同删除预览并二次确认后提交
bytedcli --site cn --json maat gray delete --project demo-web --name demo-gray --yes --confirm-plan <fingerprint>
```

## 边界与停止条件

- 支持已初始化灰度配置的普通前端单 SCM 项目，新增、修改和单条删除灰度均支持。非 CN 区域必须由项目明确声明；仅兼容旧项目未声明区域时的 CN 默认值。`volcengineConfig.renderChain` 未设置、为空或为 `maat` 时使用 Maat 灰度路线，为 `volcengine` 或未知非空值时拒绝。未初始化项目不自动初始化；父子项目、KuraCloud、Goofy 托管、后端灰度、多 SCM、锁定/禁止灰度的项目拒绝提交。不要改用手写请求绕过这些边界。
- 生产仓库构建仅使用 `onlyBuild`；联调环境构建可能自动部署到该环境，按上文单独确认。不全量上线、不删除项目/构建/联调环境、不回滚。灰度删除仅支持上述单条确认流程。项目基本信息仅支持上述管理员变更，联调配置仅支持单环境字段；不绕过权限、审批或封禁。冻结查询失败即停止。灰度是否受某项冻结限制由 Maat 规则决定，不能把“有冻结提示”或“灰度例外”理解成任意发布授权。
- 服务端使用整份灰度配置更新；CLI 保留非目标条目及其顺序，提交前重查快照。不具备已验证的服务端原子 CAS，预览到提交期间避免多人同时操作。
- 所有写请求最多发送一次。新增的 ID 分配也只在确认后发生；分配后若配置变化则停止，不发送灰度更新。
- 需要线上命中验证时，另行确认真实访问地址和条件，再检查相应响应；不要仅凭控制台配置或构建成功宣称已命中灰度。

接口字段与验证边界见 [接口契约](references/contracts.md)。
