---
name: merlin-profiling
description: 查询和下载 Merlin profiling 资产；用户需要按任务或 trial 查找 Perfetto、Nsys、BGCP、Memotrace 文件、查看元信息或保存到本机时使用。
---

# Profiling 资产查询与下载

查询 Perfetto、Nsys、BGCP、Memotrace 等资产，并下载到运行 bytedcli 的机器。

```bash
bytedcli merlin profiling list --job-id demo-job --limit 20
bytedcli merlin profiling list --trial-id demo-trial
bytedcli merlin profiling get --sid demo-asset
bytedcli --site i18n-bd --vregion seed merlin profiling get-tos-link --sid demo-asset --dry-run
bytedcli --site i18n-bd --vregion seed merlin profiling download --sid demo-asset --output ./demo-trace.perfetto
# 已配置 HDFS 客户端时可以直接读取 HDFS
bytedcli merlin profiling download --sid demo-asset --use-hdfs --output ./demo-trace.perfetto
```

`--job-id` 映射为 MCP 的 `job_run_id`；它与 `--trial-id` 互斥。元信息请求直接使用已核实的 MCP 注册名，权限或业务失败不触发备用工具重试。

`get-tos-link` 和 TOS 下载使用当前站点的 Reporting 服务。HDFS 资产可能先被复制到 TOS。失败时不会跨站点重试；已有目标文件不会被覆盖；下载失败会清理临时文件。`--use-hdfs` 要求本机 HDFS 客户端及其权限，不会自动改走 TOS。

`--dry-run` 不认证、不访问网络、不写文件。列表按 `limit` / `offset` 分页；需要全量时检查 `has_more` 后继续查询。批量下载应使用有界并发。

本入口提供查询、签名链接和下载。本地文件上传没有原生实现；不要把文件路径作为 `profiling upload` MCP 参数发送，远端工具不能读取本机文件。

出现 401/403 时检查所选站点的登录状态。MCP 元信息成功但旧签名工具报 `record not found` 时，使用上面的 `get-tos-link` 或 `download`，并核对站点与 Seed 虚拟区域。
