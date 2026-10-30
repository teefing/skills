# 利率代码 / Interest rate code (`ref-interest-rate-code`)

## Model selection

Read interest-rate code definitions by known `mdm_code`. Returned `identifier`, `ccy`, `type`, `tenor` and multilingual `name` describe the definition. Keep this model separate from interest-rate values and the 货币代码 entry.

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
bytedcli --json cis-master-data ref-interest-rate-code get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data ref-interest-rate-code batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data ref-interest-rate-code multi-get --field mdm_code --value demo-record-a --value demo-record-b
```
