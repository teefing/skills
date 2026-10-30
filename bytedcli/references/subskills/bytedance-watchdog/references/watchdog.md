# Watchdog Diag commands

HTTP/FaaS 调用走 `watchdog http execute`；日志检索走 `watchdog log search`。HTTP 请求体为 JSON 对象/数组时编码为 `j`+Base64，普通文本编码为 `s`+原文。ROW 的明文在 `--json data`；合规区 HTTP 仅返回断言或结构，日志无断言时可返回后端允许的 `complianceLogs`。

```bash
bytedcli --json --site i18n-tt watchdog http execute --region sg1 \
  --url https://api.example.com/demo --method GET --query 'id=demo-id'
bytedcli --site us-ttp watchdog http execute --region USTTP \
  --url https://api.example.com/demo --method POST --body-file ./demo-request.json \
  --header 'Content-Type: application/json' --assert 'status = ok'
bytedcli --json --site i18n-tt watchdog log search --region sg1 \
  --psm example.service.api --include-keyword timeout --range 1h
bytedcli --json --site us-ttp watchdog log search --region USTTP --log-id demo-log-id
```

HTTP 的 `--header`、`--query` 和日志的 `--psm`、关键词均可重复；日志也支持 Unix 秒 `--start`/`--end`、AND/OR、`--no-case-sensitive`、`--page-size`（默认 20）。详细参数以命令 `--help` 为准。

BDEE 无法直接调用 US-TTP / EU-TTP 内的 RPC。Diag 在合规区内执行 RPC/DB 并对结果断言。当前命令覆盖 RPC 与 RDS。CLI 按 `--site` / `--region` 自动选择 execute 控制面，不要手写 host。

```bash
bytedcli watchdog region list

# ROW：可读回包，用来对照写 --assert
bytedcli --json --site i18n-tt watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region sg1 \
  --body-file ./demo-request.json

# PPE 泳道
bytedcli --json --site i18n-tt watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region sg1 \
  --env ppe_demo \
  --body-file ./demo-request.json

# 合规区（US-TTP / EU-TTP）：只能断言，不回业务明文；按已知业务预期写断言
bytedcli --site us-ttp watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region useast5 \
  --body-file ./demo-request.json \
  --assert 'VideoDetails.demo-id.EpisodeNum = 1' \
  --assert 'VideoDetails.demo-id.Title = demo-title'
bytedcli --site eu-ttp watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region USEASTRED \
  --vdc useast2b \
  --body-file ./demo-request.json \
  --assert 'VideoDetails.demo-id.IsPreview = true'

# RDS ROW：可读行
bytedcli --json --site i18n-tt watchdog db execute \
  --db-name example_db \
  --region Singapore-Central/alisg \
  --sql 'SELECT id, extra FROM demo_table WHERE id=1'
# RDS 合规区：使用当前 CLI 已收录的 vregion/dc
bytedcli --site us-ttp watchdog db execute \
  --db-name example_db \
  --region US-TTP2/useast8 \
  --sql 'SELECT id, extra FROM demo_table WHERE id=1' \
  --assert 'id = 1' \
  --assert 'extra.multi_language.contract_language = zh'
bytedcli --site eu-ttp watchdog db execute \
  --db-name example_db \
  --region US-EastRed/us_east_gcp \
  --sql-file ./demo.sql \
  --assert 'extra.multi_language.contract_language = zh'
bytedcli --site eu-ttp watchdog db execute \
  --db-name example_db \
  --region EU-TTP2/no1a \
  --sql 'SELECT id FROM demo_table WHERE id=1' \
  --assert 'id = 1'
bytedcli --site eu-ttp watchdog db execute \
  --db-name demo_db \
  --region EU-Compliance2/ie2 \
  --sql 'SELECT 1 AS probe_value' \
  --assert 'probe_value = 1'
```

`--site i18n-tt --region sg1` 走 ROW execute，可返回 `data` 与 `data_outline`。`--site us-ttp` / `--site eu-ttp` 按 region 打对应合规区 execute 平面，JWT 分别用 `us-ttp` / `eu-ttp`，每个 `--assert` 一次 `where` + `fetch`，只回是否命中。断言未命中时命令以 `WATCHDOG_ASSERT_FAILED` 非零退出。`USEASTRED` RPC 必须带 `--vdc useast2b`。`--env ppe_demo` 写入 `Base.TrafficEnv` 和 `x-tt-env` / `x-use-ppe`。请求体用 `api-test gen-request` 生成，不要手写 schema。`--assert` 语法是 `<path> = <value>`，snowflake key 写成 `Map.demo-id.Field` 或 `Map["demo-id"].Field`。`--body` 与 `--body-file` 互斥；`--body-file` 原样编码进 Diag `j`+Base64 request，snowflake ID 保持 JSON number。`--body` 必须是 JSON 对象，不能是数组、null 或标量。

RDS `--region` 推荐使用 `vregion/dc`。当前 CLI 本地收录：`Singapore-Central/alisg`；`US-BOE/boei18n`、`US-Compliance/useast11a`、`US-East/awsvagm`、`US-East/maliva`、`US-East/maliva_sensitive`、`US-East/useastdt`、`US-EastRed/us_east_gcp`、`US-TTP/ova`、`US-TTP2/useast8`；`EU-TTP/ie`、`EU-TTP/iedt`、`EU-TTP2/no1a`、`EU-Compliance2/ie2`。该列表是 CLI 覆盖范围，平台网页提供的区域更多，见下节。

RDS 行是扁平列；带点的 `--assert 'extra.foo = zh'` 表示 `extra` 是 JSON 字符串列，CLI 发 `getFirst` + `getJSON` + `where`。`watchdog db execute` 命中 DB SQL 禁入清单时以 `DB_SQL_BLOCKED` 拒绝。SQL 只允许单条 SELECT / SHOW TABLES / SHOW CREATE TABLE / EXPLAIN SELECT，DML/DDL 以 `RDS_SQL_NOT_READ_ONLY` 拒绝。RPC `--vdc` 只接受该 region 的 VDC 令牌（`useast2b` / `us_east_gcp`），不要把 `USEASTRED` 这类 region 名传给 `--vdc`；`--region us_east_gcp --vdc USEASTRED` 会报错。RDS 的 DC 来自自己的 `--region` 解析，不使用 RPC 的 `--vdc`。

## RDS 网页区域枚举与 CLI 覆盖

Diag 网页的 `VRegion` 选择执行控制面；SQL 查询器的 Region 选择数据库执行区域。已验证在 `VRegion: EU-TTP` 下，`diag.rds.execute({ region: "EU-Compliance2/ie2", ... })` 可以执行原生数据库只读查询与断言。CLI 的 `watchdog db execute` 支持 `--region EU-Compliance2/ie2` 和 `--region ie2`，使用 EU execute 服务和 `eu-ttp` 认证，发送 `vregion: EU-Compliance2`、`dc: ie2`。RPC `--region ie2` 发送的字段是 `vdc: ie2`；两种参数由不同枚举解析。

网页 `VRegion` 下拉框可选：`Singapore-Central`、`Singapore-Compliance`、`MY-Compliance`、`US-EastRed`、`US-East`、`US-TTP`、`US-TTP2`、`EU-TTP`、`EU-TTP2`、`China-North`、`China-BOE`、`US-BOE`。这个控制面列表与 RDS Region 列表不同，不能要求两个选择值同名。

以下清单于 2026-10-28 从 EU-TTP 控制面下的「插入 SQL 查询 → Region」逐项展开读取，共 16 组、24 个选择项；其中 23 项显示 `vregion/dc`，`MY-Compliance` 是未展示 DC 的单层项。CLI 当前收录其中 14 个 `vregion/dc`。网页可选仅说明界面提供该选项；除上述 `EU-Compliance2/ie2` 的已验证结论外，本清单未逐项执行查询，也不代表每个控制面都能执行所有区域或当前账号具备访问权限。

| 网页 Region | 网页 DC / 选择项 | CLI 当前收录的 DC |
| --- | --- | --- |
| `Singapore-Central` | `alisg`、`sg_sensitive`、`sg2`、`sgdt` | `alisg` |
| `Singapore-Compliance` | `awssg`、`awssg_sensitive` | — |
| `MY-Compliance` | 单层选项，未展示 DC | — |
| `US-EastRed` | `us_east_gcp` | `us_east_gcp` |
| `US-East` | `maliva`、`maliva_sensitive`、`useastdt`、`awsvagm` | 全部 |
| `US-TTP` | `ova` | `ova` |
| `US-TTP2` | `useast8` | `useast8` |
| `EU-TTP` | `ie`、`iedt` | 全部 |
| `EU-TTP2` | `no1a` | `no1a` |
| `China-North` | `cn` | — |
| `China-BOE` | `boe` | — |
| `US-BOE` | `boei18n` | `boei18n` |
| `EU-Compliance2` | `ie2` | `ie2` |
| `ID-Compliance` | `id1a` | — |
| `ID-Compliance2` | `id2a` | — |
| `US-Compliance` | `useast11a` | `useast11a` |

### RDS 区域选择与网页入口

1. 查看 `bytedcli watchdog db execute --help` 和 `bytedcli --json watchdog region list`。JSON 的 `regions` 是 RPC 列表，`rds` 是 RDS 列表；按资源类型查看对应列表，确认 CLI 已收录的区域和别名。
2. 若报 `WATCHDOG_INPUT_ERROR` / `Unsupported Watchdog RDS region`，这是请求发出前的本地区域校验。错误 hint 中的区域列表同样来自本地枚举，不能作为平台不支持的证据。核对网页 SQL 查询器的 Region 选择项、生成代码与平台文档，分别确认控制面与数据库执行区域。
3. `EU-Compliance2/ie2` 可直接使用上面的 CLI 示例，`--region ie2` 是同一 RDS 区域的 DC 别名。使用网页时，进入 Watchdog 的 Diag（TTP 交互式诊断）notebook，选择 `VRegion: EU-TTP`；网页脚本调用 `diag.rds.execute` 时传 `region: "EU-Compliance2/ie2"`、`db: "demo_db"`、`sql: "SELECT 1 AS probe_value"`、`args: []`，并通过 `where("probe_value", "=", 1).fetch()` 返回断言结果。该常量查询验证执行链路，业务结论需要已知业务预期的只读查询与断言。
4. 合规区仍只返回断言是否命中，不使用 `fetchRaw()` 获取业务明文。网页入口同样遵守数据库禁入、平台权限和单条只读 SQL 要求；其他区域的执行能力需独立确认，不能通过替换为 `ie` / `no1a` 来验证 `ie2` 的数据库。

## EU RPC 地区与调用方式

RPC 支持 `--region ie2`（`EU-Compliance2`）、`--region ie`（`EU-TTP` / `EUTTP`）、`--region de`（`EU-Compliance`）。CLI 自动发送对应 VDC，并使用 EU execute 服务与 `eu-ttp` 认证；仍只返回断言结果。

`--use-direct-rpc` 是可选的 Watchdog RPC 调用方式开关，对应后端 `useDirectRPC=true`，默认不发送。后端返回 watchman 权限错误且提示 `useDirectRPC=true` 时可尝试启用；它不改变权限要求。若报 `peek instance error: psm instance not found`，检查目标 PSM 在该 region / cluster 是否有部署，不要把 ie、ie2、de 当作可互换别名。预期的业务状态可直接用 `BaseResp.StatusCode` 断言；Diag 执行失败仍然报错。

需要带调用上下文（如商家身份）时用 `--rpc-context key:value:persistent`，可重复，格式同 `api-test rpc-call --rpc-context`，写进 Diag 的 `rpcArgs.headers`。同一字段 5 分钟内的断言次数有上限（数字 10 次，字符串按长度放宽，布尔不限），超限报 `WATCHDOG_RATE_LIMITED`，这条断言没有被判定，等 5 分钟或换字段再断言。

```bash
bytedcli --json --site eu-ttp watchdog rpc execute \
  --psm example.service.api --method DemoMethod \
  --region ie2 --env prod --cluster default \
  --body-file ./demo-request.json \
  --assert 'BaseResp.StatusCode = 110005'
```
