# 国籍 / Nationality (`ref-nationality`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup fields: `mdm_code`, `code`
- Accepted single-field `query` criteria: `mdm_code`, `code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-nationality get --field code --value <nationality-code>
bytedcli --json cis-master-data ref-nationality query --criterion 'code=<nationality-code>'
bytedcli --json cis-master-data ref-nationality search --keyword <nationality-name-fragment>
bytedcli --json cis-master-data ref-nationality list --page-size <bounded-page-size>
```

Use `list` when the user asks to browse nationality choices. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
