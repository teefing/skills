# 成本中心扩展 / Cost Center Extended Information (`biz-cost-center`)

## Methods and Fields

- Methods: `get`, `batch-get`, `multi-get`, `query`.
- Exact fields and single-field `query` criteria: `mdm_code` only.
- No `search` or `list`. Extension fields and remarks are not lookup criteria.

This is extended information for the same business object as [成本中心](md-cost-center.md), with the same detail query permission. Reuse its returned cost center `mdm_code`. When only a name or business code is known, locate the basic information first; do not pass that value as `mdm_code`.

Collection results do not promise input order or placeholder records for misses. `query` returns `next_page_token` when another page exists; pass only that returned token. Keep default sorting. If the user asks for effective cost centers, first select the basic information with its documented status filter, then reuse those returned codes here. Do not treat an extension field as the business object's effective status.

## Returned Information

`fee_type` is the fee type code in extended information. Ordinary numeric values are returned as strings, including zero. Use a returned `enum_labels` entry when available to explain its code; do not invent a label. If `fee_type` is absent, report that it was not returned rather than concluding that no fee type exists.

Optional `references` may provide names for `product_mdm_code`, `allocated_product_mdm_code`, `exclude_product_mdm_code`, `region_mdm_code`, `confirm_region_mdm_code`, `middle_platform_mdm_code`, and `product_group_mdm_code`. Parse returned array strings as JSON and match each code to `references[field][code]`; summaries retain available name languages. Keep original codes for later calls. They do not authorize target details.

## Examples

```bash
bytedcli --json cis-master-data biz-cost-center get --field mdm_code --value <cost-center-code>
bytedcli --json cis-master-data biz-cost-center batch-get --criterion 'mdm_code=<code-1>' --criterion 'mdm_code=<code-2>'
bytedcli --json cis-master-data biz-cost-center multi-get --field mdm_code --value <code-1> --value <code-2>
bytedcli --json cis-master-data biz-cost-center query --criterion 'mdm_code=<cost-center-code>'
```
