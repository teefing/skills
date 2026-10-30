---
name: merlin-recipe-e2e-eval-verify
description: 按数据导入、版本配置、启动和结果查询验证 Seed 评估；用户要检查平台评估配置、运行小数据集验证或核对实际结果时使用。说明原生命令支持范围及旧实例查询边界。
---

# 验证评估配置与运行结果

按数据、版本配置、启动、结果四步验证。每步保留实际返回的 SID 和状态，不用示例 ID 代替真实对象。

1. 通过 [数据上传](../merlin-eval-data-upload/GUIDE.md) 创建上传任务并查询至完成，核对表结构和 snapshot。
2. 通过 Exercise 查询命令读取版本，确认数据、模型、评估代码和资源。
3. 先预览启动请求；在授权范围内提交一次，记录返回的任务链接和 ID。
4. 按对象类型读取结果；对于 ArenaJob，读取任务及 case 明细；旧 Exercise Instance 的快捷结果聚合尚无原生实现，使用对应控制台核对。

```bash
bytedcli merlin data datacard-upload-jobs get --sid demo-upload-job
bytedcli merlin exercise get-version --sid demo-version
bytedcli merlin exercise launch-version --sid demo-version --dry-run
bytedcli merlin arena jobs get --sid demo-arena-job
bytedcli merlin arena cases list --schema
```

小数据集验证通过后再启动完整数据集。不要因为创建请求超时、返回空实例或暂时查不到结果就立即重试创建；先检查是否已创建。CLI 请求成功、任务运行完成、评估指标满足预期是三个不同的结论。

相关说明：[运行评估](../merlin-recipe-eval-run/GUIDE.md)、[评估结果](../merlin-eval-get-result/GUIDE.md)、[Collection 配置](../merlin-recipe-eval-collection/GUIDE.md)。
