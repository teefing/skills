# CIS业务线 / CIS Business Line (`md-cis-business-line`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup field: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `parent_mdm_code`, `name`
- Fixed `search` fields: `name`
- All methods, including fuzzy `search`, require access to this model. If access is denied, surface the returned application link instead of changing the model or query.

For directory filtering, use fields listed by `list --help`; `description` is a detail field,
not a list filter.

## Examples

```bash
bytedcli --json cis-master-data md-cis-business-line get \
  --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data md-cis-business-line query \
  --criterion 'parent_mdm_code=<parent-master-data-code>'
bytedcli --json cis-master-data md-cis-business-line query \
  --criterion 'name=<exact-business-line-name>'
bytedcli --json cis-master-data md-cis-business-line search \
  --keyword <business-line-name-fragment>
bytedcli --json cis-master-data md-cis-business-line list --page-size <bounded-page-size>
```

Use `name` as a single-field `query` criterion or search its fragments to discover candidates.
Read the selected record's description and other detail fields by its returned `mdm_code`.

Use `list` when the user asks to browse the CIS business-line directory. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
