# Issue and monitor Merlin trials with Claude Code, Codex and pi

## Contract

The same native `bytedcli merlin trial watch` service supports all three clients.
There are three independent lifetimes:

1. The trial runs on Merlin.
2. A host/profile daemon supervises one collector per registered trial. It saves
   observations, events, phase clocks and stop intent independently of agent sessions.
3. An agent reader streams saved events and reports them to its parent/session.
   Closing the reader does not stop the collector or the trial.

The owner is the responsible session recorded at registration. A reader is a
consumer with its own ACK cursor. Attaching another reader does not transfer the
owner or grant stop authority. Use the same host and authentication profile to
resume a watch. The state is local, not a cross-host consensus service.

## Submit and register

Use a reviewed submit-ready YAML and select the intended site explicitly. Trial
submission requires the user's experiment authorization; registering observation
does not authorize a new workload or retry.

```bash
bytedcli --site i18n-tt --json merlin job submit \
  --body-file ./trial.yaml --watch-owner demo-session \
  --tracking-project-id demo-project --tracking-run-id demo-run \
  --min-stable-steps 2
```

`monitoring.ready` reports whether background monitoring became ready. Save the
job identity and watch receipt. If the launch succeeds but registration fails,
repair monitoring for the returned job id. **Do not rerun submit.** The submission
receipt explicitly reports this case and preserves the launched job identity.
Submission-attached monitoring is notify-only.
If `readback.ready` is false, submission still succeeded: retain the returned job
identity and recover readback and monitoring for that job. Unknown trial/status
fields remain null; never submit a duplicate to recover a failed readback.

For an existing job, or to recover registration:

```bash
bytedcli --site i18n-tt --json merlin trial watch start \
  --job demo-job-run --owner demo-session \
  --tracking-project-id demo-project --tracking-run-id demo-run \
  --min-stable-steps 2
bytedcli --site i18n-tt --json merlin trial watch status --watch-id <watch-id>
```

Use the `watch_id` returned by start. Require a live daemon and collector, or a
recorded completed observation. Registration alone is not a readiness proof.
Repeating start with the identical contract reuses the watch; incompatible owner,
tracking, budgets or stop policy are rejected instead of silently replacing them.
Without a tracking pair, the watch still detects startup stalls and failures and
can observe terminal success, but it cannot prove a training milestone.

Registration also freezes the effective `--as`, `--auth-site`, proxy/TLS settings,
HTTP timeout/retries, environment proxy/no-proxy settings and ZTI opt-in. Each
collector restores its own settings even when the daemon was started by a different
session. Use durable profile authentication: request-scoped or environment JWTs,
environment application credentials, custom auth headers, per-command AI auth
overrides and credential-bearing proxy URLs are rejected before managed registration
or submission with `--watch-owner`. Tokens are never copied into watcher state.
Use foreground `watch follow` for request-scoped credentials, or configure a
separately authenticated profile and a credential-free proxy for managed watching.

Tracking must identify the watched job or trial. Health requires all expected
current-run role slots running and at least `--min-stable-steps` **new steps since
this run's tracking baseline was observed**. This is an advance count, not an
absolute training-step target. The baseline resets on a robust-generation change
or tracking counter reset. Existing high step values do not prove fresh progress.
`--min-stable-seconds` is a deprecated compatibility option and cannot prove health.

The queue budget (`--max-queue-seconds`, default 86400) ends when current-run
instances become ready; the observation budget (`--max-watch-seconds`, default
7200) starts then. Robust restarts do not renew the observation budget. A managed
collector emits `PHASE_BUDGET_EXCEEDED` and continues protecting the trial.
The foreground `watch follow` command exits on budget exhaustion.

## One reader and explicit handling

```bash
bytedcli --site i18n-tt --json merlin trial watch events \
  --watch-id <watch-id> --reader demo-session --follow
# In the handling turn, after reviewing a contiguous prefix:
bytedcli --site i18n-tt --json merlin trial watch ack \
  --watch-id <watch-id> --reader demo-session --up-to-seq 12
```

`events` emits JSONL with `watch_id`, `job_run_id`, `trial_id`, `seq`, `kind`,
`summary` and evidence fields. `--follow` delivers new events without waiting for
reader exit; it ends when observation is completed or explicitly stopped.
Without `--follow`, it returns the unacknowledged prefix once. `--follow --until-event`
prints only the actionable events of one delivery and exits (routine `WATCH_STARTED`,
`RUN_STARTED`, `STEP_PROGRESS`, `STOP_PENDING` and `SCHEDULING_DIAGNOSIS` stay stored and
are covered by the next ACK); an exit without an event prints `WATCH_CONCLUDED`,
`WATCH_INACTIVE` or `WATCH_COLLECTOR_DOWN`. ACK is never implicit.
A restarted reader replays unacknowledged events. Deduplicate delivery by
`(watch_id, seq)` but retain unhandled incidents. Do not ACK future or undelivered
sequences; do not ACK past an unhandled earlier incident.

Record the observation assignment beside the receipt:

- exact job/trial/watch identity, owner, profile, current phase and evidence;
- question and completion condition (terminal or a measured milestone);
- parent's concrete next action after completion;
- trial disposition and existing stop/retry authorization.

Completion of monitoring does not automatically complete the experiment. A step
milestone may require inspecting artifacts or comparing measurements. Expected
failure can satisfy a reproduction objective, but does not authorize a retry.

## Managed completion and observation failures

A managed watch has a separate completion state from the platform trial.
`STOP_LOSS_TRIGGERED` means a crash-loop policy matched, with `stopped:false`;
notify-only handling reports the incident, ACKs and continues reading. In auto
mode the collector persists stop intent and proceeds through sending, accepted
or uncertain states. None is proof of a stopped trial or released resources.
Never repeat a stop RPC merely because its result was uncertain.

On `STABLE`, `TERMINAL`, `STOP_CONFIRMED` or another completion candidate, read
`bytedcli --site i18n-tt --json merlin trial watch status --watch-id <watch-id>`
once. Normal completion requires `completed=true`; when `stop` exists, also
require `stop.phase=confirmed`. A platform terminal event can precede allocation
release and the final checkpoint update. While pending, ACK the handled prefix
and re-mount the reader rather than polling status. Capture `last_seq` from the
completed status snapshot and handle/ACK its full contiguous prefix before a
normal final handoff. An earlier delivery batch may omit later events; use
`watch events` without `--follow` to inspect the remaining prefix, including
filtered routine records. Never ACK unseen events to the cutoff. Retain unresolved
events in an abnormal handoff. `active` is the owner's control switch, not a
completion indicator.
Identity changes and collector failure have their own handoff reasons and never
transfer stop authority or establish trial success.

Observation-source failures are incidents distinct from trial failures. The
collector persists per-source incident state in the checkpoint and exposes it as
`watch status.observation_incidents`. Sources include robust runs, instances,
alerts, tracking and the top-level poll. Failure events carry `source`,
`incident_id`, `incident_state`, `error_class`, `fingerprint`, `first_seen`,
`last_seen`, `count` and source identity context. First failures and changed
failure classes/contexts are actionable; repeated unchanged failures update state
without emitting a new alert each poll. The state survives collector restart.

`ROBUST_RUNS_FETCH_FAILED`, `INSTANCES_FETCH_FAILED`, `ALERT_FETCH_FAILED`,
`TRACKING_FETCH_FAILED` and `WATCH_POLL_FAILED` mean the affected evidence is
unavailable or untrusted. Preserve the run baseline and treat health as unknown.
Only a successful, validated observation of that source emits one
`OBSERVATION_SOURCE_RECOVERED`; a skipped query or invalid snapshot is not recovery.
Recovery closes that source incident, not other failures or the whole watch.
A later recurrence opens a new incident and must notify again. These rules do not
suppress distinct `RUN_DIED` events or replace delivery ACKs.

Agents notify the parent for a new or changed incident requiring action. Record
recovery in the receipt, ACK and continue; notify the parent only when recovery
changes its pending decision. Never treat a counter increment as another alert,
and never ACK past an earlier unhandled incident.

## Claude Code adapter

Use one background reader attached through the client's supported process or
monitor facility. A Monitor-capable integration should consume stdout **line by
line**, forward each actionable event to the session, and keep the reader alive
while the agent diagnoses the event. Run bounded diagnosis separately.

A generic background shell task that only notifies on process completion is not a
streaming event adapter. In that environment use a monitor integration that forwards
new JSONL lines, or keep the session actively waiting on the process. Do not claim
real-time handling merely because the background task exists.

On session resume, read watch status, recover the original assignment, and start
one reader using the original reader id. If the old reader is still attached, reuse
it or detach only that reader before replacing it. ACK after handling, not on receipt.

## Codex adapter

Codex sees a running command's output only when the command exits: a wait on a
still-running `--follow` reader returns at the end of its full yield, so events arrive
up to one yield late (20-26 min measured with a 30 min yield). Give a watcher child the
assignment and the exit-on-event reader:

```bash
bytedcli --site i18n-tt --json merlin trial watch events \
  --watch-id <watch-id> --reader <session-id> --follow --until-event
```

The child waits on it with the runtime's longest yield. Each return with an event:
handle it, ACK the handled prefix, mount the same command again. Routine status
(`TRIAL_RUNNING`) goes to the receipt, not the parent; milestones, failures and
terminal candidates go to the parent only when they require a decision or complete
the assignment. Event names alone do not decide the child lifetime: use the managed
completion rules below. `WATCH_INACTIVE` and `WATCH_COLLECTOR_DOWN` require an explicit
inactivity or coverage-failure handoff, not a trial-success claim. `WATCH_CONCLUDED`
requires one completion-state check and a final handoff; do not re-mount on these exit
lines. A return with no exit after the full yield is
the heartbeat: check `trial watch status` once and wait again on the same process.
To stop, the parent runs `trial watch stop` itself; a message cannot reach a child
inside its wait, while the reader exits on the inactive watch within a second. Do not
replace this with repeated status/queue API calls.

Codex sandbox requirements: the reader writes its cursor under
`<bytedcli data>/merlin/trial-watch/<watch_id>/readers`, so that directory (not the
whole bytedcli tree, which holds credentials) must be in
`sandbox_workspace_write.writable_roots`. The sandbox has its own PID namespace, so
`collector_live` and `daemon_live` read false there even for a healthy collector; judge
health by `collector_heartbeat_age_seconds` (stale beyond 720 s), which
`--until-event` also uses for `WATCH_COLLECTOR_DOWN`.

Codex's idle parent is not guaranteed to start a new turn when a watcher event is
written. The parent must remain in an active child-wait operation while monitoring
is its current responsibility. In runtimes exposing `wait_agent`, use one long wait
with the runtime's configured timeout. A timeout alone is not a trial event: wait
again without launching another watcher or issuing a pool/status poll. A real child
message or new user instruction starts the handling turn.

The daemon can preserve events and execute explicitly authorized stop-loss while
Codex is absent. This does not establish that the parent received or handled them.
Delivery, ACK, successful diagnosis and experiment acceptance are separate facts.

## pi adapter

Use a pi extension that owns one subprocess per watch reader and parses JSONL as
stdout arrives. Persist `watch_id`, reader id, assignment and the handled cursor in
session/extension state. On extension/session reload, reuse those identifiers and
replay pending events. A milestone starts handling without detaching the stream.

An existing extension for `merlin trial-watch` is not automatically compatible:
change its executable/argv to `bytedcli ... merlin trial watch events`, map the
receipt to `watch_id` and `reader`, and route ACK to `watch ack --up-to-seq`.
Do not reuse the old CLI's client namespace, `--continuous`, `--wake-on-step`,
receipt-file schema, or `state_root` flags: they are not bytedcli options.
Do not buffer all output until reader exit. Do not ACK in the stdout callback.

This document defines the adapter contract; it does not install a Claude Monitor,
Codex scheduler hook or pi extension. Their event-injection APIs are owned by the
client runtime and must be verified in that runtime before unattended use.

## Event handling

| Event | Meaning | Response |
| --- | --- | --- |
| `RUN_STARTED` | Robust execution evidence appeared | Check phase; not training success |
| `TRIAL_RUNNING` | All expected current-run instances are running | Begin startup/training observation; progress remains unverified |
| `SCHEDULING_STALLED` | No acknowledgment/XPU allocation progress for the configured window | Inspect scheduling diagnosis and queue capacity; cause is not inferred from zero counters |
| `PARTIAL_START_STALLED` | Some role slots started but made no progress | Inspect pending slots and GPU allocation; a CPU-only head may be waiting normally |
| `SCHEDULING_DIAGNOSIS` | Best-effort platform diagnostic response | Correlate with the stall; empty diagnostics are not a healthy verdict |
| `RUN_DIED`, `ERROR_ALERT` | Failure/restart or platform error | Handle immediately, even if the platform already restarted the run; historical deaths are marked |
| `STEP_PROGRESS`, `STABLE_OBSERVED` | Tracking advancement / requested advance achieved | Verify the original acceptance condition and perform the parent's next action |
| `WATCH_POLL_FAILED`, `ROBUST_RUNS_FETCH_FAILED`, `INSTANCES_FETCH_FAILED`, `ALERT_FETCH_FAILED`, `TRACKING_FETCH_FAILED` | New or changed observation incident | Treat health as unknown, report once per incident change, ACK and retain the watcher |
| `OBSERVATION_SOURCE_RECOVERED` | One source returned trusted data again | Record recovery, ACK and continue; notify the parent only if its pending decision changes |
| `PHASE_BUDGET_EXCEEDED` | Queue or observation decision deadline | Review the budget and trial; collection continues |
| `STOP_LOSS_TRIGGERED` | Crash-loop/repeated-failure policy matched | Report, ACK and continue; notify-only and pending auto stop are not observation completion |
| `STOP_PENDING`, `STOP_CONFIRMATION_OVERDUE` | Stop or release not yet verified | Inspect platform state; never blindly repeat a stop RPC with an unknown result |
| `STOP_CONFIRMED` | Terminal state and zero allocated XPU observed | Record resource release; perform remaining artifact/acceptance checks |
| `WATCH_IDENTITY_UNVERIFIED` | Current trial identity is unavailable | Preserve observation and pending stop intent; wait for matching identity before accepting status |
| `WATCH_IDENTITY_CHANGED` | Job now refers to another trial | Review the replacement, then register its own watch; old authority does not transfer |
| `STABLE`, `TERMINAL` | Platform terminal outcome in managed mode | Check completed/stop state and acceptance evidence; continue reading while stop confirmation or release is pending |

For head-only startup, default to diagnosis. Stop/retry only when evidence and
existing authorization justify it. Automatic requeue is not implemented: it can
lose queue position and does not repair unavailable capacity or incompatible resources.

## Authorized stop-loss and migration

Foreground `poll/follow` and submission-attached watches are notify-only. A new
managed watch can be granted automatic crash-loop stopping explicitly:

```bash
bytedcli --site i18n-tt --json merlin trial watch start \
  --job demo-job-run --owner demo-session --stop-loss auto --yes
```

This grants the daemon permission to stop this exact job/trial after a newly
observed, non-benign completed failure with an in-window end timestamp satisfies
the repeated-failure policy. The default threshold is three completed failures
in one role (three runs shorter than 1800 seconds each, or three accumulated
failures regardless of duration). A death with unknown timing still notifies but
cannot authorize automatic stopping. It does not grant retry,
requeue, priority changes or automatic head-only stopping. Failures predating the
first observation do not trigger an automatic stop. Stop intent is durable before
the RPC; an interrupted/uncertain send is reconciled by readback, never blindly resent.

Before migrating from another watcher, preserve its unhandled events, assignment
and authority. Validate the new watcher using a separate test trial in notify-only mode first.
Choose the production watch policy before its first registration: a registered
notify-only watch cannot be promoted to auto by repeating start or stop/resume.
Retire the old automatic stop owner before registering the production automatic watch. This is a controlled cutover:
this CLI does not import the Python watcher's checkpoints or coordinate stop
ownership with another host/tool. Do not enable two automatic stop owners.

Stop or resume local observation without stopping the trial:

```bash
bytedcli --site i18n-tt merlin trial watch stop --watch-id <watch-id> --owner demo-session
bytedcli --site i18n-tt merlin trial watch resume --watch-id <watch-id> --owner demo-session
bytedcli --json merlin daemon status
bytedcli merlin daemon start
# For a host service manager, run the supervisor in the foreground:
bytedcli merlin daemon execute
```

Resume preserves the original checkpoint, budgets and stop policy. Do not reset
state to suppress unresolved events. Use a persistent host and a service manager
with restart enabled for protection across daemon crashes and host restarts.
Detached `merlin daemon start` survives agent/terminal exit; it is not an operating-system
boot service installer. Never purge the watcher state directory as disposable cache.

## Adapter acceptance checks

Before switching operational monitoring to a client adapter, verify with an isolated
test watch: queue-to-running arrives before reader exit; a stall and a run failure
reach handling; an unacknowledged event replays after reader restart; ACK does not
stop collection; the daemon recovers its phase clocks after restart; a milestone
does not detach monitoring; and terminal evidence leads to the recorded parent action.
These checks are independent of the unit tests for the CLI's detector and event store.
