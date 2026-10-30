# 利率 / Interest Rate (`biz-interest-rate`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`
- Exact lookup field: `mdm_code`
- Accepted `query` criterion field sets:
  - `mdm_code`
  - `identifier,price_type` with the latest-value constraints below
  - `identifier,price_type,value_ts`
- `search` and `list` are not exposed for this model.

Use `identifier`, `price_type` and `value_ts` together to retrieve a stored record at an exact
timestamp. Ask for missing values; do not guess a price type or time.

For the latest effective stored rate, provide `identifier,price_type` together with
`--filter status=equal:1`, `--sort value_ts:desc` and an explicit `--page-size 1`.
For the latest effective record on or before a timestamp, also add
`--filter value_ts=lte:<as-of-timestamp>`. Preserve the supplied values and report an empty result
when no stored record matches; do not invent a rate or replace the effective-state condition.

These constraints are required for a latest-value lookup. Neither a small page alone nor a sort
alone enables an unbounded historical series. Do not enumerate timestamps to assemble history.
On timeout, preserve the error and request identifier without automatic retries or scope changes.
Latest-value queries return the first record only and do not accept a continuation token.

## Interpreting Reference Codes

A returned `ir_mdm_code` refers to the separate 货币代码 data object, not 币种 (`ref-currency`).
Use the returned `ir_mdm_code` unchanged with `ref-currency-code get --field mdm_code` to read
that reference record. Do not use it with `ref-currency` or infer the reference name from the code.
Use `identifier` only as documented below.

## Examples

```bash
bytedcli --json cis-master-data biz-interest-rate get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-interest-rate query \
  --criterion 'identifier=<rate-identifier>' \
  --criterion 'price_type=<price-type>' \
  --criterion 'value_ts=<value-timestamp>'
bytedcli --json cis-master-data biz-interest-rate query \
  --criterion 'identifier=<rate-identifier>' --criterion 'price_type=<price-type>' \
  --filter status=equal:1 --sort value_ts:desc --page-size 1
```

Use exactly one documented criterion field set. Do not substitute `list` for a missing or incomplete
documented query criterion.
