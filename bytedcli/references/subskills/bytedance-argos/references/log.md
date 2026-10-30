# Argos 日志查询与分页

普通日志搜索、PSM/LogID、Pod/实例/泳道、Footprint、长时间窗滚动与日志分析优先使用 `bytedance-log`。当用户明确要求 Argos、需要这里的 Argos Tool 合同，或专用入口不覆盖时，使用本页。

## 能力选择

| 目标 | 首选 Tool | 必要输入 |
| --- | --- | --- |
| 关键词、level、KV、排除词或精确 term 检索 | `log.search.keywords_stream` | PSM、region、固定时间窗 |
| 按 LogID 追踪 | `log.logid_prune` | LogID、region |
| 错误日志聚合 | `log.error_log` | PSM、region、时间窗 |
| Pod 本地日志文件 | `log.local_file` | PSM、region、Pod、路径、时间窗 |

过滤条件按用户目标选用，keywords 并非必填。优先使用用户已有的关键词、level、KV 或排除条件缩小范围，不捏造过滤；用户明确要求固定短窗全部日志时，不强求额外过滤。范围过大时，建议缩小时间窗或增加过滤条件。

`log.search.keywords` 不具备同等结构化过滤能力；`log.key_word_v2` 是兼容入口，新查询优先 `log.search.keywords_stream`。

## 结构化关键词/KV查询

```bash
# 关键词 + 绝对 RFC3339 时间窗
bytedcli argos tool log.search.keywords_stream \
  --psm-list example.service \
  --region China-North \
  --keywords timeout,error \
  --start 2026-10-15T02:00:00Z \
  --end 2026-10-15T03:00:00Z

# 没有关键词也可按 level / KV 过滤，不要强行补造 keywords
bytedcli argos tool log.search.keywords_stream \
  --psm-list example.service \
  --region China-North \
  --level ERROR \
  --kv-filters '[{"key":"_podname","values":["sample-pod"]}]' \
  --start 2026-10-15T02:00:00Z \
  --end 2026-10-15T03:00:00Z
```

`level` 是 `_level` KV filter 的简写，不能同时传 `--level` 和 key 为 `_level` 的 `--kv-filters`。数组/对象参数必须是合法 JSON。

## 一批结果、完成状态与续查

结构化参数模式默认自动收集**一批**结果：

- 首批 `--max-results` 默认 1000；请求已带 cursor 时默认 1500。
- 索引首轮单页最多 1000；非索引或索引状态未知时首轮 100、后续 200；带 cursor 的续查页每页 500。
- `--max-pages` 默认 100，是这一批的页数预算；`limit` 是单次后端页大小，不能把两者混为一谈。
- 只有后端明确返回 `finished=true` 才表示整个查询范围完成。达到预算、cursor 缺失/重复或后续页失败，都只能说明本批停止。

检查 `pagination.complete`、`pagination.truncated`、`pagination.stop_reason`、cursor 和日志数量。后续页失败时，已有日志与可用 cursor 会保留，错误写入 `pagination.error`；这些是部分结果，不能宣称代表整个时间窗。

需要更多证据时，保持 PSM、关键词/过滤条件、region 和**同一个绝对时间窗**，把 cursor 原样传回：

```bash
bytedcli argos tool log.search.keywords_stream \
  --psm-list example.service \
  --region China-North \
  --keywords timeout,error \
  --start 2026-10-15T02:00:00Z \
  --end 2026-10-15T03:00:00Z \
  --cursor '<opaque-cursor>'
```

cursor 是不透明值，不要解析、重建或修改。Tool 响应没有前端使用的 `log_size`，因此当前 CLI 不能精确执行前端 100 MB 暂停门槛。

## 单页模式与 raw 模式

```bash
# 仍走结构化参数优化，但关闭自动分页，只取当前 cursor 页
bytedcli argos tool log.search.keywords_stream \
  --psm-list example.service \
  --region China-North \
  --keywords timeout \
  --duration 1h \
  --no-auto-page

# 原始 JSON 只透传一次：不补时间/default，不自动分页
bytedcli argos tool log.search.keywords_stream \
  --input '{"psm_list":["example.service"],"region":"China-North","keywords":["timeout"],"start":"2026-10-15T02:00:00Z","end":"2026-10-15T03:00:00Z"}'
```

`--no-auto-page` 不等于 raw：结构化字段仍经过 handler。`--input` 才会绕过参数优化和自动分页。

## LogID、错误聚合与 Pod 本地日志

```bash
bytedcli argos tool log.logid_prune \
  --log-id '<log-id>' \
  --region China-North

# 多区域 LogID：整个 region 值加引号，可选 PSM 过滤
bytedcli --site cn argos tool log.logid_prune \
  --log-id '<log-id>' \
  --region 'China-North|China-North6' \
  --psm-list example.service

bytedcli argos tool log.error_log \
  --psm example.service \
  --region China-North \
  --duration 1h

bytedcli argos tool log.local_file \
  --psms example.service \
  --regions China-North \
  --pod-names sample-pod \
  --paths /opt/tiger/toutiao/log/app.log \
  --duration 15m
```

- `log.error_log` 的结构化 handler 将时间转换为后端所需 Unix 秒，并默认 `aggregator=location`。
- `log.local_file` 未传 `--seek-position` 时，按 `--duration` 生成 `seek_position.time_range`。
- `log.logid_prune` 的多 region 值用 `|` 分隔并整体加引号；不要用逗号或重复 `--region`。这项约定不能套到关键词流、错误聚合或其它 Tool；跨站点时分别查询。普通多区域 LogID 仍优先使用 `bytedance-log` 的默认入口。
- Argos Footprint 日志下载（viewlog `argos` / `argos_keyword` 类型）仍使用 `bytedance-log`，不要改写为这里的 Tool。
- `eu-ttp` Agent Center 的 server 模式调用 `log.search.keywords_stream` 可能返回 403；保持默认 `auto` 执行模式，让 SDK 优先使用 WebSocket，不要为规避错误换错控制面。

## 结果判断

先判断查询是否命中正确 PSM、region、绝对时间窗和过滤条件，再解释内容。日志为 0 时优先检查控制面、时间单位、索引/过滤语义和权限；部分结果只支持有边界的阶段性结论。若需要根据日志证据决定跨域下一步或解释根因，再进入 [Argos Agent 调查](./argos-agent.md)，而不是因为调用次数多就转入。
