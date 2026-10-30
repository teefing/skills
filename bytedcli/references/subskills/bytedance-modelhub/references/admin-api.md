# ModelHub Admin Request Contract

Use this reference to prepare account deployment imports/updates or interpret captured request metadata. The CLI command mapping is in the ModelHub skill entry point.

## Evidence Boundaries

| Operation | Request evidence | Remaining verification |
| --- | --- | --- |
| `product names` | GET `/modelhub/platform/product/query_name_list`; unwrapped `product_name_list` string array | Minimum authentication and failure responses |
| `product list` | GET `/modelhub/platform/product/query_list` with `product_name`, `page=0`, `page_size=1000`, or with `model`, `page=0`, `page_size=10`; unwrapped `product_info_list` and `total` | Minimum authentication, combined-filter semantics, failure responses, and record variants |
| `product get` | GET `/modelhub/platform/resource/product/query_detail` with `product_name`; success response uses `base.StatusCode` and grouped resources | Minimum authentication, failure responses, and resource variants |
| `account-deploy list` | GET `/modelhub/platform/resource/account_deploy/list` with `product_name` and `region`; unwrapped `accounts` array | Minimum authentication, failure responses, and record variants |
| `account-deploy update` | POST `/modelhub/platform/resource/account_deploy/update` with a JSON object; empty `{}` acknowledgement | Required fields, write authentication, failure responses, and omitted-field behavior |
| `account-deploy delete` | POST `/modelhub/platform/resource/account_deploy/delete` with `product_name`, `region`, `account_id`; empty `{}` acknowledgement | Write authentication, failure responses, missing-record and cascade behavior |
| `account-deploy import` | POST `/modelhub/platform/resource/account_deploy/import` with `product_name`, `region`, and `items[]`; unwrapped `added_count` and `skipped_ids` | Required fields, write authentication, failure responses, and skipped-entry format/semantics |

Classify a cURL by its URL, explicit method, and body, not the surrounding label. A cURL with `--data-raw` and no method override is POST. A GET `/account_deploy/list` is not an update. Do not substitute update's `account_id` / `data` envelope for import's `items[]` envelope.

## Authentication Evidence

The captured calls carry `x-jwt-token` (a ByteCloud-style person-account JWT) and browser cookies together, plus `x-requested-with: XMLHttpRequest`. Import/update/delete include same-origin `origin` and a UI `referer`. This does not isolate which credentials or headers the backend requires. Keep `--headers-file` as the explicit caller-owned credential path until authentication is verified; do not introduce JWT-only login or automatic cookie fallback on this evidence alone.

Do not persist raw captures containing Cookie/JWT values, personal identifiers, or live account URLs in the repository. Use fresh authorized credentials privately. Browser version, language, priority, and `sec-*` headers are not established business inputs. The UI referer is not a source of product/channel defaults: command options and JSON body fields determine the request.

Account-list `region` is a backend deployment filter. It does not switch the control-plane origin, authentication site, or cloud provider region.

## Observed Product Names Response

[product-names.example.json](product-names.example.json) illustrates GET `/modelhub/platform/product/query_name_list`. This endpoint returns `product_name_list` at the top level without `base`, `code`, or `success`.

- Validate `product_name_list` as an array of strings. An empty array is valid, but a missing field, null, a non-array value, or non-string element is a response error. Do not coerce invalid values to strings or replace a missing list with an empty one.
- Preserve all names exactly, including case, punctuation, duplicates, order, and trailing spaces. The example intentionally includes a trailing-space identifier. Quote a selected name in `--product-name`; the CLI preserves whitespace while rejecting blank inputs.
- This endpoint-specific shape is sufficient for success on a successful HTTP response. Explicit failures in `code`, `success`, or `base.StatusCode` still win; malformed base fields are still rejected. Do not use the presence of `product_name_list` to bypass status checks on other endpoints.
- JSON output retains the array at `data.response.product_name_list`. No pagination, total count, sorting, or deduplication is inferred from this response.

## Observed Product List Response

The same endpoint supports a model-only backend query: `?model=demo-model&page=0&page_size=10`. Use `product list --model demo-model --page 1 --page-size 10`; `--product-name` is not required in this form and its query key is omitted. The model filter is distinct from the returned `product_name`; do not derive one from the other.

Public pagination is one-based: `--page` defaults to 1 and `--page-size` to 20, and page 0 is rejected. The API adapter subtracts one exactly once when building the backend query: CLI page 1 requests backend page 0; CLI page 2 requests backend page 1. The request evidence above records raw backend page indexes and sizes, not CLI defaults. JSON `data.page` retains the requested one-based page, and `data.page_size` retains the requested size.

[product-list.example.json](product-list.example.json) illustrates GET `/modelhub/platform/product/query_list`. The response has top-level `product_info_list` and `total` without `base`, `code`, or `success`.

- Validate the list as an array of objects and total as a nonnegative integer, even when a success marker is present. Missing/malformed fields are errors; empty arrays and zero totals are valid. Record fields are preserved without imposing a complete required-field schema from one sample.
- This shape permits success only on the product-list endpoint. Explicit failure markers and malformed base fields are still rejected; this is not a bypass for detail or deployment operations.
- Preserve `ext`, `price`, and `product_func` as JSON-encoded strings. Do not silently decode, normalize, or re-encode them. Item-level `status` is a product field, not an envelope success/failure marker; enum meanings are not inferred.
- Preserve arrays, nested `auto_approval_info`, numeric zeros, empty strings, and unknown fields. Do not infer pricing units or access policy from sample values.
- JSON output retains `data.response.product_info_list` and `data.response.total`, with the requested `data.page` and `data.page_size`. The total is the backend value, not the number of records on this page. No auto-pagination or client-side truncation occurs.

## Observed Product Detail Response

[product-detail.example.json](product-detail.example.json) is a sanitized structural example for GET `/modelhub/platform/resource/product/query_detail`, not `/modelhub/platform/product/query_list`. The browser page's detail view does not make those two API endpoints interchangeable.

- Success is signaled by numeric `base.StatusCode: 0`; `base.StatusMessage` alone is not a success marker. Nonzero status is a business failure, regardless of `code: 0` or `success: true` elsewhere. A malformed base/status field is a response-validation error.
- The shared parser retains compatibility with top-level `code: 0`, `code: "0"`, and `success: true`; it rejects any explicit contradiction. Name discovery, product list, and account-deploy list/import have separate endpoint-specific unwrapped shapes; update/delete have empty-object acknowledgements. None of these exceptions applies to product detail.
- `resource_level_2_detail_map` is a map whose key can be the empty string. Preserve that key and any other resource-level keys; do not replace or discard them.
- Each demonstrated resource-level entry has `paygo_info` and `ptu_info_list`. PayGo is one object; PTU is an array of objects. Both group shapes contain `channel_resource_info_list` and `user_info_list` arrays. Do not flatten or combine their resource types.
- `user_product_limits_map` is present on the sample PayGo user but absent on the PTU user. Missing limits are not zero limits; preserve absence instead of copying defaults from another group.
- Preserve zero QPM/TPM, empty deployment strings, numeric IDs, timestamp strings, and boolean `is_online` values. Channel and user regions are independent fields, not control-plane host selectors.
- Treat `ak`, `sk`, account URLs, owner details, PSMs, and tenant information as private. The example contains only placeholders; do not share full live output in tickets or logs.

The CLI retains this object at `data.response`, including the upstream field names. It validates the success envelope while preserving resource records; the sample is not a complete required-field schema for every resource variant. No additional production records are needed to exercise this shape offline.

## Observed Account Deployment List Response

[account-deploy-list.example.json](account-deploy-list.example.json) illustrates GET `/modelhub/platform/resource/account_deploy/list`. It returns top-level `accounts` without `base`, `code`, or `success`.

- Validate `accounts` as an array of objects, even when a success marker exists. Empty arrays are valid; missing/null/non-array fields and non-object records are errors. Preserve record fields without inferring a complete required-field schema from one sample.
- This shape permits success only on account-deploy list. Explicit failure markers and malformed base fields still fail, and an `accounts` array cannot establish success for import/update or product APIs.
- Preserve `deployment: "null"` as the literal string. It is different from the import example's JSON null and update example's empty string; do not normalize these states or infer a write payload from this response.
- Preserve slash-containing IDs, `end_point`, `api_ver`, `dedicated_to_list`, numeric flags, and unknown fields. Account `product` and provider `region` need not match the request's `product_name` and deployment `region`.
- The observed `key1` and `key2` are masked as `"***"`. Preserve masks, do not attempt to recover keys, and never treat masks as usable credentials in a write body. Keep account endpoints and tenant identifiers private even when keys are masked.
- JSON output retains `data.response.accounts`. No total or pagination metadata is present in this sample; do not manufacture a backend total from array length or infer complete inventory coverage.

## Observed Import Body

[import-body.example.json](import-body.example.json) preserves the captured import field names and value types using placeholders. Import sends one JSON object with top-level `product_name`, `region`, and an `items` array. The capture contains one item; it does not establish a maximum batch size, partial-failure behavior, or atomicity.

- Preserve `items` as an array, including item order and all supplied fields; do not flatten a single item into an update body or split it into separate requests.
- Item `product` and `region` are independent of top-level `product_name` and `region`. Preserve slash-containing `id` and the endpoint string unchanged.
- Preserve `deployment: null` and `on_demand: false` exactly. Do not coerce null to an empty string, drop false values, or convert numeric flags into booleans.
- Preserve `api_ver`, `dedicated_to_list`, `select_rate`, `use_limit`, and `valid_key` as supplied. Their allowed values and business meanings still need backend documentation or response evidence.
- Treat `key1` as potentially sensitive. The example uses `sample-key-reference`, not a live value. Full preview output includes the body, so do not publish it or copy it into shared logs.
- Do not fill in update-only `account_id`, `data`, `deploy_region`, `tpm`, or `qpm` fields just because they appear in the update example. Missing fields and explicit null are different JSON states.

```bash
# Preview the private import body without reading credentials or sending a request
bytedcli --json modelhub admin account-deploy import --body-file ./demo-import.json
# Submit the same body only after authorization
bytedcli --json modelhub admin account-deploy import --body-file ./demo-import.json --headers-file ./demo-headers.json --yes
```

## Observed Import Response

[import-response.example.json](import-response.example.json) illustrates the supplied POST import response: `{"added_count":1,"skipped_ids":[]}`, without `base`, `code`, or `success`.

- Require a nonnegative integer `added_count` and an array `skipped_ids`, even when a success marker exists. Missing/malformed fields fail validation. Zero additions and empty arrays are valid; preserve unknown fields and any skipped entries unchanged.
- The observed skipped array is empty, so its element schema and reasons for skipping are not established. Do not infer duplicate detection, atomicity, idempotency, or a relationship between the count and request length from this sample.
- This shape permits success only for import. Explicit failure markers and malformed base fields still fail; the same object cannot establish update success.
- Output retains both fields at `data.response`. Report added counts and skipped entries rather than equating command success with every item being added. Do not automatically retry skipped records; inspect the result and query account-deploy list before planning any further write.
- This response handling does not change the write guard: preview by default, explicit `--yes` for submission, no automatic POST retries, and an unknown outcome after timeout/disconnection.

## Observed Update Body

[update-body.example.json](update-body.example.json) retains the captured field names and value types with placeholder identifiers and URL. It is a shape example, not a deployable configuration or a statement that every field is required.

- Top-level `product_name` selects the ModelHub product; nested `data.product` is a separate value and may differ.
- Top-level `account_id` and nested `data.id` contain slash-separated identifiers in the example. Preserve them unchanged; one example does not establish an equality constraint.
- Top-level `region`, nested `data.region`, and nested `data.deploy_region` are distinct fields. Do not overwrite any from global `--site` or infer one from another.
- Preserve `end_point`, `api_ver`, and `deployment` as supplied strings, including an empty deployment. Do not rewrite the endpoint or infer an API version from the provider name.
- Preserve numeric fields `valid_key`, `tpm`, `qpm`, `select_rate`, and `use_limit`, including zero values. Their units, permitted ranges, and enum meanings are not established by this capture.
- Preserve `dedicated_to_list` as an array of strings; do not join it, discard entries, or populate it from the logged-in user.

Prepare a private body using the known-good request for the intended account, then preview and explicitly authorize that same body:

```bash
# Preview only; no credentials are read and no request is sent
bytedcli --json modelhub admin account-deploy update --body-file ./demo-update.json
# After approval of the actual target and complete body
bytedcli --json modelhub admin account-deploy update --body-file ./demo-update.json --headers-file ./demo-headers.json --yes
```

The CLI validates JSON-object shape and sends the body unchanged. The response below does not establish backend field requirements or whether omitted fields are preserved during update.

## Observed Update Response

[update-response.example.json](update-response.example.json) records the supplied POST update acknowledgement: `{}`.

- Accept exactly the empty JSON object on a successful HTTP response for account-deploy update or delete. Do not treat an empty HTTP body, null, an array, or an arbitrary nonempty object without status markers as the same acknowledgement.
- Explicit failures in `code`, `success`, or `base.StatusCode` and malformed base fields still fail. Recognized success envelopes remain supported for compatibility; the empty-object exception does not weaken other endpoints.
- Preserve the acknowledgement at `data.response` without manufacturing updated counts, changed fields, or an updated account record. Query account-deploy list to inspect the resulting record before claiming the intended configuration is present.
- Preview remains the default and submission requires `--yes`. Do not automatically retry after a timeout or ambiguous response: the write may already have happened. No live update is needed to validate this response shape offline.

## Account Deployment Delete

[delete-body.example.json](delete-body.example.json) illustrates the POST payload with exactly `product_name`, `region`, and `account_id`. The CLI requires the corresponding nonblank `--product-name`, `--region`, and `--account-id` options, preserving their exact strings. It does not accept `--body-file`, extra payload fields, or infer the target from a referer or current login.

The supplied [delete response](delete-response.example.json) is `{}`. Like update, only a successful HTTP response containing this empty JSON object is accepted without status markers. Explicit failures still win. An acknowledgement contains no deleted count or record and does not establish cascade behavior, idempotency, or what happens if the record was already absent.

```bash
# Inspect records in the exact deployment region before selecting a target
bytedcli --json modelhub admin account-deploy list --product-name demo-product --region demo-region --headers-file ./demo-headers.json
# Preview only; no credentials are read and no network request is made
bytedcli --json modelhub admin account-deploy delete --product-name demo-product --region demo-region --account-id global/demo-account
# After explicit approval of this product, region, and account ID
bytedcli --json modelhub admin account-deploy delete --product-name demo-product --region demo-region --account-id global/demo-account --headers-file ./demo-headers.json --yes
# Verify absence in the same product/region; do not automatically repeat deletion
bytedcli --json modelhub admin account-deploy list --product-name demo-product --region demo-region --headers-file ./demo-headers.json
```

Delete makes one POST with retries disabled and rejects redirects. Timeout/disconnection leaves the outcome unknown; inspect the record before proposing another write. This removes a ModelHub account deployment record, not a request to delete provider cloud resources.
