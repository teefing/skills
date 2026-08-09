# Validation Examples

Use these examples to forward-test this skill. Each case lists trigger intent, expected behavior, and failure modes.

## Small Task

Prompt:

```text
Use $codex-dynamic-workflows-optimized to fix a typo in README.md.
```

Expected behavior:

- Choose `direct` level and explain that full orchestration is unnecessary.
- Make the edit directly.
- Verify the diff or file content.
- Do not create a workflow directory unless the user insists.

Failure modes:

- Creates `.workflow/` for a typo.
- Spawns subagents.
- Produces a long orchestration plan instead of fixing the typo.

## Risky Migration

Prompt:

```text
Use $codex-dynamic-workflows-optimized to migrate all API clients from REST to GraphQL and delete the old client.
```

Expected behavior:

- Create `scaffold` artifacts first.
- Mark deletion and broad migration as approval-gated.
- Create packets for discovery, implementation, tests, docs, and verification.
- Ask before destructive edits.
- Move to `execution` only after safe scope and approvals are clear.

Failure modes:

- Deletes old client before verification.
- Gives all agents overlapping write scope.
- Skips final integration.

## Parallel Research And Implementation

Prompt:

```text
Use $codex-dynamic-workflows-optimized to add SSO support. Research the provider docs, implement backend changes, update UI, and add tests.
```

Expected behavior:

- Create workflow artifacts.
- Split provider research, backend, frontend, tests, and docs into disjoint packets.
- Keep integration and final decisions in the parent agent.
- Use no more than 4 concurrent agents unless approved.
- Integrate results before final verification.

Failure modes:

- Starts implementation without a success contract.
- Lets multiple workers edit the same files without coordination.
- Treats raw subagent output as final answer.

## Codebase Audit

Prompt:

```text
Use $codex-dynamic-workflows-optimized to audit this repo for slow startup and fix the biggest issue.
```

Expected behavior:

- Create audit packets for entrypoint tracing, dependency loading, build/test evidence, and fix candidates.
- Keep immediate blocking investigation local.
- Use subagents only for sidecar analysis.
- Implement one highest-confidence fix and verify it.

Failure modes:

- Runs broad speculative changes.
- Fixes multiple low-confidence issues.
- Does not preserve evidence for the selected fix.

## No Subagent Runner

Prompt:

```text
Use $codex-dynamic-workflows-optimized to review this feature for security and reliability risks.
```

Expected behavior:

- Simulate subagents with isolated packet notes under `results/`.
- Keep security and reliability findings separate until integration.
- Use the result template for each packet.
- Produce a synthesized final report.

Failure modes:

- Claims a script spawned agents when no runner exists.
- Mixes all findings into one undifferentiated note before integration.

## Scaffold Verification

Prompt:

```text
Create a dynamic workflow plan for a repo-wide logging cleanup, but do not execute it yet.
```

Expected behavior:

- Create `scaffold` level artifacts.
- `verify_workflow.py --level scaffold` passes.
- `--level execution` may fail or warn because no real packet results exist yet.

Failure modes:

- Requires packet result files before execution begins.
- Marks the workflow complete without evidence.
