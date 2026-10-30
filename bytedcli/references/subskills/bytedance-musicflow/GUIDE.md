---
name: bytedance-musicflow
description: "Use when finding, creating or editing MusicFlow workflows, ASL definitions, batches, operators or production routes, binding or publishing a definition, inspecting execution failures, or creating or retrying one execution through bytedcli."
---

# MusicFlow resources, definitions, batches, operators, production routes and executions

Use `bytedcli musicflow` to inspect and manage workflows, their ASL definitions, batches, operators, production routes, and execution records through the Dashboard BFF.

## Authentication and sites

Use global `--site cn`, `--site i18n-tt`, or `--site boe`. Authentication uses your ByteCloud user JWT; the Dashboard must have JWT support deployed. Unsupported sites fail without falling back to CN. For a CN PPE deployment, add `--lane ppe_<name>` to the MusicFlow leaf command; this sends `x-tt-env` and `x-use-ppe` only to the Dashboard request.

## Commands

- `workflow list [--search <text>] [--owner <user>] [--status init|running|stopped]`: find business workflows.
- `workflow get --id <id>`: inspect one business workflow and its bound definition ID.
- `workflow definition list --workflow-id <id>`: list definitions belonging to a business workflow.
- `workflow definition get --id <id>`: inspect a definition, including its ASL.
- `batch list [--name <name>] [--owner <user>] [--workflow-id <id>] [--status running|stopped]`: find batches before listing executions.
- `batch get --id <id>`: inspect one batch and its configuration.
- `operator list [--search <text>] [--owner <user>]` and `operator get --id <id>`: inspect operator definitions.
- `production-route list [--name <name>] [--owner <user>] [--status init|running|stopped]`: find production routes (page size at most 50).
- `production-route get --id <id>`: inspect one production route, its bound definition and latest init draft.
- `production-route definition list --route-id <id> [--status init|running|deprecated]`: list definitions for a route.
- `production-route definition preview --config|--config-file ... --param|--param-file ... [--business-key <key>]`: read-only render of batch params for a config; always submits (no `--yes`).
- `execution get --id <id>`: inspect one execution, including status, error information and available definition/RDM details.
- `execution create --batch-id <id> --business-key <key> --param <json>|--param-file <path> [--priority 1-99] [--dedup-key <key>]`: preview creating one execution in a batch; add `--yes` to submit with Kani batch `all` permission. Priority defaults to 50. The param JSON text is sent unchanged, so 64-bit integers keep full precision.
- `execution retry --id <id>`: preview a single execution retry; add `--yes` to submit with Kani batch `all` permission. Add `--force` to pass Broker ForceRetry; it still previews without `--yes`. Deploy the matching BFF first.
- `execution list --batch-id <id>`: query one page of executions in a known batch. Optional filters: `--status init|running|success|failed`, `--business-key <key>`.
- Add `--start` and `--end` together for a creation-time window, inclusive start and exclusive end. Use ISO timestamps with a timezone and whole seconds (fractional seconds are rejected); the window must be at most 31 days. `--error-like` uses a SQL LIKE pattern (% = any sequence, \_ = one character), requires this window and accepts 1-512 UTF-8 bytes. Matching case sensitivity follows the selected database.

### Writes

Every write below previews by default and submits only with `--yes`; the owner is always the logged-in user. Workflow and definition writes need Kani workflow `all`, batch writes batch `all`, operator writes operator `all`, production-route writes production_route `all` (Kani resource `music_flow_production_route`). Production-route trigger is not exposed; business callers use Broker `TriggerProductionRoute`.

- `workflow create --name <name>`: create a business workflow. Names are unique.
- `workflow definition create --workflow-id <id> --name <name> [--asl <json>|--asl-file <path>]`: create a definition; it always starts in `init`. The ASL must be a JSON object whose `StartAt` names a state in `States`; its text is sent unchanged.
- `workflow definition update --id <id> [--name <name>] [--asl <json>|--asl-file <path>] [--status running]`: rename, replace the ASL (only while `init`), or publish `init` to `running`.
- `workflow update --id <workflow-id> --definition-id <id>`: bind a `running` definition as the active definition. The previously bound definition becomes `deprecated`; a never-bound workflow switches to `running`. The preview reads both records and lists these effects in `warnings`.
- `batch create --workflow-id <id> --name <name> [--config <json>|--config-file <path>]` and `batch update --id <id> [--name <name>] [--config ...]`: the config object accepts `qps_limit`, `exec_keep_rules`, `retry_config`, `monitor_rules` and `process_config`. Batch update never changes the batch status.
- `operator create --spec <json>|--spec-file <path>`: fields `name` (3-100 characters), `type` (`rpc`, `http`, `local_method`, `workflow`), `available_regions` (non-empty), `target_detail` (required), optional `id` (decimal string), `async`, `available_idc`, `qps_limit`, `input_param`, `output_param`, `data_dependency`, `data_destination`.
- `operator update --id <id> --spec <json>|--spec-file <path>`: only `available_regions`, `available_idc`, `status` (`active`, `deprecated`), `target_detail`, `qps_limit`, `data_dependency` and `data_destination` can change; other fields are rejected because the Dashboard BFF does not forward them.
- `production-route create --name <name>`: create a production route in `init`.
- `production-route update --id <id> [--name <name>] [--owner <user>] [--status running|stopped]`: rename, transfer ownership, or start/stop. Publishing a definition is what first moves `init` to `running`.
- `production-route definition create --route-id <id> --name <name> --config|--config-file ...`: create an `init` definition. Config is a JSON object with `Inputs` and a non-empty `BatchTargets` array; it is sent as a nested object.
- `production-route definition update --id <id> --route-id <id> [--name <name>] [--config ...]`: rename or replace config while `init`. `--route-id` is required so the preview can load the current definition (there is no definition-detail route).
- `production-route definition publish --route-id <id> --definition-id <id>`: publish an `init` definition as the active one. The previously bound definition becomes `deprecated`; a never-published route switches to `running`. The preview lists these effects in `warnings`.
- Config and operator JSON fields may be JSON objects or strings containing JSON. Objects are serialized, so quote values that contain integers above 2^53 as a JSON string. Production-route definition config is sent as a nested JSON object, not a stringified field.

```bash
bytedcli --site boe auth login
bytedcli --site cn -j musicflow workflow list --lane ppe_music_test
bytedcli --site boe -j musicflow workflow list --search demo
bytedcli --site boe -j musicflow workflow definition list --workflow-id 1234567890123456789
bytedcli --site boe -j musicflow workflow definition get --id 1234567890123456791
bytedcli --site boe -j musicflow batch list --workflow-id 1234567890123456789
bytedcli --site boe -j musicflow operator get --id 1234567890123456792
bytedcli --site boe -j musicflow execution get --id 1234567890123456789
bytedcli --site boe -j musicflow execution retry --id 1234567890123456789
# Submit only after the user has authorized retrying this execution.
bytedcli --site boe -j musicflow execution retry --id 1234567890123456789 --yes
bytedcli --site boe -j musicflow execution create --batch-id 1234567890123456790 --business-key demo-key --param-file ./param.json --dedup-key demo-key-20260101
# Submit only after the user has authorized creating this execution.
bytedcli --site boe -j musicflow execution create --batch-id 1234567890123456790 --business-key demo-key --param-file ./param.json --dedup-key demo-key-20260101 --yes
bytedcli --site boe -j musicflow execution list --batch-id 1234567890123456790 --status failed --page 1 --page-size 20
bytedcli --site boe -j musicflow execution list --batch-id 1234567890123456790 --business-key demo-key
bytedcli --site boe -j musicflow execution list --batch-id 1234567890123456790 --status failed --start '2026-01-01T00:00:00+08:00' --end '2026-01-02T00:00:00+08:00' --error-like '%timeout%'
bytedcli --site boe -j musicflow workflow definition create --workflow-id 1234567890123456789 --name demo-v2 --asl-file ./demo.asl.json
bytedcli --site boe -j musicflow workflow definition update --id 1234567890123456791 --status running
bytedcli --site boe -j musicflow workflow update --id 1234567890123456789 --definition-id 1234567890123456791
# Submit writes only after the user has authorized the previewed change.
bytedcli --site boe -j musicflow workflow update --id 1234567890123456789 --definition-id 1234567890123456791 --yes
bytedcli --site boe -j musicflow batch update --id 1234567890123456790 --config '{"qps_limit": {"qps": 10}}'
bytedcli --site boe -j musicflow operator update --id 1234567890123456792 --spec-file ./operator.json
bytedcli --site boe -j musicflow production-route list --name demo-route
bytedcli --site boe -j musicflow production-route definition create --route-id 1234567890123456789 --name demo-v1 --config-file ./route-config.json
bytedcli --site boe -j musicflow production-route definition publish --route-id 1234567890123456789 --definition-id 1234567890123456793
# Submit only after the user has authorized the previewed publish.
bytedcli --site boe -j musicflow production-route definition publish --route-id 1234567890123456789 --definition-id 1234567890123456793 --yes
```

## Interpreting results

- `status_name` distinguishes `init`, `running`, `success`, `failed`; only success and failed have `is_terminal: true`. Unknown states have `status_name: unknown` and `is_terminal: null`.
- `error_info` is preserved when present. An Init or Running execution is not a successful execution.
- Status/business-key filters are sent to the server before pagination. Lists require a batch ID and never scan all batches.
- Default page size is 20, maximum 100. The backend permits at most 100 pages. `has_more` indicates remaining records; `next_page` is null at the limit, with `page_limit_reached: true` and a hint to narrow filters. One page is not a complete export. An empty later page does not prove the batch has no failures.
- IDs remain decimal strings. Preserve full precision.
- Resource lists return one page with `total`, `has_more`, and `next_page`; use `--page` and `--page-size` (1–100, production-route lists 1–50). A page is not a full export.
- Workflow, definition, batch, operator and production-route reads require the corresponding Kani read permission. The Dashboard BFF must have JWT access for these exact routes deployed.
- HTTP 200 with `success: false` is a query error, not an empty result.
- Time/error filters run on the server before both counting and pagination. Deploy the matching Manager and BFF first; a missing filter acknowledgement is an error, never an unfiltered fallback.
- Retry completion is not execution success. The Broker may return without retrying a non-failed execution; a stopped batch prevents retry. Check state with `execution get` afterward. No transport retry on timeout/5xx; inspect state before resubmitting after an ambiguous failure.
- Retry preview and submission share `dry_run`, `force`, `lane`, `execution_id`, `method`, `endpoint`, `query`, `result` and `hint`. Preview returns `result: null`; submission puts the BFF response in `result`. List `hint` is null unless the page limit requires narrowing filters.
- ForceRetry retains Broker eligibility checks: successful executions are still skipped, stopped batches are rejected, and non-failed executions must be at least two hours old. It uses the Broker force retry-count ceiling instead of the batch ceiling; it is not unlimited retry.
- Execution create is not idempotent without `--dedup-key`: every submission creates another execution. Prefer a dedup key. After `is_new: false`, the dedup key matched an existing execution and nothing new was created. A created execution is not a successful execution; check it with `execution get`.
- Execution create preview and submission share `dry_run`, `execution_id`, `is_new`, `method`, `endpoint`, `body`, `lane` and `hint`. Preview returns `execution_id: null` and `is_new: null`.
- Resource writes share `dry_run`, `method`, `endpoint`, `body`, `lane`, `current`, `warnings`, `result` and `hint`. Preview returns `result: null`; after `--yes`, creates return `result: {id}` and updates return the BFF response. Creates return `current: null`. Binding returns `current.workflow` (`id`, `name`, `status`, `definition_id`, null when unbound) and `current.definition` (`id`, `name`, `biz_workflow_id`, `status`, `status_name`). Other updates return the current values of the fields being changed; definition update also reports `status`, `status_name` and, with a new ASL, `asl_changed`. Read `warnings` before adding `--yes`: they list effects such as deprecating the previous definition and changes Manager will reject or ignore.
- `MUSICFLOW_WRITE_UNCONFIRMED` means a write or retry may have reached Manager or Broker (5xx, timeout, business error, invalid receipt, or a `--force` retry the BFF did not acknowledge). Never resubmit blindly; first run the lookup command from the hint. Duplicate workflow, definition and batch names are rejected, but execution create without `--dedup-key` is not protected. Authentication failures and HTTP 4xx keep their original error codes and changed nothing.
- Deleting, starting or stopping workflows and batches, and node-specific retry are not exposed.

## References

- [Invocation](../../invocation.md): read for CLI setup, authentication, global site selection and JSON invocation. MusicFlow supports only the three sites listed above.
- [Troubleshooting](../../troubleshooting.md): read when authentication, invocation or response handling fails.
