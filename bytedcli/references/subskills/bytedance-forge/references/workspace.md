# Saved Workspace views

Use `bytedcli forge workspace` to manage saved comparison views. This changes display/configuration only: it does not create, kill, restart, reprioritize, or deploy training jobs.

## Read and identify the view

Select the control plane explicitly with global `--site`, or pass a formal Workspace `--url`. URL and explicit site/id conflicts fail before authentication. Draft URLs containing `tempViewId` are rejected.

```bash
bytedcli --site eu-ttp --json forge workspace list --project-id 17
bytedcli --site eu-ttp --json forge workspace get --view-id 41
# Export the complete configuration; normal stdout remains a compact summary.
bytedcli --site eu-ttp --json forge workspace get --view-id 41 --output demo-config.json
bytedcli --site eu-ttp --json forge workspace get --view-id 41 --section config
```

`get` returns the formal URL, a snapshot hash, and every panel's criterion ids, job ids, canonical head names, target mappings, metrics, dates, and baseline. No AUC query or training-status polling is needed to edit a view. `--output` exports the configuration object, which `--content-file` accepts. Import is a complete replacement, not a partial merge: configuration saves and panel synchronization require a valid `serializedDiStore` object/string containing a `panels` array. Missing, null or malformed stores are rejected before writing; an explicitly empty `panels: []` remains distinguishable from missing configuration.

## Batch changes and save once

Writes preview by default. JSON previews include an ordered `requests` array for every planned native write, including both the view save and backend panel synchronization; use `--jq` to select summary fields when a full payload would be too large for the agent context. Review the intended change before explicitly applying the same inputs with `--yes`.

```bash
# Replace two reruns throughout every existing panel; keep aliases and settings.
bytedcli --site eu-ttp --json forge workspace update --view-id 41 --replace-job 101:303,102:304
bytedcli --site eu-ttp --json forge workspace update --view-id 41 --replace-job 101:303,102:304 --expected-hash '<hash-from-get>' --yes
# Add to all panels using a known template, switch baseline, and remove an old job.
bytedcli --site eu-ttp --json forge workspace update --view-id 41 --add-job 305 --template-job-id 202
bytedcli --site eu-ttp --json forge workspace update --view-id 41 --baseline-job 303 --remove-job 202
# Change the displayed sample dates and native graph mode.
bytedcli --site eu-ttp --json forge workspace update --view-id 41 --start-date 2026-02-01 --end-date 2026-02-07 --show-mode diff --layout 2
# Import a full exported configuration, optionally followed by batch operations.
bytedcli --site eu-ttp --json forge workspace update --view-id 41 --content-file demo-config.json --operations-file demo-operations.json
```

Addition clones all head/metric/filter criteria belonging to the template job in each panel, filling missing combinations without duplicating existing ones. Metric counts and task heads are not fixed.

Replacement/addition resolves the new model from the job id and matches each canonical head name against its metadata. Numeric `head_N` indices can differ between jobs. Missing heads, ambiguous models, or duplicate replacement criteria reject the batch before writing. Every existing panel is processed without a fixed metric list or count.

The existing aliases, criterion names/ids, baseline pins, panel order, dates, filters, display mode, and unmodified/unknown fields are preserved on replacement. Adding a job creates new criterion ids and never pins it automatically. Remove a pinned baseline only after selecting a replacement baseline. The tool does not remove unrelated jobs to work around the UI's comparison limit.

### Operations file

An ordered JSON array composes the common edits in one save. For a job exposing several model versions, specify `modelName` on its `replace-job` or `add-job` operation.

```json
[
  {"op":"replace-job","from":101,"to":303,"modelName":"demo-model"},
  {"op":"alias","jobId":303,"value":"demo-strategy"},
  {"op":"baseline","jobId":202},
  {"op":"order","jobIds":[202,303]},
  {"op":"visibility","jobId":303,"visible":true},
  {"op":"display","mode":"origin","layout":1},
  {"op":"time","start":"2026-02-01","end":"2026-02-07"},
  {"op":"panel-head","panel":"demo-panel-id","head":"demo:ctr"},
  {"op":"set","path":["serializedDiStore","panels","0","name"],"value":"demo-title"}
]
```

For a panel with multiple criteria for the same job, select a single native baseline explicitly, for example `{"op":"baseline","panel":"demo-panel-id","jobId":202,"criterionId":"demo-criterion-id"}`. An ambiguous baseline is rejected before saving.

Also supported: `add-job` with `jobId`, optional `templateJobId`, `modelName`, `alias`; `remove-job` with `jobId`. `order` puts listed jobs first and retains the relative order of others. `visibility` changes checked comparison jobs while preserving their criteria; enabling a job requires an existing panel criterion. Null job-id lists normalize to empty lists consistently, replacement preserves number/string scalar job references, and removal retains the native empty-string unset sentinel. `set` edits a JSON field (for example a metric title, metric type, existing color/filter/display setting, or granularity) while retaining surrounding fields. Use paths from the exported configuration; do not invent backend fields. Use `--template-job-id` only with the `--add-job` shortcut; JSON additions specify their own `templateJobId`. Unsafe prototype paths and invalid array indices are rejected. Use a full content file to replace the entire serialized store or panels array.

## View lifecycle

```bash
# Create an empty view or initialize one from an exported configuration.
bytedcli --site eu-ttp --json forge workspace create --project-id 17 --name demo-view
bytedcli --site eu-ttp --json forge workspace create --project-id 17 --name demo-view --content-file demo-config.json
# Copy all panels/settings without changing the source view.
bytedcli --site eu-ttp --json forge workspace create --from-view-id 41 --name demo-copy
# Rename or preview deletion; add --yes only for an authorized write.
bytedcli --site eu-ttp --json forge workspace update --view-id 41 --name demo-renamed
bytedcli --site eu-ttp --json forge workspace delete --view-id 41
```

An empty newly created view has no templates: initialize panels from a source view or full configuration before using `add-job`. Adding jobs never silently creates checked ids without comparison criteria. Create previews mark `view_owner` and the new sync `view_id` as deferred fields, with placeholders bound only at apply time.

Creation takes the owner from the current authenticated user at apply time; there is no owner-transfer flag. Duplicate names fail rather than causing another creation. An uncertain creation response must be reconciled with `list` before retrying. Never recreate a user-deleted view unless explicitly requested.

## Verification, conflicts, and recovery

- A successful save synchronizes the backend DeepInsight panel definitions, then reads the saved view back and compares the requested configuration. Use the returned formal URL for one final browser check; avoid reopening after every criterion edit.
- `--expected-hash` checks the snapshot and an additional pre-save read checks for changes observed during preparation. This is client-side stale-write detection, **not atomic server compare-and-swap**. Do not let multiple writers concurrently edit the same view.
- `FORGE_WORKSPACE_VERIFY_ERROR` means readback completed but observed settings differed, or a deleted view was still listed. It retains the persisted/delete-accepted identity; inspect the difference before retrying.
- A `FORGE_WORKSPACE_PARTIAL_SAVE` error identifies the already-persisted view when synchronization or readback could not complete. Recover by reading that view and running `workspace update --view-id <existing-view-id> --sync-panels --yes`; do not create another view.
- `FORGE_WORKSPACE_PARTIAL_DELETE` means delete was accepted but list verification failed; reconcile with `list` before retrying.
- `FORGE_WORKSPACE_WRITE_UNCERTAIN` requires readback/reconciliation before any retry. Write requests disable transport retries and credential-bearing redirects.
- The returned formal URL is for the native Forge workspace. If a screenshot or native graph enlargement/export is requested, open that URL in the authenticated browser and capture it there. This CLI does not produce replacement plots or automatically launch a browser.
- EU/US-TTP Workspace requests use the site's existing BDEE API origin and ByteCloud JWT. They do not use the Tracing origin or require browser Cookie extraction. Only EU-TTP has live integration verification for this capability; other registered sites have offline routing coverage.
