# 国家/地区 / Country/Region (`ref-country`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`, `list`
- Single-record `get` fields: `mdm_code`, `code`, `three_character_code`
- `batch-get` / `multi-get` fields: `mdm_code`, `code`, `three_character_code`, `name`
- In `batch-get`, `name` is valid only when every repeated criterion uses `name`.
- Accepted single-field `query` criteria: `mdm_code`, `code`, `three_character_code`, `name`, `full_name`
- Fixed `search` fields: `name`, `full_name`

## Examples

```bash
bytedcli --json cis-master-data ref-country get --field code --value <country-code>
bytedcli --json cis-master-data ref-country query \
  --criterion 'three_character_code=<three-character-code>'
bytedcli --json cis-master-data ref-country search --keyword <country-name-fragment>
bytedcli --json cis-master-data ref-country list --page-size <bounded-page-size>
```

Use `list` when the user asks to browse the country/region directory. For a specific record or named subset, use the documented lookup or search that expresses those conditions.
Do not use `list` to recover from a failed query, missing lookup values, or a permission denial.
Start with a bounded page size. Stop when the requested page or collection scope is satisfied;
continue with a returned `next_page_token` only when more of that collection is needed.
`current_count` describes this page, not a total count. Use only documented optional fields.
