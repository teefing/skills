# 总账侧业务线 / General-Ledger Business Line (`biz-financial-report-business-line`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `list`
- `get` fields: `mdm_code`
- `batch-get` and `multi-get` fields: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`. Choose exactly one per query; do not combine these fields.

Prefer a returned `mdm_code` to identify a specific record. `get` returns one matching record; use `query` or `multi-get` when the request needs the matching collection. Collection results can contain several matches for one value; they do not promise input order or placeholder records for misses.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` when the user explicitly requests effective records. Do not add that restriction by default. Multilingual names are exact criteria where listed above, not filter fields. Keep default sorting and pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token.

Use `list` when the user asks to browse general-ledger business-line choices. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.

## Examples

```bash
bytedcli --json cis-master-data biz-financial-report-business-line get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-financial-report-business-line batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data biz-financial-report-business-line multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data biz-financial-report-business-line query --criterion 'mdm_code=<exact-value>'
bytedcli --json cis-master-data biz-financial-report-business-line list --page-size 20
```
