#!/usr/bin/env python3
"""Create an optimized AI-agent dynamic workflow artifact directory."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

LEVELS = ("scaffold", "execution", "audit")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64].strip("-") or "workflow"


def write_new(path: Path, content: str) -> None:
    if path.exists():
        return
    path.write_text(content, encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def packet_template(packet_id: str, title: str, owner: str = "parent-or-subagent") -> str:
    return f"""---
id: {packet_id}
status: pending
owner: {owner}
write_scope: read-only or paths
---

# Packet: {packet_id}

## Objective

Describe this packet's objective for: {title}

## Context

## Files Or Sources

## Do

## Do Not

## Expected Output

## Verification
"""


def result_template(packet_id: str) -> str:
    return f"""---
packet_id: {packet_id}
status: pending
verification_status: pending
---

# Result: {packet_id}

## Summary

## Accepted

## Rejected

## Conflicts

## Decisions

## Risks

## Verification Evidence

## Follow-up
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("title", help="Workflow title or task summary")
    parser.add_argument(
        "--root",
        default=".workflow",
        help="Directory where workflow runs are stored (default: .workflow)",
    )
    parser.add_argument("--slug", help="Optional explicit workflow slug")
    parser.add_argument(
        "--level",
        choices=LEVELS,
        default="scaffold",
        help="Initial workflow level (default: scaffold)",
    )
    parser.add_argument(
        "--packet",
        action="append",
        default=[],
        help="Packet ID to create. Repeat for multiple packets. Default creates 00-template.",
    )
    args = parser.parse_args()

    slug = slugify(args.slug or args.title)
    run_dir = Path(args.root) / slug
    packets_dir = run_dir / "packets"
    results_dir = run_dir / "results"
    packets_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    created_at = now_iso()
    packet_ids = args.packet or ["00-template"]
    packets = [
        {
            "id": packet_id,
            "objective": "",
            "context": "",
            "files_or_sources": [],
            "ownership": "parent-or-subagent",
            "write_scope": "read-only or paths",
            "do": [],
            "do_not": [],
            "expected_output": "",
            "verification": [],
            "status": "pending",
            "result_path": f"results/{packet_id}.md",
        }
        for packet_id in packet_ids
    ]
    state = {
        "title": args.title,
        "slug": slug,
        "created_at": created_at,
        "last_updated_at": created_at,
        "status": "planned",
        "workflow_level": args.level,
        "current_phase": "scaffold",
        "non_goals": [],
        "success_criteria": [],
        "constraints": [],
        "risks": [],
        "approval": {"required": False, "granted": None, "events": [], "notes": ""},
        "max_concurrent_agents": 4,
        "max_total_agents": 12,
        "packets": packets,
        "active_packets": [],
        "integration_policy": {
            "owner": "parent",
            "conflict_resolution": "Inspect authoritative sources before choosing.",
            "accepted": [],
            "rejected": [],
            "decisions": [],
            "remaining_risks": [],
            "final_output": "",
        },
        "verification": {"status": "not_started", "checks": []},
        "blocked_reason": "",
        "reusable_artifacts": [],
    }

    write_new(
        run_dir / "plan.md",
        f"""# {args.title}

## Goal

## Non-goals

## Success Criteria

## Current Context

## Constraints

## Risks

## Approval Required

## Workflow Level

{args.level}

## Work Packets

## Integration Policy

## Verification

## Reusable Artifacts
""",
    )
    write_new(
        run_dir / "orchestration.md",
        f"""# Orchestration: {args.title}

## Execution Rules

- Keep the original objective intact.
- Ask for approval before risky, expensive, external, or destructive actions.
- Keep immediate blocking work local.
- Delegate only bounded, disjoint, materially useful packets.
- Keep final integration in the parent agent.
- Integrate packet results before final verification.

## Branching Rules

## Packet Prompts

## Completion Audit
""",
    )
    write_new(run_dir / "state.json", json.dumps(state, indent=2) + "\n")
    write_new(
        run_dir / "final-report.md",
        f"""# Final Report: {args.title}

## Outcome

## Accepted Results

## Rejected Results

## Conflicts Resolved

## Decisions

## Verification Evidence

## Remaining Risks

## Reusable Follow-up
""",
    )

    for packet_id in packet_ids:
        write_new(packets_dir / f"{packet_id}.md", packet_template(packet_id, args.title))
        write_new(results_dir / f"{packet_id}.md", result_template(packet_id))

    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
