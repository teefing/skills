# BITS 发布单 FaaS 上线 Playbook（demo-faas 实战沉淀 2026-08-04）

> 本文档来自 example.faas.demo-service 空 post 重试修复（MR #50）上线实战，覆盖 BITS 发布单跑 FaaS 升级流水线（`create_faas_upgrade_ticket`）的完整链路：从解锁 can-run 到 FaaS 工单模板变量与 run 入参、人工卡点放行、发布后日志验证。**核心结论：FaaS 发布流水线的 `faas_deploy_config` 系统变量取自 run 请求里的 `strategy.faasStrategy`。`bits release pipeline run` 在发布阶段会自动附上部署策略，先 `--dry-run` 核对集群再 `--yes`；非发布阶段的 FaaS 泳道部署 CLI 暂不支持，走页面。**

本文目录：
0. 发布链路总览
1. 解锁 can-run 固定顺序
2. FaaS 升级工单模板变量与 run 入参（最高频坑）
3. 发布单维度门禁与 QCSS 处理
4. 125536 阶段流转失败
5. 本地直调 BITS API
6. 发布后验证
7. 飞书战报/直播卡

## 0. 发布链路总览（开发任务 → 发布单）

FaaS 服务（如 demo-faas）上线**必须走 BITS 开发任务 → 发布单**，禁止 FaaS 平台直发。链路：

```text
dev task（MR 合入 master）→ 建发布单（r2）→ 解锁 can-run → bits release pipeline run（--dry-run 核对后 --yes）
→ 人工卡点放行 → Canary→Single DC→All DCs → stage operation → RELEASED (status=6)
```

## 1. 解锁 can-run 的固定顺序（canRun=false reason 2 时照做）

```bash
# 发布单维度推进（r2 门禁全绿 + canRun=true 后，直接走发布单，不再碰 dev pass-stage）
bytedcli bits release complete-integration --ticket-id <rtId> --operator <operator>   # status 3→4
bytedcli bits release start-integration --ticket-id <rtId> --yes                    # stageStatus 0→1
bytedcli bits release stage check --ticket-id <rtId> --stage-id <stageId> --operator <operator>
# ★ 真正的解锁键：release 维度 QCSS 人工项（先 dry-run 解析 report/check id）
bytedcli bytestable qcss manual pass --space-id <space_id> --dev-id <rtId> --stage <stageId> \
  --check-name "确认本次上线依赖的TCC配置完成" --remark "<TCC 证据或无变更说明>" --dry-run
# 去掉 --dry-run 正式通过
bytedcli bits release pipeline can-run --ticket-id <rtId> --stage-id <stageId>      # → true
```

- `--dev-id` 在 release 维度传**发布单 id**（不是 dev task id），`--stage` 传**数字 stageId**（`bits release stages` 拿）。
- `qcss manual pass` 返回 13001「报告完结态不可改」= 解析到旧报告，以 `final-result` 为准。

## 2. FaaS 升级工单模板变量与 run 入参（最高频踩坑，务必先读）

**症状**：发布流水线「创建FaaS升级工单」节点失败，job 详情报：

```text
faasmodel.CreateFAASTicketStreamCtx.ClusterInfo: []*v2.ReleaseClusters:
decode slice: expect [ or n, but found ", error found in #10 byte of ...|cluster_info":"{{sys.release_ticket.faas_deploy_config['cluster_i|...
```

**根因**：流水线模板 `create_faas_upgrade_ticket` 的 inputs 引用 `{{sys.release_ticket.faas_deploy_config['cluster_info']}}` / `['rolling_percentage']`，取值来自 `cd/pipeline/run` 请求 `params.selectedProjects[].strategy.faasStrategy`。run 请求不带这个字段时模板变量不解析。

**做法：用 CLI 跑，先 dry-run 核对**

```bash
bytedcli bits release pipeline run --ticket-id <rtId> --stage-id <stageId> --username <operator> \
  --psm <psm> --use-change-items --dry-run
# 核对 payload.params.selectedProjects[].strategy.faasStrategy 后真实运行
bytedcli bits release pipeline run --ticket-id <rtId> --stage-id <stageId> --username <operator> \
  --psm <psm> --use-change-items --yes
```

CLI 与发布确认页走同一序列：`run_vars` → 权限预检 → `run_pre_check` → `pre_set_batch_stage_pipeline_run_key` → `run`，两次请求的 `params` 相同。以下任一条件成立时，CLI 读取 `GET .../change_item/deploy_strategy`，把完整部署策略作为 FaaS 项目的 `strategy` 发送：

- 阶段 `nodeType=2`（发布阶段），读取 `bits release stages` 同源的阶段信息；
- 显式传 `--attach-deploy-strategy`；
- 传了 `--psm`（包括 `all`）。

`strategy.deployResource` 优先取 `change_item/deploy_strategy` 返回的非空 `deployResource`；该对象为空时才整体回退到变更项的 `artifact`，再回退到变更项的 `deployResource`。`scmArtifacts[].targetCommitHash` 随所选对象原样透传，不会逐字段用变更项提交 SHA 回填。提交 SHA 为空时先核对变更项与 `change-item deploy-strategy get` 的结果，必要时用 `change-item deploy-strategy update` 修正，再重新 dry-run 核对最终 `strategy.deployResource.scmArtifacts[].targetCommitHash`。`grayPercentage` / `rollingPercentage` 未设置时默认 10。

| 报错 | 含义与处理 |
|---|---|
| `BITS_RELEASE_FAAS_STRATEGY_INVALID` | 部署策略没有集群或没有选中集群。`change-item deploy-strategy get` 核对，需要时 `deploy-strategy update` 保存集群选择后重跑 |
| `BITS_RELEASE_STAGE_TYPE_UNKNOWN` | 读不到阶段类型，且没显式要求附策略；CLI 拒绝静默不带策略运行。`bits release stages` 确认阶段，发布阶段加 `--attach-deploy-strategy` 重跑 |

**页面与 CLI 的 run 入参对照**（发布单 1247297990146，FaaS 项目，2026-10 实测）：

| 阶段 | 页面提交 | CLI 发送 |
|---|---|---|
| 发布阶段 | `strategy` = 完整部署策略记录（`faasStrategy`、`deployResource`、`upgradeMode`、`reviewers` 等），`envProjectConfigs: []`，不带 `env` | 同一份部署策略记录（另带 `scmMergeBuildInfo`），`envProjectConfigs: []`，`env: null` |
| 非发布阶段（测试/预发泳道） | `strategy: null`；`env` 带 BOE/PPE 泳道；`envProjectConfigs` 每条泳道一个 `faasProjectConfig`；顶层 `envProjectData`（`RefreshNodeAndProjectConfigs`） | `strategy: null`；`env: null`；`envProjectConfigs: []`；不带 `envProjectData` |

非发布阶段的泳道配置 CLI 目前组不出来，FaaS 泳道部署请在发布单详情页「Run deployment pipeline」运行。

要点：
- `pre_set_batch_stage_pipeline_run_key` 的 `stageId` 是**数字**，`run`/`run_vars`/`run_pre_check` 是**字符串**（CLI 已处理）。
- 不要在非发布阶段为了"带上策略"而传 `--psm` / `--attach-deploy-strategy`：页面在该阶段发送 `strategy: null`。

## 3. 发布单维度门禁与 QCSS 处理

- 发布阶段门禁是**发布单维度**：优先用 `bits release gatekeeper list --ticket-id <rtId> --stage-id <数字stageId>`（按阶段 nodeType 自动识别发布 / 自定义 / 归档维度；不传 `--stage-id` 时自动取进行中的阶段，没有进行中的则取第一个待开始阶段，全部完成会报错并提示显式指定）；需要手工指定维度时用 `bits develop gatekeeper list --release-ticket-id <rtId> --stage <数字stageId> --stage-kind release|self-defined|archive`。
- 「质量门禁」QCSS 项 skippable=true，可直接 `gatekeeper skip --check-id <id> --reason "..."`（会生成 BPM 审批单，approver 收到后通过即转 Success）。
- 项目流水线人工卡点（`user_confirm`，审批人=操作者自己）：放行

```bash
bytedcli bits job-run continue-release --job-run-id <jobRunId> --pipeline-run-id <runId>
```

## 4. 125536 阶段流转失败（dev 指针钉已取消发布单）

**症状**：`bits develop publish` / `pass-stage` 报 `125536 阶段流转失败: 请重试`。125536 可能来自关联异常或门禁阻塞，不能直接等同于 QCSS 人工项待处理。命令会保留原始错误并附加只读诊断；确认旧关联单已取消时，`details.reason_code` 为 `release_ticket_association_invalid`，不建议通过 QCSS 人工项。

**根因**：dev 任务 `releaseTicketAssociatedOneDevTask` 指针钉在**已取消的旧发布单**（r1），pass-stage 按关联单解析 QCSS 报告 → 报告不存在 → 125536。**QCSS 全绿也照样报**（它查的不是当前单）。

**解法**：先用 `bits release get` / `bits release stages` 核对目标有效发布单，再按发布单 ID + 数字 stageId 读取该阶段门禁。**不要**试图解绑 dev（`bind-release` 在合入阶段报 125006「合入阶段无法解绑」）。确认有效目标单门禁全绿 + canRun=true 后，**走发布单维度**（§1 的 complete-integration → start-integration → stage check → pipeline run）。诊断为 `diagnosis_unknown` 时先补齐查询证据，不审批不存在的人工项，也不反复重试 dev pass-stage。

## 5. 本地直调 BITS API（免浏览器）

> 说明：以下端点可直接以 HTTP 方式直调（如 `curl` / 脚本）；无需浏览器。鉴权头见上。

鉴权：`X-Jwt-Token`（`bytedcli auth get-bytecloud-jwt-token`）+ `X-Accept-Format: bytecycle/v1`，无需浏览器/登录态。

高频端点（反编译前端 JS 全量入库 1398 端点，缓存 `/tmp/bits-api-catalog.json`）：

| 用途 | 端点 |
|---|---|
| can-run 预检 | `GET /api/v1/cd/release_ticket/<rt>/stage/<sid>/pipeline_runnable` |
| 阶段流水线概览 | `GET /api/v1/cd/release_ticket/<rt>/stage/<sid>/pipeline` |
| 流水线 run 列表/详情 | `GET /api/v1/pipelines/runs?pipelineId=<pid>&pageSize=5&pageNum=1` |
| job 操作枚举 | `POST /api/v1/p/pipelines/group_job_run_operation/batch` body `{"pipelineRunIds":["<rid>"],"spaceId":<sid>}` |
| 阶段状态 | `GET /api/v1/cd/release_ticket/<rt>/execution/latest_status` |
| 部署策略 | `GET /api/v1/cd/release_ticket/<rt>/change_item/deploy_strategy?controlPlane=1&projectUniqueId=<psm>&projectType=2` |
| 系统变量 | `GET /api/v1/cd/release_ticket/vars?workspaceId=<ws>&releaseTicketId=<rt>&includeSysVars=true` |

## 6. 发布后验证（日志回捞 + 错误率对比）

```bash
# 修复生效验证：回捞新签名，应命中 retry_count_source=s:retry
bytedcli log search-psm-log --psm example.faas.demo-service \
  --keyword "skip article commit wake-up event" --start <RFC3339> --end <RFC3339> --output console
# 错误率对比（同一错误签名）
bytedcli log search-psm-log --psm example.faas.demo-service \
  --keyword "article commit post data is empty" --start <pre> --end <pre> --output console
```

判定标准：
- 回捞 `skip ... wake-up` 出现 `retry_count_source=s:retry` → 修复生效（EventBus header 重投计数读取成功）。
- 新实例（cold-start pod）错误率 vs 发布前基线：风暴 32/min → 稳态 ~1/min 且 ack 数远大于 retry 数 → 收敛。
- 发布后短窗口内错误含**旧实例滚动下线残留**，要按 `_podname` 过滤（`<old-pod-prefix>-*` 旧 vs `cold-start-instance-*` 新）。

## 7. 飞书战报/直播卡

- 直播卡：`.agents/skills/release-lark-card`（发布开始发卡 Pin → 原地刷新 → 成功绿卡自动取消 Pin）。
- 战报卡：schema 2.0 green template，column_set 大数字 + stage_table 对比行；table rows 必须 5 字段 dict（stage/status/start/time/note），数组行会 200914。
