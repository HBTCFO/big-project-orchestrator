#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from orchestrator_common import (
    append_history,
    last_review_path,
    load_json,
    orch_dir,
    read_text,
    save_json,
    state_path,
)


def _finding(code: str, severity: str, title: str, detail: str) -> dict:
    return {
        "code": code,
        "severity": severity,
        "title": title,
        "detail": detail,
    }


def _count_checked_todos(todo_text: str) -> int:
    return sum(1 for line in todo_text.splitlines() if line.strip().startswith("- [x]"))


def run_review_pass(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    orch = orch_dir(repo)
    milestone_id = state.get("current_milestone_id")
    milestone = next((item for item in state.get("milestones", []) if item.get("id") == milestone_id), None)

    verification = state.get("verification", {})
    current_requirements = read_text(orch / "current_requirements.md")
    status_text = read_text(orch / "status.md")
    handoff_text = read_text(orch / "handoff.md")
    todo_text = read_text(orch / "todo.md")

    findings: list[dict] = []

    if verification.get("status") != "passed":
        findings.append(
            _finding(
                "verification-not-green",
                "blocker",
                "Verification must pass before archive",
                "Review cannot approve a milestone while verification is red or missing.",
            )
        )

    if "TBD" in current_requirements or "## Acceptance criteria" not in current_requirements:
        findings.append(
            _finding(
                "current-requirements-incomplete",
                "blocker",
                "Current milestone requirements are incomplete",
                "current_requirements.md still contains placeholders or is missing acceptance criteria.",
            )
        )

    if "## Validation commands" not in current_requirements or "# Add project-specific validation commands here." in current_requirements:
        findings.append(
            _finding(
                "validation-commands-missing",
                "blocker",
                "Validation commands are not concrete",
                "The active milestone must name real commands before it can pass review.",
            )
        )

    if "- Active milestone:" not in status_text or "- Phase:" not in status_text:
        findings.append(
            _finding(
                "status-out-of-date",
                "warn",
                "Status file is missing required summary fields",
                "status.md should include phase and active milestone before archive.",
            )
        )

    if "Put the next commands here." in handoff_text or "## Commands to run next" not in handoff_text:
        findings.append(
            _finding(
                "handoff-placeholder",
                "warn",
                "Handoff still contains placeholder guidance",
                "handoff.md should contain a concrete resume command or next step.",
            )
        )

    if _count_checked_todos(todo_text) == 0:
        findings.append(
            _finding(
                "todo-not-progressed",
                "warn",
                "No checklist items are marked complete",
                "todo.md should reflect at least the work already finished in this cycle.",
            )
        )

    if state.get("project_mode") == "greenfield":
        if not (repo / "README.md").exists() or not (repo / "src").exists() or not (repo / "tests").exists():
            findings.append(
                _finding(
                    "greenfield-bootstrap-missing",
                    "blocker",
                    "Greenfield bootstrap is incomplete",
                    "README.md, src/, and tests/ must exist before archive in greenfield mode.",
                )
            )

    blocking = [item for item in findings if item["severity"] == "blocker"]
    warnings = [item for item in findings if item["severity"] == "warn"]
    status = "passed" if not blocking else "needs_repair"

    lines = [
        "# Review",
        "",
        "## Review status",
        "",
        f"- Status: {status}",
        f"- Blocking findings: {len(blocking)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Findings",
        "",
    ]
    if findings:
        for finding in findings:
            lines.append(f"- [{finding['severity']}] {finding['title']}: {finding['detail']}")
    else:
        lines.append("- No review findings.")

    lines.extend(["", "## Hardening actions", ""])
    if blocking:
        for finding in blocking:
            lines.append(f"- [ ] Resolve {finding['code']}")
    elif warnings:
        for finding in warnings:
            lines.append(f"- [ ] Consider {finding['code']}")
    else:
        lines.append("- [x] No hardening action required before archive.")

    (orch / "review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "status": status,
        "milestone_id": milestone_id,
        "milestone_title": milestone["title"] if milestone else None,
        "blocking_findings": len(blocking),
        "warnings": len(warnings),
        "findings": findings,
    }
    save_json(last_review_path(repo), payload)

    state["review"] = {
        "status": status,
        "last_result_path": str(last_review_path(repo).relative_to(repo)),
        "blocking_findings": len(blocking),
    }
    state["current_phase"] = "archive" if status == "passed" else "repair"
    state["next_action"] = "archive" if status == "passed" else "repair review findings"
    save_json(state_path(repo), state)
    append_history(repo, f"run_review_pass status={status} blockers={len(blocking)} warnings={len(warnings)}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a mandatory review gate before milestone archive")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = run_review_pass(repo)
    print(last_review_path(repo))
    print(f"status={result['status']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
