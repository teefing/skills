# 海外征稿任务与线索补充命令

以下命令使用 `--site i18n`，调用 Vimo User BFF。运行具体叶子命令的 `--help` 可查看源接口字段及必填约束。数组和对象参数使用 JSON 文本，也可通过 `--body-file` 传完整 JSON 对象；显式参数覆盖文件中的同名字段。64 位 ID 保持为字符串。

| 命令路径（接在 `bytedcli --site i18n vimo` 后） | 用途                     |
| ----------------------------------------------- | ------------------------ |
| `creator task approval-status get`              | 批量查询任务审批状态     |
| `creator task status update`                    | 下线征稿任务             |
| `creator task rule generate`                    | 按任务描述生成奖励规则   |
| `creator task factor list`                      | 查询任务达成条件因子     |
| `creator task preview-url get`                  | 查询任务预览地址         |
| `creator task visibility get`                   | 判断用户是否可见指定任务 |
| `creator task pin region list`                  | 查询任务置顶国家列表     |
| `creator task reward order update`              | 调整任务奖励投稿排序     |
| `creator clue task-form get`                    | 从线索取得任务表单初始值 |
| `creator clue delete`                           | 删除线索记录             |
| `creator clue ai-region list`                   | 查询 AI 线索区域         |
| `creator clue record list`                      | 查询线索记录列表         |

```bash
bytedcli --site i18n --json vimo creator task approval-status get --task-ids '["sample-task-1"]'
bytedcli --site i18n --json vimo creator clue record list
bytedcli --site i18n --json vimo creator task status update --task-id sample-task-1
bytedcli --site i18n --json vimo creator task status update --task-id sample-task-1 --yes --reasons '任务已结束'
```

写命令默认返回请求体预览，只有 `--yes` 才提交；L3 风险规则还要求 `--reasons`。服务端会再校验业务权限和字段。`clue delete` 是源平台的研发清理接口，仅在明确需要删除指定记录时使用。若提交后出现 `VIMO_MUTATION_OUTCOME_UNKNOWN`，先查询资源状态，再决定是否需要人工重试。
