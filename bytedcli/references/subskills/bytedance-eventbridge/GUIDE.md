---
name: bytedance-eventbridge
description: "Query EventBridge projects, rules, event samples, sources, types, Auth Events, and JWT Events; manage CLI subscriptions and receive live notifications through bytedcli eventbridge. Trigger when users mention EventBridge、事件桥、事件查询、CLI 订阅、订阅管理、通知监听 or 实时事件通知."
---

# EventBridge

Use `bytedcli eventbridge` for EventBridge operations. Query commands call the EventBridge HTTP API through the selected ByteCloud gateway under `/api/v1/eventbridge`.

## Scope

- Control-plane reads cover EventBridge projects, rules, rule event samples, event sources, event types, auth events, and JWT events.
- The CLI must use ByteCloud CLI routing, authentication, error handling, and JSON envelope behavior. Do not invent endpoint paths, credentials, request fields, or response fields.
- CLI subscriptions support list/get and preview-first create/update/delete. Live notifications use a WebSocket connection through Frontier.
- Event submission and rule creation are not exposed. Creating a subscription does not create a rule or grant project permissions.

## Commands

- `bytedcli eventbridge project list --page 1 --page-size 20`: List EventBridge projects.

- `bytedcli eventbridge project get --uid <project-uid>`: Get one EventBridge project. Use `--id` only for the deprecated numeric ID.

- `bytedcli eventbridge rule list --project-uid <project-uid>`: List EventBridge rules. Use `--pid` only for the deprecated numeric project ID.

- `bytedcli eventbridge rule get --uid <rule-uid>`: Get one EventBridge rule. Use `--id` only for the deprecated numeric ID.

- `bytedcli eventbridge rule event-sample get --source <source-id> --type <event-type-id>`: Get a sample event for an EventBridge rule.

- `bytedcli eventbridge source list --pid <project-id> --category bytecloud`: List EventBridge event sources.

- `bytedcli eventbridge source get --event-bus-id <bus-id> --event-source-id <source-id>`: Get one EventBridge event source.

- `bytedcli eventbridge type list --event-source <source-id>`: List EventBridge event types.

- `bytedcli eventbridge event auth-event list --start <unix-time> --end <unix-time>`: List EventBridge auth events.

- `bytedcli eventbridge event jwt-event list --access-key <ak>`: List EventBridge JWT events.

- `bytedcli eventbridge subscription list --project-uid <project-uid> --page 1 --page-size 20`: List CLI notification subscriptions; optionally filter with `--keyword`.

- `bytedcli eventbridge subscription get --project-uid <project-uid> --subscription-id <id>`: Get one subscription using its positive numeric ID.

- `bytedcli --as user eventbridge subscription create --project-uid <project-uid> --name demo-subscription --service-account <sa-id>`: Preview creation; notifications are enabled by default.

- `bytedcli --as user eventbridge subscription update --project-uid <project-uid> --subscription-id <id> --name demo-subscription --enabled=false`: Preview an update; both `--name` and explicit `--enabled=true|false` are required.

- `bytedcli --as user eventbridge subscription delete --project-uid <project-uid> --subscription-id <id>`: Preview deletion.

- `bytedcli --as app --json eventbridge notification listen --subscription-id <id> --duration 60s --max-events 10`: Receive live notifications with bounded listening time. Read the command guide before choosing the identity, site, or output consumer.

## Safety

- Query commands are read-only.
- Subscription create/update/delete require direct personal authentication and rule write permission. Preview first; apply the authorized request by adding `--yes` to the same command. The bound application account must already have project authorization.
- Listening requires an application identity matching the subscription's service account, or a supported personal OAuth JWT carrying the signed `cli_sa` binding. An ordinary personal JWT cannot listen. Use the host's supported authentication; do not copy tokens into commands.
- In Agent tasks, bound listeners with `--duration` or `--max-events`. JSON mode emits one envelope per notification (NDJSON), with diagnostics on stderr. ACK confirms CLI output, not downstream processing; there is no offline backlog or replay guarantee.
- Only one listener owns a subscription. Starting another replaces the first. Authentication failures, disabled subscriptions, and replacement stop the listener.
- Never print JWTs, Authorization headers, Gateway tokens, or raw credential material.

## References

- [Command guide](references/eventbridge.md): Query commands, subscription authentication and write recovery, supported notification routes, and delivery semantics.
- [Invocation](../../invocation.md)
- [Troubleshooting](../../troubleshooting.md)
