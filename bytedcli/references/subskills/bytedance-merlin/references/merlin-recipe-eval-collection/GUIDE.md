---
name: merlin-recipe-eval-collection
description: 从一个或多个 Exercise Version 创建评估 Collection。当需要将多个已存在的 Exercise Version 组织为 Seed 平台的 Collection 时使用。触发词：创建 collection、create collection、评估集合、exercise 组装 collection、collection version、组合 exercise、合并 exercise、collection 创建。即使用户没有明确说"collection"，只要涉及将多个 Exercise 组合到一起进行统一评估管理，都应使用本 skill。
---

# 创建评估 Collection

先创建 Collection，再通过 v4 Collection Version 请求显式指定评测树。不要把本地组合流程 `collection +create-from-exercises` 当作远端工具调用。

```bash
bytedcli merlin collection create --name demo-collection --type TEST --owners '["demo-user"]' --dry-run
bytedcli merlin evaluation collection-versions create --schema
# collection SID、exercise SID、version SID 和 metric 必须来自实际查询结果
bytedcli merlin evaluation collection-versions create --collection-sid demo-collection --name demo-version --tree '{"name":"demo-metric","exercise_metric":{"exercise_sid":"demo-exercise","exercise_version_sid":"demo-version","metric":"demo-metric"}}' --dry-run
bytedcli merlin evaluation collection-versions get --sid demo-collection-version
bytedcli merlin evaluation collection-versions list --collection-sid demo-collection --page-size 20
```

确认资源、owner、指标和评测树后，在授权范围内移除 `--dry-run` 提交。目录节点的 `nodes` 与叶子的 `exercise_metric` / `environment_metric` 互斥；不要猜测指标名。先通过对应版本配置确认指标，然后构造树。创建后用返回的 SID 读取，核对树与版本关联。

创建 Collection 不会自动运行评估。启动入口见 [运行评估](../merlin-recipe-eval-run/GUIDE.md)。
