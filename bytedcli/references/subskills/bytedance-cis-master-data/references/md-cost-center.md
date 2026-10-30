# 成本中心 / Cost Center (`md-cost-center`)

## Cost center workflows

Choose the object the user requested before searching. **成本中心 is `md-cost-center`;
部门 is `md-department`.** A name that sounds like a department does not change the requested object.
For example, “查询成本中心 示例研究院” searches cost centers by that name. “查询示例研究院部门所属的成本中心”
starts with department discovery and then reads its mapping. Read the linked model reference for
supported fields before calling the command. Ordinary “查X” is name discovery; explicit “名称严格等于X”
uses exact name matching.

| User need | Query flow |
| --- | --- |
| Find a cost center by name | [`md-cost-center search`](md-cost-center.md) with `--keyword`; identify the intended candidate from returned cost center IDs and names. For explicitly exact names, use its documented `query --criterion 'name=<exact-name>'`. |
| Read a known cost center | `md-cost-center get --field mdm_code --value <cost-center-id>`; use `source_code` instead when the user supplies its business code. |
| Find a department's current cost center | With a department ID, use [`biz-dept-cost-center-mapping get`](biz-dept-cost-center-mapping.md) with `--field mdm_code --value <department-id>`. With only a department name, first [`md-department search`](md-department.md), identify the intended department, then read its mapping. The mapped cost center ID is `cc_mdm_code`. |
| Find a cost center's directly associated departments | Read the cost center and parse its `department_mdm_code` JSON array string; use returned reference summaries for names. This does not enumerate departments that inherit the cost center. |
| Read current or historical department relationships | Use [`department-cost-center-snapshot`](department-cost-center-snapshot.md) with explicit department IDs and version `Now` or a saved version returned by `version-list`. |

```bash
# Cost center name -> identify a candidate -> basic information
bytedcli --json cis-master-data md-cost-center search --keyword 'demo-cost-center'
bytedcli --json cis-master-data md-cost-center get --field mdm_code --value <returned-cost-center-id>
# Department name -> identify a department -> its assigned cost center
bytedcli --json cis-master-data md-department search --keyword 'demo-department'
bytedcli --json cis-master-data biz-dept-cost-center-mapping get --field mdm_code --value <returned-department-id>
```

### Complete the requested lookup

- Search returns candidates. If the user only needs matching names or IDs, those results can satisfy
  the request. For a general “查询成本中心 + 名称” request, read basic information with the returned
  cost center ID once the intended candidate is established. Ask the user to choose if several
  candidates remain plausible; do not select the first match arbitrarily. When the returned result
  unambiguously identifies the requested object, continue without an extra confirmation question.
- Read [`biz-cost-center`](biz-cost-center.md) with that same cost center ID when the
  user needs extended information such as fee type, products or regions. Do not fetch extensions
  for every name search by default.
- Department search completes department discovery. To answer which cost center a department
  belongs to, continue to its mapping. A returned cost center ID and available reference name can
  satisfy an assignment lookup; read basic or extended information when the requested fields need it.
- An empty result means no visible match for that query. Keep the requested model; do not silently
  switch from cost centers to departments. Search name matches alone do not establish parent/child
  relationships. A single result page does not prove all matches were returned.
- Label IDs by object in the answer: cost center `mdm_code` is **成本中心ID**, `source_code` is
  **成本中心业务编码**; department search/mapping `mdm_code` is **部门ID**; mapping `cc_mdm_code`
  is **成本中心ID**. Do not present a department candidate table as cost center results.
- Distinguish a candidate summary from requested details that were not returned. Preserve permission
  warnings and only returned application links; do not infer hidden assignments.

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`, `search`.
- `get` fields: `mdm_code`, `source_code`.
- `batch-get` and `multi-get` fields: `mdm_code`, `source_code`, `name`.
- Accepted single-field `query` criteria: `mdm_code`, `source_code`, `parent_mdm_code`, `name`. Choose exactly one; never combine these fields.
- Fixed `search` field: `name`. Supply `--keyword`; it returns candidate codes and names. Detail access is checked separately, so successful search does not authorize details.
- `name` is an exact multilingual name when used in `query`, `batch-get`, or `multi-get`. In `batch-get`, every criterion must use `name` if any uses it. Ordinary `mdm_code` and `source_code` criteria may be mixed independently.

## Basic and Extended Information

成本中心 and [成本中心扩展](biz-cost-center.md) describe the same business object and share its detail query permission. Use the same returned `mdm_code` to read the other entry. If only a name fragment is known, search the basic information first, identify the intended candidate, then use its returned code. Search candidates do not contain full details.

Prefer a returned `mdm_code` for a stable record. Collection results may contain multiple matches and do not promise input order or placeholder records for misses. `source_code` is a cost center business code; department IDs belong to [部门成本中心映射](biz-dept-cost-center-mapping.md).

## Returned Information

`mdm_code` is the cost center ID and `source_code` its business code. The basic record's `department_mdm_code` contains its directly associated department IDs. It is returned as a JSON array encoded in a string; parse that string as JSON before reading the IDs. This array does not list every descendant department that inherits the cost center. To find a department's final assignment, query the department mapping entry.

A permitted field may be absent from a response. Absence does not prove that the business value is empty or that the record has no associated departments.

## Filters and Pagination

`query` and `multi-get` accept `--filter status=equal:1` only when the user explicitly asks for effective records. Do not add it by default. Multilingual `name` is an exact criterion where listed, not a filter. Keep default sorting. Pass only a returned `next_page_token` to `query --page-token`; `multi-get` has no continuation token. `search` uses `--page` and `--page-size`.

This model does not expose `list`. Ask for a documented lookup value when the request lacks one; do not enumerate name keywords to bypass this boundary.

Optional `references` may provide names for `department_mdm_code`, `parent_mdm_code`, and `affiliated_business_line`. Match codes in each returned field to `references[field][code]`; summaries retain available `name` or `name.<language>` values. They do not authorize a referenced object's full details.

## Examples

```bash
bytedcli --json cis-master-data md-cost-center get --field source_code --value <cost-center-business-code>
bytedcli --json cis-master-data md-cost-center multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data md-cost-center batch-get --criterion 'name=<exact-name-1>' --criterion 'name=<exact-name-2>'
bytedcli --json cis-master-data md-cost-center query --criterion 'parent_mdm_code=<parent-cost-center-code>'
bytedcli --json cis-master-data md-cost-center search --keyword <name-fragment>
```
