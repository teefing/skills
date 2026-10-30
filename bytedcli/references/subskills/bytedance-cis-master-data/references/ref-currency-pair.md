# 币种对 / Currency pair (`ref-currency-pair`)

## Model selection

Read a configured currency-pair record by `mdm_code`. Returned `x_currency` and `y_currency` identify its two sides. `pair_type` is a serialized JSON array string; parse it when interpreting the record.

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
bytedcli --json cis-master-data ref-currency-pair get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data ref-currency-pair batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data ref-currency-pair multi-get --field mdm_code --value demo-record-a --value demo-record-b
```
