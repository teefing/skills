# 部门 / Department (`md-department`)

This entry discovers **departments**, not cost centers. Label returned `mdm_code` as 部门ID.
For a request to find a cost center by its name, use [成本中心](md-cost-center.md).
For a department's assigned cost center, identify the intended department here and then read
[its mapping](biz-dept-cost-center-mapping.md) using the returned department ID. Department
discovery alone does not answer its cost center assignment. Similar names and name prefixes
do not establish department hierarchy.

## Methods and Fields

- Methods: `search` only. Do not use `get`, `batch-get`, `multi-get`, `query`, or `list`.
- Fixed `search` field: `name`. Supply a department name fragment with `--keyword`.
- Search is fuzzy name matching, not an exact lookup by department ID, code, name, or parent department.
- Department search does not accept `--filter` or `--sort`; use only the name fragment and pagination.
- Read the returned `mdm_code` and name to identify visible matches. A returned code does not enable a department detail command.
- Follow search pagination with `--page` and `--page-size` for the supplied name fragment. Do not use a page token or enumerate keywords to obtain all departments.

## Unsupported Requests

If the user supplies only a department ID or requests exact, batch, parent-department, or full-directory
lookup, explain that the department CLI does not support that operation. Do not pass an ID as a name
keyword or silently substitute fuzzy search for an exact lookup. Ask for a department name fragment
and explicit acceptance of fuzzy matching when that would change the requested task.
A search page is not the full department directory and does not establish that no other departments exist.

## Example

```bash
bytedcli --json cis-master-data md-department search --keyword <name-fragment>
```
