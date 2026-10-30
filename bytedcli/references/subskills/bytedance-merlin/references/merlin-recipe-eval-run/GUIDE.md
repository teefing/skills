---
name: merlin-recipe-eval-run
description: 启动已有 Exercise Version 或创建旧评估实例；用户要运行模型评估、核对启动配置或查询 Arena 任务状态时使用。旧实例的快捷结果聚合不在本入口范围内。
---

# 运行评估

先读取 Exercise Version，检查模型、资源和启动配置。按已配置版本启动使用 v4 `launch-version`；旧评估实例入口为 `create-version-instance`，两者的参数模型和返回 ID 不可混用。

```bash
bytedcli merlin exercise get-version --sid demo-version
bytedcli merlin exercise launch-version --sid demo-version --dry-run
bytedcli merlin exercise create-version-instance --schema
# 显式模型列表的旧实例入口
bytedcli merlin exercise create-version-instance --exercise-sid demo-exercise --exercise-version-sid demo-version --verified-models '["demo-model"]' --dry-run
```

核对实际版本、模型和资源后，在用户授权范围内移除 `--dry-run`。版本启动依赖版本中已配置的 `launch_spec`；不要把旧包装器的 `hdfs_config_items` 等字段直接传给新接口。

返回成功但实例信息为空，或者请求超时时，不要自动重新创建。先根据返回的任务链接/ID 或控制台核实是否已受理。独立工具的 `exercise run/list-runs/get-result` 包装流程未作为原生入口提供。

Arena 评估按 ArenaJob SID 查询状态和明细：

```bash
bytedcli merlin arena jobs get --sid demo-arena-job
bytedcli merlin arena cases list --schema
```

不要把 Exercise Instance SID、Merlin JobRun ID 与 ArenaJob SID 相互替换。结果查询边界见 [评估结果](../merlin-eval-get-result/GUIDE.md)。
