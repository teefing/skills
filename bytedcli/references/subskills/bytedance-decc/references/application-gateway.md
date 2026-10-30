# Application Gateway (AG) API registration

Use `bytedcli decc ag` for `/application_gateway/psm_detail/...` and `/application_gateway/api_detail/...` entries. These are separate from `decc gateway` OG entities and endpoint IDs. The AG commands use the authenticated DECC portal API, not a browser dependency or an exported cookie.

The mutation workflow supports **new HTTP APIs under an existing, approved, US-only Web/AG PSM**. PSM creation, existing approved API revisions, other regions and field-level tagging remain portal operations. A channel with multiple reviewing geos is refused rather than implicitly submitting to all of them.

## Inspect the target and BAM contract

Authentication uses the personal `i18n-tt` login even though the target registration region is US. AG channel, API, draft and ticket IDs remain strings; BAM endpoint IDs remain validated safe-integer numbers. Global HTTP/proxy options apply normally.

```bash
bytedcli --site i18n-tt --json decc ag psm list --psm example.demo.api
bytedcli --site i18n-tt --json decc ag psm get --channel-id demo-channel-id
bytedcli --site i18n-tt --json decc ag api list --channel-id demo-channel-id --stage approved
bytedcli --site i18n-tt --json decc ag api list --channel-id demo-channel-id --stage draft
bytedcli --site i18n-tt --json decc ag api get --id demo-api-id
bytedcli --site i18n-tt --json decc ag bam list --psm example.demo.api
bytedcli --site i18n-tt --json decc ag bam get --psm example.demo.api --path /demo/items --method POST
```

PSM and API lists are paginated (`--page`, `--page-size`, default page size 20). BAM list returns the endpoints visible to DECC at the current BAM version. Match the exact method and path to the merged IDL; do not import every endpoint of a PSM merely because it appears in BAM.

## Import one API and annotate its draft

All writes default to a read-only preview. Import verifies the exact PSM, endpoint, serializer and BAM version. It scans approved APIs, drafts and submitted tickets before saving, refusing duplicate or incomplete scans. An existing draft is preserved; inspect and update it explicitly instead of overwriting it with BAM.

```bash
bytedcli --site i18n-tt --json decc ag api import --psm example.demo.api --path /demo/items --method POST --dry-run
# Review bam_version from the preview, then pin that exact version.
bytedcli --site i18n-tt --json decc ag api import --psm example.demo.api --path /demo/items --method POST --expect-bam-version 1.0.1 --yes
bytedcli --site i18n-tt --json decc ag draft get --draft-id demo-draft-id
bytedcli --site i18n-tt --json decc ag draft update --draft-id demo-draft-id --description 'Lists configured items within the authorized account.' --audience users --business-domain 'demo|items' --auth-level authorized-users --dry-run
# Repeat the same annotation command with its reviewed snapshot_digest.
bytedcli --site i18n-tt --json decc ag draft update --draft-id demo-draft-id --description 'Lists configured items within the authorized account.' --audience users --business-domain 'demo|items' --auth-level authorized-users --expect-snapshot <snapshot_digest> --yes
```

Use an English description that explains the action, object and request/response scope. Copy `--business-domain` only from a semantically compatible approved API, using its leaf ID path. The annotation update preserves the existing draft fields and schema and rereads the saved result.

- Audience: `users` = For TT Users; `developers` = For TT Development (external TikTok developer OpenAPI); `lark` = For Lark. Internal employee tooling is not automatically an external developer OpenAPI.
- Authorization: `unauthenticated`, `authenticated-users`, `authorized-users`. Select according to the actual endpoint authentication and authorization contract. Do not broaden authorization simply to satisfy the form.
- A snapshot binds the operation, current draft/channel and intended request. An edited draft or changed annotation arguments require a new preview. The draft is reread after duplicate scanning before the write snapshot is checked; this client-side check is not an atomic server-side lock.

## Submit and read back the ticket

```bash
bytedcli --site i18n-tt --json decc ag draft submit --draft-id demo-draft-id --dry-run
# This flow deliberately submits API-level annotations without request/response schema fields.
bytedcli --site i18n-tt --json decc ag draft submit --draft-id demo-draft-id --api-level-only --expect-snapshot <snapshot_digest> --yes
bytedcli --site i18n-tt --json decc ticket get --surface portal --ticket-id demo-ticket-id
```

`--api-level-only` is explicit acknowledgement of API-level submission. Drafts with field annotations are refused instead of silently stripping those annotations. This does not prove field-level coverage or real TTP traffic. Submit checks existing registrations and tickets again, then verifies the returned ticket's PSM, method/path, region, serializer, BAM identity and API-level attributes. Preserve the returned status: automated approval may already be `finished`; `pending` means approval is outstanding.

Mutation HTTP retries are disabled. A timeout, malformed success response or failed readback returns `DECC_AG_OUTCOME_UNKNOWN`. The write may have succeeded. Inspect the returned draft/ticket ID (when available) and the target API lists in DECC before retrying; never blindly replay a submission.
