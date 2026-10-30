# Argos Alert Actions

Use these deterministic OpenAPI commands for alert ACK, silence, cancellation and
rule-level silence records. No Agent session or model execution is involved.

## Commands

```bash
# Read the rule to distinguish its internal id from its console uid.
bytedcli --json --site i18n-tt apm argos alarm rule get --uid 123456789

# All mutations preview by default. Copy the exact group and monitoring region
# from trusted alert context. Tags use key/val, not key/value.
bytedcli --json --site i18n-tt apm argos alarm ack --alert-group-id demo-alert-group --check-vregion Singapore-Central --tags '[{"key":"cluster","val":"demo-cluster"}]'
bytedcli --json --site i18n-tt apm argos alarm silence --alert-group-id demo-alert-group --check-vregion Singapore-Central --tags '[{"key":"cluster","val":"demo-cluster"}]' --minutes 10
bytedcli --json --site i18n-tt apm argos alarm reset-silence --alert-group-id demo-alert-group --check-vregion Singapore-Central --tags '[{"key":"cluster","val":"demo-cluster"}]'

# Only after the user confirms the exact preview, append --yes to that command.
# --dry-run explicitly previews; --yes and --dry-run cannot be combined.

# Read one page of effective records using the internal rule ID, not its UID.
bytedcli --json --site i18n-tt apm argos alarm silence-list --rule-id 123456789 --check-vregion Singapore-Central --effective-only --page 1 --page-size 20
```

`ack`, `silence`, and `reset-silence` require exactly one `--alert-group-id` or
`--rule-uid`, plus explicit `--check-vregion` and `--tags` JSON. Prefer the alert
group for one alert. A rule UID targets that rule's matching alerts. `--tags '[]'`
explicitly removes tag restrictions; never supply it merely because tags are
missing. Rule identifiers are positive signed 64-bit decimal strings and are
sent losslessly as JSON integers. Broad PSM/tree-node and batch writes are not
exposed by these commands.

`silence` requires whole `--minutes` in 2..10079, strictly longer than one minute
and shorter than one week. It does not ACK. `reset-silence` does not undo ACK.
For "confirm and silence", preview and authorize both commands, then ACK once
and silence once. They are independent requests, not an atomic operation. If ACK
fails or is uncertain, stop. If silence fails after ACK succeeds, retain the ACK
receipt and inspect current state; never repeat the whole sequence.

## Authentication And Routing

- Supported control planes: global `--site cn` and `--site i18n-tt`. Other sites
  fail before authentication or HTTP; no cross-site fallback is attempted.
- Credentials use the existing site-specific `SSOClient` chain, including global
  user/app selection and Argos-managed service-account JWT injection. There is no
  new token flag, token store, or browser-cookie fallback. Keep tokens out of
  command arguments, output and temporary files.
- The API uses the ByteCloud gateway, `Domain: alarm-platform`, Bearer auth and
  `x-jwt-token`, not the alarm-rule BFF. ROW production hosts use the existing
  `BYTEDCLI_NETWORK_PROFILE=prod` convention. Host overrides for the rule BFF,
  metrics or Argos Agent do not override this fixed alert route.
- Optional `--ack-by` is upstream audit attribution, not a credential or a way
  to gain permissions. Omit it to leave attribution to the backend identity.

## Results And Verification

Mutation output includes `mode` (`preview`, `dry_run`, or `accepted`), the exact
wire request body, receipts, and `state_verified: false`. `accepted` requires a
zero API error code, successful per-item receipts, and matching selector/region;
it does not establish persistent ACK state, Lark card synchronization, or incident
recovery. The response may omit the submitted tags; the request body preserves
them without claiming independent verification.

Writes disable automatic HTTP retries and redirects. Timeout, malformed response,
target mismatch, explicit failure or partial failure must not be retried blindly.
Partial-failure errors preserve per-item receipts. Read current state first.

After silence/cancellation, use `silence-list --effective-only` for the associated
internal rule ID and compare region, tags, user and expiry. Follow pagination if
needed: default page size 20, allowed 1..500. An absent upstream total stays null,
not the current page length. Omit `--effective-only` for all retained records.
No automatic readback is claimed because these endpoints do not supply a
verified alert-group-to-internal-rule-ID lookup.

The list API only exposes rule-level records. Empty results cannot rule out a
PSM-level silence. `is_ack` describes the record type and is not an authoritative
query of an alert's current ACK state.
