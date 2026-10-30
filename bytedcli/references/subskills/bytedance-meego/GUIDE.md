---
name: bytedance-meego
description: "Use for Meego/Meegle operations through `bytedcli meego ...`. MCP-backed commands share a tenant-scoped login profile; this skill also documents bytedcli-only GoAPI, shortcuts, compatibility output, and offline helpers."
---

# bytedcli Meego

## 路由边界

`bytedcli meego` 同时包含两类能力，先判断命令归属再加载说明：

1. **平台命令面**：读取安装目录中的 `references/meegle/GUIDE.md`，并按其中链接继续读取对应 reference。该 reference 由 `bytedcli self skill install/update` 在安装/更新时自动补齐；仓库源包只保留 bootstrap guide。若读到 bootstrap guide，先按其中命令刷新 skill，再继续业务操作。
2. **bytedcli 自有命令**：读取本文件。包括快捷命令、GoAPI 删除/view preference、输出兼容、tool 管理和离线 URL 解析；其中需要 MCP 的步骤仍通过 official CLI 执行。

所有业务命令统一从 `bytedcli meego ...` 进入；遇到命令路径差异时以 `bytedcli meego --help` 和具体子命令 `--help` 为准，不要直接猜别名，也不要直接执行任何外部命令。认证统一从 `bytedcli meego login` 进入。

## 认证边界

认证边界如下：

- **official MCP profile**：默认租户使用 `bytedcli` profile，DCD 使用 `bytedcli-dcar` profile；全部 MCP-backed 命令都从这里取凭据。直接执行 `meegle ... --profile bytedcli` 与 `bytedcli meego ...` 使用同一登录态和 refresh token。
- **GoAPI / Web session**：推荐由用户在本机浏览器保持 Meego 登录并自行设置 `export BYTEDCLI_MEEGO_BROWSER=chrome`（可选 `chrome-beta` / `chromium` / `vivaldi`）；设置即授权 bytedcli 无确认地读取该浏览器的 Meego cookie（macOS 首次读取会弹钥匙串授权），Agent 不要替用户设置。cookie 缓存缺失、过期或被服务端拒绝时，bytedcli 会自动从该浏览器恢复并校验（该浏览器只能有一个 profile 登录 Meego），无需 Feishu session 或重新登录。缓存缺失时 `meego status` 的 `providers.goapi` 为 `state=bootstrap_available, source=browser_cookie`（表示优先尝试的来源），恢复后写入缓存显示 `meego_cookie_cache`；变量值非法时为 `state=missing` 并在 `reason` 说明，命令报 `MEEGO_GOAPI_BROWSER_INVALID`。也可执行 `bytedcli auth login --session --feishu`，其纯 HTTP 双域换票可能停在飞书登录页，此时 `meego_goapi_session_ready` 为 false，改用 `BYTEDCLI_MEEGO_BROWSER`。成功输出中的 `feishu_web_session_ready` 与 `meego_goapi_session_ready` 是两项独立状态；只有后者为真才表示 Meego 双域换票或经探活的浏览器 Cookie 恢复已经完成。需要复用已登录 Meego 的本机浏览器时，可显式使用 `--session-method browser-cookie --browser <browser> --yes`。`bytedcli meego status` 会区分现成 Meego cache 与可用于 bootstrap 的浏览器或共享 Feishu session；`meego logout` 只清理当前租户的派生 cache，不退出共享 Feishu session。

`bytedcli meego auth login` 不存在；统一入口是 `bytedcli meego login`。official CLI 缺失、版本不兼容或未登录时直接报错，不回退到另一套凭据。`--dry-run` 在本地预览，不触发登录或网络调用。

### 受管环境注入凭据（无头 / CI 零交互）

受管平台（Agent 沙箱、CI）可以注入凭据，无需扫码或本地登录：

```bash
export MEEGLE_USER_ACCESS_TOKEN='demo-meego-access-token'
export BYTEDCLI_MEEGO_COOKIE='session=demo-session; sl_session=demo-sl; meego_csrf_token=demo-csrf; passport_web_did=demo-did; login_asset_key=demo-asset; login_tenant_key=demo-tenant'
bytedcli meego status
```

- `MEEGLE_USER_ACCESS_TOKEN` 覆盖 official CLI profile token；`BYTEDCLI_MEEGO_ACCESS_TOKEN` 仅作为兼容别名翻译到该变量。
- `BYTEDCLI_MEEGO_COOKIE` 是完整 Cookie 请求头（不含 `Cookie:` 前缀，需包含上面 6 个 cookie），覆盖 GoAPI 链路（`--no-auto-chat` 或 `--delete-role` / `--role-owner` 建单、`view preference`）；`providers.goapi.source` 会显示 `env_cookie`。
- 两个变量都只被透传：bytedcli 不签发也不刷新，过期后由受管平台重新注入；未注入时 official CLI 使用 profile 内的 refresh token 自动刷新。
- 示例值一律用 `demo-*` / `example.*` 这类占位值，不要把真实 token、cookie、空间名写进脚本、日志或文档。

## official proxy 命令

下列领域的常规业务命令优先加载官方 Skill，不在本文件重复参数与 SOP：

- project、mywork/todo、workhour/schedule
- workitem 常规 create/get/query/update、字段/角色/类型元数据、操作记录
- workflow/state/node 常规查询、流转、更新
- view 常规 get/search/create/update
- chart、team、user search
- relation、comment list
- attachment official shortcuts 及其他由 official catalog 动态暴露的命令

调用流程：

1. 读取安装期注入的 `references/meegle/GUIDE.md`。
2. 按任务读取它指向的领域 reference/SOP；不要一次加载全部 references。
3. 先运行 `bytedcli meego status` 查看 primary/provider 状态；缺少 official provider 时运行 `bytedcli meego login`。
4. 使用 `bytedcli meego <resource> <verb> ...` 执行业务命令；路径不确定时先查看 `--help`。

命令运行时由 bytedcli 自动准备并保证版本兼容，无需手动安装。

## 人员身份解析（user_key）

Meego 人员字段最终使用 `user_key`。邮箱前缀、飞书 `open_id`、Meego `out_id` 与
`user_key` 之间没有可推导的格式关系；部分老用户的 `user_key` 恰好等于邮箱前缀，
不能据此生成其他人的值。

从飞书人员信息出发时，按以下链路解析：

1. 用飞书 `open_id` 从通讯录取得公司邮箱。
2. 把邮箱传给 `meego user search`；`--project-key` 使用目标工作项所在空间。
3. 按返回记录的完整邮箱做大小写不敏感的精确匹配，并只取该记录的 `user_key`。
4. 比较请求邮箱与返回邮箱集合，显式记录未命中的人员；接口成功不代表每个输入都已解析。

```bash
bytedcli --json meego user search \
  --project-key demo-project \
  --user-keys '["sample.user@example.com","other.user@example.com"]'
```

- 不要把邮箱 `@` 前面的字符串当作 `user_key`，也不要用姓名或邮箱代替人员字段里的
  `user_key`。数字形态的 `user_key` 仍按字符串原样传递，避免精度损失。
- 默认查询只返回在职用户。确实需要解析其他状态的用户时，用同一批输入加
  `--need-all-status` 重试；仍未返回的人员按“未开通或无法解析”处理，不要合成兜底 ID。
- 不要用 `lark_user_id` 关联飞书用户。该字段可能以超过 JavaScript 安全整数范围的数字
  返回并发生精度损失；飞书侧关联以通讯录邮箱为桥接键。
- 批量查询最多 20 人。调用方若分批查询，仍需在所有批次结束后统一核对未命中集合。
- 创建或更新人员字段返回 `ErrnoCannotFindUserInfo` 时，先检查每个提交值是否都来自
  `meego user search` 的 `user_key`，并确认请求人员没有被查询结果静默漏掉。

## bytedcli 认证与配置

```bash
bytedcli meego login
bytedcli meego status
bytedcli meego logout
bytedcli meego config --space demo-project
```

- `meego login` 检查或登录 tenant-scoped official profile；已登录时直接复用，未登录时只打开一次网页。`--force` 强制 official OAuth；`--begin/--complete` 使用 official device-code 两阶段。授权完成后必须由新的 official CLI 进程确认同一 profile 为 `authenticated:true`，否则不会报告登录成功。
- `meego status` 返回 `official/goapi` provider map。`meego logout` 退出 official profile并清理 GoAPI cache，但保留共享 Feishu Web session。
- `meego config` 保存 `--space`、`--dev-owner`、`--dev-role`；`--tenant dcar` 仅限懂车帝飞书租户。
- `meego tool list/inspect` 默认读取内置 schema；需要联网的 MCP 调用统一使用 official profile。

## 快捷建单

```bash
bytedcli meego create --space demo-project --title "登录优化"
bytedcli meego story --space demo-project --title "登录优化"
bytedcli meego workitem create --no-auto-chat \
  --project-key demo-project \
  --work-item-type story \
  --fields '[{"field_key":"name","field_value":"登录优化"},{"field_key":"template","field_value":100000}]' \
  --delete-role Server \
  --role-owner 'FE:sample.user'
bytedcli meego workitem create \
  --project-key demo-project \
  --work-item-type story \
  --fields '[{"field_key":"name","field_value":"登录优化"},{"field_key":"template","field_value":100000}]' \
  --delete-role Android
```

- `meego create` 使用极简模板快速创建需求，支持 `--description`、`--dev-owner`、`--dev-role`、`--template-id`。
- `meego story` 先按标题查找相似需求，未找到时给出创建提示。
- GoAPI 建单的 `--fields` 支持字符串 `description`，bytedcli 自动转为网页富文本对象，按纯文本保留换行；需要格式时传原生富文本对象。多行字符串在 JSON 中使用 `\n`，不要提前把数组、布尔值或富文本对象 stringify。
- `meego workitem create --no-auto-chat` 走网页同款 GoAPI 建单且不自动拉群；先执行 `bytedcli auth login --session --feishu`。创建时可重复传 `--delete-role <role>` 原子删除模板角色，并用 `--role-owner '<role>:<user-key[,user-key]>'` 设置负责人；role 支持短 key、完整 role key 或角色名。CLI 创建后自动回读所传角色策略，不一致时返回已创建工作项 URL 供检查与清理。
- 不带 `--no-auto-chat`、但传了 `--delete-role` / `--role-owner` 时，同样走网页同款 GoAPI 建单（MCP `create_workitem` 不支持建单时改角色），并**保留自动拉群**（`group_type=auto`）。适合单端需求在建单时删掉另一端的角色及其节点（如 `--delete-role Android`），同时照常拉「需求同步群」。同样需要 `auth login --session --feishu`，不支持 `--dry-run` / `--set` / `--params` / `--select` / `--envelope` / `--format ndjson`。

## 评论

阅读用户给出的工作项链接时，完整检查评论：

```bash
bytedcli meego comment list --url "https://meego.larkoffice.com/demo-project/story/detail/123456"
```

## 分页与子任务参数

```bash
bytedcli meego todo list --action todo --page 2
bytedcli meego comment list --project-key demo-project --work-item-id 123456 --page 2
bytedcli meego node subtask update --project-key demo-project --work-item-id 123456 --node-id waiting_for_development --action update --task-id 789012 --fields '[{"field_key":"name","field_value":"更新后的子任务"}]'
```

- generated Meego 列表命令统一用 `--page <n>`；bytedcli 会转换为 official Meegle 的分页参数。
- `node subtask update` 的 `--work-item-id` 始终传父工作项 ID。`update`、`confirm`、`rollback` 还必须传子任务 `--task-id`；`create` 不传 `--task-id`。

## GoAPI 修改命令

以下命令先执行 `bytedcli auth login --session --feishu`：

```bash
bytedcli meego workitem delete --url "https://meego.larkoffice.com/demo-project/story/detail/123456"
bytedcli meego workitem join-chat --url "https://meego.larkoffice.com/demo-project/story/detail/123456"
bytedcli meego node subtask delete --project-key demo-project --work-item-id 123456 --task-id 789012
```

- `workitem delete` 支持 `--url`，或 `--project-key` + `--work-item-id` + `--type`。
- `workitem join-chat` 把当前用户加入工作项需求群，支持 URL 或显式项目/工作项参数。
- `node subtask delete` 的 `--task-id` 支持单个或逗号分隔。

## View preference

```bash
bytedcli meego view preference apply \
  --project-key demo-project \
  --target-url "https://meego.larkoffice.com/demo-project/issueView/view-id" \
  --group-fields priority,template,work_item_status \
  --sorts priority:ASC \
  --dry-run

bytedcli meego view preference apply-template \
  --project-key demo-project \
  --template-url "https://meego.larkoffice.com/demo-project/issueView/template-id" \
  --target-url "https://meego.larkoffice.com/demo-project/issueView/view-id" \
  --filter merge --group replace --sort replace --dry-run
```

这两条命令走 Meego Web GoAPI。先 dry-run 检查 diff；多排序写成 `priority:ASC,updated_at:DESC`。

## 扩展 MCP 命令

这些命令由 bytedcli 保留参数和输出兼容层，但底层 MCP 调用统一通过 official `meegle` binary：

- `meego view list-multi-project-workitems`：自动遍历全景视图分页。
- `meego deliverable list`：查询交付物的根工作项和来源工作项。
- `meego resource create` / `resource meta-fields`：创建资源实例、查询资源库字段和角色。
- `meego wbs draft list/create/update/publish/reset/progress`
- `meego wbs instance list`
- `meego wbs element-template list`

WBS `draft update` 的 operation 结构复杂，先运行：

```bash
bytedcli meego tool inspect edit_wbs_draft
```

全量发布草稿前必须确认：“本人及协同者的全部编辑内容均会被发布，请确认是否全量发布？”部分发布无需该确认。

## 其他 bytedcli 自有命令

- `meego workitem batch-get`：最多 200 个唯一 ID、固定 3 并发；支持 `--work-item-ids`、`--ids-file`、`--format ndjson`、`--envelope`。
- `meego comment create`：保留 bytedcli Markdown sanitize；`--raw` 只用于复现服务端限制。
- `meego user me`：固定查询 `current_login_user()`。
- `meego url decode --url <url>`：纯本地解析 80+ Meego URL 路径，不需要任何登录态。
- `meego tool list/inspect`：读取内置 schema；`--refresh` 同步 official command catalog 后返回内置 schema。
- `meego tool sync`：同步 official command catalog，不读取或保存第二套 OAuth 凭据。
- `meego tool refresh`：刷新 official CLI 命令目录 cache。

## Markdown 多行换行（必读）

`meego comment create --content`、`meego create --description` 这类接收 Markdown 的参数必须用 `$'...'` 写换行，双引号里的 `\n` 只会被当成两个字面字符，富文本侧会渲染成单行：

```bash
bytedcli meego comment create \
  --project-key demo-project \
  --work-item-id 123456 \
  --content $'第一行\n第二行'
```

反例（会渲染成单行）：`--content "第一行\n第二行"`。示例里的项目、URL、token 一律用 `demo-*` / `example.*` 占位值。

## 输出兼容

- 全局 JSON 模式写作 `bytedcli --json meego ...`。
- generated 命令支持 `--select <paths>`、`--params/-P <json-or-@file>`、可重复 `--set key=value`。
- `--envelope` 暴露 logid；`--format ndjson` 按主数组逐行输出。
- `workitem batch-get` 的 ndjson 按输入顺序每个工作项一行，不输出 summary 行。
- `--no-auto-chat` 或 `--delete-role` / `--role-owner` 建单走 GoAPI 特化路径，不支持 generated 命令的 `--select`、`--params`、`--set`、`--envelope` 或 ndjson。

## 排障

- official CLI 提示未认证：运行 `bytedcli meego login`；不要再执行第二个登录命令。
- official profile 状态异常：运行 `meegle auth status --format json --profile bytedcli` 诊断，它与 bytedcli 使用同一凭据。
- GoAPI 提示缺少 session：运行 `bytedcli auth login --session --feishu`。
- 从 GitHub 安装 official Skill 遇到 API 限流：可设置 `GITHUB_TOKEN` 后重试；token 只发送给 `api.github.com`，不会透传到下载 URL。
- 参数和命令路径不确定：先执行具体层级的 `--help`，不要从 URL 或上游命令名猜 bytedcli 别名。
