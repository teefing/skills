# 时区 / Time Zone (`ref-time-zone`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup fields: `mdm_code`, `time_zone_id`
- Accepted single-field `query` criteria: `mdm_code`, `time_zone_id`, `name`
- Fixed `search` field: `name`

## Examples

```bash
bytedcli --json cis-master-data ref-time-zone get \
  --field time_zone_id --value <time-zone-id>
bytedcli --json cis-master-data ref-time-zone query --criterion 'time_zone_id=<time-zone-id>'
bytedcli --json cis-master-data ref-time-zone search --keyword <time-zone-name-fragment>
bytedcli --json cis-master-data ref-time-zone list --page-size <bounded-page-size>
```

Use `list` when the user asks to browse time-zone choices. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
