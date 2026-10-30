# 地产项目 / Real-estate project (`md-real-estate-project`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `list`
- `get` fields: `mdm_code`
- `batch-get` fields: `mdm_code`
- `multi-get` fields: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`
- `search` is not available.

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data md-real-estate-project get --field mdm_code --value demo-code
bytedcli --json cis-master-data md-real-estate-project batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data md-real-estate-project multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data md-real-estate-project query --criterion 'mdm_code=demo-value'
bytedcli --json cis-master-data md-real-estate-project list --page-size 16
```

All exact and bounded lookups require `mdm_code`. `name` is not a supported query criterion
and this model does not expose `search`. Ask for `mdm_code` when a name fragment is supplied;
use a bounded `list` only for an explicit browsing request.

Use `list` when the user asks to browse the real-estate project directory. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
