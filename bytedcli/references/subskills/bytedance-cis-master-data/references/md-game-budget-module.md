# 游戏预算模块 / Game budget module (`md-game-budget-module`)

## Model selection

Browse game budget module choices by name, module type, level or leaf flag, or find a parent’s direct children with `parent_mdm_code`. `module_type` and `parent_mdm_code` contain module codes. Read owner configuration separately through `biz-matter-owner`.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `list`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`
- Accepted `query` criterion field sets:
  - `parent_mdm_code`

## Filters, sorting and results

For `multi-get`, `query`, `list`, documented business filter fields are `name`, `parent_mdm_code`, `module_type`, `level`, `is_leaf`, `status`. Use `--filter field=operator:value`; filters are additional AND conditions. A filter does not replace a required query criterion.
Use `equal` or `in` for documented scalar codes and categories, and `contain` for documented text fragments. Other returned fields do not add supported filters.
Keep default sorting. `multi-get`, `query`, `list` support `--sort mdm_code:asc`.
For `list`, a requested projection can use `--return-field` repeatedly with these record fields: `name`, `module_type`, `level`, `is_leaf`, `remark`, `mdm_code`, `parent_mdm_code`, `status`.
Use `list` to browse budget module choices within the requested name, parent, module type, level, leaf flag or status.

`query` returns a collection and an optional `next_page_token`. Pass that exact token to `--page-token` for continuation.
`list` supports page or cursor pagination. Use `--page` for a requested page, or pass a returned continuation token to `--page-token`; never combine them. Start with a bounded page size and continue until the requested collection is complete.
An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data md-game-budget-module get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data md-game-budget-module batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data md-game-budget-module multi-get --field mdm_code --value demo-record-a --value demo-record-b
bytedcli --json cis-master-data md-game-budget-module query --criterion 'parent_mdm_code=demo-parent-mdm-code' --page-size 20
bytedcli --json cis-master-data md-game-budget-module list --filter 'module_type=equal:demo-module-type' --filter 'name=contain:demo-module-name' --page-size 20
```
