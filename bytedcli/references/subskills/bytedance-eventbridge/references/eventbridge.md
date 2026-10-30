# EventBridge command guide

## Current state

Resource queries and CLI subscription management use the ByteCloud gateway under `/api/v1/eventbridge`. Live notification listening uses Frontier WebSocket; its supported sites differ from the query routes below.

Gateway routing:

| CLI selection | Gateway base |
| --- | --- |
| `--site cn` | `https://cloud.bytedance.net/api/v1/eventbridge` |
| `--site boe` | `https://cloud-boe.bytedance.net/api/v1/eventbridge` |
| `--vregion va` or `--vregion maliva` | `https://bc-maliva-gw.tiktok-row.net/api/v1/eventbridge` |
| `--vregion sg` | `https://bc-sg-gw.tiktok-row.net/api/v1/eventbridge` |

## Command surface

| Command | Behavior | Read/write |
| --- | --- | --- |
| `bytedcli eventbridge project list --page 1 --page-size 20` | List EventBridge projects visible to the current identity | Read |
| `bytedcli eventbridge project get --uid <project-uid>` | Get one EventBridge project | Read |
| `bytedcli eventbridge rule list --project-uid <project-uid>` | List EventBridge rules | Read |
| `bytedcli eventbridge rule get --uid <rule-uid>` | Get one EventBridge rule | Read |
| `bytedcli eventbridge rule event-sample get --source <source-id> --type <event-type-id>` | Get a sample event | Read |
| `bytedcli eventbridge source list --pid <project-id> --category bytecloud` | List EventBridge event sources | Read |
| `bytedcli eventbridge source get --event-bus-id <bus-id> --event-source-id <source-id>` | Get one EventBridge event source | Read |
| `bytedcli eventbridge type list --event-source <source-id>` | List EventBridge event types | Read |
| `bytedcli eventbridge event auth-event list --start <unix-time> --end <unix-time>` | List EventBridge auth events | Read |
| `bytedcli eventbridge event jwt-event list --access-key <ak>` | List EventBridge JWT events | Read |
| `bytedcli eventbridge subscription list --project-uid <project-uid> --page 1 --page-size 20` | List subscriptions; optionally filter with `--keyword` | Read |
| `bytedcli eventbridge subscription get --project-uid <project-uid> --subscription-id <id>` | Get one subscription | Read |
| `bytedcli --as user eventbridge subscription create --project-uid <project-uid> --name demo-subscription --service-account <sa-id>` | Preview creation; add `--yes` to apply | Write after confirmation |
| `bytedcli --as user eventbridge subscription update --project-uid <project-uid> --subscription-id <id> --name demo-subscription --enabled=false` | Preview name/enabled changes; add `--yes` to apply | Write after confirmation |
| `bytedcli --as user eventbridge subscription delete --project-uid <project-uid> --subscription-id <id>` | Preview deletion; add `--yes` to apply | Write after confirmation |
| `bytedcli --as app --json eventbridge notification listen --subscription-id <id> --duration 60s --max-events 10` | Receive live notifications and ACK successful CLI output | Stream with ACK |

## Implementation boundaries

- Control-plane reads use EventBridge APIs through the selected ByteCloud Site/VRegion route.
- Use explicit flags, not positional arguments. Required, one-of and exactly-one constraints must be expressed through `PluginContext.Commands`.
- Query commands return stable public DTOs and render human output through presenters.
- Prefer global `--json` before `eventbridge` for automation and Agent use. Notification listening emits NDJSON rather than a single JSON document.

## Subscription workflow

Resolve the project UID with `project list` or `project get`, then use `subscription list` to select a subscription. Subscription IDs are positive decimal integers, not project or rule UIDs. Keep the selected site and project scope when reusing identifiers.

Create/update/delete preview by default. Review the target, application binding, name, and enabled state; add `--yes` only when the same change is authorized:

```bash
# Resolve the subscription in the selected project.
bytedcli --site cn --json eventbridge subscription list --project-uid demo-project-uid --page 1 --page-size 20
bytedcli --site cn --json eventbridge subscription get --project-uid demo-project-uid --subscription-id 123
# Preview creation, then apply the reviewed request when authorized.
bytedcli --site cn --as user --json eventbridge subscription create --project-uid demo-project-uid --name demo-subscription --service-account demo-service-account
bytedcli --site cn --as user --json eventbridge subscription create --project-uid demo-project-uid --name demo-subscription --service-account demo-service-account --yes
# Preview disabling or deleting the selected subscription.
bytedcli --site cn --as user --json eventbridge subscription update --project-uid demo-project-uid --subscription-id 123 --name demo-subscription --enabled=false
bytedcli --site cn --as user --json eventbridge subscription delete --project-uid demo-project-uid --subscription-id 123
```

- Writes require direct personal authentication and rule write permission. The application account must already have project authorization; the CLI does not grant it.
- `--service-account` binds the listener identity and is immutable after creation. The server supplies `authorized_username`; do not invent a flag for it.
- Creation defaults `--enabled` to true. Updates require both `--name` and an explicit `--enabled=true|false`.
- Create/update read back the resource after applying. If readback fails with `applied: true`, inspect the resource before retrying; the write has already happened. Mutations are not automatically retried.
- Deletion can return a conflict while a rule references the subscription. Resolve the rule reference before retrying deletion.
- Creating a subscription does not create a rule. Configure the rule target in the console with `type=cli`, `config.cli_subscription_id=<id>`, and `config.retry.count=1`; the server validates supported bus ownership and project scope. Event submission and rule creation are outside this CLI command surface.

## Notification routes and authentication

- Listening supports CN (`--site cn`) and Singapore (`--site i18n-tt --vregion sg`). BOE, TTP, and other unsupported routes are rejected. Singapore routing support does not guarantee notification enablement for every project.
- For a PPE lane, use the same `--env <lane>` on subscription and listen commands. Omit it for production; there is no automatic production fallback.
- Use the host's supported authentication. `bytedcli --as app` selects application credentials whose service-account username must match the subscription binding. Supported personal OAuth JWTs can instead carry a signed `cli_sa` binding. An ordinary personal JWT without the required application identity cannot listen.
- Do not request or print JWTs. No Frontier AppKey, device ID, `aid`, or `fpid` is needed. Reconnect obtains credentials from the provider again but cannot renew a fixed expired injected token.

```bash
bytedcli --site cn --as app --json eventbridge notification listen --subscription-id 123 --duration 60s --max-events 10
bytedcli --site i18n-tt --vregion sg --as app --json eventbridge notification listen --subscription-id 123 --duration 60s --max-events 10
```

## Notification output and lifecycle

- JSON mode emits one standard success envelope per notification (NDJSON). The complete notification is in `data`, and its business payload is in `data.payload`. Non-JSON mode also prints one compact JSON notification per line. Connection and reconnect diagnostics go to stderr; heartbeat frames are handled internally.
- ACK is sent only after the CLI successfully writes the notification to stdout. It does not confirm durable storage, successful pipe-reader processing, or Agent completion. A broken output destination stops the listener without acknowledging that notification.
- Recent notification IDs are deduplicated within a bounded session window. The window resets on reconnect, so consumers must handle duplicates using `notification_id`. There is no offline backlog or replay guarantee.
- Reconnect defaults to enabled with at most 10 attempts per invocation. Use `--reconnect=false` or `--max-reconnects <n>` to change this. Authentication failures, replacement, disabled subscriptions, protocol errors, and slow-consumer closures stop the listener.
- Only one listener can own a subscription; a second listener replaces the first. Avoid starting another listener without accounting for the active consumer.
- `--duration` bounds total listening time including reconnect waits. `--max-events` counts printed notifications across connections. Both default to zero (unlimited); use a finite bound for Agent tasks. Ctrl+C or SIGTERM closes the connection.
- Listening does not execute local commands or automatically launch an Agent. Consumers decide how to process the stream.
