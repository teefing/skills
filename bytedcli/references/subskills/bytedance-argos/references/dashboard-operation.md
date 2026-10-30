# Dashboard operation through an Argos Agent session

Use `bytedcli argos run` for Argos Dashboard/Folder administration, Grafana or Metrics-FE imports, and dashboard creation from Metrics SDK declarations. The Argos server provides the `dashboard-operation` skill only when the current control plane and project support it.

This is different from reading metrics or patrolling a dashboard. For object selection and deterministic monitoring queries, first read [监控对象与查询](./monitoring.md). For the Agent execution, output, recovery and permission contract, read [Argos Agent 调查](./argos-agent.md).

## Invocation

```bash
# Read-only example
bytedcli --site cn argos run \
  --prompt "Use dashboard-operation to list my CN dashboard folders. Do not modify anything."

# Write example with an explicit preview gate
bytedcli --site cn argos run \
  --prompt "Use dashboard-operation to prepare a dashboard named sample-service Metrics in sample-team folder. Preview the proposed change and do not apply it until I confirm."
```

No local skill path is required. If the server or project does not provide the capability, preserve the Agent/server error and explain that dashboard operation is unavailable in that session.

bytedcli currently has no separate command to discover which project exposes `dashboard-operation`. Use the project named by the user or the configured personal project, start with a read-only request when possible, and treat a missing-skill/missing-tool response as an explicit capability gap. Do not probe unrelated projects or claim support before the session confirms it.

For a manual CN verification, run the read-only example with global `--json`. The check passes when the session succeeds, returns the requested folder result, and reports an empty `files_modified` array. A missing-skill or missing-tool response means the current session does not provide the capability.

## Session-only boundary

The dashboard skill and its MCP tools execute inside the Argos Agent session. They are not direct `bytedcli argos tool <name>` commands and do not belong to the user-callable Tool catalog. Consequently, `bytedcli argos tool list` is not an availability check for this capability.

## Safety

- State the target site/region, dashboard and folder explicitly.
- Keep read-only requests read-only. For writes, request a preview and confirmation before applying the proposed change.
- Do not treat a normal `--session` follow-up as permission approval. bytedcli does not implement the Tool-approval interaction for a permission-type `needs_input`; report the execution session and pending Tool information, then hand it to an approved client that supports that workflow. The approval client/server decides whether the same session resumes automatically or requires a follow-up, so do not promise either behavior.
- Follow the server-provided skill's validation, V1 migration, identity matching and dry-run requirements.
- Treat the server-provided `dashboard-operation` skill as the source of truth for its exact tools, scripts, dependencies and supported chart types.
