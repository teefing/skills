# 楼层 / Building floor (`md-building-layer`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `list`
- `get` fields: `mdm_code`
- `batch-get` fields: `mdm_code`
- `multi-get` fields: `mdm_code`
- Accepted single-field `query` criteria: `mdm_code`, `building_mdm_code`, `layer_code`
- `search` is not available.

Use exactly one listed field per query; the field list does not permit arbitrary combinations.

## Examples

```bash
bytedcli --json cis-master-data md-building-layer get --field mdm_code --value demo-code
bytedcli --json cis-master-data md-building-layer batch-get \
  --criterion 'mdm_code=demo-code-1' --criterion 'mdm_code=demo-code-2'
bytedcli --json cis-master-data md-building-layer multi-get \
  --field mdm_code --value demo-code-1 --value demo-code-2
bytedcli --json cis-master-data md-building-layer query --criterion 'layer_code=demo-value'
bytedcli --json cis-master-data md-building-layer list --page-size 16
```

Use `building_mdm_code` with `query` for floors of a known building. `layer_code` supports
`query` only and can match multiple records. Do not construct `search` or use `layer_code` as a
`get`, `batch-get`, or `multi-get` field. Ask for a documented criterion when only a name fragment
is provided; do not automatically start a broad list scan.

Use `list` when the user asks to browse the floor directory. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
