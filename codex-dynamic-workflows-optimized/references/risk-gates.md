# Risk Gates

Use this checklist before launching or continuing a dynamic workflow.

## Ask For Approval

Ask one clear approval question before work that may:

- delete, overwrite, mass-rename, force-push, rewrite history, or make irreversible repository changes;
- deploy, publish, email, post, create public resources, or mutate external systems;
- run database migrations, broad codemods, broad dependency upgrades, or generated changes across many files;
- touch credentials, secrets, billing, production data, user accounts, or private customer data;
- spawn more than 4 concurrent agents, more than 12 total agents, or consume unusual time, money, or compute;
- make changes outside the requested repository or workspace.

## Safe Without Extra Approval

Usually safe:

- reading local files in the requested workspace;
- drafting plans, packet prompts, reports, or local artifacts;
- running narrow tests, linters, typechecks, dry runs, and read-only inspections;
- creating non-destructive workflow directories under `.workflow/`;
- spawning a small number of subagents when the user explicitly asked for subagents, a swarm, parallel agents, or this dynamic workflow skill, and the run stays within local safe bounds.

## Ambiguous Risk Protocol

Prefer a reversible next step:

1. Do a read-only inspection.
2. Draft the exact command or action.
3. Explain the likely effect and blast radius.
4. Ask for approval before execution.

Do not bury multiple risky approvals in one broad question. If the user denies or does not answer, continue only with safe planning, local drafts, or non-destructive checks.

## Approval Event Template

Record approvals in `state.json` using this shape:

```json
{
  "at": "2026-06-09T00:00:00+00:00",
  "question": "Approve deleting the old REST client after GraphQL migration verification passes?",
  "decision": "approved",
  "notes": "User approved deletion only after tests pass."
}
```
