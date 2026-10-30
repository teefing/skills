# ACO

Use this route for ACO Proxy, cloud control-plane and task operations through `bytedcli aco`. Aiden task creation and management use the Aiden route.

The command implementation and complete Skill are maintained in the ACO repository:
https://code.byted.org/webcast/aco

## Bootstrap

1. Install the official plugin and check its runtime contract:

```bash
bytedcli self plugin install --name aco
bytedcli self plugin doctor --name aco
bytedcli aco --help
```

2. Read the installed plugin’s bundled `aco` Skill for ordinary Proxy operations, or `aco-cloud-worker` for Cloud Task collaboration. Local tasks use the Runtime-injected Worker Skill. Bundled instructions match the installed version. Requires bytedcli `>=0.160.0` and Node.js `>=20.19.0`.

3. Resolve task ownership in this order: the existing Run's workspace and project, explicit inputs for this invocation, the nearest directory binding found by searching upward from the current directory, then a user selection. Read an existing Run with `bytedcli aco run get <run-id> --output json`; do not replace its ownership with local defaults or create another Run. Runner-provided workspace context is explicit input, not permission to guess a project.

4. When there is no existing Run and explicit ownership is incomplete, use `bytedcli aco init --check --output json` to check for a reusable directory binding. Reuse a ready binding. If missing or invalid, list accessible workspaces with `bytedcli aco workspace list --output json`, then projects with `bytedcli aco project list --workspace <id> --output json`, and ask the user to select. Do not silently choose the first candidate. Authentication or network errors are not a missing binding.

5. Save the selected defaults with `bytedcli aco init --workspace <id> --project <id>` when directory reuse is useful. This lightweight plugin command supports ordinary directories and does not register a Repository, generate a Project Guide, or install, start or bind a Local Host. Aiden Cloud, TAE and Aime may use a fresh environment on every execution: check for reusable context first, and never assume previous local storage survives. For one-off or unwritable environments, pass `--workspace <id> --project <id>` directly to `bytedcli aco goal`; saving a binding is optional. Explicitly repository-free tasks also use `--without-repository`.

6. Use `bytedcli aco proxy prepare --workspace <id> --output json` and read the returned skillPath. `bytedcli aco goal` keeps the current Agent as Proxy and automatically reuses its existing bytedcli login; no standalone ACO CLI, setup or Host is required. Ask about a required repository only when it is not already known. A fresh Runner can also use `ACO_SERVER_URL`, `ACO_WORKSPACE_ID` and Runner-managed `SDMA_CLI_OPERATOR_JWT_PATH` without a resident Host or local profile. Valid identity and workspace/project permissions are required. Explicit Task / Proxy contexts retain their own authorization scope and never fall back to local login. Do not copy credentials into prompts, arguments, Skills or logs.

Automation and Bot integrations can use platform-launched Cloud Proxy Runs on Aiden, TAE and Aime through `bytedcli aco run launch --input <file>`; inspect their execution with `bytedcli aco run runtime <run-id>`. Do not use run launch to replace the current Agent when the user asks it to act as Proxy. Read the bundled Proxy Skill and command help for launch inputs, provider configuration and authorization.

Proxy and Worker use the role-appropriate commands in their bundled Skills. `repository` and `tool bytedcli` share public command names while retaining Run or Task authorization. Task collaboration uses `task send`, `task wait`, `task complete` and `artifact add`; transport does not change role permissions or permit login fallback. Cloud tasks run `worker prepare` and read the returned Skill before business work. Consult command help for JSON stdin and `--input` support.

Cloud intermediate artifact reuse is provided by the ACO plugin through `artifact list`, `artifact get` and `artifact download`. Aiden Cloud, TAE Agent and Aime use the same active Task identity and can read registered artifacts within their Run. Downloads verify SHA-256 before publishing the local file. Read the installed `aco-cloud-worker` Skill for the version's JSON input and available commands; an older plugin may not expose these operations. Upgrade the plugin through its official release channel rather than clearing Task context or falling back to ordinary login.

For planning, orchestration, execution recovery and delivery, follow the bundled `aco` routing to its specialist Skills. Blocked-work diagnosis and human escalation belong to `aco-run`; this guide does not duplicate recovery rules. Upgrade the official ACO plugin to receive updated Skills.

Shared commands use the same ACO parser, arguments, defaults, output and exit codes. The standalone `aco init` retains its Repository, Project Guide and Local Host behavior; it is distinct from the lightweight `bytedcli aco init` directory binding. `setup`, `codex`, resident Host management, disk maintenance, standalone updates and shell completion stay with the standalone installation. This guide only routes to the maintained Skill and does not define a second command contract.
