# 证件类型 / Identity-Document Type (`md-card-type`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup field: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `name`
- Fixed `search` fields: `name`. Read description and other detail fields using the selected record's `mdm_code`.

For directory filtering, use fields listed by `list --help`; `description` is a detail field,
not a list filter.

## Examples

```bash
bytedcli --json cis-master-data md-card-type get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-card-type query --criterion 'mdm_code=<master-data-code>'
bytedcli --json cis-master-data md-card-type search --keyword <document-type-fragment>
bytedcli --json cis-master-data md-card-type list --page-size <bounded-page-size>
```

Use `list` when the user asks to browse document-type choices. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
