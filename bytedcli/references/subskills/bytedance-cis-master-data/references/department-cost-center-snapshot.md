# 部门成本中心关系与历史快照 / Department Cost Center Relationships and Snapshots (`department-cost-center-snapshot`)

## Commands

- `version-list` discovers saved historical versions, ordered newest first. Each record contains `cutoff_version` (saved version) and `cutoff_version_date` (saved date). Use the returned `cutoff_version` value; do not guess a date-based identifier.
- `get --version <version> --department-id <department-id>` reads one department in that version. Use exact `Now` for current relationships or a returned saved version for historical records. It returns optional `data`: absent means no visible matching record, not proof that the department never existed. Multiple matches are a contract error rather than an arbitrary selected row.
- `query --version <version>` reads the caller's accessible relationship records in the version. For both `Now` and saved historical versions, explicitly provide 1..128 department IDs by repeating `--department-id`; omitted departments are rejected locally. Pagination applies only to the requested, accessible departments. The default page size is 128, covering all matching requested departments on page 1; ordinary queries need no pagination flags. Use `--page` (default 1) and `--page-size` (default 128, maximum 512) only when explicitly requesting smaller pages. Output includes `records`, `total`, `page`, and `page_size`; use this offset pagination rather than `--page-token`.
- Exact `Now` reads live department-cost-center relationship rows with current department and cost center attributes. It is distinct from a current mapping-only lookup and does not select the newest saved snapshot. `now`, `NOW`, and surrounding whitespace are invalid spellings. `version-list` lists saved historical versions; choose `Now` explicitly for current data.

The department ID and cost center code are different identifiers: request department IDs via `--department-id`. Read the returned cost center fields together; a historical `mdm_code` alone does not establish a cost center identity. Use current names for `Now` and names saved in the snapshot when explaining historical results. Fetching current cost center details would describe today's information, so do not replace snapshot names with current reference names. Permission-limited results must not be described as an unrestricted complete version.

This group does not support name search, reverse lookup by cost center, general filters, sorting, or implicit current-version fallback. If the user requests current relationships, use `Now`; for historical requests, discover saved versions and confirm the intended returned identifier. Every get/query requires an explicit version and department scope. Neither current nor saved historical versions offer an unrestricted relationship list. If department IDs are missing, ask for the intended department IDs; do not enumerate departments through guessed keywords to bypass this requirement.

## Permission-limited Results

Both current and saved relationship queries may succeed with empty or partial data and a
`permission_warning`. Preserve that warning when `get` has no `data`; the absence is not proof that
the relationship does not exist. `query` totals and pagination cover the requested, accessible
departments, not the entire version or all requested departments regardless of permission. Do not
attribute every missing row to permissions or infer hidden values. If the requested result is
available, answer directly without requiring a permission application.

Use only returned `permission_apply_urls` when additional access is relevant. Role permissions define
the department range; the application page does not let the caller choose an arbitrary range. If an
existing role does not cover the need, ask the permission owner to review that scope. Applying for the
same role does not guarantee more data. `version-list` discovers metadata independently of department
relationship access, so a returned version is not evidence that its relationships are readable.

## Examples

```bash
bytedcli --json cis-master-data department-cost-center-snapshot version-list
bytedcli --json cis-master-data department-cost-center-snapshot get --version Now --department-id <department-id>
bytedcli --json cis-master-data department-cost-center-snapshot query --version Now --department-id <department-1> --department-id <department-2>
bytedcli --json cis-master-data department-cost-center-snapshot get --version <saved-version> --department-id <department-id>
bytedcli --json cis-master-data department-cost-center-snapshot query --version <saved-version> --department-id <department-1> --department-id <department-2>
bytedcli --json cis-master-data department-cost-center-snapshot query --version <saved-version> --department-id <department-1> --department-id <department-2> --page 2 --page-size 32
```

## Returned Information

`department_id` identifies the department in the selected version. When a cost center is identified, `mdm_code` is its ID and `source_code` its business code. `name` and `en_name` are cost center names; `department_name` and `department_en_name` are department names. `fee_type`, when returned, is a code as a string. With `Now`, these describe current data; with a saved version, they are saved names and attributes. Do not replace historical values with current detail or reference names. Rows without a configured cost center may omit its fields; do not invent a cost center from department information.

Saved historical rows can contain `mdm_code` equal to `department_id` while `source_code`, `name`, and `en_name` are absent. In that case, the returned fields do not establish a cost center identity: preserve the saved values, explain that the cost center cannot be identified from this row, and do not use that department ID for a cost center detail lookup. Do not infer an assignment from the current mapping or treat the ambiguity as proof that the historical relationship never existed.
