# 汇率 / Exchange Rate (`biz-exchange-rate`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`
- Exact lookup field: `mdm_code`
- Accepted `query` criterion field sets:
  - `mdm_code`
  - `date,rate_type`
  - `x_currency,y_currency` with the latest-value constraints below
  - `x_currency,y_currency,date`
  - `x_currency,y_currency,date,rate_type`
- `search` and `list` are not exposed for this model.

## Query scope

For a stored point lookup, provide both currencies and the effective date; add `rate_type` when
that category is requested. Reuse a returned `mdm_code` for a specific record.

For the most recent stored rate of a known pair and rate type on or before a supplied date, use
both currency criteria, `--filter date=lte:<as-of-date>`, `--filter rate_type=equal:<rate-type>`,
`--sort date:desc` and `--page-size 1` together. This selects a stored record; it does not fabricate
a rate when none exists or reproduce automatic type-priority selection.
Latest-value queries return the first record only and do not accept a continuation token.

For the stored daily collection of a specified rate type, provide `date,rate_type` together.
Return all matching currency pairs in that collection and follow its returned pagination.
Do not invent a type or silently choose a preferred one when the user asks for all types.

All-type daily collections, base-currency collections and date-range history are unavailable.
A small page, date filter or sort alone does not enable those collections.
Do not invent dates, enumerate currency pairs or time points, or scan directories to assemble them.
Ask for missing point or latest-value inputs only when the user wants that supported task.
On timeout, preserve the error and request identifier without automatic retries or scope changes.

## Examples

```bash
bytedcli --json cis-master-data biz-exchange-rate get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-exchange-rate query \
  --criterion 'x_currency=<base-currency-code>' \
  --criterion 'y_currency=<quote-currency-code>' \
  --criterion 'date=<effective-date>' \
  --criterion 'rate_type=<rate-type>'
bytedcli --json cis-master-data biz-exchange-rate query \
  --criterion 'date=<effective-date>' --criterion 'rate_type=<rate-type>'
bytedcli --json cis-master-data biz-exchange-rate query \
  --criterion 'x_currency=<base-currency-code>' --criterion 'y_currency=<quote-currency-code>' \
  --filter 'date=lte:<as-of-date>' --filter 'rate_type=equal:<rate-type>' \
  --sort date:desc --page-size 1
```
