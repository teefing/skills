---
name: step
description: Clarify user requirements without executing. Invoke when user says 'step' or wants to define scope via structured interview; runs grill-me to sharpen intent but stops before implementation.
disable-model-invocation: true
---

# Step — Requirements Clarification Only

This skill is a **requirements-clarification stage**. It reuses the `grill-me` interview flow to converge on a shared understanding of what the user actually wants, but it **must not execute, implement, code, or otherwise act** on the outcome.

## Behavior

1. Run a `/grilling` session (via `grill-me`) to interview the user about the request.
   - Ask one question at a time; wait for the answer before moving on.
   - Prefer looking up **facts** from the environment (filesystem, tools) rather than asking.
   - For each **decision**, put it to the user and record their answer.
2. When the interview converges, produce a concise **Requirements Summary** containing:
   - Goal / problem statement
   - In-scope items
   - Explicit out-of-scope items
   - Confirmed decisions (with the user's answer for each)
   - Open questions / assumptions still to be validated
   - Acceptance criteria — how we will know it is done
3. Ask the user to confirm the summary. Wait for explicit confirmation.

## Hard Constraints — Do Not Execute

While operating in `step` mode:

- **Do not** write, edit, or delete production code, configuration, or docs.
- **Do not** run builds, tests, migrations, deploys, or any side-effectful commands.
- **Do not** create branches, commits, PRs, or issues.
- **Do not** call tools that mutate remote state (CI, chat, tickets, dashboards).
- Read-only lookups (Read, ls, grep, doc/MCP queries) are allowed **only** to gather facts needed to ask better clarifying questions.

If the user asks you to implement during a `step` session, remind them that `step` only clarifies requirements, and ask whether they want to exit `step` and proceed to implementation as a separate action.

## Output Shape

End the session with a Markdown block like:

```markdown
## Requirements Summary
- **Goal**: ...
- **In scope**: ...
- **Out of scope**: ...
- **Decisions**:
  - Q: ... → A: ...
- **Open questions / assumptions**: ...
- **Acceptance criteria**: ...

Status: Awaiting user confirmation. No implementation performed.
```
