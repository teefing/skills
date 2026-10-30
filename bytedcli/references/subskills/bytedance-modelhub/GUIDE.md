---
name: bytedance-modelhub
description: "Manage ModelHub admin product names, product lists/details, and account deployment records through bytedcli modelhub admin. Use for ModelHub registry queries and account-deploy import/update/delete, not cloud provisioning or model-access approval decisions."
---

# ModelHub Admin

Use `bytedcli modelhub admin` for product discovery and account deployment administration. This skill does not provision cloud resources, invoke models, or approve access requests.

## Authentication and Scope

Live commands require `--headers-file <path>`, a private UTF-8 JSON object mapping HTTP header names to string values from an authorized ModelHub request. The CLI does not assume an authentication scheme or automatically log in. Keep this file outside the repository, restrict its permissions, and never print or commit its contents. Do not copy browser transport headers such as Host, Content-Length, Transfer-Encoding, or Connection.

Only the configured control-plane endpoint is supported. `--region` is a deployment filter, not a host selector; global `--site` does not select another ModelHub deployment.

Captured requests include `x-jwt-token` alongside browser cookies and `x-requested-with: XMLHttpRequest`; import/update/delete requests also include Origin/Referer. This is observed request metadata, not proof that every header is required or that JWT alone works. Do not copy captured credentials into this skill or assume automatic login is established.

Read [Admin request contract](references/admin-api.md) when preparing import/update bodies or investigating authentication. It distinguishes observed request shapes from unverified requirements. If the caller has not supplied a known-good header file or write body, ask for those inputs rather than invent credentials or required fields.

## Commands

The supported scope is these seven operations. Paths are relative to the configured ModelHub control-plane origin; product detail intentionally uses the resource API, not the product-list API.

| Command after `bytedcli modelhub admin` | Method | Endpoint | Input |
| --- | --- | --- | --- |
| `product names` | GET | `/modelhub/platform/product/query_name_list` | None |
| `product list` | GET | `/modelhub/platform/product/query_list` | `--product-name` or `--model`, one-based `--page` (default 1), `--page-size` (default 20) |
| `product get` | GET | `/modelhub/platform/resource/product/query_detail` | `product_name` |
| `account-deploy list` | GET | `/modelhub/platform/resource/account_deploy/list` | `product_name`, `region` |
| `account-deploy import` | POST | `/modelhub/platform/resource/account_deploy/import` | JSON object body |
| `account-deploy update` | POST | `/modelhub/platform/resource/account_deploy/update` | JSON object body |
| `account-deploy delete` | POST | `/modelhub/platform/resource/account_deploy/delete` | `--product-name`, `--region`, `--account-id` |

Import and update have distinct observed bodies: import uses `product_name`, `region`, and `items[]`; update uses `product_name`, `region`, `account_id`, and `data`. See the separate [import example](references/import-body.example.json) and [update example](references/update-body.example.json). These are sanitized shape examples, not deployable configurations or complete validation schemas.

Success response examples for all seven operations are documented in the [Admin request contract](references/admin-api.md). Minimum authentication and complete backend business constraints still need verification. Replace credentials and account identifiers with placeholders in shared samples; actual credentials belong only in the caller's private header file. Treat body fields such as `key1` as potentially sensitive and keep full previews private.

```bash
# Discover products, then query one page (defaults: page 1, page size 20)
bytedcli --json modelhub admin product names --headers-file ./demo-headers.json
bytedcli --json modelhub admin product list --product-name demo-product --page 1 --page-size 20 --headers-file ./demo-headers.json
# Filter by model instead of product name using the same list API
bytedcli --json modelhub admin product list --model demo-model --page 1 --page-size 10 --headers-file ./demo-headers.json

# Resource product detail and deployment records
bytedcli --json modelhub admin product get --product-name demo-product --headers-file ./demo-headers.json
bytedcli --json modelhub admin account-deploy list --product-name demo-product --region demo-region --headers-file ./demo-headers.json

# Preview the complete endpoint-specific JSON body; no credentials or network required
bytedcli --json modelhub admin account-deploy import --body-file ./demo-import.json
bytedcli --json modelhub admin account-deploy update --body-file ./demo-update.json

# Submit only after the user approves the same previewed body
bytedcli --json modelhub admin account-deploy import --body-file ./demo-import.json --headers-file ./demo-headers.json --yes
bytedcli --json modelhub admin account-deploy update --body-file ./demo-update.json --headers-file ./demo-headers.json --yes

# Preview deletion of one exact account deployment, then submit only after approval
bytedcli --json modelhub admin account-deploy delete --product-name demo-product --region demo-region --account-id global/demo-account
bytedcli --json modelhub admin account-deploy delete --product-name demo-product --region demo-region --account-id global/demo-account --headers-file ./demo-headers.json --yes
```

## Payloads and Results

- Product list requires at least one nonblank `--product-name` or `--model`. Only supplied filters are sent, without rewriting their values; model-only queries do not send `product_name`. If both are supplied, both are forwarded, but their combined backend semantics have not been verified. Other product/deployment commands still require `--product-name`.
- Product pages are one-based: `--page` defaults to 1 and `--page-size` to 20. Page 0 is invalid. The API adapter converts page 1 to backend page 0 and page 2 to backend page 1; `data.page` remains the requested one-based page and `data.page_size` the requested size.
- Import and update accept a JSON object unchanged. Use the corresponding endpoint's known-good body; do not assume they share required fields or that update is a partial patch. Preview validates JSON shape only, not backend business constraints.
- Without `--yes`, writes return `status: "dry_run"`, `applied: false`, and the complete `request.body`. Headers are not read or included. Preview bodies may contain sensitive account configuration; keep output private.
- Live results retain the upstream response at `data.response`. Name discovery accepts the observed unwrapped `{ "product_name_list": [...] }` response; the array must contain strings and may be empty. This shape is accepted only for `product names`. See the [sanitized names example](references/product-names.example.json).
- Returned names retain their order, case, duplicates, and whitespace. Pass a selected name exactly in a quoted `--product-name`; trailing spaces can be part of an identifier. Product-name inputs preserve whitespace but reject empty/all-whitespace values.
- Product detail uses numeric `base.StatusCode: 0`; the shared client also accepts `code: 0`, `code: "0"`, or `success: true`. Any explicit failure marker wins, and malformed base status fields are rejected. Apart from the validated endpoint-specific product names/list, account-deploy list/import, and empty update/delete acknowledgements, missing markers fail closed.
- Product detail preserves `resource_level_2_detail_map`, including the empty-string key, `paygo_info`, and `ptu_info_list` groups. Keep outputs private: they can include `ak`/`sk`, account endpoints, and user details. See the [sanitized response example](references/product-detail.example.json); do not assume optional fields are present in every group.
- Product lists accept an unwrapped `product_info_list` array of objects and nonnegative integer `total`, retained at `data.response`, plus the requested `data.page` and `data.page_size`. They make one request, do not auto-paginate or locally truncate, and preserve the backend total independently of page length. An empty page does not prove that all products were retrieved. Item fields `ext`, `price`, and `product_func` remain JSON-encoded strings, not parsed objects/arrays; see the [sanitized list example](references/product-list.example.json).
- Account deployment lists accept an unwrapped `accounts` array of objects, retained at `data.response.accounts` without inventing totals or pagination. Preserve `deployment: "null"` as a string, distinct from import's JSON null and update's empty string. Masked `key1`/`key2` values are not usable credentials; do not copy list records into write bodies without a known-good write contract. See the [sanitized account-list example](references/account-deploy-list.example.json).
- Import accepts unwrapped `added_count` (nonnegative integer) and `skipped_ids` (array), preserved at `data.response`; see the [import response example](references/import-response.example.json). Report both, including zero added records or skipped entries, rather than claiming every requested record was added. The empty sample array does not establish skipped-entry types or reasons; do not automatically retry skipped records.
- Update accepts exactly `{}` as its empty success acknowledgement, preserved at `data.response`; see the [update response example](references/update-response.example.json). Only update/delete accept this empty-object shape on successful HTTP responses, not arbitrary unmarked objects or empty HTTP bodies. Do not invent updated counts or a returned record.
- Delete requires nonblank `--product-name`, `--region`, and `--account-id`, preserving the exact strings and slash-containing ID. It builds only those three payload fields; no `--body-file` is used. Review the exact target before `--yes`. Its [request](references/delete-body.example.json) and [empty acknowledgement](references/delete-response.example.json) are distinct from import/update bodies. Query account-deploy list with the same product/region to verify removal; do not infer a deleted count, cascade behavior, or cloud-resource deletion.
- A successful write response is the server's acknowledgement, not proof that the deployment is usable. Query `account-deploy list` to verify the resulting record. Timeout/disconnection leaves the write outcome unknown; do not blindly retry. POST requests have no automatic retries and do not follow redirects.
- Authentication failures require refreshing the caller's authorized headers; `bytedcli auth login` is not yet a verified ModelHub login path.
