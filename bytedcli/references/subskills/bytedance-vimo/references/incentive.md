# 海外 Vimo 用户激励配置

只用于“用户激励活动”业务下的运营活动、活动玩法及推荐模板强插配置。
普通模板 Feed 推荐、推荐算法排名、用户实际看到的内容不属于这些接口。
鉴权与网络沿用 [i18n.md](i18n.md)。列表命令只读；复制命令默认预览。

## 选择对象

| 页面/用户意图 | 命令 | BFF 路径（前缀 `/user/api/UserIncentive/`） | 结果 |
| --- | --- | --- | --- |
| 运营活动列表、父活动 | `incentive operation-activity list` | `getOperationActivityList` | `data.activities` |
| 复制运营活动为未上线草稿 | `incentive operation-activity copy` | `getOperationActivityList` → `saveOperationActivity` | `data.payload`、提交确认 |
| 活动玩法列表、父活动下的玩法 | `incentive activity list` | `getActivityList` | `data.activities` |
| 推荐模板列表、活动关联的强插模板 | `incentive template list` | `getForceInsertTemplates` | `data.templates` |

“查询活动”在上下文不足时需要区分运营活动与活动玩法；不要因例子中有 `activity list`
就默认选择玩法。`--activity-id` 在两类列表中表示各自的 ID；玩法的父活动条件使用
`--operation-activity-id`。TemplateID 可以关联到模板，但强插配置记录不是模板详情。

```bash
# 用户激励中的运营活动
bytedcli --site i18n --json vimo incentive operation-activity list \
  --activity-name 'demo-activity' --page-size 20
# 先预览复制请求；确认后追加 --reasons 和 --yes 提交
bytedcli --site i18n --json vimo incentive operation-activity copy \
  --activity-id '<operation-activity-id>' --name 'demo-activity-copy'
# 指定运营活动下的活动玩法
bytedcli --site i18n --json vimo incentive activity list \
  --operation-activity-id '<operation-activity-id>' --page-size 20
# 指定运营活动关联的推荐模板强插配置
bytedcli --site i18n --json vimo incentive template list \
  --operation-activity-id '<operation-activity-id>' --page-size 20
# 查看某模板的强插配置，不用于证明它实际获得曝光
bytedcli --site i18n --json vimo incentive template list --template-id '<template-id>'
```

`copy` 用 `--activity-id` 精确查询一条源运营活动，以 `--name` 指定新名称。
复制父运营活动的配置与时间范围，创建请求不带源 `ActivityID`，状态固定为未上线（`Status=0`）。
默认只读取源活动并返回创建 payload；确认后添加 `--reasons '...' --yes` 提交一次。
活动玩法、推荐模板强插关联不会随父活动复制；提交后用列表查询核对新活动。
若源活动配置了保存接口不支持的 `RecommendContentComponent`，命令会拒绝复制，避免遗漏该组件。

## 筛选与分页

- 运营活动支持 `--activity-id`、`--activity-name`、`--status`。
- 活动玩法支持 `--activity-id`、`--title`、`--activity-type`、`--status`、`--biz-ids`，
  以及父运营活动的 `--operation-activity-id`、`--operation-activity-name`。
- 推荐模板配置支持 `--template-id`、`--biz-ids`、`--operation-activity-id`、
  `--operation-activity-name`。
- 当前 `--status`、`--activity-type` 接受逗号分隔的整数编码。三类对象的状态不能互套；
  只有页面或接口契约明确编码时才传入，不从中文状态名称猜数字。
- `--biz-ids` 是地区 business ID，不能使用顶层 CapCut bid 或应用 AppID 替代。
- 三类查询使用 `--cursor`，首页省略；`--page-size` 默认 `20`，最多 `100`。
  仅在 `data.has_more=true` 时，把 `data.next_cursor` 原样传入下一页，保留业务筛选。
  不使用 `--page`。活动玩法与推荐模板的 `current_count` 是本页数量，不是总量。

结果只证明配置存在。若用户要实际推荐命中、排名、转化、奖励到账或活动效果，
保留这些未完成的问题并查对应运行时/分析证据；不能把配置列表作为效果结论。
