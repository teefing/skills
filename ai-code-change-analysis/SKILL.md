---
name: "ai-code-change-analysis"
description: "Analyzes AI-related branch diffs, architecture, state flows, and user-action call chains. Invoke for AI code change analysis or an architecture report, optionally delivered to Lark."
---

# AI Code Change Analysis

Analyze AI feature changes from repository evidence. Produce an architecture explanation that lets a reader answer:

- What changed relative to the baseline?
- Which layer owns each responsibility?
- What happens, method by method, after each user action?
- How are async results, stale interactions, cleanup, and fallback handled?
- Which conclusions are verified, and which remain assumptions?

## Inputs

Resolve these before analysis:

- **Base**: use the user-specified commit, branch, or tag. Otherwise use `master`.
- **Target**: use the user-specified target. Otherwise use `HEAD`.
- **Scope**: determine whether the user wants committed branch changes, staged changes, unstaged changes, or all three.
- **Delivery**: chat, local document, new Lark document, or update to an existing Lark document.

State the resolved base, target, merge base, and included working-tree scope in the report. If the named base is unavailable, ask for a valid base instead of silently substituting another ref.

## Required Dependencies

Before acting:

1. Read the repository's `AGENTS.md` files that govern every touched path.
2. For Lynx, ReactLynx, TTML, TTSS, Rspeedy, component, event, rendering, or lifecycle behavior, query LynxBase MCP before explaining the behavior. Follow the repository's Lynx skill as well.
3. Use Lynx DevTool only when the user explicitly requests runtime inspection.
4. For Lark delivery, invoke the `lark-doc` skill and follow its v2 create/update workflow. Do not duplicate its CLI or XML rules here.

## Workflow

### 1. Freeze the comparison scope

Collect:

```bash
git status --short --branch
git rev-parse --abbrev-ref HEAD
git merge-base <base> <target>
git diff --name-status <base>...<target>
git diff --stat <base>...<target>
git diff --numstat <base>...<target>
```

If working-tree changes are included, inspect them separately:

```bash
git diff --name-status
git diff --cached --name-status
```

Keep these scopes separate throughout the report:

- `<base>...<target>`: committed branch delta from the merge base.
- `git diff --cached`: staged local delta.
- `git diff`: unstaged local delta.

Completion criterion: every changed file in the selected scope is classified or explicitly marked generated, vendored, fixture, or irrelevant with a reason.

### 2. Build a change inventory

Classify changed files by responsibility, not only directory:

- entry point and lifecycle wiring
- UI component and view model
- controller or orchestrator
- state machine and session state
- AI SDK, model, prompt, or context adapter
- event protocol and payload types
- data collection and exposure/click context
- host effects, JSB, network, storage, or feed adapter
- logging, reporting, feature flags, and runtime configuration
- tests, mocks, fixtures, and generated artifacts

Read targeted diffs and surrounding code. Prefer `rg`, `git diff -- <path>`, and bounded `sed` ranges over dumping the full repository diff.

Completion criterion: the inventory names each meaningful file, its role before and after the change, and its direct collaborators.

### 3. Reconstruct architecture from wiring

Start from actual construction and registration sites. Trace this spine:

```text
page/card lifecycle
  -> dependency construction
  -> event registration/subscription
  -> controller/orchestrator
  -> state machine or headless core
  -> SDK/port/adapter
  -> host side effect
  -> callback/event response
  -> UI publication
  -> cleanup/reset
```

For each layer, record:

- owned state
- accepted inputs
- emitted outputs
- side effects
- lifecycle and cleanup owner
- invariants and guards

Distinguish direct calls, event-bus calls, async callbacks, timers, and host/JSB calls. Do not infer an edge from matching names alone.

Completion criterion: every architecture arrow is backed by a call site, event registration, subscription, callback binding, or interface implementation.

### 4. Extract state and protocol contracts

Identify:

- state union or enum
- transition events and guards
- state-to-view configuration mapping
- event names and payload types
- session identifiers, source identifiers, revisions, request IDs, or operation IDs
- sticky-event behavior
- feature flags and runtime configuration
- timeout and retry constants

Build a transition table:

| Current state | Trigger | Guard | Next state | Side effect | Recovery |
|---|---|---|---|---|---|

Verify where counters are incremented, where IDs are generated, and where version checks reject stale work. A declared type is not proof that runtime payloads have that shape; inspect normalization and guards.

Completion criterion: every changed state, event field, guard, and configuration value is accounted for.

### 5. Trace user-action call chains

List all user-visible operations supported by the changed code. Typical AI flows include:

- page load and initial hiding/unlocking
- item exposure
- item click
- feed scroll start and idle
- AI entrance render and shown callback
- entrance click and panel open
- open-parameter handshake
- AI streaming product/result callback
- batching and insertion
- SDK finish and error
- close, split close, delete, or cancel
- negative feedback or recommendation refresh
- pull refresh
- page hidden and visible again
- view-finish cleanup
- page or controller destruction

For each operation, use this format:

| User operation | Source event | Ordered methods | Guard / state change | Side effect / result |
|---|---|---|---|---|

The **Ordered methods** cell must show the real sequence across components, for example:

```text
UI handler
  -> publishEvent
  -> popup/page event proxy
  -> controller handler
  -> state-machine transition
  -> SDK/adapter method
  -> callback
  -> state publication
  -> UI update
```

Include early returns and alternative branches such as stale revision, debug action, timeout, JSB rejection, fallback, and hidden-page deferral.

Completion criterion: every changed public handler and every registered event is reachable from at least one flow or documented as internal/debug-only.

### 6. Audit async reliability and cleanup

Inspect these failure classes explicitly:

| Risk | Evidence to locate |
|---|---|
| stale UI interaction | `sourceId`, `revision`, current-publication checks |
| old AI callback contaminates a new session | session/request ID checks, timer cancellation |
| duplicate queue processing | processing lock, idempotent operation ID |
| host operation timeout | pending-operation map, timeout callback, fallback |
| page hidden during callback | visibility queue and resume logic |
| partial insertion/deletion | inserted-item tracking and compensating delete |
| refresh or destruction leak | unsubscribe, timer clear, SDK close, store reset |
| terminal-state cleanup loss | callback execution on delete, refresh, reset, and view finish |
| unsupported client capability | version check and JSB-to-legacy fallback |

Treat cleanup callbacks as part of the behavior contract. Follow them through delete, refresh, session replacement, terminal state, and destroy paths.

Completion criterion: each applicable risk has a concrete defense, a documented gap, or an explicit “not applicable” reason.

### 7. Check tests and observability

Map tests to:

- transition guards
- stale-event rejection
- session isolation
- streaming batches
- timeout/fallback
- cleanup
- visibility deferral
- error handling

Also identify logs and reports that can verify the production flow. Separate implemented coverage from recommended coverage.

Completion criterion: the report states what was tested, what was only statically verified, and the highest-risk untested path.

### 8. Produce the report

Use this order:

1. comparison scope and executive summary
2. changed-file inventory
3. architecture and module responsibilities
4. state machine and protocol contracts
5. end-to-end AI request/result flow
6. user-action ordered method flows
7. stale interaction, concurrency, cleanup, and fallback
8. configuration, logging, and debugging
9. tests and residual risks
10. source index

Use source links or `path:line` references for important claims. Mark uncertain statements as assumptions and name the missing evidence.

For Lark delivery:

- Create a new document when no destination is supplied.
- Update the existing document when the user supplies a URL or asks to extend the previous report.
- Prefer a summary table followed by detailed ordered flows.
- Verify the update result and report the document URL.
- Remove temporary local content files after a successful update.

## Quality Gate

The analysis is complete only when:

- comparison scope is explicit
- every meaningful changed file is classified
- architecture arrows have code evidence
- all changed events and public handlers appear in a flow
- user operations show ordered method chains
- state guards and stale-work rejection are explained
- cleanup is traced through every terminal path
- fallback and timeout behavior are covered
- tests and unverified risks are separated
- requested delivery has been verified

Never replace missing evidence with a plausible framework story. Continue reading the code until the call chain is proven or report the precise gap.
