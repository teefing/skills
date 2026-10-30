# TCE 资源恢复、删除工单回滚与失败诊断

## 恢复已回收的 TCE 服务

`env service recover-tce` 恢复 `resource_status=recycled` 的资源，沿用现有版本。它不创建新服务，也不提交升级部署。`using` 资源即使实例数为零，也不适用此命令；先检查服务和集群现状。

```bash
# 默认只读预览：精确匹配 PSM，展示资源 ID、原版本和恢复请求
bytedcli env service recover-tce \
  --env ppe_demo --psm example.service.api --standard-env online_cn

# 确认目标及影响后提交；--days 是恢复后的租期天数，默认 14，须为正整数
bytedcli env service recover-tce \
  --env ppe_demo --psm example.service.api --standard-env online_cn --days 14 --yes

# BOE 默认 env-type=boe_feature；恢复 BOE Base 资源时显式指定 boe_base
bytedcli env service recover-tce \
  --env boe_demo --psm example.service.api --standard-env boe --env-type boe_base

# 提交后继续查询服务和工单
bytedcli env service list --env ppe_demo --standard-env online_cn --search example.service.api
bytedcli env ticket list --env ppe_demo --psm example.service.api --standard-env online_cn
bytedcli env ticket get --ticket-id 1234567890123456789 --standard-env online_cn
```

- `--standard-env` 必填，支持 `online_cn`、`online_i18n`、`online_i18nbd`、`online_usttp`、`online_euttp`、`boe`；在线控制面使用 `env-type=ppe`。
- 不带 `--yes` 或带 `--dry-run` 时只预览；`--yes` 与 `--dry-run` 不能同时使用。
- 模糊搜索结果须精确匹配 PSM 与 TCE 类型；多个匹配、资源身份不一致或搜索超过 100 页时拒绝提交。
- 提交后读回资源与第一页工单。JSON 的 `phase=submitted` 表示请求已接受；`resource_after` 是即时资源状态；`verification=pending` 表示尚未验证实例恢复结果。
- 恢复接口不返回工单 ID。`ticket_candidates` 是前后查询新增的候选记录，`ticket_association=unconfirmed`，不能直接认定为本次操作的工单。工单可能延迟出现；没有即时候选工单也不能据此认定完成。按返回的 `follow_up` 继续核实。
- `resource_status=using` 只说明资源状态已改变；实例可能仍因配额等原因拉起失败。确认对应工单终态并检查实例后，再判断恢复是否完成或是否需要继续升级。

## 恢复删除工单涉及的资源

`env ticket rollback` 绑定原始删除工单组 ID，通过平台回滚接口创建恢复工单。它用于恢复删除操作；不是发布版本回退入口。平台判断工单是否支持回滚。

```bash
# 展示原始工单、受影响的资源与恢复来源，不提交
bytedcli env ticket rollback --ticket-id 1234567890123456789 --standard-env online_cn

# 确认原始删除工单后提交，输出新工单 ID 并即时读回新工单
bytedcli env ticket rollback --ticket-id 1234567890123456789 --standard-env online_cn --yes

# 使用响应中的 new_ticket_id 检查实际执行状态
bytedcli env ticket get --ticket-id 2234567890123456789 --standard-env online_cn
```

工单 ID 始终按字符串传递，保留 64 位精度。默认预览，`--dry-run` 显式预览，`--yes` 提交；两者互斥。成功响应中的 `new_ticket_id` 代表恢复工单已创建，`ticket` 是即时读回的状态，不表示资源已恢复完成。

恢复或回滚请求失败时检查结构化错误的 `submission`、目标、请求与 `follow_up`：`unknown` 表示提交结果不确定，`accepted` 表示请求已被接受但读回失败。回滚读回失败时保留 `new_ticket_id`。先查询当前状态，不要盲目重复提交；写请求不自动重试。

## 诊断失败工单

```bash
# query 是工单 URL 或失败描述；可直接使用 ticket get/list 输出中的工单信息
bytedcli env ticket diagnose --description 'demo ENV deletion ticket failed: quota unavailable'

# 默认最多等待 180 秒，固定每 5 秒查询；可缩短等待时间（1–180 秒）
bytedcli env ticket diagnose --description 'demo ENV deployment ticket failed' --timeout 30

# 超时或查询失败后，使用错误中的 job_id 继续查同一个诊断任务
bytedcli env ticket diagnose --job-id demo-job --timeout 180
```

`--description` 与 `--job-id` 必须且只能提供一个。诊断不改变环境资源，恢复查询不会再次创建诊断任务。成功时文本输出诊断结论（保留换行，转义终端控制字符），JSON 在 `report` 中保留原始内容、文件:行号、根因、解决方案与链接；诊断失败、中断、超时或成功却缺报告均返回错误，并保留已知 job ID 与重查命令。

ENV 普通资源与工单操作使用 Bits ENV 网关；工单诊断使用独立的 `boe-platform.bytedance.net/resources/api/v1` 网关，两者都使用当前全局站点的 ByteCloud JWT。诊断任务的成功仅表示报告已生成，不表示工单故障已修复。
