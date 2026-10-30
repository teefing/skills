# Pearl SRE semantic read contract

Read this reference when using:

- `routing-main-rule list|get`
- `routing-sub-rule list|get`
- `warehouse-priority list|get`

These commands read current configurations, not actual execution hits, candidate
exclusions, or historical Simulation snapshots. They use the existing private
Pearl session and six registered POST read methods:

```bash
# Exact-ID get uses ListMainAllocRule, not a separate backend Get API
bytedcli --site us-ttp --json pearl supply-chain routing-main-rule get \
  --rule-id 7000000000000000001 --rule-domain online
bytedcli --site us-ttp --json pearl supply-chain routing-main-rule list \
  --country US --status valid --test-flag online --policy-domain fbt

# Simulation is a separate configuration domain: select it explicitly
bytedcli --site eu-ttp --json pearl supply-chain routing-sub-rule list \
  --main-rule-id 7000000000000000001 --type percent --type route-priority \
  --status valid --rule-domain simulation
bytedcli --site i18n-tt --json pearl supply-chain routing-sub-rule get \
  --sub-rule-id 7000000000000000002

# Warehouse priorities have no online/simulation domain selector
bytedcli --site us-ttp --json pearl supply-chain warehouse-priority list \
  --status valid --country US --zone 1 --page 1 --page-size 20
bytedcli --site us-ttp --json pearl supply-chain warehouse-priority get \
  --rule-id 7000000000000000001
```

## Parameters and local pre-check

- Main/sub list needs at least one filter. This is a CLI safety policy, not a
  backend required-field claim. `--rule-domain` alone is not a filter.
- `--rule-domain online|simulation` defaults to online. `--test-flag online|test`
  maps to 0/1 independently; no status/policy filter is added automatically.
- Main list: repeat `--rule-id` or `--status`; optionally use
  `--logistics-service-id`, `--test-flag`, `--country`, `--policy-domain fbt|fs`.
  Logistics service ID is not a last-mile shipping service ID.
- Sub list: repeat `--main-rule-id`, `--sub-rule-id`, `--type`, `--status`, or
  `--name`. Types are `percent=20`, `route-priority=21`, `blacklist=22`,
  `min-limit=23`, `max-limit=24`, `algo=60`. Names retain backend matching
  semantics; fuzzy search is not guaranteed. Routing statuses are
  `created=10`, `valid=20`, `invalid=30`, `gray=40`.
- Warehouse list: single `--rule-id`, optional `--name` (1..100 characters),
  `--zone` (decimal string 1..9, matching the frontend options), repeatable
  `--biz-warehouse-id`, `--seller-id`, `--status`, `--country`.
  Warehouse statuses are `draft=0`, `valid=1`, `invalid=2`.
- IDs are positive decimal int64 strings (maximum 9223372036854775807);
  repeatable filters allow at most 1000 values. Countries must be uppercase
  ISO-2. Invalid input is rejected locally with `PEARL_SRE_INPUT_ERROR`.
- Warehouse list always sends a page: `--page >=1` (default 1), page size
  1..500 via `--page-size` (default 20), with a bounded int32 offset. A single
  CLI rule ID becomes `rule_id: [id]` for `SearchWarehousePriorityConfig`;
  `GetWarehousePriorityConfig` sends scalar `rule_id`. No
  entity-warehouse/ZIP/logistics-service search parameters are added from the
  wider RPC schema.

## Output and safety

- JSON includes `site`, credential `control_plane`, `api_origin`, actual
  `rule_domain`, `query.filters`, `items` or `item`, `returned_count`,
  `pagination`, and `completeness`. BDEE credentials remain in row-bdee while
  business queries use the US API.
- Main/sub lists do not expose `--page`, `--all`, or fabricated totals.
  `completeness.backend_pagination` is `backend-pagination-unavailable`;
  `configuration_complete` remains null because complete configuration-set
  coverage cannot be proven. Warehouse pages preserve unknown total/has_more
  as null rather than replacing total with returned count.
- `completeness.backend_truncated` is `true` only for explicit backend
  truncation and `null` when the backend does not provide that signal.
- Text and JSON retain full nested `global_config`, all sub-rule bodies,
  warehouse sub-rules, unknown fields and historical spellings (`prioirty`,
  `warehoue_name`). Numeric ID fields/lists are normalized to decimal strings.
  Timestamps stay in their original units; absent version/time fields are not
  invented. Known backend truncation marks the list response incomplete.
  The Pearl Supply Chain credential sanitizer still applies; its use is marked
  in `completeness.safety_sanitization`, not bypassed by these commands.
- Route-priority (type 21) is carrier/route preference, not warehouse priority.
  Sub-rule `priority` is also distinct from configuration/warehouse priority.
- ZIP/TOS/compressed references remain unexpanded, even if a backend returns
  only a reference. No download, permission application, browser/keychain
  access, cross-domain/site fallback, mutation, or automatic authorization is
  performed. The transport uses a 30-second timeout and a 16MiB response bound.
- Exact gets report `PEARL_SRE_NOT_FOUND` for zero rows, `PEARL_SRE_CONFLICT`
  for multiple/nonmatching IDs, and `PEARL_SRE_RESPONSE_INCOMPLETE` for explicit
  truncation. Malformed responses return `PEARL_SRE_RESPONSE_INVALID`; business
  and HTTP permission failures are not treated as successful empty results.
- Missing/expired sessions return `PEARL_AUTH_REQUIRED` with the exact
  `bytedcli --site <site> auth pearl-session login` command. Run login
  explicitly; SRE semantic reads do not auto-refresh authorization.
