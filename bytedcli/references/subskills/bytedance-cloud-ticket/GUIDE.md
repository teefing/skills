---
name: bytedance-cloud-ticket
description: "Operate Cloud Ticket workflow tickets: read full detail or the base record, query pending approvals and created/all tickets with filters/time ranges, and approve workflow transitions."
---

# Cloud Ticket（bytedcli）

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

## When to use

- 查询待我审批的工单
- 查询我发起的工单
- 查询全部工单并按条件过滤（ID/关键字/状态/申请人/时间范围）
- 读取工单完整详情或独立读取基础记录
- 对工单执行“通过/流转”操作（approve）

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`

## Quick start

```bash
# 站点/环境列表（best-effort）
bytedcli cloud-ticket list-sites

# 待我审批（默认最近 3 个月）
bytedcli cloud-ticket list-pending-approval

# 我发起的
bytedcli cloud-ticket list-created

# 全部
bytedcli cloud-ticket list-all

# 完整详情（默认包含流程、审批信息和日志）
bytedcli cloud-ticket get --ticket-id demo-ticket

# 仅基础记录，不请求流程、审批信息和日志
bytedcli --json cloud-ticket get --ticket-id demo-ticket --record-only

# 通过工单（自动选择 next）
bytedcli cloud-ticket approve --ticket-id demo-ticket

# 通过链式审批（同一审批人可继续时自动跟进）
# 说明：一次 approve 后如果你仍是下一节点的可审批人，可再次执行 approve。
# 判断方法：先执行 cloud-ticket list-all（或 list-pending-approval）确认工单仍在待办，
# 且下一步可执行操作可见 next；再重复执行 cloud-ticket approve。
# 连续通过时无需复杂脚本，按人工/脚本循环“approve + 查询状态”即可。
```

## Notes

- 默认时间范围为最近 3 个月，可用 `--start/--end/--range` 覆盖
- `get` 默认请求 record、pipeline、approval info 和 logs；`--pipeline`、`--approval-info`、`--logs` 保持完整详情行为。`--record-only` 仅请求 record，不能与这三个开关组合；JSON 中未请求的 `pipeline`、`approval_info`、`logs` 为 `null`。`--logs-page-size` 仅在读取日志时生效。已请求的接口失败仍使命令失败，不返回部分成功。
- 使用全局 `--site` 选择站点（`cn|boe|boei18n|i18n|i18n-row`）；`boei18n` 对应 `cloud-boei18n.bytedance.net`（BOE 国际测试，需 ByteDance SSO），`i18n-row` 对应 `cloud.tiktok-row.net`（TikTok ROW，需先以 `BYTEDCLI_CLOUD_SITE=i18n-tt` 登录 TikTok SSO）。Per-service `--cloud-ticket-site` is a hidden alias for backward compatibility.
- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json cloud-ticket get ...`）

## References

- `references/cloud_ticket.md`
