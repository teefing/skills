# Kani Quick Start

在以下场景读取本文件：

- 你已经确定要用 Kani skill，但想先看一组最短可用命令
- 你想快速区分 `workflow create` / `workflow get` / `workflow list` / `workflow approve|reject|cancel` 的入口
- 你需要一份面向 Agent 的常用命令速查表

## 常用命令

```bash
# 查看帮助
bytedcli kani --help

# 检索 Kani 知识库
bytedcli kani knowledge search --query "如何申请 Kani 资源权限"

# Kani OpenAPI 第一步：先找当前 identity 能访问的 namespace
bytedcli kani openapi identity namespace list --identity-key alice

# 列出 workflow（默认查当前/running）
bytedcli kani openapi workflow list

# 创建 workflow（`create` 走 `--body-file` 模式）
bytedcli kani openapi workflow create --body-file ./workflow-create-resource.json

# 查询 workflow 详情
bytedcli kani openapi workflow get \
  --workflow-id wf_demo \
  --namespace kani_demo \
  --applicant alice

# 确认用户意图和 work order 详情后，再审批、驳回或撤回 workflow work order
bytedcli kani openapi workflow approve --workorder-id wo_demo --comment "Approved for rollout"
bytedcli kani openapi workflow reject --workorder-id wo_demo --comment "Missing business context"
bytedcli kani openapi workflow cancel --workorder-id wo_demo --comment "Superseded by a new request"

# write-log 默认查当前 identity 最近 30 天
bytedcli kani openapi write-log list

# 机器可读输出（全局参数，必须放在子命令前）
bytedcli --json kani openapi workflow list
bytedcli --json kani knowledge search --query "如何申请 Kani 资源权限"
```

## 快速规则

- `workflow create` / `workflow get` / `workflow list` 可直接查询或提交；`workflow approve|reject|cancel` 有审批/撤回副作用，执行前必须获得用户明确确认
- `workflow approve|reject|cancel` 按 `--workorder-id` 操作，不是按 `--workflow-id`；先用 `workflow get` 核对申请对象、申请理由、审批节点和 `WorkOrders[].ID`
- `workflow list` 默认查当前/running；若需要查已完成记录，传 `--status finished`
- `workflow list` 在 running 场景下使用公开 `--page/--page-size` 分页时，默认查询 `urgent=false` 的稳定 bucket
- `workflow list` 复用 Kani review backend，不会因 `BYTEDCLI_NETWORK_PROFILE=prod` 切到 KaniV2 OpenAPI `*.byted.org` host
- `workflow create`：`--body-file` 模式，直接提交原始 JSON request body
- `--region row` 默认按 ROW SG 解释；ROW US(i18n) 显式用 `--region va`
- 默认未设置 `BYTEDCLI_NETWORK_PROFILE` 时优先使用办公网 OpenAPI 入口；生产网运行时设置 `BYTEDCLI_NETWORK_PROFILE=prod`
- `cn` / `boe`：默认办公网入口分别为 `kani-v2-openapi-cn.bytedance.net` / `kani-v2-openapi-boe.bytedance.net`；`prod` profile 切到 `*.byted.org`
- `sg` / `row` / `va`：默认办公网入口分别为 `kani-openapi-sg.tiktok-row.net` / `kani-openapi-sg.tiktok-row.net` / `kani-openapi-va.tiktok-row.net`；`prod` profile 切到对应 `kani-v2-openapi-{sg|va}.byted.org`
- 隐藏兼容路径仍可用，但不作为对外推荐入口
