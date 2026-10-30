# 公共假期 / Public Holiday (`md-public-holiday`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Exact lookup fields: `mdm_code`, `holiday_item_id`
- Accepted `query` criterion field sets:
  - `mdm_code`
  - `holiday_item_id`
  - `holiday_year`
  - `holiday_year,holiday_mdm_code`
  - `holiday_item_name`
- Fixed `search` field: `holiday_item_name`

## Examples

```bash
bytedcli --json cis-master-data md-public-holiday get \
  --field holiday_item_id --value <holiday-item-id>
bytedcli --json cis-master-data md-public-holiday query \
  --criterion 'holiday_year=<holiday-year>' \
  --criterion 'holiday_mdm_code=<holiday-master-data-code>'
bytedcli --json cis-master-data md-public-holiday search --keyword <holiday-name-fragment>
bytedcli --json cis-master-data md-public-holiday list --page-size <bounded-page-size>
```

Use exactly one documented query field set. Use `list` when the user asks to browse the public-holiday directory; use the documented `holiday_year` query for a specified year. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
