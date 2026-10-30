# Grafana

## V7 取数契约与入口选择

| 入口 | HTTP 200 业务错误 | 回退条件 |
| --- | --- | --- |
| `grafana data --url <url>` | 原始 payload 不变；CLI 外层 success、exit 0；MCP `isError: false` | OpenAPI 请求抛错（网络/HTTP 非 2xx）且 URL 带 `viewPanel` / `panelId` 时直连 |
| `grafana screenshot --only-data --url <url>` | 同样原样返回 | V7 不使用 `data` 的直连回退 |
| `grafana query <url-or-uid> --panel <id>` | 识别非零数值 `code` 或数值 `status >= 400`，尝试既有回退 | 通常为 OpenAPI → Byteplot → direct；已知 panel / 优先 Byteplot 特例保留原路由 |
| `grafana panel query --uid <uid> --panel-id <id>` | 直接查询 datasource | 适用于已知 gateway 不可达的网络，避免等待 gateway 超时 |

例如 OpenAPI 返回 HTTP 200 与 `{code:-1,status:500,msg:"no JSON data collected"}` 时，V7 `data` 的 CLI JSON 外层仍为 `status: "success"`、`error: null`，MCP proxy `run_command` 与具名 `grafana_data` 均为 `isError: false`。这些信号表示命令成功返回了 raw payload，不保证业务取数成功；应检查该 payload 的 `code/status/msg`，不能据此触发额外请求。相同规则适用于数值 `status >= 400` 的 payload。

`{code:0,count:0,total:[]}` 是合法零行成功；不要把空结果当作业务错误。普通非空成功结果也保持原样返回。需要识别业务错误并恢复时选择 `query`；V7 全部路径失败时，业务错误保留 `GRAFANA_OPENAPI_ERROR` 和原消息，网络/HTTP 错误保留原错误码与消息，`details.fallback` 补充失败路径。`data` 无 panel 时仅报原请求错误，不尝试直连。

直连成功继续返回 `data.source: "grafana_ds"`、`data.query_api: "tsdb"`。部分 datasource 失败时，`query/data` 返回其余 datasource 的结果，`data.failed_datasources` 列出失败信息，文本另提示未应答的 datasource；`panel query` 对任一 datasource 失败报错。V10 使用既有版本路由，不套用 V7 raw 契约。

## 版本、命令与输出

所有 Grafana leaf command 都支持 `--grafana-version <v7|v10>`。不传时保持 V7；完整 URL 的 allowlist host 会自动推断实例，`grafana.byted.org` / `grafana-i18n.byted.org` 的路径带 `/v10/`（如 `grafana.byted.org/v10/d/...`、`grafana-i18n.byted.org/v10/d/...`）时推断 V10（`grafana-10.bytedance.net` 本身即 V10），其他 allowlist host 带 `/v10/` 路径报 `GRAFANA_SITE_UNSUPPORTED`。URL host 与 flag 冲突时报 `GRAFANA_INPUT_ERROR`，未知 URL host 报 `GRAFANA_SITE_UNSUPPORTED`。V10 支持 `--site cn` 与 `--site i18n-tt`：i18n V10 与 V7 共用 `grafana-i18n.byted.org`、挂在 `/v10` 路径下，且仅办公网可用（生产网域名 `grafana-i18n-api.byted.org` 没有 `/v10` 路由）。

i18n `/v10` URL 对直连 API 的命令（`dashboard` / `group` / `panel` / `variable` / `link` / `inject-metrics-links` / `info` / `search`）直接生效。OpenAPI 网关不识别 `/v10`，仍按 URL host / 全局 `--site` 选择网关，因此纯 OpenAPI 命令 `dashboard describe`、`expr-parse` 与普通 `screenshot` 会报 `Dashboard not found`；`data`、顶层 `query`、`screenshot --only-data` 同样先收到该 OpenAPI 错误，随后回退到 V10 直连 datasource（`/api/ds/query` 或 OpenTSDB proxy），文本面板等没有可查 target 的面板返回 `GRAFANA_V10_OPENAPI_UNSUPPORTED`（`details.direct.code` 为 `GRAFANA_INPUT_ERROR`）。

直连 Grafana API 的命令支持 `--grafana-url <origin>` 覆盖请求地址，并要求用 `--grafana-version v7|v10` 显式选择最接近的官方 API 协议族。folder 默认值和 JWT 站点默认沿用 `--grafana-version` / 全局 `--site` 的既有逻辑；`--grafana-url` 命中已知 v10 host 时 JWT 随 host 推导（`grafana-10.bytedance.net` / `grafana.byted.org` → cn，共享 i18n host 默认 i18n-bd，`--site i18n-tt` 时为 i18n-tt）。对 v10 挂在 `/v10` 前缀下的 host（`grafana-i18n.byted.org`、`grafana.byted.org`），传 `--grafana-version v10` 时会自动补 `/v10`；生产网别名 `grafana-i18n-api.byted.org` 没有 `/v10` 路由，直接报 `GRAFANA_SITE_UNSUPPORTED`；其余自定义 origin 按传入地址原样使用。只接受无路径、query、fragment、credentials 或自定义端口的内部 HTTPS origin；同时传 dashboard URL 时两者 origin 必须一致。OpenAPI 命令 `dashboard describe`、顶层 `query`、`screenshot`、`data`、`expr-parse` 不支持该参数。

```bash
# V7 默认调用
bytedcli --json grafana search "demo service"
bytedcli --json grafana info "demo-uid"
bytedcli --json grafana query "demo-uid" --panel 123 --from now-30m --to now --var dc=hl

# 自定义内部实例：仅用于直连 API 命令
bytedcli --site cn --json grafana dashboard get --uid "demo-uid" --grafana-url "https://grafana-team.example.byted.org" --grafana-version v10
bytedcli --site cn --json grafana panel query --uid "demo-uid" --panel-id 123 --grafana-url "https://grafana-team.example.byted.org" --grafana-version v10

# V10：仅有 UID、search 或 create 时显式选择版本
bytedcli --json grafana search "demo service" --grafana-version v10
bytedcli --json grafana dashboard get --uid "demo-uid" --grafana-version v10
bytedcli grafana dashboard create --title "demo-v10-dashboard" --folder-uid "demo-folder-uid" --grafana-version v10

# V10：完整 dashboard/panel URL 自动推断
bytedcli --json grafana info "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?var-dc=lf"
bytedcli --json grafana dashboard describe --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug"

# V10：i18n（/v10 路径前缀，仅办公网）
bytedcli --site i18n-tt --json grafana dashboard get --uid "demo-uid" --grafana-version v10
bytedcli --json grafana info "https://grafana-i18n.byted.org/v10/d/demo-uid/demo-slug?orgId=1"

# Dashboard
bytedcli grafana dashboard get --uid "demo-uid"
bytedcli grafana dashboard create --title "demo-dashboard"
bytedcli grafana dashboard update --uid "demo-uid" --title "demo-updated"
bytedcli grafana dashboard delete --uid "demo-uid"

# Group
bytedcli grafana group list --uid "demo-uid"
bytedcli grafana group create --uid "demo-uid" --title "demo-group"
bytedcli grafana group get --uid "demo-uid" --group-title "demo-group"
bytedcli grafana group update --uid "demo-uid" --target-group-title "demo-group" --title "demo-renamed"
bytedcli grafana group delete --uid "demo-uid" --group-title "demo-group"

# Panel：V7 新建默认 graph；V10 新建默认 timeseries
bytedcli grafana panel list --uid "demo-uid"
bytedcli grafana panel get --uid "demo-uid" --panel-id 123
bytedcli grafana panel create --uid "demo-uid" --panel-json '{"title":"demo-panel","type":"graph"}'
bytedcli grafana panel create --uid "demo-uid" --grafana-version v10 --panel-json '{"title":"demo-timeseries","datasource":{"type":"demo-sql","uid":"demo-ds-uid"},"options":{"legend":{"displayMode":"table","placement":"bottom"}}}'
bytedcli grafana panel update --uid "demo-uid" --panel-id 123 --panel-json '{"title":"demo-updated"}'
bytedcli grafana panel delete --uid "demo-uid" --panel-id 123

# Panel query：V7 的 SQL 与 OpenTSDB 指标 panel 都走 /api/tsdb/query；V10 普通 datasource /api/ds/query，OpenTSDB UID proxy
bytedcli --json grafana panel query --uid "demo-uid" --panel-id 123 --from now-1h --to now --var applicationId=application_demo_123
bytedcli --json grafana panel query --uid "demo-uid" --panel-id 123 --grafana-version v10 --from now-1h --to now

# Variable / link
bytedcli grafana variable get --uid "demo-uid"
bytedcli grafana variable update --uid "demo-uid" --variables-json '[{"name":"interval","type":"custom","query":"30s,1m,5m"}]'
bytedcli grafana link get --uid "demo-uid"
bytedcli grafana link update --uid "demo-uid" --links-json '[{"title":"demo-link","url":"https://example.com","targetBlank":true}]'

# Tools
bytedcli grafana inject-metrics-links --uid "demo-uid"
bytedcli grafana data --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?viewPanel=123"
bytedcli grafana screenshot --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug?viewPanel=123"
bytedcli grafana expr-parse --url "https://grafana-10.bytedance.net/d/demo-uid/demo-slug"
```

- V7 create 未传 folder 时继续使用 site 默认 `folderId`。V10 未传时使用 root folder；可传 `--folder-uid` 或 `--folder-id`，二者不能同时使用。
- V10 panel datasource `{type,uid}`、`options.legend`、targets、field overrides 与未知字段会按 dashboard JSON 原样保留。读取已有 graph panel 后更新不会强制迁移为 timeseries。
- `grafana data` 在 V10 公司 OpenAPI data 不兼容时读取 panel 与真实 datasource type：普通 datasource 回退到 `/api/ds/query`，OpenTSDB/ByteTSD 直接走 `/api/datasources/proxy/uid/<uid>/api/query`，不会先探测 `/api/ds/query`，也不会切到 V7。
- V7 实例上，`grafana query`（OpenAPI 报错或返回错误结果、且 Byteplot 回退也不可用之后）与 `grafana data`（OpenAPI 请求报错且 URL 带 panel ID）直连 `/api/tsdb/query`：`data.source` 为 `grafana_ds`、`data.query_api` 为 `tsdb`；target 分布在多个 datasource 的 panel 多一列 `datasource`，部分 datasource 未应答时返回其余 datasource 的数据，并在 `data.failed_datasources` 列出未应答的。全部路径都失败时仍返回 OpenAPI 的错误，`details.fallback` 带各回退路径的失败原因。
- `grafana panel query` 的 `query_api` 为 `tsdb`、`ds` 或 `opentsdb_proxy`，并提供 `datasource_uid`、`datasource_type`、`columns`、`column_names`、`row_count`。V7 的 OpenTSDB/ByteTSD 指标 target 经 `/api/tsdb/query` 查询（`query_api` 为 `tsdb`），输出与 OpenTSDB proxy 相同的 `time`/`value`/`metric`/`tags`/`aggregate_tags`/`series` 长表列；未用 `--var` 传入的模板变量取 dashboard 当前值，仍无法解析时返回 `GRAFANA_VARIABLE_UNRESOLVED`；target 分布在多个 datasource 的 panel 按 datasource 分别查询，结果多一列 `datasource` 标明每行的来源（此时顶层 `datasource` / `datasource_id` 为 `null`），任一失败时返回 `GRAFANA_TSDB_ERROR`，可用 `--datasource <name>` 只查其中一个；这类 panel 上的 `--datasource-id` 或不属于该 panel 的 `--datasource` 返回 `GRAFANA_INPUT_ERROR`。OpenTSDB proxy 的 HTTP 200 + 空 series 是成功零行结果；鉴权、HTTP 查询和 response schema 错误分别返回结构化错误。
