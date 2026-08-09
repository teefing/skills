# Plan Schema

Use this schema when a machine-readable workflow plan helps coordination. Keep `plan.md` as the human source of truth.

```json
{
  "goal": "string",
  "non_goals": ["string"],
  "success_criteria": ["string"],
  "current_context": "string",
  "constraints": ["string"],
  "workflow_level": "direct | scaffold | execution | audit",
  "risks": [
    {
      "risk": "string",
      "severity": "low | medium | high",
      "approval_required": true,
      "mitigation": "string",
      "status": "open | mitigated | accepted"
    }
  ],
  "approval": {
    "required": false,
    "granted": null,
    "events": [
      {
        "at": "ISO-8601 string",
        "question": "string",
        "decision": "approved | denied | deferred",
        "notes": "string"
      }
    ]
  },
  "max_concurrent_agents": 4,
  "max_total_agents": 12,
  "packets": [
    {
      "id": "01-discovery",
      "objective": "string",
      "context": "string",
      "files_or_sources": ["string"],
      "ownership": "parent | subagent | simulated",
      "write_scope": "read-only or path list",
      "do": ["string"],
      "do_not": ["string"],
      "expected_output": "string",
      "verification": ["string"],
      "status": "pending | in_progress | complete | blocked | skipped",
      "result_path": "results/01-discovery.md"
    }
  ],
  "integration_policy": {
    "owner": "parent",
    "conflict_resolution": "Inspect authoritative sources before choosing.",
    "accepted": ["string"],
    "rejected": ["string"],
    "decisions": ["string"],
    "remaining_risks": ["string"],
    "final_output": "string"
  },
  "verification": [
    {
      "check": "string",
      "command": "string or null",
      "required": true,
      "status": "pending | passed | failed | skipped",
      "evidence": "string"
    }
  ],
  "reusable_artifacts": ["string"],
  "last_updated_at": "ISO-8601 string"
}
```

Suggested defaults:

- `workflow_level`: start with `scaffold`; move to `execution` only when work is approved and underway.
- `max_concurrent_agents`: 2-4 for normal work.
- `max_total_agents`: 6-12 unless the user approves a larger run.
- Packet IDs: prefix with two digits so files sort naturally.
- Status values: `pending`, `in_progress`, `complete`, `blocked`, `skipped`.
- Verification status values: `pending`, `passed`, `failed`, `skipped`.

Use `state.json` to track recovery state. A workflow should be resumable after interruption by reading `state.json`, `plan.md`, packet files, and result files.
