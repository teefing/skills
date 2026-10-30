# 行业分类 / Industry classification (`biz-industry`)

## Model selection

Browse industry classifications, or query a parent’s direct children using `parent_mdm_code`. When requested, `brand=0` selects 飞书 and `brand=1` selects Lark. Records are returned as rows; use their parent codes to interpret the hierarchy.

`name_i18n` and `remark_i18n` are serialized multilingual strings in the result. Preserve their contents when interpreting the returned names and descriptions.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `list`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`
- Accepted `query` criterion field sets:
  - `parent_mdm_code`

## Filters, sorting and results

For `multi-get`, `query`, `list`, documented business filter fields are `code`, `parent_mdm_code`, `brand`, `level`, `status`. Use `--filter field=operator:value`; filters are additional AND conditions. A filter does not replace a required query criterion.
Use `equal` or `in` for documented scalar codes and categories, and `contain` for documented text fragments. Other returned fields do not add supported filters.
Keep default sorting. `multi-get`, `query`, `list` support `--sort mdm_code:asc`.
For `list`, a requested projection can use `--return-field` repeatedly with these record fields: `mdm_code`, `status`, `name_i18n`, `code`, `parent_mdm_code`, `level`, `remark_i18n`, `order_code`, `brand`.
Use `list` to browse the industry classification directory, selecting the requested business code, parent, brand, level or status.

`query` returns a collection and an optional `next_page_token`. Pass that exact token to `--page-token` for continuation.
`list` supports page or cursor pagination. Use `--page` for a requested page, or pass a returned continuation token to `--page-token`; never combine them. Start with a bounded page size and continue until the requested collection is complete.
An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data biz-industry get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data biz-industry batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data biz-industry multi-get --field mdm_code --value demo-record-a --value demo-record-b
bytedcli --json cis-master-data biz-industry query --criterion 'parent_mdm_code=demo-parent-mdm-code' --page-size 20
bytedcli --json cis-master-data biz-industry list --filter 'brand=equal:0' --filter 'status=equal:1' --page-size 20
```
