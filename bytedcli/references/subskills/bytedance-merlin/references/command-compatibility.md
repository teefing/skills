# Merlin 命令与接口

生成命令按已核实的远端接口注册。v4 命令调用所选站点的 HTTP API；兼容命令使用真实 MCP 注册名。命令路径不作为 MCP 工具名发送。

```bash
bytedcli --site cn --vregion seed merlin job-v2 runs get --sid demo-run
bytedcli --site i18n-bd --vregion seed merlin job-v2 runs list --schema
bytedcli merlin training checkpoint-dirs list --schema
bytedcli merlin arena jobs get --sid demo-arena-job --dry-run
```

`--schema` 是当前接口的请求结构。对象、数组参数按字段传 JSON；全局 `--json` 控制输出。通用 `--dry-run` 只在本地显示请求，不认证、不发起 HTTP/MCP 调用；后端请求字段 `dry_run` 单独使用 `--request-dry-run`，它可能仍创建远端资源。

保留原生 `job submit/extract/trials/get-timeline`、CPU Devbox 生命周期、SSH、公钥和 profiling 下载等已有工作流。`profiling list --job-id` 继续支持，并映射到远端 `job_run_id`。

以下旧入口曾把本地流程误当作 MCP 工具。当前使用已实现的原生操作，不能把旧参数直接套到新接口上：

| 旧流程 | 当前入口或边界 |
| --- | --- |
| `data upload/get-job/list-jobs` | `data datacard-upload-jobs create/get/list`；上传配置改为 v4 嵌套字段 |
| `exercise run` | 已配置版本用 `exercise launch-version`；显式旧实例用 `exercise create-version-instance` |
| `exercise get-result/list-cases/list-runs/export-result` | 不是原生快捷入口；Arena 任务用 `arena jobs get` / `arena cases list`，旧实例不能混用 Arena SID |
| `collection +create-from-exercises` | `collection create` 后使用 `evaluation collection-versions create` 显式设置评测树 |
| `exercise +quick-create` | `exercise create` 与 `exercise create-version` 分步创建 |
| `exercise import` / `collection import` | 本地 YAML 编排尚无原生实现；按对应资源 schema 分步处理 |
| `job execute-script` / `job-v2 runs execute-script` | 远端执行使用原生 `job exec`；先看帮助，不沿用本地包装器参数 |
| `job-v2 templates get-versions` | 使用 `job-v2 template-versions list` |
| `job-v2 run-trials exit-info` | 使用原生 `job trials` / `trial diagnose`，结果结构不同 |
| `job-v2 run-trial-tls-logs fetch` | 使用原生 `logs get` 查询日志 |
| `job clone` / `job-v2 runs fork` | 可用 `job fork-run` 的兼容 MCP 流程；不承诺复制本地持久卷包装器行为，Seed 优先原生 `job extract` 后调整配置再 `job submit` |
| `profiling upload`、Grafana 截图/面板本地流程、Arnold 本地诊断和 Ray Dashboard 包装器 | 尚无对应原生实现，不注册为不存在的 MCP 工具 |

上游已删除的 `arena delete-evaluation`、`exercise delete`、`evaluation collections delete` 和 `evaluation insight-significances create` 不再提供。不要将删除操作猜测映射到另一个资源接口。

命令支持不等于账号在每个站点都有权限。遇到鉴权或业务错误时核对站点、资源和权限，不自动换站点或重试写请求。
