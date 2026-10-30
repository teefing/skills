# 预算科目扩展 / Budgetary Account Extension (`biz-budgetary-account`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`
- `get` fields: `mdm_code`
- `batch-get` and `multi-get` fields: `mdm_code`
- Accepted single-field `query` criterion: `mdm_code`.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Basic and Extended Information

预算科目扩展 and [预算科目](md-budgetary-account.md) describe the same business object and share its query permission. Use the same returned `mdm_code` to read the other entry. When only a basic-information name is known, locate the basic information first and reuse its returned code.

For a budgetary-account lookup, discover the intended account through its basic name or code and
reuse its `mdm_code` for extension details. Keep that identity when the user requests several
extension fields; do not construct text criteria or probe records with an empty value.
Read `oa_remark` from the returned extension details.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

Use the basic budgetary-account entry for name discovery, then read this entry by its returned `mdm_code`.

## Examples

```bash
bytedcli --json cis-master-data biz-budgetary-account get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-budgetary-account batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data biz-budgetary-account multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data biz-budgetary-account query --criterion 'mdm_code=<master-data-code>'
```
