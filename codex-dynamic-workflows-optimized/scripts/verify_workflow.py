#!/usr/bin/env python3
"""Check optimized AI-agent dynamic workflow artifacts at staged completeness levels."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_FILES = ("plan.md", "state.json", "orchestration.md", "final-report.md")
REQUIRED_DIRS = ("packets", "results")
REQUIRED_STATE_KEYS = (
    "title",
    "slug",
    "status",
    "workflow_level",
    "approval",
    "packets",
    "integration_policy",
    "verification",
)
RESULT_SECTIONS = (
    "## Summary",
    "## Accepted",
    "## Rejected",
    "## Conflicts",
    "## Decisions",
    "## Risks",
    "## Verification Evidence",
    "## Follow-up",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def non_template(files: list[Path]) -> list[Path]:
    return [file for file in files if not file.stem.startswith("00-template")]


def add_base_checks(workflow_dir: Path, failures: list[str]) -> dict:
    if not workflow_dir.is_dir():
        failures.append(f"Missing workflow directory: {workflow_dir}")
        return {}
    for name in REQUIRED_FILES:
        path = workflow_dir / name
        if not path.is_file():
            failures.append(f"Missing file: {path}")
        elif not read_text(path).strip():
            failures.append(f"Empty file: {path}")
    for name in REQUIRED_DIRS:
        path = workflow_dir / name
        if not path.is_dir():
            failures.append(f"Missing directory: {path}")

    state_path = workflow_dir / "state.json"
    if not state_path.is_file():
        return {}
    try:
        state = json.loads(read_text(state_path))
    except json.JSONDecodeError as exc:
        failures.append(f"Invalid JSON in {state_path}: {exc}")
        return {}
    for key in REQUIRED_STATE_KEYS:
        if key not in state:
            failures.append(f"Missing state key: {key}")
    return state


def check_scaffold(workflow_dir: Path, failures: list[str], warnings: list[str], state: dict) -> None:
    packet_files = sorted((workflow_dir / "packets").glob("*.md")) if (workflow_dir / "packets").is_dir() else []
    result_files = sorted((workflow_dir / "results").glob("*.md")) if (workflow_dir / "results").is_dir() else []
    if not packet_files:
        failures.append("No packet template or packet files found under packets/")
    if not result_files:
        failures.append("No result template or result files found under results/")
    if state and state.get("max_concurrent_agents", 0) > 4:
        warnings.append("max_concurrent_agents exceeds the safe default of 4; approval should be recorded.")
    if state and state.get("max_total_agents", 0) > 12:
        warnings.append("max_total_agents exceeds the safe default of 12; approval should be recorded.")


def check_execution(workflow_dir: Path, failures: list[str], warnings: list[str], state: dict) -> None:
    packet_files = sorted((workflow_dir / "packets").glob("*.md")) if (workflow_dir / "packets").is_dir() else []
    result_files = sorted((workflow_dir / "results").glob("*.md")) if (workflow_dir / "results").is_dir() else []
    real_packets = non_template(packet_files)
    real_results = non_template(result_files)
    if not real_packets:
        failures.append("Execution level requires at least one non-template packet file under packets/.")
    if not real_results:
        failures.append("Execution level requires at least one non-template result file under results/.")
    for result_file in real_results:
        text = read_text(result_file)
        missing = [section for section in RESULT_SECTIONS if section not in text]
        if missing:
            failures.append(f"Result file missing required sections: {result_file} ({', '.join(missing)})")
    if state:
        packet_ids = {packet.get("id") for packet in state.get("packets", []) if packet.get("id")}
        file_ids = {file.stem for file in real_packets}
        missing_state = sorted(file_ids - packet_ids)
        if missing_state:
            warnings.append(f"Packet files not listed in state.json: {', '.join(missing_state)}")


def check_audit(workflow_dir: Path, failures: list[str], warnings: list[str], state: dict) -> None:
    final_report = workflow_dir / "final-report.md"
    text = read_text(final_report) if final_report.is_file() else ""
    required_report_sections = ("## Outcome", "## Verification Evidence", "## Remaining Risks")
    for section in required_report_sections:
        if section not in text:
            failures.append(f"Final report missing section: {section}")
    if "## Verification Evidence" in text:
        after = text.split("## Verification Evidence", 1)[1].split("##", 1)[0].strip()
        if not after:
            failures.append("Audit level requires non-empty final-report verification evidence.")
    verification = state.get("verification", {}) if state else {}
    checks = verification.get("checks", []) if isinstance(verification, dict) else []
    required_checks = [check for check in checks if check.get("required")]
    not_passed = [check.get("check", "unnamed") for check in required_checks if check.get("status") != "passed"]
    if not_passed:
        failures.append(f"Required verification checks not passed: {', '.join(not_passed)}")
    if not checks:
        warnings.append("No verification checks recorded in state.json.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow_dir", help="Path to .workflow/<slug>")
    parser.add_argument(
        "--level",
        choices=("scaffold", "execution", "audit"),
        default="audit",
        help="Completeness level to verify (default: audit)",
    )
    args = parser.parse_args()

    workflow_dir = Path(args.workflow_dir)
    failures: list[str] = []
    warnings: list[str] = []
    state = add_base_checks(workflow_dir, failures)

    if not failures:
        check_scaffold(workflow_dir, failures, warnings, state)
    if not failures and args.level in {"execution", "audit"}:
        check_execution(workflow_dir, failures, warnings, state)
    if not failures and args.level == "audit":
        check_audit(workflow_dir, failures, warnings, state)

    if failures:
        print(f"Workflow verification failed at level '{args.level}':")
        for failure in failures:
            print(f"- {failure}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"- {warning}")
        return 1

    print(f"Workflow verification passed at level '{args.level}': {workflow_dir}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
