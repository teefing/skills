# Agent building and publishing

Agent drafts and published versions use the `agent` commands. `app get --type agent`
also reads the full Agent draft through the same Agent-specific interface.
Creating, updating, binding resources, and publishing default to a request preview;
add `--yes` to submit. Configuration updates preserve unspecified fields. Resource
`add`/`remove` changes only the selected binding and preserves the other bindings;
`remove` does not delete the underlying Skill, workflow, MCP server, knowledge base,
or plugin. Agent configuration import/export is not provided. Previews may read
platform metadata to resolve defaults, permissions, draft state, and versions;
they submit no writes. To pin the creation icon, pass an explicit `--icon-uri`.

```bash
bytedcli aicolate app list --space <spaceId> --type agent
bytedcli aicolate agent icon list
bytedcli aicolate agent create --space <spaceId> --name demo-agent --desc "Demo Agent"
# --icon-uri is optional and defaults to the platform default icon.
# Creation defaults to the platform's codex runtime. Submit the preview with --yes.
bytedcli aicolate agent create --space <spaceId> --name demo-agent \
  --desc "Demo Agent" --icon-uri <platformIconUri> --yes
bytedcli aicolate agent get --id <agentId>
bytedcli aicolate model list --space <spaceId>
bytedcli aicolate agent update --id <agentId> --name demo-agent \
  --model-id <modelId> --temperature 0.5 --max-tokens 4096 --yes
bytedcli aicolate agent update --id <agentId> --prompt-file ./prompt.md --yes
bytedcli aicolate agent update --id <agentId> --prompt $'First line\nSecond line' --yes
bytedcli aicolate agent update --id <agentId> --runtime codex \
  --reasoning-effort high --output-mode safe --native-mcp --yes
bytedcli aicolate agent update --id <agentId> --no-native-mcp --yes
```

Runtime choices are `single_agent`, `deerflow`, `codex`, and `claude`.
`--output-mode safe|raw_debug` and `--native-mcp`/`--no-native-mcp` apply only to
Codex. Claude custom sandboxes use `--sandbox-psm` and `--sandbox-region` together.
Model updates also support `--top-p` and `--history-rounds`; reasoning effort is
provider-dependent. Switching to `single_agent` clears runtime Skill selections.
`--prompt` and `--prompt-file` are mutually exclusive; an empty `--prompt` clears
the prompt. If creation succeeds but runtime initialization fails, the error
includes the created Agent ID and a recovery update command; do not create a
second Agent.

### Merge Agent drafts into a new Agent

Merge reads drafts only, accepts an optional baseline, and creates a new Agent
from a single reviewed YAML workfile. All inputs must share a space and runtime.
Resource names and source comments make the file readable; IDs determine resource
identity. Prompt/model conflicts remain explicit until the user's Agent reviews
and edits the result. The source snapshots stay complete and immutable.

```bash
bytedcli aicolate agent merge --source demo-a --source demo-b \
  --baseline demo-main --name demo-merged --out review.yaml
# The Agent reviews/edits result and resolves conflicts in this same file.
bytedcli aicolate agent merge --file review.yaml
bytedcli aicolate agent merge --file review.yaml --yes
```

Read [Agent merge review](agent-merge.md) for the YAML schema, name lookup,
provenance, long-prompt analysis, review decisions, and creation receipts. This is
a whitelist merge workfile, not an arbitrary platform configuration import. The
CLI does not rewrite prompts through a built-in AI service.

### Markdown multiline text

Use `$'First line\nSecond line'` or `--prompt-file` for multiline prompts.
Double-quoted `"First line\nSecond line"` sends a literal backslash and `n` in
bash/zsh and does not create a line break.

### Resource discovery and bindings

Discover resources through the shared `aicolate skill catalog`, `workflow`, `mcp`,
`knowledge`, and `plugin` commands. The resource subcommands under `agent` manage
bindings with `add`/`remove`. Use `bytedcli aicolate agent get --id <agentId>` to
inspect the Agent's current bindings.

**An Agent's workflow must come from the resource library（资源库工作流）.**
Select it with `aicolate workflow list --space <agentSpaceId>` without
`--project-id`; its `project_id` must be empty. A workflow developed inside a
workflow project（workflow 项目中的工作流）belongs to that project and cannot be
used as an Agent workflow binding. Use the resource-library workflow ID as
`--workflow-id`, not a project ID or a project workflow ID.
The resource-library workflow must have a published version before binding;
publish it with `aicolate workflow publish --id <resourceWorkflowId> --space
<agentSpaceId>` if needed. Binding rejects unpublished workflows before writing.

```bash
# skill list returns usage statistics; catalog list returns actual Skill resources.
bytedcli aicolate skill catalog list --space <spaceId> --keyword demo
bytedcli aicolate skill version list --space <skillSpaceId> --id <skillId>
bytedcli aicolate agent skill add --id <agentId> --skill-id <skillId> --yes
bytedcli aicolate agent skill remove --id <agentId> --skill-id <skillId> --yes
# Select a resource-library workflow in the Agent's space; omit --project-id.
bytedcli aicolate workflow list --space <agentSpaceId>
bytedcli aicolate agent workflow add --id <agentId> --workflow-id <resourceWorkflowId> --yes
bytedcli aicolate agent workflow remove --id <agentId> --workflow-id <resourceWorkflowId> --yes
bytedcli aicolate mcp list --space <spaceId>
bytedcli aicolate agent mcp add --id <agentId> --mcp-id <mcpServerId> \
  --tool-name <toolName> --yes
bytedcli aicolate agent mcp remove --id <agentId> --mcp-id <mcpServerId> --yes
bytedcli aicolate knowledge list --space <spaceId>
bytedcli aicolate agent knowledge add --id <agentId> --knowledge-id <datasetId> --yes
bytedcli aicolate agent knowledge remove --id <agentId> --knowledge-id <datasetId> --yes
bytedcli aicolate plugin list --space <spaceId>
bytedcli aicolate plugin api list --id <pluginId>
bytedcli aicolate agent plugin add --id <agentId> --plugin-id <pluginId> --api-id <apiId> --yes
bytedcli aicolate agent plugin remove --id <agentId> --plugin-id <pluginId> --api-id <apiId> --yes
```

Runtime Skills require Codex, Claude, or Deerflow and a published `prod` version.
For a shared Skill owned by another space, pass `--skill-space <skillSpaceId>` when
adding it. MCP binding loads the server's transport metadata and tool schemas;
repeat `--tool-name` to select tools, or omit it to bind all available tools.
Adding an already bound resource or removing an absent resource performs no write.

### Agent publication and Application Management release

Agent publication and Application Management release are separate steps:

```bash
bytedcli aicolate agent connector list --id <agentId>
# Defaults to API connector 1024; the platform generates the Agent version.
bytedcli aicolate agent publish --id <agentId> --note "Demo release"
bytedcli aicolate agent publish --id <agentId> --note "Demo release" --yes
bytedcli aicolate agent version list --id <agentId> --connector-id 1024
bytedcli aicolate agent get --id <agentId> --version <agentVersion>
bytedcli aicolate app-service cluster list --space <spaceId>
bytedcli aicolate app-service api-key list
bytedcli aicolate app-service agent create --space <spaceId> --agent-id <agentId> \
  --name demo-agent-api --desc "Demo Agent service" --host-prefix <clusterPrefix> \
  --api-id <patMetadataId> --row-qps 1 --us-ttp-qps 0 --eu-ttp-qps 0 --yes
bytedcli aicolate app-service version list --id <appServiceId>
bytedcli aicolate app-service publish --id <appServiceId> --version <agentVersion> \
  --small-traffic-percent 10 --note "Demo rollout" --yes
bytedcli aicolate app-service publish-record advance --id <publishRecordId> --yes
```

Agent service registration uses the Agent ID and has no project/workflow ID.
Only Agent versions published to the API connector appear as eligible App Service
versions. Registration does not bring a service online. Use `app-service publish`
to create a staged release, then `publish-record advance` to enter each stage;
while a stage is running, the command reports `wait` and submits no extra action.
Version publication receipts use `resource_scope: "app-service"` for both Agent
and workflow services. The older `workflow_scope` field remains in generic App Service
publication receipts for compatibility; use `resource_scope` when consuming these
receipts. See [Workflow operations](workflow-operations.md) for Application
Management PAT/cluster selection and regional quotas. These commands do not
create PAT secrets.

