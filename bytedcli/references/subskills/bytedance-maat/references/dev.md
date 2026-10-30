# 联调环境

## 查询与定位

```bash
bytedcli --site cn --json maat dev list --project demo-web --search sample --page 1 --page-size 20
bytedcli --site cn --json maat dev list --project demo-web --search sample-dev --exact --only-watch
bytedcli --site cn --json maat dev get --project demo-web --name sample-dev
bytedcli --site cn --json maat dev config get --project demo-web
bytedcli --site cn --json maat dev proxy list --project demo-web --search demo --page 1 --page-size 20
bytedcli --site cn --json maat dev logs --project demo-web --name sample-dev --page 1 --page-size 20
bytedcli --site i18n --json maat dev list --project demo-web --region Singapore-Central
bytedcli --site i18n --json maat dev get --project demo-web --region Singapore-Central --name sample-dev
```

`list` 支持 `--search`、`--exact`、`--only-watch`（当前用户订阅）和 `--only-create`（当前用户创建），默认不筛掉其他可见环境。分页返回真实 `total`、`page`、`page_size`、`current_count`、`has_more`；列举全部时翻到 `has_more=false`。`get/update/build/logs` 必须精确唯一名称，不会选第一条、近似名称或另一区域。

`config get` 是**项目级公共设置只读**，无需区域参数；未初始化返回 `initialized:false`，不调用初始化。其 `scmList` 才是联调仓库配置，可能与项目生产仓库完全不同。`proxy list` 列出可供规则引用的共享 API 代理目标；不修改这些目标本身。

查询采用字段白名单。环境的模板内容、未知字段不会输出；API 代理自定义指令的 `value` 脱敏；日志只返回状态、ID 和时间，省略可能含敏感信息的自由文本。不能把脱敏结果原样当作可写配置。

历史环境可能只有顶层 `resourceType/branchName/scmVersion`，缺少 `scmList`。查询会保留这些顶层资源信息，并返回空 `scmList`，不猜测仓库 ID；此类环境可以查看，但修改和构建会停止，需先在控制台核对联调仓库配置。

## 修改单个环境

```bash
# 常用字段：只有被指定的字段改变；省略的字段保持不变
bytedcli --site cn --json maat dev update --project demo-web --name sample-dev --branch feature/demo
# 多 SCM 时明确目标 ID，不按仓库位置猜测
bytedcli --site cn --json maat dev update --project demo-web --name sample-dev --branch feature/demo --scm-id sample-scm
bytedcli --site cn --json maat dev update --project demo-web --name sample-dev --description 'sample description' --watch-users demo-alice,demo-bob
# 显式清空描述和订阅人
bytedcli --site cn --json maat dev update --project demo-web --name sample-dev --description '' --watch-users ''
# 复杂字段用严格 JSON patch，不与上述字段选项混用
bytedcli --site cn --json maat dev update --project demo-web --name sample-dev --patch-file sample-patch.json
```

`--patch-file` 最多 256 KiB，只接受以下字段，拒绝未知字段、身份/项目/区域/名称/状态修改：

| 字段                                  | 语义                                                                        |
| ------------------------------------- | --------------------------------------------------------------------------- |
| `desc`                                | 替换描述，空字符串清空                                                      |
| `watchUserList`                       | 完整替换订阅用户名列表，`[]` 清空，不是管理员授权                           |
| `scmList`                             | 按 `scmId` 合并指定仓库的修改；不增删仓库，不重排其他仓库                   |
| `scmList[].resourceType`              | `branch` 或 `scm`；分支模式必须有 `branchName`，固定版本必须有 `scmVersion` |
| `scmList[].branchName`                | 精确分支；使用该联调 SCM 查询并绑定最新提交                                 |
| `scmList[].scmVersion`                | 精确成功构建版本，校验属于该联调 SCM                                        |
| `scmList[].path`                      | `/` 开头的静态资源路径                                                      |
| `scmList[].redirect` / `redirectList` | 跳转开关和完整规则列表；每条 `{regex,target}`，target 为 HTTP(S) URL        |
| `apiProxyList`                        | **完整替换**代理规则列表，遗漏的规则会被移除；`[]` 明确清空                 |

代理规则字段为 `_id?`、`pathname`、`pathMatchType`（`prefix`/`regexp`）、`apiId`、`customDirectiveList?`。保留现有规则时使用 `get` 返回的 `_id`，未指定的规则字段保留；没有 `_id` 表示新规则。每个 `apiId` 必须在当前项目的代理目标列表中验证。自定义指令是完整替换数组，每条 `{name,value}`；name 支持 `add_header`、`proxy_set_header`、`return`、`rewrite`，value 为不含换行、分号或大括号的单行值。指令密值只参与指纹，不打印；不要从脱敏输出复制 `[REDACTED]` 作为配置。

```json
{
  "desc": "sample environment",
  "watchUserList": ["demo-alice"],
  "scmList": [
    { "scmId": "sample-scm", "resourceType": "branch", "branchName": "feature/demo", "path": "/" }
  ]
}
```

预览展示站点、区域、项目、环境 ID、执行账号、before/after、分支提交、冻结提示和 fingerprint。修改代理规则时还展示所引用代理目标并绑定其配置。**单独等待用户确认**后原参数加 `--yes --confirm-plan <fingerprint>`；提交前重读环境及公共配置。指纹变化必须新预览、新确认。未指定字段和未知字段在内部快照中保留。

`verified` 是配置回读一致；`verified_after_error` 是写请求报错但回读匹配，不能归因于本次写成功。更新可能触发平台自动构建/部署或通知，但 CLI 不额外发送构建、网关/文件部署请求。不证明真实流量已命中。

## 触发构建与恢复

```bash
# 默认只读预览，读取该环境当前配置，不顺带修改分支
bytedcli --site cn --json maat dev build --project demo-web --name sample-dev
# 仅在用户确认本次预览后，带相同指纹提交一次
bytedcli --site cn --json maat dev build --project demo-web --name sample-dev --yes --confirm-plan <fingerprint>
# 之后用只读状态和历史查询，不重复触发
bytedcli --site cn --json maat dev get --project demo-web --name sample-dev
bytedcli --site cn --json maat dev logs --project demo-web --name sample-dev
```

构建操作面向环境，不是单个 SCM。只有所有 SCM 都是分支模式才允许触发，会逐仓库验证分支及最新 SHA。修改分支和触发构建是两个独立确认的动作；不把更新确认复用于构建。

构建使用控制台 `/api/devEnv/triggleBuild`（服务端原拼写），body 只有 `{_id}`，没有已验证的“仅构建、不部署”开关。按可能重建并部署该联调环境来告知和确认，不自动调用独立的部署 API，也不会改生产/灰度配置。

`accepted` 只证明触发请求被受理。没有已验证的稳定 job ID、请求幂等键或本次构建关联字段，因此不提供会误认旧状态的 `--wait`。`dev get/logs` 返回当前状态与环境历史，不能据此单独认定某次触发成功或准确 SHA 已部署。需要精确验收时，进一步核对控制台日志与 SCM 产物，再确认访问地址进行运行验证。

`pre_build/building/deploying_file/deploying_static` 时禁止再次修改或触发；未知状态停止。`MAAT_DEV_BUILD_UNKNOWN` / `MAAT_DEV_UPDATE_UNKNOWN` 后只能查现状和日志，不自动重试。客户端双重检查不是服务端 CAS；避免多人同时改环境或推分支。

## 范围与证据

支持 CN/i18n 普通前端联调环境；i18n 环境操作传准确区域。写入要求未封禁的项目管理员或 Maat 管理员，服务端权限仍然生效。拒绝锁定项目、Kura/Goofy 特殊形态，以及与公共配置不一致的 SCM 列表。项目级域名/SSO/页面路由、共享代理目标只读；不创建、删除、复制、初始化环境，不修改子项目/Kura 模板配置。

契约来自官方前端联调页面的列表、编辑表单、构建操作和日志面板，并经 CN/i18n 只读请求验证。写流程有离线测试；没有为开发验收而修改真实联调环境或触发真实联调构建。
