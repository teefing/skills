# Lumios training and DevBox GPU reservations

Use `bytedcli aicolate train` for Lumios operations in ROW. These commands
use the shared personal ByteCloud JWT, native bytedcli JSON output and HTTP
configuration. Authentication is shared with other Aicolate commands.

Paginated commands accept `--page-size` from 1 to 20 (default 20). Task lists
return `page_count`, `has_more` and `scan_complete`; the latter is false when
more backend pages remain and true when the scan is complete or an exact ID
has been resolved. The previous `aicolate dev train list` entry is replaced by
`aicolate train list`.

## Identify the user and select a scope

```bash
bytedcli --site i18n-tt auth login
bytedcli --json aicolate train identity get
bytedcli --json aicolate train tenant list
bytedcli --json aicolate train resource list --tenant <tenantId>
bytedcli --json aicolate train environment diagnose
```

Use the employee login returned by `identity get`. Tenant selection contains
permitted teams and businesses, including business scene IDs. Select the exact
`cluster`, `topic_name` and `gpu_type` tuple from resource list. Only a unique
candidate may be selected automatically; do not invent IDs or resource names.

Ordinary task creation requires an active child business (`--sub-business-id`).
`business_scene_id` from tenant list identifies its parent business. Run
`bytedcli aicolate train sub-business list --tenant <id> --parent-business-id <business_scene_id>`
to select the child ID. Creation can select it automatically only when that
parent has exactly one active child. Cloning preserves the source child ID.
Stable A1 uses business A1 resources,
other stable priorities use team quota, and SPOT uses global Spot resources.
SPOT requires C1 and cannot be retryable. Availability can be zero while the
resource still has capacity: the request can queue.

## Preview, create, inspect and clone a training task

```bash
# Preview a template submission. Add --yes after inspecting this exact request.
bytedcli --json aicolate train create \
  --tenant <tenantId> --team-id <teamId> --business-id <businessId> \
  --sub-business-id <sceneId> --task-name demo-train \
  --task-type stable --priority B1 \
  --cluster demo-cluster --topic-name demo-topic --gpu-type demo-gpu --gpu-count 2 \
  --template-name demo-template --template-version 1 \
  --prod-line demo-namespace --entrypoint 'python train.py'

# A JSON file may contain the original task submission or platform_input.
bytedcli --json aicolate train create \
  --tenant <tenantId> --team-id <teamId> --business-id <businessId> \
  --sub-business-id <sceneId> --task-name demo-scratch \
  --task-type spot --priority C1 \
  --cluster demo-cluster --topic-name demo-topic --gpu-type demo-gpu --gpu-count 2 \
  --task-params ./demo-params.json --launch-mode from_scratch

bytedcli --json aicolate train list --tenant <tenantId> --page 1 --page-size 20
bytedcli --json aicolate train list --tenant <tenantId> --platform-task-id <jobRunId>
bytedcli --json aicolate train list --tenant <tenantId> --task-name demo-train --submitter demo-user
bytedcli --json aicolate train get --id <aicolateId> --tenant <tenantId>
bytedcli --json aicolate train status get --id <aicolateId> --tenant <tenantId>
bytedcli --json aicolate train diagnose --id <aicolateId> --tenant <tenantId>
bytedcli --json aicolate train clone --id <aicolateId> --task-name demo-clone
bytedcli --json aicolate train cancel --id <aicolateId> --tenant <tenantId>
```

Creation writes one platform-visible Aicolate row. It does not also create a
second resource-management task. List/get/status/clone-source lookup read the
same platform row projection. Aicolate row ID, Lumios task ID and Merlin JobRun
ID are different identifiers; `--id` on ordinary task commands is the Aicolate
row ID. Cancel requires the explicit Lumios mapping from that row. Missing or
unknown status/mapping is an error, rather than a guessed cancellation target.
An accepted submission resolves its Aicolate row ID with one list read. Use the
returned `task_id` / `aicolate_task_id` for get and cancel; `lumios_task_id` and
`submission_task_id` are separate identifiers. If `lookup.status` is pending or
failed, list by the returned tenant and task name. The write was accepted and
must not be resubmitted just because that follow-up read failed.

Lists are tenant-scoped and preserve `page`/`page_size`. Filters include ID,
platform task ID, name, submitter, status, team, business, scene, quota class and
cluster. Client filters scan at most 50 backend pages. Inspect `scan_complete`
and `has_more`; omitted totals mean the server did not provide a complete total.
Get/clone/cancel can discover accessible tenants if `--tenant` is omitted, and
report an incomplete lookup rather than falsely claiming absence at the scan limit.

Clone submits as the current employee. Supply a new name; omitted quota and
retry settings are inherited. It preserves namespace/product line, code branch
and commit, `train_params`, safe UI form snapshot, source GPU variant and
non-template launch mode. Namespace/code overrides update the nested parameter
and form copies together. Runtime credentials are replaced by the current user
credential; they are redacted in output and rejected in input files. Template
overrides on a `from_scratch` source are rejected. If original parameters are
missing, provide `--task-params` explicitly rather than inventing them.

GPU totals must equal the sum of all Arnold `num * gpu` allocations. A single
role's `--gpu-count` / `--role-num` overrides must divide evenly. For multiple
roles, provide a complete updated parameter file instead of an ambiguous total
or role-count override.

## Immediate B1/C1 DevBox reservation

```bash
# Preview. Reuse the returned key with --idempotency-key on the confirmed submission.
bytedcli --json aicolate train reservation create \
  --tenant <tenantId> --team-id <teamId> --business-id <businessId> \
  --cluster demo-cluster --topic-name demo-topic --gpu-type demo-gpu \
  --gpu-count 1 --priority B1 --idempotency-key demo-request-key

bytedcli --json aicolate train reservation list --tenant <tenantId> --creator demo-user
bytedcli --json aicolate train reservation get --id <reservationId>
bytedcli --json aicolate train reservation-match list --id <reservationId> --page 1 --page-size 20
bytedcli --json aicolate train reservation cancel --id <reservationId>
bytedcli --json aicolate train usage get --team-id <teamId>
```

After a confirmed create, `reservation_id` is `null` when the response does not
include an ID. `lookup.status` is then `pending`, with list filters and the
original `idempotency_key`; inspect `reservation list` for that exact key.
Do not infer an ID or retry with a new key. A returned ID sets
`lookup.status` to `resolved`.

Reservations immediately join the unified B1/C1 queue. There is no scheduled
start time, update operation, sub-business field or automatic Merlin worker
launch. PENDING_RESOURCE consumes no quota. RESERVED consumes shared used quota
and supplies `reserved_at` / `expire_at`, a creation window for a Merlin DevBox
worker. A quota grant or match does not prove physical GPUs have been allocated.
Notifications and no-show recording remain server responsibilities.

Launch the user-authorized Merlin worker with the exact resource tuple during
the returned window, using Merlin tooling available in the execution environment.
The reservation matches user, time and resource; the matched job inherits the
reservation's team/business. This does not independently prove tenant ownership
from a shared queue or invent a sub-business association.

`reservation-match list` supplies the matched Aicolate/Lumios IDs, JobRun ID and
accounting flags. A matched reservation cannot be cancelled. Cancel its task
separately using the Aicolate row ID. A pending or reserved unmatched reservation
can be cancelled; cancellation acceptance is asynchronous and does not itself
confirm quota release. Inspect `settled_at` and compare quota usage to the
baseline. SETTLED describes the reservation window, and is not proof that a
matched worker has finished or its quota was released. After a task ends, check
its actual terminal state and quota holders. Other tasks can keep total used
quota above zero. Preserve all overview pagination/completeness flags.

## PPE and network routing

Append `--ppe-env <lane>` to every command targeting a PPE lane:

```bash
bytedcli --json aicolate train reservation list --ppe-env ppe_demo_lane
bytedcli --json aicolate train usage get --team-id <teamId> --ppe-env ppe_demo_lane
```

The lane is applied to identity, context, resource, task and reservation requests,
including a network fallback. Without it, the command uses PROD. PPE and PROD
share quota counters, so PPE grants and releases should also change PROD's
available quota. Test changes affect this shared quota.

ROW uses bytedcli's existing office/production network selection. Set
`BYTEDCLI_NETWORK_PROFILE=prod` when choosing the production-network route.
A business error 4005 or certificate failure on a GET request triggers one
retry at the configured ROW backup. After success, subsequent requests in the
same command use that route. TLS verification remains enabled. SSL failures on
writes, timeouts and other uncertain write outcomes do not cause write replay.
`--no-url-fallback` disables this route change. These Lumios commands support
ROW only; do not use another region's resources as a fallback.
