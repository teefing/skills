---
name: merlin-eval-get-result
description: 读取 Arena 任务和分页 case 明细，并区分 Exercise 版本、旧评估实例和 ArenaJob；用户查询评估结果或指标时使用。旧 Exercise Instance 的本地聚合快捷流程尚无原生入口，完整 Arena 导出见 merlin-eval-result-export。
---

# 查询评估结果

先区分对象：Exercise Version 是配置版本，Exercise Instance 是一次旧评估实例，ArenaJob 是 Arena 评估任务。它们的 SID 不可互换。

Arena 评估通过原生 v4 命令读取任务和分页明细：

```bash
bytedcli merlin arena jobs get --sid demo-arena-job
bytedcli merlin arena cases list --schema
```

`arena cases list` 需要 `arena_job` 对象和 `exercise_version_sid`；按 schema 选择任务及评测版本。只有成功的评估部分才有完整结果；运行中或失败任务可能返回部分数据。保留响应中的 `page_token` 等分页信息，继续读取下一页，不把单页当成全量。

查询 Exercise 配置和版本绑定的数据：

```bash
bytedcli merlin exercise get --sid demo-exercise
bytedcli merlin exercise get-version --sid demo-version
bytedcli merlin exercise get-version-data-card-info --exercise-sid demo-exercise --exercise-version-sid demo-version
```

数据卡信息不是评估指标。原先的 `exercise get-result/list-cases/export-result` 是独立工具的本地组合流程，不能直接作为 MCP 工具调用；当前原生入口不承诺这些快捷命令。仅持有旧 Exercise Instance SID 时，通过对应控制台核对结果，不能把它传给 `arena jobs get`。

完整 Arena 明细导出见 [评估结果导出](../merlin-eval-result-export/GUIDE.md)。任务详情和 case 明细不是本地导出文件；下载应使用导出任务成功后返回的结果链接。
