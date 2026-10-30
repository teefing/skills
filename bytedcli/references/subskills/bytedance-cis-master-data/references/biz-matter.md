# 业务事项 / Business matter (`biz-matter`)

## Model selection

Search multilingual business-matter name fragments or browse the business-matter hierarchy. Use the list filters to select a business code, parent business code, level or status. `parent_code` is a business code, distinct from a record MDM ID.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`, `search`, `list`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`
- Fixed `search` fields: `name`. Pass `--keyword`; do not add a search field.

## Filters, sorting and results

For `multi-get`, `search`, `list`, documented business filter fields are `code`, `parent_code`, `level`, `status`. Use `--filter field=operator:value`; filters are additional AND conditions.
Use `equal` or `in` for documented scalar codes and categories, and `contain` for documented text fragments. Other returned fields do not add supported filters.
Keep default sorting. `multi-get`, `list` support `--sort mdm_code:asc`.
For `search`, omit `--sort` and use `--page` for continuation. With additional filters, search considers at most 512 keyword candidates; `total` reflects the filtered candidate set. Narrow the keyword when needed.
For `list`, a requested projection can use `--return-field` repeatedly with these record fields: `mdm_code`, `status`, `name`, `code`, `parent_code`, `remark`, `level`, `sort`.
Use `list` to browse business matters within the requested code, parent business code, level or status.

`list` supports page or cursor pagination. Use `--page` for a requested page, or pass a returned continuation token to `--page-token`; never combine them. Start with a bounded page size and continue until the requested collection is complete.
`search` returns `total`, `page` and `page_size`; continue with `--page`.
An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data biz-matter get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data biz-matter batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data biz-matter multi-get --field mdm_code --value demo-record-a --value demo-record-b
bytedcli --json cis-master-data biz-matter search --keyword demo-name-fragment --page-size 20
bytedcli --json cis-master-data biz-matter list --filter 'parent_code=equal:demo-parent-code' --page-size 20
```
