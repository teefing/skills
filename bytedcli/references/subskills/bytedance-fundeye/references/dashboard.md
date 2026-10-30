# FundEye 驾驶舱详情

三个只读命令：

```bash
bytedcli --json fundeye dashboard rule-quality list --business-line-id demo-biz --start-date 2026-10-12 --end-date 2026-10-12 --product '["fullink","tcheck"]' --priority '["P1"]' --issue-type runtime-failure --owner demo-owner
bytedcli --json fundeye dashboard alarm-rule list --business-line-id demo-biz --start-date 2026-10-12 --end-date 2026-10-25 --receiver demo-receiver --sort process-rate --order asc
bytedcli --json fundeye dashboard alarm-record list --business-line-id demo-biz --start-date 2026-10-12 --end-date 2026-10-25 --rule-id demo-rule --rule-version v3 --sub-rule-id 'edge_seq=2' --sub-rule-type DOUBLE_DS_CHECK --status pending --full
```

## 共同约定

- `--business-line-id`、`--start-date`、`--end-date` 必填，字符串不能为空。日期使用有效 YYYY-MM-DD，起止有序，最多 365 个自然日；这不是历史保留期承诺。
- 全部请求固定包含所有子业务线；不能通过原始 JSON、文件、header 或 flag 修改查询上下文。
- `--product` 为一次 JSON string[]：`fullink/tcheck/state`；`--priority` 为一次 JSON string[]：`P0/P1/P2`。省略或 `[]` 表示全部，重复 flag 报错。
- 其他多选参数重复 flag，每次一项，自动去重；可选多选的空条件表示不限。
- `--page` 为 1..1001，默认 1，每页固定 10，offset=(page-1)*10。没有自动全量、page-size、has_more 或客户端过滤。
- 仅支持 CN、ByteDance 个人用户身份，JWT 与用户名来自同一身份；省略 `--as` 或显式使用 `--as user`。全局非 CN / app / AI Auth / 显式 `--as auto` 明确拒绝。无 OpenAPI token、固定 token 或其他认证回退。
- 全局 `--json` 使用统一结果信封；`--full` 只扩展输出，不修改请求、分页、身份或额外查询。

## 三类独立参数

| 命令 | 除共同 6 项业务参数之外的参数 |
| --- | --- |
| rule-quality | `--issue-type high-noise/runtime-failure/delivery-failure`；可重复 `--owner`；`--sort issue-count/recurrence-count`（默认 issue-count）；`--order asc/desc`（默认 desc） |
| alarm-rule | `--rule-id`、`--rule-version`、`--sub-rule-id`、`--sub-rule-type`；可重复 `--status pending/handled`；`--timely-status met/unmet`；可重复 `--reason-level-1`、`--reason-level-2`、`--receiver`（告警接收人）；`--sort alarm-count/alarm-days/process-rate/timely-rate`（默认 alarm-count）；`--order asc/desc`（默认 desc） |
| alarm-record | 与 alarm-rule 相同的身份、状态、及时、原因、接收人筛选，但无 `--sort` / `--order` |

三条命令分别有 10/17/15 个业务 flag，另有 `--full`。版本允许 `3` 或 `v3`，范围 0..9223372036854775807，无损发送 JSON i64 数字；子规则 ID 和类型直接使用返回值，不能猜测枚举或去掉 `edge_seq=` 等前缀。两个原因级别是独立集合，不按位置配对。

两个告警命令均不支持 `--handler`；`handler` 仅为单条告警的可选输出字段。

不支持 date-dimension、week-start、focus-period-key、change-type、latest-publisher-keyword、issue-keyword、issue-reason、sitename、region、querycontext 或原始请求覆盖。

## 当前后端能力限制

1. **规则质量仅单日可用**：`start-date` 必须等于 `end-date`。已核验的线上 SQL 仍按选中周期取问题，跨日范围会漏掉窗口中后部问题，CLI 因此拒绝跨日。多日全窗口质量尚不能上线。
2. **规则告警状态筛选不可用**：线上 SQL/服务链路未贯通状态参数。传非空 `--status` 会报错；单条告警的状态筛选正常可用。
3. **规则告警天数排序不可用**：线上 SQL 没有计算 alarm_days，也不支持该排序。`--sort alarm-days` 会报错；输出保留服务端的 `alarm_days=0`，不能解释成真实零天。
4. **及时归因条件受生效配置限制**：只有传 `--timely-status` 才读取定义；只有启用 RULE（1）维度才允许筛选。ALARM-only（2）明确报错，不改配置、不静默删参数。

两个告警内部固定 DAY=1，不公开周期参数；同一日期范围的 DAY/WEEK 真实对照一致。

## 返回值

统一 `status/data/error/context`。成功数据为 `items`、字符串 `total`、`page`、`page_size=10`、`data_state`、可选 `snapshot_date`。状态 ready/empty/partial/unknown 直接映射上游；缺失快照不以请求日期补齐。HTTP 200 的业务拒绝仍为标准错误和非零退出。

默认规则结构 `rule` 展平 `rule_detail.rule_key`，保留 product_type、rule_id、rule_version、sub_rule_type、sub_rule_id 和实际 business_line_id（可能属于子业务线），不按名称或规则 ID 去重。count/total/i64/时间为十进制字符串；rates 保留上游数值与尺度。

响应可选字段兼容省略和 `null`，统一视为缺失，不影响同页其他条目。后端 IDL 的必填字段（包括 issue_reason、process_rate、原因聚合 rate、alarm_order_id、send_time_ms、is_attributed、diff_url）仍严格校验；缺失、`null` 或类型错误返回 `FUNDEYE_DASHBOARD_PARSE_ERROR`，不丢弃条目或补造事实。空字符串、0 和 false 按契约保留。

- 质量：保留全部 issue_detail、error_message、permission_resource_list、issue_reason、复发字段及问题段起止和次数。缺失可选字段不补 0/false。质量 total 是过滤后分页前的源规则执行单元数，不是唯一 rule_id 数；issue 展开后 items 数可能不同。超出页时服务端 total 可能退回 0，CLI 不重算。复发和 episode 限查询窗口。
- 规则告警：保留次数、天数、处理/待处理次数和处理率、及时指标及 eligibility 布尔值、接收人和原因聚合，不根据单条告警重算。process_rate 为百分数，终端直接附加 `%`，JSON 保留原始数值。线上 SQL 按产品/规则/子规则/优先级聚合；未指定版本时可累计多个版本，返回 rule_version 为其中最新版本，不能把全部次数解释成只属于该版本。需要按版本与单条告警对照时，两个命令都显式传相同 --rule-version。
- 单条告警：保留身份、发送/归因时间、归因状态、及时 eligibility/status、接收人、handler、独立原因列表/名称、耗时、diff_url。reason_level_1_list 和 reason_level_2_list 在默认与 full 输出中始终为 string[]：非空新原因列表优先，否则非空旧单值作为单元素列表；无原因统一为 `[]`。
- full：增加规则 latest_publisher、质量 suggestion、episode_id/period_label、matched_period_label_list、告警原始单值原因、上游存在时的 data_state_code、规范化逻辑输入 context.request。共同字段路径和值保持一致；full 也不输出凭据、headers、后端信封或未知原始字段。
- 终端默认显示重点列、total、实际快照和部分状态提醒；完整事实使用 `--json`，或终端 `--full`。
