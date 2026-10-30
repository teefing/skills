---
name: bytedance-bfo
description: "Operate BFO (Byte FinOps) via bytedcli: search service tree nodes, query CPU spec upgrade summary/clusters/details/profit, evaluate performance profit across two periods with v2/v3 methods. Use when tasks mention BFO, Byte FinOps, CPU 规格升级, 规格升配, 性能优化, 收益回收, 收益评估, or ProfitAnalyse."
---

# BFO

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

BFO (Byte FinOps) 平台的 CLI 操作工具，支持 CPU 规格升级查询与性能收益评估。

## Capabilities

- 服务树搜索：通过关键词搜索 Galaxy 服务树节点，获取 node ID
- CPU 规格升级概览：查看指定服务树节点下的 CPU 规格升级推荐覆盖范围与预估收益
- 逻辑集群列表：分页列出推荐升级的逻辑集群，支持按 Pod CPU 规格过滤
- 物理集群详情：查看逻辑集群下的物理集群规格详情（当前规格、建议规格、预期收益）
- 收益回收记录：查看 CPU 规格优化后的实际收益回收数据
- 收益评估：指定 PSM、基准和优化后两个时间段，按口径二/三对比 CPU 与效率指标

## Usage

```bash
# 搜索服务树节点（获取 node-id）
bytedcli bfo tree search --keyword example-service

# CPU 规格升级概览
bytedcli bfo cpu-spec summary --node-id 17

# 列出推荐升级的逻辑集群（分页）
bytedcli bfo cpu-spec list --node-id 17 --page-num 1 --page-size 20

# 按 Pod CPU 规格过滤（小于 8 核）
bytedcli bfo cpu-spec list --node-id 17 --cpu-spec 8

# 查看物理集群详情
bytedcli bfo cpu-spec detail --psm example.service.api --cluster default

# 指定 region
bytedcli bfo cpu-spec detail --psm example.service.api --cluster default --region China-East

# 查看收益回收记录
bytedcli bfo cpu-spec profit --node-id 17

# 收益分析页的收益评估：时间参数均为 Unix 秒时间戳，CN 站点
bytedcli --json --site cn bfo profit evaluate --psm example.service.api \
  --base-start 1767225600 --base-end 1767312000 \
  --new-start 1767484800 --new-end 1767571200 --version v2

# 口径三适用于流量合并/裁剪场景，不提供 QPS 或单核效率指标
bytedcli --json --site cn bfo profit evaluate --psm example.service.api \
  --base-start 1767225600 --base-end 1767312000 \
  --new-start 1767484800 --new-end 1767571200 --version v3

# Agent 调用必须加上 --json
bytedcli --json bfo tree search --keyword example-service
bytedcli --json bfo cpu-spec summary --node-id 17
bytedcli --json bfo cpu-spec list --node-id 17
bytedcli --json bfo cpu-spec detail --psm example.service.api --cluster default
bytedcli --json bfo cpu-spec profit --node-id 17
```

## Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--region <region>` | Region | `China-North` |
| `--page-num <num>` | Page number | `1` |
| `--page-size <size>` | Page size | `10` |
| `-j, --json` | JSON output | - |

## 收益评估参数

`bfo profit evaluate` 对应 `/cost/ProfitAnalyse` 的“收益评估”。

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| `--psm <psm>` | 服务 PSM，必填；直接对应页面叶子服务节点 | - |
| `--base-start <seconds>` / `--base-end <seconds>` | 基准时间段，必填，正整数 Unix 秒时间戳（最多 10 位） | - |
| `--new-start <seconds>` / `--new-end <seconds>` | 优化后时间段，必填，同上；每个时间段结束须晚于开始 | - |
| `--version <version>` | `v2`：口径二，自然流量；`v3`：口径三，流量合并/裁剪 | `v2` |

输出包含 `version`、可复现的 `request`、`psm`、`cpuTotal`、`optimizationCore`、`basic`（优化前）与 `optimization`（优化后）。v2 还包含 `deltaCorePerQps` 与 QPS/单核效率指标；v3 不返回这些指标。时间不采用页面的动态默认值，须显式传入四个秒时间戳。

## Agent Guidance

- `bfo profit evaluate` 是只读评估，不会登记收益或执行资源回收。已有 `cpu-spec profit` 查询 CPU 规格升级后的收益记录，两者用途不同。
- 收益评估目前仅支持 `--site cn`，走 BFO 控制台 `/api/v1/costplatform/query_psm_perf` GET，使用 CN 用户 ByteCloud JWT；CPU 规格命令继续走 general-f2b 的 item-service POST 接口。
- 评估接口不接收 `--node-id` 或 `--region`；传服务 PSM 即可。页面 URL 中的四个 `*Time` 参数是 Unix 秒时间戳，对应四个时间参数。
- `cpuTotal`、`optimizationCore`、`deltaCorePerQps` 及前后指标保留服务端值，包含单位和正负号。不要把负收益改写为正回收，也不要对已是百分数的 CPU 利用率再次乘 100；v2 常返回不带 `%` 的百分数字符串，v3 常返回带 `%` 的字符串。
