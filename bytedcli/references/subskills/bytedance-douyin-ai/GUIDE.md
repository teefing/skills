# Douyin AI platform

Douyin AI platform commands are maintained in the official independent plugin.
Before using Douyin AI, check whether the official plugin is installed. If it is absent, install and validate it:
When replacing the former bundled `bytedance-douyin-ai` Skill, remove that builtin installation before installing or updating the plugin: use `bytedcli self skill remove --global --skill bytedance-douyin-ai` for a global installation, and `bytedcli self skill remove --skill bytedance-douyin-ai` in each project where it was installed. These commands remove the old Skill copies and ownership records. Use the original profile; do not remove plugin-managed or unrelated Skills. Other ownership conflicts must be reported rather than bypassed.

```bash
bytedcli --json self plugin info --name douyin-ai
bytedcli self plugin install --name douyin-ai
bytedcli self plugin doctor --name douyin-ai
```

Main-site requests use the host-verified personal JWT. Trace Span and legacy Trace retain their CN Mango session.
Install only when info reports PLUGIN_NOT_FOUND. If an enabled official npm installation is older than 0.2.0, run `bytedcli self plugin update --name douyin-ai` and validate it. Report other errors, disabled installations, or non-npm sources that do not provide the required command; do not silently remove them. Reload the Agent Skill catalog and restart MCP after installation or update. Read the complete Skill bundled with the plugin.
