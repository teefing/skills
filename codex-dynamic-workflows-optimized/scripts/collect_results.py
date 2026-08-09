#!/usr/bin/env python3
"""Summarize structured workflow packet results into an integration checklist."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REQUIRED_SECTIONS = (
    "Summary",
    "Accepted",
    "Rejected",
    "Conflicts",
    "Decisions",
    "Risks",
    "Verification Evidence",
    "Follow-up",
)

FALLBACK_MARKERS = (
    "Accepted",
    "Rejected",
    "Conflict",
    "Decision",
    "Risk",
    "Verification",
    "TODO",
)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip("\n")
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data, body


def parse_sections(body: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in body.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def interesting_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if stripped.startswith(("-", "*", "#")) or any(marker.lower() in lowered for marker in FALLBACK_MARKERS):
            lines.append(stripped)
    return lines[:40]


def heading_for(path: Path, metadata: dict[str, str]) -> str:
    packet_id = metadata.get("packet_id") or metadata.get("id") or path.stem
    return packet_id.replace("-", " ").replace("_", " ").title()


def render_structured(file: Path, metadata: dict[str, str], sections: dict[str, str]) -> list[str]:
    lines = [f"## {heading_for(file, metadata)}", ""]
    status = metadata.get("status", "unknown")
    verification_status = metadata.get("verification_status", "unknown")
    lines.extend([f"- Status: {status}", f"- Verification: {verification_status}", ""])

    missing = [section for section in REQUIRED_SECTIONS if section not in sections]
    if missing:
        lines.append(f"- Missing sections: {', '.join(missing)}")
        lines.append("")

    for section in REQUIRED_SECTIONS:
        value = sections.get(section, "").strip()
        if value:
            lines.extend([f"### {section}", "", value, ""])
    if not any(sections.get(section, "").strip() for section in REQUIRED_SECTIONS):
        lines.append("No structured result content found; inspect this result manually.")
        lines.append("")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow_dir", help="Path to .workflow/<slug>")
    parser.add_argument(
        "--output",
        help="Optional output Markdown path (default: print to stdout)",
    )
    args = parser.parse_args()

    workflow_dir = Path(args.workflow_dir)
    results_dir = workflow_dir / "results"
    if not results_dir.is_dir():
        raise SystemExit(f"Missing results directory: {results_dir}")

    files = sorted(results_dir.glob("*.md"))
    lines = [f"# Integration Checklist: {workflow_dir.name}", ""]
    if not files:
        lines.extend(["No result files found.", ""])
    for file in files:
        text = file.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)
        sections = parse_sections(body)
        if sections:
            lines.extend(render_structured(file, metadata, sections))
        else:
            lines.extend([f"## {heading_for(file, metadata)}", ""])
            snippets = interesting_lines(text)
            if snippets:
                lines.extend(snippets)
            else:
                lines.append("No checklist-like lines found; inspect this result manually.")
            lines.append("")

    lines.extend(
        [
            "## Integration Decisions",
            "",
            "Accepted:",
            "",
            "Rejected:",
            "",
            "Conflicts:",
            "",
            "Decisions:",
            "",
            "Remaining risks:",
            "",
            "Verification still needed:",
            "",
        ]
    )
    output = "\n".join(lines)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
