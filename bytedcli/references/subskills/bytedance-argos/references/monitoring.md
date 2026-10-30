# Argos 监控对象与查询

先辨认 Measurement、Metrics 和 Dashboard，再选择确定性取数或开放式调查。普通 QPS/SLA、CPU/MEM、依赖拓扑、Redis、中间件、Query DSL、多 region、Bosun、报警规则与值班计划等，优先使用 `bytedance-apm` 已有能力；已知需要 Argos Tool、专用入口不覆盖或用户指定 Argos 时使用本页。

## 三类对象

| 对象 | 核实内容 | 当前路径 |
| --- | --- | --- |
| Measurement / 服务测点 | 服务、精确测点标识或定义、observable object、维度、时间 | 已知查询纠偏/元数据检查可用 `timeseries.inspect`；不要把显示名直接当 metric |
| Metrics | 精确指标名、字段/聚合、Tag、tenant、region、时间 | `metrics.*` 或专用 APM；必要时先发现元数据 |
| Dashboard / Folder | 链接或 ID；是读面板、巡检，还是修改/导入 | 巡检/解释可用 Argos Agent；写入/导入只走支持它的 Agent Session 服务端能力 |

`timeseries.inspect` 不是任意自然语言指标发现工具。它只对**已知** Measurement/Metrics 查询做纠偏、元数据检查，或解析携带完整查询状态的 URL。

## Metrics 元数据与取数

不知道精确指标名或标签时，可按 `name_suggestion` → `tag_key` → `tag_value` → `data` 的确定性步骤执行；如果输入已经完整，不必每次重走发现流程。

```bash
bytedcli argos tool metrics.name_suggestion \
  --region China-North \
  --tenant default \
  --metrics-name-prefix sample. \
  --limit 10

bytedcli argos tool metrics.tag_key \
  --region China-North \
  --metrics-name sample.metric

# wire 字段 tagK 对应 CLI 参数 --tag-k
bytedcli argos tool metrics.tag_value \
  --region China-North \
  --metrics-name sample.metric \
  --tag-k _psm

bytedcli argos tool metrics.data \
  --metric sample.metric \
  --region China-North \
  --duration 1h \
  --tags '[{"key":"_psm","value":"example.service","function":"literal_or","is_filter":true}]'
```

结构化模式下，`metrics.data` 默认补 `aggregator=avg`、`top_bottom=top-20-max`、`tenant=default`；`metrics.name_suggestion` 默认 `namespace=default`、`tenant=default`、`limit=10`；`tag_key/tag_value` 默认 `namespace=default`、`tenant=default`。显式参数优先。

Timer/counter 多字段指标通常还需声明字段表达式：

```bash
bytedcli argos tool metrics.data \
  --metric sample.timer.metric \
  --region China-North \
  --start-time 2026-10-15T10:00:00+08:00 \
  --end-time 2026-10-15T11:00:00+08:00 \
  --top-bottom top-20-max \
  --aggregator avg \
  --is-multi-field true \
  --multi-field-expr 'weighted_avg(value=pct99,weight=counter)'
```

## Timeseries Inspect

```bash
# 仅按已知前缀纠正可能的 Metrics 名称
bytedcli argos tool timeseries.inspect \
  --command suggest_names \
  --source metrics \
  --name-prefix sample. \
  --region China-North

# 查看已知 Measurement 的结构；显示名不能代替精确 name
bytedcli argos tool timeseries.inspect \
  --command describe \
  --source measurement \
  --name sample.measurement \
  --observable-object service:example.service \
  --region China-North
```

`command` 支持 `suggest_names`、`describe`、`values`、`parse`；前三种的 `source` 为 `measurement` 或 `metrics`。字段依赖对象类型，以 `bytedcli argos tool timeseries.inspect --schema` 为准。

### 解析已有查询 URL

以下是 CN 示例，必须保留 URL 中完整查询状态：

```bash
# Metrics FE 指标详情：保留完整 hash
bytedcli argos tool timeseries.inspect \
  --command parse \
  --url 'https://metrics-fe.byted.org/web/plot/metrics#now-1h,now,,,,,,,China-North,false,,;sum:store:top-20-max:sample.metric{}{_psm=literal_or(example.service)};0'

# Metrics FE Bosun：保留 bosun 查询参数
bytedcli argos tool timeseries.inspect \
  --command parse \
  --url 'https://metrics-fe.byted.org/web/bosun/cn?bosun=sum%28q%28%22sum%3Asample.metric%7B_psm%3Dexample.service%7D%22%2C%223600s%22%2C%220s%22%29%29&region=China-North'

# Argos Explore / Dashboard / Overview：保留 queries 参数
bytedcli argos tool timeseries.inspect \
  --command parse \
  --url 'https://cloud.bytedance.net/argos/dashboard/demo?queries=%5B%7B%22queryType%22%3A%22metrics%22%2C%22metrics%22%3A%7B%22metric%22%3A%22sample.metric%22%2C%22tenant%22%3A%22default%22%2C%22aggr%22%3A%22avg%22%2C%22region%22%3A%22China-North%22%2C%22tags%22%3A%5B%5D%7D%7D%5D&from=now-1h&to=now'
```

普通大盘首页和 Grafana URL 不在 `parse` 支持范围内。解析只返回 `measurement.data` / `metrics.data` / `bosun.data` 的 `parsed_queries`，不会执行查询，也不会验证指标存在。

## Dashboard 与报警

- Dashboard/Folder 的创建、修改、复制、迁移或 Grafana/Metrics-FE/Metrics SDK 导入，不是直接 `bytedcli argos tool` 子命令。它们通过服务端提供的 Agent Session 能力执行；可用性取决于控制面、project 和服务端配置。见 [Dashboard Agent Session 操作](./dashboard-operation.md)。
- 读面板与巡检不是写入。已知确定性 APM/CLI 能力可直接用；需要判断异常、跨面板解释原因时再用 [Argos Agent 调查](./argos-agent.md)。
- 报警规则查找、规则/值班计划读写等确定性任务继续使用实际支持的专用 APM/CLI 路径。已有规则的诊断/优化按 [报警规则优化](./alarm-rule-optimization.md) 生成待采纳方案；报警 RCA 与治理建议属于开放式调查，但不能因为文本出现“报警”或“oncall”就一律调用 `argos run`。

## 结果判断

确认对象类型、metric/Measurement 精确标识、聚合与字段、Tag、tenant、region 和时间窗后再解释曲线。空结果不能直接解释为流量为零；先排查对象混淆、控制面、权限和过滤。固定的元数据→data 多步流程仍是确定性查询；只有下一步需要随证据改变或需要解释/归因时才进入 Argos Agent。
