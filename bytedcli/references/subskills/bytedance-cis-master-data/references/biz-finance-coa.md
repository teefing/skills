# 财务COA段0值 / Finance COA segment zero (`biz-finance-coa`)

## Model selection

Discover cost-center or product/business-line segment-0 values by code or name, or browse the corresponding directory with `md_type=cc` or `md_type=pd`.

`code` and `name` can repeat across `md_type` values. `get` returns one service-selected match; use `mdm_code` to identify a specific row. To retain all matching business-key rows, use `multi-get` or `query` with the requested `md_type` filter. Same-field `batch-get` can return multiple rows per criterion; mixed-field `batch-get` reads one match for each independent criterion.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`, `code`, `name`
- Accepted `query` criterion field sets:
  - `code`
  - `name`
- Fixed `search` fields: `code`, `name`. Pass `--keyword`; do not add a search field.

## Filters, sorting and results

For `multi-get`, `query`, `search`, `list`, documented business filter fields are `md_type`, `code`, `name`, `status`. Use `--filter field=operator:value`; filters are additional AND conditions. A filter does not replace a required query criterion.
Use `equal` or `in` for documented scalar codes and categories, and `contain` for documented text fragments. Other returned fields do not add supported filters.
Keep default sorting. `multi-get`, `query`, `list` support `--sort mdm_code:asc`.
For `search`, omit `--sort` and use `--page` for continuation. With additional filters, search considers at most 512 keyword candidates; `total` reflects the filtered candidate set. Narrow the keyword when needed.
For `list`, a requested projection can use `--return-field` repeatedly with these record fields: `mdm_code`, `code`, `name`, `md_type`, `status`.
Use `list` to browse segment-0 values for the requested `md_type`, optionally filtered by code, name or status.

`query` returns a collection and an optional `next_page_token`. Pass that exact token to `--page-token` for continuation.
`list` supports page or cursor pagination. Use `--page` for a requested page, or pass a returned continuation token to `--page-token`; never combine them. Start with a bounded page size and continue until the requested collection is complete.
`search` returns `total`, `page` and `page_size`; continue with `--page`.
An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data biz-finance-coa get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data biz-finance-coa batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data biz-finance-coa multi-get --field mdm_code --value demo-record-a --value demo-record-b
bytedcli --json cis-master-data biz-finance-coa query --criterion 'code=demo-coa-code' --filter 'md_type=equal:cc' --page-size 20
bytedcli --json cis-master-data biz-finance-coa search --keyword demo-name-fragment --filter 'md_type=equal:cc' --page-size 20
bytedcli --json cis-master-data biz-finance-coa list --filter 'md_type=equal:cc' --page-size 20
```
