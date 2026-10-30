# 成本中心_费用类型表 / Cost center fee type calculation (`biz-cost-center-fee-type-ratio`)

## Model selection

Read saved fee-type calculation, comparison and manual-confirmation records. The record’s `mdm_code` identifies the calculation record; returned `cc_mdm_code` identifies its cost center. When the cost center `mdm_code` is known, use `query --criterion cc_mdm_code=<cost-center-mdm-code>` to find its calculation/review records. Then use each returned record’s own `mdm_code` to read its details. Do not pass a cost center ID as the calculation record ID.

For the cost center’s effective `fee_type`, use `biz-cost-center get --field mdm_code --value <returned cc_mdm_code>`.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`, `query`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`
- `query` criterion field set: `cc_mdm_code`

A cost center lookup returns a collection, not a promised single record. Keep all matches. To retrieve all matching records, repeat the same query and conditions with `--page-token` set to the returned `next_page_token`, until no token is returned. Do not fabricate a token or call the first page complete. Directory `list` and name `search` are not exposed.

## Filters, sorting and results

For `query` and `multi-get`, documented business filter fields are `cc_mdm_code`, `is_agg_cc`, `fee_type`, `manual_confirm`, `status`. Use `--filter field=operator:value`; filters are additional AND conditions.
Use `equal` or `in` for documented scalar codes and categories, and `contain` for documented text fragments. Other returned fields do not add supported filters.

Filter values: `manual_confirm`（人工确认）and `is_agg_cc`（聚合成本中心）use `0=否`, `1=是`. For 已人工确认, add `--filter 'manual_confirm=equal:1'`. `fee_type` uses `2=销售部门`, `3=管理部门`, `4=成本部门`, `5=研发1部门`, `6=研发2部门`. These values filter saved calculation/review records; they do not change the lookup criterion.

Keep default sorting. `query` and `multi-get` support `--sort mdm_code:asc`.

An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data biz-cost-center-fee-type-ratio get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data biz-cost-center-fee-type-ratio batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data biz-cost-center-fee-type-ratio multi-get --field mdm_code --value demo-record-a --value demo-record-b
bytedcli --json cis-master-data biz-cost-center-fee-type-ratio query --criterion 'cc_mdm_code=demo-cost-center-mdm-code' --page-size 20
```
