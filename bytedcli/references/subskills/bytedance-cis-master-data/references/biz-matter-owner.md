# 业务事项负责人 / Business matter owner configuration (`biz-matter-owner`)

## Model selection

Read saved owner configuration for a project, budget module and module type. `item_mdm_code` identifies the project in this entry. Use list filters to select that configuration.

Returned owner IDs are stored assignments; the command does not resolve priority or default-owner fallback. Use a configuration record’s `mdm_code` for a specific saved row.

## Methods and fields

- Methods: `get`, `batch-get`, `multi-get`, `list`
- `get`, `batch-get` and `multi-get` fields: `mdm_code`

## Filters, sorting and results

For `multi-get`, `list`, documented business filter fields are `item_mdm_code`, `module_mdm_code`, `module_type`, `status`. Use `--filter field=operator:value`; filters are additional AND conditions.
Use `equal` or `in` for documented scalar codes and categories, and `contain` for documented text fragments. Other returned fields do not add supported filters.
Keep default sorting. `multi-get`, `list` support `--sort mdm_code:asc`.
For `list`, a requested projection can use `--return-field` repeatedly with these record fields: `mdm_code`, `status`, `item_mdm_code`, `module_mdm_code`, `module_type`, `item_owner_id`, `team_owner_id`, `module_owner_id`.
Use `list` to retrieve owner configuration for the requested project, module, module type or status.

`list` supports page or cursor pagination. Use `--page` for a requested page, or pass a returned continuation token to `--page-token`; never combine them. Start with a bounded page size and continue until the requested collection is complete.
An empty result is a valid no-match response. Preserve returned values and permissions; keep the requested model and conditions.

## Examples

```bash
bytedcli --json cis-master-data biz-matter-owner get --field mdm_code --value demo-record-id
bytedcli --json cis-master-data biz-matter-owner batch-get --criterion 'mdm_code=demo-record-a' --criterion 'mdm_code=demo-record-b'
bytedcli --json cis-master-data biz-matter-owner multi-get --field mdm_code --value demo-record-a --value demo-record-b
bytedcli --json cis-master-data biz-matter-owner list --filter 'item_mdm_code=equal:demo-project-mdm-code' --filter 'module_mdm_code=equal:demo-module-mdm-code' --page-size 20
```
