---
name: codex-dynamic-workflows-optimized
description: Plan and run optimized AI-agent dynamic workflows for complex, multi-track tasks that need explicit orchestration, bounded subagents, approval gates, structured packet/result artifacts, integration decisions, and staged verification. Use when the user explicitly asks for this skill, dynamic workflow orchestration, swarm/subagents/parallel agents, Claude Code-style orchestration, large migrations, repo-wide audits, or multi-track research plus implementation. Do not use for simple one-shot edits, single-file bug fixes, basic explanations, or ordinary tasks that can be completed directly.
---

# Optimized AI Agent Dynamic Workflows

Use this skill to turn a broad or risky task into a supervised workflow: define the success contract, create durable artifacts, split independent work packets, run only useful subagents, integrate results, verify evidence, and preserve reusable recipes when they will pay off later.

This skill is intentionally heavier than direct execution. Prefer direct work for small tasks. The value of this skill is drift control, risk control, resumability, and independent verification.

## Fast Decision

Use this skill when at least two are true, or when the user explicitly asks for this skill, a swarm, subagents, parallel agents, a dynamic workflow, or Claude Code-style orchestration:

- The task has independent research, implementation, QA, docs, design, security, or migration tracks.
- The task is broad enough that explicit success criteria reduce drift.
- The task is risky: destructive edits, external writes, deploys, secrets, production data, billing, user accounts, large repo-wide changes, or unusual cost.
- A separate verification pass would materially improve confidence.
- The workflow could become a reusable recipe.

Skip full orchestration and do the work directly when the task is:

- a single small edit, typo fix, rename, or explanation;
- a focused single-file or single-function bug fix;
- a read-only answer that does not need durable artifacts;
- a task where packet setup would take longer than execution.

If the user explicitly invokes this skill for a small task, briefly say full orchestration is unnecessary, complete the task directly, and report the lightweight verification used.

## Operating Contract

When using this skill:

1. Restate the goal, non-goals, and success criteria.
2. Choose a workflow level: `direct`, `scaffold`, `execution`, or `audit`.
3. Create or update a workflow artifact before delegation or multi-step execution.
4. Ask approval before risky, expensive, external, irreversible, or destructive steps.
5. Split work into disjoint packets with clear ownership and expected evidence.
6. Spawn subagents only when the environment supports them and their work is concrete, bounded, and non-duplicative.
7. Keep critical-path decisions and final integration in the parent agent.
8. Simulate subagents with isolated packet notes when no subagent runner exists.
9. Integrate results explicitly; never paste raw worker dumps as the final answer.
10. Verify with checks matched to the task's blast radius.
11. Save reusable artifacts only when they will reduce future work.

## Workflow Levels

Use the lightest level that preserves safety and quality:

| Level | Use when | Required artifacts | Verification expectation |
|---|---|---|---|
| `direct` | The task is small, even if the user named this skill | none, unless useful | narrow check or diff review |
| `scaffold` | The user asks for a plan, or risk/approval blocks execution | `plan.md`, `state.json`, `orchestration.md` | artifact completeness |
| `execution` | The task will be implemented across packets | packets, results, integration notes | task-specific tests/checks |
| `audit` | The workflow is complete enough to hand off or reuse | final report, verification evidence, decisions | completeness plus evidence review |

## Workflow Artifacts

Prefer creating a local run directory:

```text
.workflow/<slug>/
|-- plan.md
|-- state.json
|-- orchestration.md
|-- packets/
|   `-- 00-template.md
|-- results/
|   `-- 00-template.md
`-- final-report.md
```

Use the scaffolder:

```bash
python3 /path/to/codex-dynamic-workflows-optimized/scripts/new_workflow.py "Task title"
```

Useful flags:

```bash
python3 /path/to/codex-dynamic-workflows-optimized/scripts/new_workflow.py "Task title" --level execution --packet 01-discovery --packet 02-verification
```

Keep `plan.md` as the human source of truth. Use `state.json` for machine-readable status, approvals, packets, integration decisions, and verification state. Use `orchestration.md` for execution order, branching rules, and packet prompts.

## Orchestration Plan

Draft a concise plan with:

```text
Goal:
Non-goals:
Success criteria:
Current context:
Constraints:
Risks:
Approval required:
Workflow level:
Workflow artifact path:
Work packets:
Integration policy:
Verification:
Reusable artifacts:
```

Do not over-plan obvious work. The plan should guide delegation and verification, not replace execution.

## Approval Gates

Ask one clear approval question before:

- deleting, overwriting, mass-renaming, force-pushing, or rewriting history;
- running migrations, broad codemods, or dependency upgrades;
- deploying, publishing, emailing, posting, or changing external systems;
- touching credentials, secrets, production data, billing, or user accounts;
- spawning more than 4 concurrent agents, more than 12 total agents, or long-running expensive jobs;
- making changes outside the requested repository or workspace.

Small subagent usage does not need a second approval when the user explicitly asked for this skill, subagents, a swarm, or parallel agents, and the run stays within `max_concurrent_agents <= 4`, `max_total_agents <= 12`, and safe local read/write bounds.

Read `references/risk-gates.md` when risk is unclear.

## Subagent Policy

Use subagents for sidecar work that can proceed independently while the parent agent advances the critical path. Good packets include codebase discovery, dependency/API research, tests/fixtures, docs/examples, UX/product review, security review, and final verification.

Keep these limits unless the user approves more:

- `max_concurrent_agents`: 2-4
- `max_total_agents`: 6-12
- no duplicate ownership across packets
- no overlapping write scope for code-edit packets

Tell workers they are not alone in the codebase, must not revert others' changes, and must adapt to concurrent edits. Wait for subagents only when their result is needed for the next critical-path decision.

When no subagent runner is available:

- simulate the swarm with isolated packet passes;
- read only packet-relevant files during each pass;
- write packet notes under `results/` using the result template;
- integrate only after packet outputs are separate.

## Packet Format

Each packet file should follow this template:

```text
---
id: 01-discovery
status: pending
owner: parent-or-subagent
write_scope: read-only or paths
---

# Packet: 01-discovery

## Objective
## Context
## Files Or Sources
## Do
## Do Not
## Expected Output
## Verification
```

For code-edit packets, assign non-overlapping files or modules. If overlap becomes necessary, stop and integrate before editing.

## Result Format

Each result file should follow this template:

```text
---
packet_id: 01-discovery
status: complete
verification_status: pending
---

# Result: 01-discovery

## Summary
## Accepted
## Rejected
## Conflicts
## Decisions
## Risks
## Verification Evidence
## Follow-up
```

This structure lets `collect_results.py` produce stable integration checklists instead of relying only on loose Markdown heuristics.

## Integration

After packets complete, synthesize:

```text
Accepted:
Rejected:
Conflicts:
Decisions:
Final changes:
Remaining risks:
Verification evidence:
```

Resolve conflicts explicitly. If packets disagree, inspect the authoritative source before choosing. Keep the final answer concise and integrated; attach or cite packet files only when useful.

Use the collector:

```bash
python3 /path/to/codex-dynamic-workflows-optimized/scripts/collect_results.py .workflow/<slug> --output .workflow/<slug>/integration-checklist.md
```

## Verification

Run the narrowest reliable checks first, then broaden as risk warrants:

- unit tests for touched code;
- typecheck or lint;
- build;
- browser or UI smoke test;
- script dry run;
- source citation check;
- migration dry run;
- manual checklist for non-code work.

Use staged workflow verification:

```bash
python3 /path/to/codex-dynamic-workflows-optimized/scripts/verify_workflow.py .workflow/<slug> --level scaffold
python3 /path/to/codex-dynamic-workflows-optimized/scripts/verify_workflow.py .workflow/<slug> --level execution
python3 /path/to/codex-dynamic-workflows-optimized/scripts/verify_workflow.py .workflow/<slug> --level audit
```

Report skipped checks honestly. Do not call the workflow complete until evidence supports the original success criteria.

## Short Happy Path

1. Decide `direct` vs workflow; skip orchestration for small work.
2. Scaffold `.workflow/<slug>/` for multi-track or risky work.
3. Fill goal, success criteria, risks, approval gates, packets, and verification.
4. Run or simulate disjoint packets.
5. Collect results and resolve conflicts.
6. Verify at the narrowest sufficient level, then report outcome and remaining risks.

## Reusable Recipes

When a run produces a useful pattern, save a concise recipe in `.workflow/recipes/<name>.md` or a repo docs folder. Include trigger, plan shape, packet list, verification checklist, and known risks.

Do not save transcripts, secrets, bulky logs, credentials, or sensitive personal details.

## References

- Read `references/plan-schema.md` when a machine-readable workflow plan helps coordination.
- Read `references/risk-gates.md` before risky or ambiguous operations.
- Read `references/validation-examples.md` when forward-testing or improving this skill.
