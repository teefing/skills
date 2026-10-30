# Douyin AI Trace Span

Use this route when the user asks for Douyin AI Trace Span details, flat spans, LogID-based trace pagination, or the total Span count for a Douyin AI trace.

The complete command guidance is bundled with the official plugin; its source is maintained at:
https://code.byted.org/open/bytedcli-plugin-douyin-ai/blob/master/skills/bytedance-douyin-ai-trace-span/SKILL.md

## Bootstrap

1. Check the official plugin and install it when it is absent:
When replacing the former bundled `bytedance-douyin-ai` Skill, remove that builtin installation before installing or updating the plugin: use `bytedcli self skill remove --global --skill bytedance-douyin-ai` for a global installation, and `bytedcli self skill remove --skill bytedance-douyin-ai` in each project where it was installed. These commands remove the old Skill copies and ownership records. Use the original profile; do not remove plugin-managed or unrelated Skills. Other ownership conflicts must be reported rather than bypassed.

```bash
bytedcli --json self plugin info --name douyin-ai
bytedcli self plugin install --name douyin-ai
bytedcli self plugin doctor --name douyin-ai
```

Install only when info reports PLUGIN_NOT_FOUND. If an enabled official npm installation is older than 0.2.0, run `bytedcli self plugin update --name douyin-ai` and validate it. Report other errors, disabled installations, or non-npm sources that do not provide the required command.

2. Reuse the bytedcli CN Mango session. The plugin has no separate credential flow; never request or hand-write a Cookie.
3. Restart the Agent or MCP session after a plugin update so the Skill and command catalog are refreshed.
4. Load the bundled `bytedance-douyin-ai-trace-span` Skill for the exact command, pagination, time-range, and output contract. Do not substitute workspace-scoped `douyin-ai trace list/get`.
5. Use runtime help if the installed plugin and the Skill disagree:

```bash
bytedcli douyin-ai trace span --help
```
