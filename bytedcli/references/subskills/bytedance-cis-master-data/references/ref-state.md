# 省/州 / State/Province (`ref-state`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Single-record `get` field: `mdm_code`
- `batch-get` / `multi-get` fields: `mdm_code`, `name`
- In `batch-get`, `name` is valid only when every repeated criterion uses `name`.
- Accepted single-field `query` criteria: `mdm_code`, `country_mdm_code`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-state get --field mdm_code --value <master-data-code>
bytedcli --json cis-master-data ref-state query \
  --criterion 'country_mdm_code=<country-master-data-code>'
bytedcli --json cis-master-data ref-state search --keyword <state-name-fragment>
bytedcli --json cis-master-data ref-state list --page-size <bounded-page-size>
```

Use `list` when the user asks to browse the province/state directory. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
