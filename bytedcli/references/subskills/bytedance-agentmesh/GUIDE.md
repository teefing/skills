# AgentMesh

Use this route for remote-agent discovery, Agent Card inspection, delegation and Gateway task recovery through `bytedcli agentmesh`. A bounded task or subtask may benefit from specialist investigation, analysis, platform operations or artifact generation even without an explicit AgentMesh request. Respect the user's local/remote routing preferences; skip self-contained answers, local-only work and prohibited delegation.

The complete `agent-mesh` Skill is maintained with the official plugin:
https://code.byted.org/ttarch/agentmesh-cli/blob/master/plugin/skills/agent-mesh/SKILL.md

## Bootstrap

Official registration does not install the plugin. Before any `agentmesh` command, including `--help`, use the host's plugin management commands below. An unavailable plugin can return the host's root help with exit code 0; that is not AgentMesh help or proof of availability.

1. Check the installed plugin through the host; this works before the plugin is installed:

```bash
bytedcli --json self plugin info --name agentmesh
```

If the response has `error.code: PLUGIN_NOT_FOUND`, install the official plugin once:

```bash
bytedcli self plugin install --name agentmesh
```

If info succeeds, reuse the installed version. If `data.plugin.enabled` is false, report the disabled state and confirm it may be enabled before using `bytedcli self plugin enable --name agentmesh`. Other errors do not mean the plugin is absent: follow their diagnostics instead of repeatedly installing. A runtime that prohibits plugins must use an approved plugin-capable environment.

After installation, or for an already installed and enabled plugin, validate the runtime contract:

```bash
bytedcli self plugin doctor --name agentmesh
```

If doctor reports a failure, resolve it before calling AgentMesh. Do not use discovery, authentication or send commands as installation probes.

The official package is `@bytedance-dev/agentmesh-cli` and requires bytedcli `>=0.149.0` and Node.js `>=18`. The plugin bundles its Go executable; no separate Go or standalone CLI installation is required.

2. Load the installed plugin's `agent-mesh` Skill at the canonical path reported by installation before selecting an Agent, sending a message or recovering a Task. Existing Shell-driven Agent sessions can read that file directly and continue: newly launched CLI processes see the installed commands immediately. Reload the Agent's Skill catalog when supported; restart a running bytedcli MCP server to refresh its tool catalog after installation or updates.
3. Check Gateway authentication before discovery or invocation:

```bash
bytedcli --json agentmesh auth status
```

The Gateway requires an AgentMesh Static Secret; a bytedcli/ByteCloud login alone is insufficient. Reuse configured credentials. If setup is needed, use `bytedcli agentmesh auth login` in a real terminal or import a runtime-provided protected `MESH_STATIC_SECRET`; non-TTY plugin calls never read stdin. Never put credentials in chat, message bodies or command arguments. Downstream CN personal ByteCloud identity follows the bundled Skill and the current host's public authentication API.

4. Search current capabilities once for the bounded task, inspect the returned Card and delegate only within the user's authorized scope. An empty search permits local fallback; a failed search does not prove that no Agent exists. Do not hardcode an Agent catalog or repeat an ambiguous send with a new Message ID. Recover an accepted Task using its saved identifiers.
5. Use runtime help for the installed version's options:

```bash
bytedcli agentmesh --help
bytedcli agentmesh send --help
bytedcli agentmesh task get --help
bytedcli self plugin update --name agentmesh
```

JSON business results are under `data`; failures retain `error.details.recovery`. Follow the bundled Skill for source identity, Task state, timeout recovery and untrusted remote results. This guide routes to that maintained contract rather than copying it.
