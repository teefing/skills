# 预算/滚测汇率 / Budget and rolling forecast exchange rate (`biz-budget-exchange-rate`)

## Model selection

Find a stored budget or rolling-forecast rate using both currencies, the calculation month and the requested scene. All four criteria are required. `year` is an additional filter and does not replace `month`.

`month` is the unpadded calendar month `1` through `12`; January is `1`. For a requested year, add `--filter 'year=equal:2026'` with that year. The scene codes are `Annual` (年度预算), `RM04` (滚动预测M4), `RM07` (滚动预测M7) and `RM10` (滚动预测M10). Preserve the requested scene; do not select one by default. The command returns stored rates without calculating a new rate.

`x_currency` is the source currency code and `y_currency` is the target currency code, for example `USD` and `CNY`. Use the exact currency `code`; when only a currency name is known, resolve it through `ref-currency` and take the returned `code`.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`, `query`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`
- Accepted `query` criterion field sets:
  - `x_currency,y_currency,month,scene`

## Filters, sorting and results

For `multi-get`, `query`, documented business filter fields are `scene`, `year`, `status`. Use `--filter field=operator:value`; filters are additional AND conditions. A filter does not replace a required query criterion.
Use `equal` or `in` for documented scalar codes and categories, and `contain` for documented text fragments. Other returned fields do not add supported filters.
Keep default sorting. `multi-get`, `query` support `--sort mdm_code:asc`.

`query` returns a collection and an optional `next_page_token`. Pass that exact token to `--page-token` for continuation.
An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data biz-budget-exchange-rate get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data biz-budget-exchange-rate batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data biz-budget-exchange-rate multi-get --field mdm_code --value demo-record-a --value demo-record-b
bytedcli --json cis-master-data biz-budget-exchange-rate query --criterion 'x_currency=USD' --criterion 'y_currency=CNY' --criterion 'month=1' --criterion 'scene=Annual' --filter 'year=equal:2026' --page-size 20
```
