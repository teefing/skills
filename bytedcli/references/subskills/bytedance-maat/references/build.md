# 分支构建与结果恢复

## 本次构建授权

用户明确要求构建，且项目、站点、区域和准确分支已由本次请求或当前任务上下文唯一确定，即授权该次 `onlyBuild`。先在 Agent 内完成只读预览和核对，再用真实指纹提交，不额外询问“是否开始构建”。描述默认取分支提交信息、环境变量保持原值、随机 request-id 等机械参数无需逐项问用户；用户指定值必须保留。

仅查询、讨论、要求先预览或等确认时不提交。必要目标不明确或有冲突时只问缺失项；预览与授权不符、出现未授权风险或冻结异常时先说明问题再确认。用户有更严格的确认要求时遵从。不把此授权扩展到 `dev build`、管理员变更或灰度发布。

“构建并灰度”先完成构建，核对产物版本及提交哈希，再把版本、流量、条件和排序合并进同一份灰度预览，只在发布前等待一次上线确认。构建请求本身不代替这次确认；仅构建则在结果验证后结束。

## 调用

`branch list` 是服务端搜索，可能截断且没有可靠总数；`branch get` 要求精确分支出现并返回 `{name,hash,message}`，不接受默认分支替代。`build list` 查询所有状态，与仅成功版本的 `version list` 不同，返回 `total/page/page_size/has_more`。`build get` 精确匹配版本，`succeeded` 只在状态为 `build_ok` 时为 true。

```bash
# 为每次新构建生成独立 UUID；示例 ID 不是可以复用的生产值
bytedcli --site cn --json maat build create --project demo-web --branch feature/demo --request-id sample-build-001
# 本次明确构建请求已授权且预览符合范围后，用同一 request-id 和真实指纹提交一次并等待
bytedcli --site cn --json maat build create --project demo-web --branch feature/demo --request-id sample-build-001 --yes --confirm-plan <fingerprint> --wait
# i18n 显式区域；其他参数相同
bytedcli --site i18n --json maat build create --project demo-web --region Singapore-Central --branch feature/demo --request-id sample-build-002
# 已受理或未知结果只能查询恢复，commit 使用原预览的完整哈希
bytedcli --site cn --json maat build wait --project demo-web --branch feature/demo --request-id sample-build-001 --commit <approved-40-character-sha> --timeout-seconds 1200 --poll-seconds 15
```

`--description` 可覆盖自动描述；命令追加 `[bytedcli:<request-id>]` 追踪标识，不覆盖用户内容。多行描述使用 `$'第一行\n第二行'`，不要使用普通双引号里的字面量 `\n`。仅保留项目默认 SCM 变量，不提供临时覆盖参数；预览显示键，不输出变量值、原始项目凭据或 SCM 产物链接。

## 安全与结果

- `build create` 默认预览，不产生构建或发布。`--yes` 必须搭配本次预览指纹；指纹绑定站点、区域、项目、身份、分支提交、描述、变量、冻结信息。
- `onlineType` 固定为 `onlyBuild`，`routerList` 只有一个 SCM，`publishType:"branch"`，`routers:[]`。仅构建模式不选择发布路由；不会更新灰度或生产流量。
- 提交前查询已有追踪标识并再核对快照。标识不是服务端幂等键，不能保证并发提交原子去重；同一任务只保留一个执行者，不并行提交相同 request-id。
- 每次写请求最多一次。网络错误、超时、401、非 JSON 或业务失败均保守返回 `MAAT_BUILD_UNKNOWN`，包含安全恢复参数；不得自动重试写入。读取记录也不能单独证明某个超时写请求成功。
- 等待按 SCM 仓库、标识、准确分支及原预览的提交哈希验证，按准确版本返回结果。只接受 `build_ok` 为成功；`build_failed/upload_failed` 失败，`prepare/uploading/building` 继续等待，其他状态停止人工核查。
- 默认等待 1200 秒，最长 3600 秒，每 15 秒查询（允许 5-60 秒）。每轮最多读 10 页、每页 100 条，扫描无法覆盖或出现多个匹配即停止。单次网络请求耗时可能超过剩余等待窗口；超时不取消远端构建。
- 服务端接收分支而不是锁定 SHA，可能在提交后被推送新提交；客户端检查降低但无法消除这一竞争。构建产物哈希与批准 SHA 不同则拒绝衔接发布，不能把新提交自动视为批准。
- `MAAT_BUILD_EXISTS` 使用原记录查询；`MAAT_PLAN_STALE` 说明输入漂移、重新预览并取得新确认，不自动换指纹；`MAAT_BUILD_TIMEOUT` 使用相同参数继续只读等待，无需重复确认查询，也不新建 request-id 再提交；`MAAT_BUILD_AMBIGUOUS` / `MAAT_TARGET_MISMATCH` 人工核对，不自行选一个版本。

接口的读取形态已做真实只读联调；构建写入及异常路径的离线测试不代表真实构建成功验收。执行真实构建必须有该次明确授权；符合本节条件的构建请求即可，不必为同一意图额外询问一次。
