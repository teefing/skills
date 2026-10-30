# 平均预估汇率 / Average forecast exchange rate (`biz-avg-exchange-rate-forecast`)

## Model selection

Read stored forecast average-rate records by known `mdm_code`. Returned `start_at` and `end_at` describe the saved interval and currently use Unix milliseconds. Preserve the returned values. This entry reads saved records without calculating a forecast.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`

## Filters, sorting and results

For `multi-get`, documented business filter fields are `status`. Use `--filter field=operator:value`; filters are additional AND conditions.
Use `equal` or `in` for the requested status. Other returned metadata does not add lookup or filter fields.
Keep default sorting. `multi-get` supports `--sort mdm_code:asc`.

An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data biz-avg-exchange-rate-forecast get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data biz-avg-exchange-rate-forecast batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data biz-avg-exchange-rate-forecast multi-get --field mdm_code --value demo-record-a --value demo-record-b
```
