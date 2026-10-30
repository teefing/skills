# Overseas Vimo creator mutations

This reference covers bounded writes to the CapCut overseas Creator BFF: permissions, labels,
related UID, creator source/type, application review, contracts, and punishment. Also read
[`users.md`](users.md), [`creator-list.md`](creator-list.md), and the parent Skill's
Auth section before executing a command.

## Mandatory preview and confirmation

Every command below is a pure dry-run unless `--yes` is present. A dry-run validates the inputs and
returns the exact `data.action`, `data.target`, and `data.payload` without acquiring a Vimo session
or sending a write. Show that payload and its effects to the user. Only after explicit confirmation
may the otherwise identical command be repeated once with `--yes`.

Only commands currently classified as L3/L4 require non-empty audit `--reasons` together with
`--yes`. Creator-audit approve is L3; creator-audit reject is L2 and has no `--reasons` option. A
business `--reason` for review rejection or punishment remains a separate input; it does not
satisfy audit `--reasons`. Follow the selected leaf's current help and policy.

Never retry a submitted mutation automatically. If a batch stops, report `completed_uids`,
`attempted_uid`, `attempted_outcome`, `unattempted_uids`, and `partial_success`. An
`attempted_outcome` of `unknown` does **not** mean that UID failed: query its current state before
deciding whether any manual retry is safe, and never submit the untouched remainder implicitly.

## Permissions and labels

Discover dynamic values first:

These reads return available permission keys and label IDs, not a specific creator's assigned
permissions or labels. For that state, query `creator list --uids '<capcut-uid>'` first.

```bash
bytedcli --site i18n --json vimo creator permission list
bytedcli --site i18n --json vimo creator label list
```

Use only returned `permissions[].key` and `labels[].id` values:

```bash
bytedcli --site i18n --json vimo creator permission grant \
  --uids '<capcut-uid>' --permissions '<permission-key>'
bytedcli --site i18n --json vimo creator permission revoke \
  --uids '<capcut-uid>' --permissions '<permission-key>'
bytedcli --site i18n --json vimo creator label add \
  --uids '<capcut-uid>' --labels '<label-id>'
bytedcli --site i18n --json vimo creator label remove \
  --uids '<capcut-uid>' --labels '<label-id>'
```

- `--uids` accepts at most 100 unique signed-i64 decimal strings.
- These commands add/remove incrementally; they do not replace a complete collection.
- A confirmed write re-reads the dynamic catalog before sending. If it changed, query and preview
  again.
- Revoking a publishing permission can clear creator level or trigger other Vimo side effects.
- These are not `vimocli material admin user grant|revoke`; that separate operator workflow uses
  numeric Material OpenAPI permissions and a different identity.

## Creator fields

```bash
bytedcli --site i18n --json vimo creator related-uid set \
  --uid '<capcut-uid>' --related-uid '<jianying-uid>'
bytedcli --site i18n --json vimo creator source set --uid '<capcut-uid>' --source operation
bytedcli --site i18n --json vimo creator business-type set --uids '<capcut-uid>' --type producer
bytedcli --site i18n --json vimo creator image-type set --uid '<capcut-uid>' --type producer
```

| Option                     | Values                                                                                                                                  |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `source set --source`      | `agency`, `model`, `operation`, `white-apply`, `tt-anchor`, `creativity`                                                                |
| `business-type set --type` | `normal`, `producer`                                                                                                                    |
| `image-type set --type`    | `producer`, `in-house`, `non-cn`, `cn`, `robot`, `cn-in-house`, `cn-robot`, `cn-producer`, `test`, `cn-test`, `cover-template-producer` |

`source set --force` selects Vimo's explicit force-update route; it is not a general validation
bypass. Source/type changes do not grant publishing permission. Preview and confirm each separate
change independently.

## Application review

UID plus exact `create_time` identifies an application. **Never derive `create_time` from the
current clock.** Query the audit record first, use the returned value verbatim, and then preview
the intended review.

### Required preflight: find the audit record

Query the overseas creator-audit store with an equality predicate on the UID; keep the UID quoted
so the 64-bit identifier is never coerced to a number. The overseas route for this lookup is
`--site i18n-tt --region alisg`.

```bash
bytedcli --site i18n-tt --json rds db query '<creator-audit-database>' \
  "SELECT user_id, create_time, region, audit_result, audit_time \
FROM <creator-audit-table> \
WHERE user_id = '<capcut-uid>' \
ORDER BY create_time DESC LIMIT 10" \
  --region alisg
```

Treat the query as a gate, not as a best-effort hint:

- Select the intended record's returned `create_time` exactly, including its timezone/format; do
  not replace it with `Date.now()`, a formatted local time, or a guessed submission time.
- Confirm that `region` is the intended review region and that the record is still pending
  (`audit_result` and `audit_time` are unset). A missing record means the user has not submitted
  an application; an already-final record must not be reviewed again.
- If multiple pending records are returned, stop and ask the operator to identify the intended
  application by its returned `create_time`. Do not choose one implicitly.

Use the platform-approved database and table identifiers for the deployment. This skill does not
embed production datastore names; the query shape, bounded `LIMIT`, required columns, and overseas
route are the stable contract.

### Command templates

After a successful preflight, first omit `--yes` to receive the mutation preview. Add `--yes` only
after the operator confirms that exact preview. L3 review submission also requires a non-empty
audit `--reasons` value.

Pass the preflight record's two-letter `region` directly with `--region`. For example, a record
with `region: ID` uses `--region ID` and sends `scene: "user_manage_region_ID"`.

```bash
# Approve: preview first (no write)
bytedcli --site i18n --json vimo creator audit approve \
  --uid '<capcut-uid>' --create-time '<exact-create-time>' \
  --region '<record-region>' \
  --reasons '<audit-reason>'

# Approve: submit the approved preview exactly once
bytedcli --site i18n --json vimo creator audit approve \
  --uid '<capcut-uid>' --create-time '<exact-create-time>' \
  --region '<record-region>' \
  --reasons '<audit-reason>' \
  --yes

# Reject: preview first (no write)
bytedcli --site i18n --json vimo creator audit reject \
  --uid '<capcut-uid>' --create-time '<exact-create-time>' \
  --region '<record-region>' \
  --reason '<reject-reason>'

# Reject: submit the approved preview exactly once
bytedcli --site i18n --json vimo creator audit reject \
  --uid '<capcut-uid>' --create-time '<exact-create-time>' \
  --region '<record-region>' \
  --reason '<reject-reason>' \
  --yes
```

Reject reasons may be comma-separated but must come from:
`link_not_working`, `editing_unqualified`, `material_unqualified`, `incorrect_language`,
`watermark_material`, `low_age_material`, `style_underage_eu_us`, `nonlocalized_us`.

Review always uses strict mode. Approval can grant publishing permissions and update creator
source. `--region` validates the returned audit-record region against the Creator Audit region
configuration and sends `scene: "user_manage_region_<region>"`. Approve is L3 and requires
`--reasons` for a live `--yes` submission; reject is L2 and accepts no `--reasons` option. Never
retry an uncertain review. A failed response may include `request_id`; preserve it in the incident
or follow-up rather than resubmitting the review.

## Contracts

```bash
bytedcli --site i18n --json vimo creator contract invite --uid '<capcut-uid>' --type image
bytedcli --site i18n --json vimo creator contract terminate --uid '<capcut-uid>' --type image
```

- New invitations support only `image`.
- Termination supports `video|image` and is only for a current pending/unsigned contract state.
- Query the corresponding contract mode with `user list` first. Contract writes do not
  automatically mutate creator permissions or image creator type.

## Creator and account punishment

```bash
bytedcli --site i18n --json vimo creator punish apply \
  --uid '<capcut-uid>' --duration 7d --reason '<reason>'
bytedcli --site i18n --json vimo creator punish cancel --uid '<capcut-uid>' --reason '<reason>'
bytedcli --site i18n --json vimo creator account-punish apply --uid '<capcut-uid>' --reason '<reason>'
bytedcli --site i18n --json vimo creator account-punish cancel --uid '<capcut-uid>' --reason '<reason>'
```

Creator punishment accepts `3d|7d|14d|30d|forever` and affects C-side publishing/sharing.
Account punishment is a separate indefinite account action. Reasons must be 1..500 readable
characters without control characters. Punishment commands require their business `--reason`;
L3 live submissions additionally require audit `--reasons`. Query current punishment fields before
and after, and distinguish publishing restrictions from account punishment before selecting a write.

## Unsupported writes

Do not expose raw `updateUser`, user create/delete, direct contract repair, score changes, copyright
reset, age-gate changes, batch auto-review, arbitrary endpoint/body, or an unmapped page button.
