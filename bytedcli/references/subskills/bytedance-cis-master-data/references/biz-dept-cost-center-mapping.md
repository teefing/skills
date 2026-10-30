# 部门成本中心映射 / Current Department Cost Center Mapping (`biz-dept-cost-center-mapping`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`.
- Exact fields and single-field `query` criteria: `mdm_code` only. **Here `mdm_code` is the department ID.**
- Returned `cc_mdm_code` identifies the mapped cost center. Reuse that value with [成本中心](md-cost-center.md) or [成本中心扩展](biz-cost-center.md) for details; those calls check detail permission separately.
- No `search` or `list`, and no reverse lookup by `cc_mdm_code`, `ebs_code`, or a cost center name.

This entry describes the current mapping. For a department name, first use `md-department search --keyword <name-fragment>`, confirm the intended department among the candidates, then use its returned `mdm_code` here. Do not select an arbitrary first name match. For a current department-cost-center relationship row with names and attributes, use `department-cost-center-snapshot get --version Now --department-id <department-id>`. Use [部门成本中心关系与历史快照](department-cost-center-snapshot.md) for a saved historical version. Do not answer a historical request from current mapping data. If neither a department ID nor a department name is available, ask for one. When a name is available, discover the department as described above; the mapping call itself requires its returned department ID, not a cost center code or a name keyword.

Keep default sorting. `query` uses only a returned `next_page_token`; `multi-get` has no continuation token. Collection results do not promise input order or placeholder records for misses. Do not invent filters or add an effective-only restriction by default.

Optional `references.mdm_code[departmentId]` provides a department name; `references.cc_mdm_code[costCenterCode]` provides a cost center name. These are distinct identifiers. Summaries may contain `name` or `name.<language>` and do not authorize target details. Missing summaries are not evidence that a department or cost center is absent.

In the answer, label `mdm_code` as 部门ID and `cc_mdm_code` as 成本中心ID. The returned assignment
and available cost center name can satisfy “which cost center does this department belong to”.
Fetch cost center basic or extended information only when the requested fields require it. Do not
present department search candidates as the final assignment or infer an assignment from a shared name.

## Permission-limited Results

Read `permission_warning` even when the query succeeds with no records. A range warning means this
lookup covers only authorized departments; it does not prove why each absent department was not
returned. For multiple requested departments, distinguish returned mappings from unresolved inputs
without inventing placeholder mappings. If the returned data satisfies the request, answer directly.
When additional access is needed, use only a returned `permission_apply_urls` entry. Department
coverage comes from the approved role; if an existing role is insufficient, the permission owner
needs to review the required scope. Reapplying for the same role does not guarantee wider coverage.

## Examples

```bash
bytedcli --json cis-master-data biz-dept-cost-center-mapping get --field mdm_code --value <department-id>
bytedcli --json cis-master-data biz-dept-cost-center-mapping batch-get --criterion 'mdm_code=<department-1>' --criterion 'mdm_code=<department-2>'
bytedcli --json cis-master-data biz-dept-cost-center-mapping multi-get --field mdm_code --value <department-1> --value <department-2>
bytedcli --json cis-master-data biz-dept-cost-center-mapping query --criterion 'mdm_code=<department-id>'
```
