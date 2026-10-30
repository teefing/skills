# 源系统标识 / Source-System Identifier (`biz-source-system`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup field: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data biz-source-system get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data biz-source-system query --criterion 'mdm_code=<master-data-code>'
bytedcli --json cis-master-data biz-source-system search --keyword <source-system-name-fragment>
bytedcli --json cis-master-data biz-source-system list --page-size <bounded-page-size>
```

Use `list` when the user asks to browse registered source-system identifiers. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
