# 实体别名 / Entity alias (`biz-entity-alias`)

## Model selection

Read saved bank-name alias mappings or list the alias dictionary for name replacement. Each record contains a stored `name` and `alias` pair. Use the documented list filters to limit the mappings to a requested name or alias.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`, `list`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`

## Filters, sorting and results

For `multi-get`, `list`, documented business filter fields are `name`, `alias`, `status`. Use `--filter field=operator:value`; filters are additional AND conditions.
Use `equal` or `in` for documented scalar codes and categories, and `contain` for documented text fragments. Other returned fields do not add supported filters.
Keep default sorting. `multi-get`, `list` support `--sort mdm_code:asc`.
For `list`, a requested projection can use `--return-field` repeatedly with these record fields: `mdm_code`, `name`, `alias`, `status`.
Use `list` to retrieve the bank-name replacement dictionary, optionally limited by `name`, `alias` or `status`.

`list` supports page or cursor pagination. Use `--page` for a requested page, or pass a returned continuation token to `--page-token`; never combine them. Start with a bounded page size and continue until the requested collection is complete.
An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data biz-entity-alias get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data biz-entity-alias batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data biz-entity-alias multi-get --field mdm_code --value demo-record-a --value demo-record-b
bytedcli --json cis-master-data biz-entity-alias list --filter 'name=contain:demo-bank-name' --page-size 20
```
