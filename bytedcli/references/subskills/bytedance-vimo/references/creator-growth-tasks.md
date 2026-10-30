# 海外 Vimo 创作者成长任务

用于用户明确查询“成长任务”的请求。命令读取成长任务配置，接口为
`POST /user/api/GrowTask/getGrowTaskList`。它不查询征稿任务、任务投稿、用户完成进度或奖励到账。
征稿任务见 [creator-tasks.md](creator-tasks.md)，可复用任务配置见
[creator-task-templates.md](creator-task-templates.md)。鉴权与网络沿用 [i18n.md](i18n.md)。

## 查询

```bash
# 从用户提供的页面/授权上下文取得区域代码
bytedcli --site i18n --json vimo creator growth-task list \
  --region '<authorized-region>' --page 1 --page-size 20
# 精确查成长任务；不要把征稿 task ID 直接复用到这里
bytedcli --site i18n --json vimo creator growth-task list \
  --region '<authorized-region>' --task-id '<growth-task-id>'
```

| 参数 | 含义 |
| --- | --- |
| `--region` | 必填，Vimo 授权区域代码；不是顶层 bid，也不是地区 business ID |
| `--task-id` | 成长任务 ID，保留为字符串 |
| `--title`、`--subtitle`、`--icon-uri` | 对应配置字段筛选 |
| `--type`、`--level`、`--status` | 当前命令接受逗号分隔的整数编码；仅使用已知页面/接口契约的值，不套用征稿任务枚举 |
| `--page`、`--page-size` | 一基页码；默认 `1`、`20`，单页最多 `100` |

缺少区域上下文时询问区域，不猜默认国家。用户只问某条任务时优先按 ID 查询，
不要全量扫描其他地区来寻找同名任务。

## 结果与分页

成功时读取 `data.tasks`，保留 `region`、`page`、`page_size` 与 `current_count`。
`estimated_total` 是上游按总页数乘页大小给出的估计值，不是精确任务总数。
需要继续浏览时保持地区和筛选条件；空页停止，满页可继续，不能把估计值当作精确计数。
该命令没有用户进度查询或写入能力，配置存在不代表某个用户已经看到或完成任务。
