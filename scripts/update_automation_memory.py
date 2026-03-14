#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from orchestrator_common import (
    append_decision,
    append_history,
    automation_memory_markdown_path,
    automation_memory_path,
    load_json,
    now_stamp,
    save_json,
    state_path,
)


def _command_id(command: str) -> str:
    return hashlib.sha1(command.encode("utf-8")).hexdigest()[:12]


def _normalize_findings(repo: Path) -> list[dict]:
    orch = repo / ".codex" / "orchestrator"
    automation = load_json(orch / "automation_report.json")
    verification = load_json(orch / "last_verification.json")
    review = load_json(orch / "last_review.json")
    escalation = load_json(orch / "escalation_report.json")
    merge_report = load_json(orch / "merge_report.json")

    findings: list[dict] = []
    for command_result in verification.get("commands_run", []):
        if command_result.get("status") != "failed":
            continue
        command = command_result.get("command", "unknown command")
        output = command_result.get("output", "").splitlines()
        detail = output[0] if output else "Verification command failed."
        findings.append(
            {
                "id": f"verification:{_command_id(command)}",
                "source": "verification",
                "severity": "high",
                "title": "Verification command failed",
                "detail": f"{command} :: {detail}",
            }
        )

    for finding in review.get("findings", []):
        findings.append(
            {
                "id": f"review:{finding.get('code', 'unknown')}",
                "source": "review",
                "severity": "high" if finding.get("severity") == "blocker" else "medium",
                "title": finding.get("title", "Review finding"),
                "detail": finding.get("detail", "Review issue detected."),
            }
        )

    active_playbook = escalation.get("active_playbook") or {}
    if active_playbook.get("kind") and active_playbook.get("kind") != "none":
        findings.append(
            {
                "id": f"escalation:{active_playbook['kind']}",
                "source": "escalation",
                "severity": "high",
                "title": active_playbook.get("title", "Escalation active"),
                "detail": active_playbook.get("reason", "An escalation playbook is active."),
            }
        )

    if merge_report.get("status") in {"blocked", "needs_repair"}:
        findings.append(
            {
                "id": f"merge:{merge_report['status']}",
                "source": "merge_orchestration",
                "severity": "high",
                "title": "Merge gate is not green",
                "detail": f"merge_report status is {merge_report['status']}.",
            }
        )

    next_action = automation.get("next_recommended_action") or {}
    if next_action.get("kind") in {"resolve_blocker", "resolve_post_merge_findings"}:
        findings.append(
            {
                "id": f"supervisor:{next_action['kind']}",
                "source": "supervisor",
                "severity": "medium",
                "title": "Supervisor recommends recovery work",
                "detail": next_action.get("reason", "Supervisor indicates recovery work is needed."),
            }
        )

    deduped: dict[str, dict] = {}
    for item in findings:
        deduped[item["id"]] = item
    return list(deduped.values())


def update_automation_memory(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    memory = load_json(automation_memory_path(repo))
    registry = memory.get("registry", [])
    recent_runs = memory.get("recent_runs", [])
    current_findings = _normalize_findings(repo)
    current_ids = {item["id"] for item in current_findings}
    timestamp = now_stamp()

    registry_by_id = {item["id"]: item for item in registry if "id" in item}
    previous_open_ids = {item["id"] for item in registry if item.get("status") == "open"}

    new_findings: list[dict] = []
    known_findings: list[dict] = []
    for item in current_findings:
        existing = registry_by_id.get(item["id"])
        if existing:
            existing["status"] = "open"
            existing["last_seen"] = timestamp
            existing["seen_count"] = int(existing.get("seen_count", 1)) + 1
            existing["detail"] = item["detail"]
            existing["severity"] = item["severity"]
            existing["title"] = item["title"]
            existing["source"] = item["source"]
            existing.pop("resolved_at", None)
            known_findings.append(existing)
        else:
            created = {
                **item,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "seen_count": 1,
                "status": "open",
            }
            registry.append(created)
            registry_by_id[created["id"]] = created
            new_findings.append(created)

    resolved_findings: list[dict] = []
    for item in registry:
        if item.get("status") == "open" and item.get("id") not in current_ids:
            item["status"] = "resolved"
            item["resolved_at"] = timestamp
            resolved_findings.append(item)

    open_findings = [item for item in registry if item.get("status") == "open"]
    run_summary = {
        "run_at": timestamp,
        "milestone_id": state.get("current_milestone_id"),
        "overall_health": load_json(repo / ".codex" / "orchestrator" / "automation_report.json").get("overall_health", "unknown"),
        "open_findings": len(open_findings),
        "new_findings": [item["id"] for item in new_findings],
        "resolved_findings": [item["id"] for item in resolved_findings],
    }
    recent_runs = [run_summary, *recent_runs][:25]

    payload = {
        "milestone_id": state.get("current_milestone_id"),
        "last_run_at": timestamp,
        "open_findings": len(open_findings),
        "new_findings": len(new_findings),
        "known_findings": len(known_findings),
        "resolved_since_last_run": len(resolved_findings),
        "current_open_ids": [item["id"] for item in open_findings],
        "registry": sorted(registry, key=lambda item: (item.get("status") != "open", item.get("id", ""))),
        "recent_runs": recent_runs,
    }
    save_json(automation_memory_path(repo), payload)

    lines = [
        "# Automation memory",
        "",
        f"- Milestone: {payload['milestone_id'] or 'none'}",
        f"- Last run: {timestamp}",
        f"- Open findings: {payload['open_findings']}",
        f"- New findings: {payload['new_findings']}",
        f"- Known findings: {payload['known_findings']}",
        f"- Resolved since last run: {payload['resolved_since_last_run']}",
        "",
        "## New findings",
        "",
    ]
    if new_findings:
        lines.extend(f"- [{item['severity']}] {item['title']} ({item['id']})" for item in new_findings)
    else:
        lines.append("- None.")
    lines.extend(["", "## Known recurring findings", ""])
    if known_findings:
        lines.extend(f"- [{item['severity']}] {item['title']} ({item['id']})" for item in known_findings)
    else:
        lines.append("- None.")
    lines.extend(["", "## Resolved since last run", ""])
    if resolved_findings:
        lines.extend(f"- {item['title']} ({item['id']})" for item in resolved_findings)
    else:
        lines.append("- None.")
    lines.extend(["", "## Open registry", ""])
    if open_findings:
        lines.extend(
            f"- [{item['severity']}] {item['title']} ({item['id']}) first_seen={item.get('first_seen')} last_seen={item.get('last_seen')} count={item.get('seen_count')}"
            for item in open_findings
        )
    else:
        lines.append("- No open findings.")
    automation_memory_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["automation_memory"] = {
        "status": "ready",
        "manifest_path": str(automation_memory_path(repo).relative_to(repo)),
        "open_findings": payload["open_findings"],
        "new_findings": payload["new_findings"],
    }
    save_json(state_path(repo), state)
    append_history(
        repo,
        "update_automation_memory "
        f"milestone={payload['milestone_id']} open={payload['open_findings']} new={payload['new_findings']} resolved={payload['resolved_since_last_run']}",
    )
    append_decision(
        repo,
        "Refresh automation finding memory",
        f"Milestone={payload['milestone_id'] or 'none'}",
        f"Open={payload['open_findings']} new={payload['new_findings']} resolved={payload['resolved_since_last_run']}.",
        "Use automation_memory.md to distinguish new recurring issues from already-known ones.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh recurring automation finding memory from the latest supervisory artifacts")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = update_automation_memory(repo)
    print(automation_memory_path(repo))
    print(f"open_findings={payload['open_findings']}")
    print(f"new_findings={payload['new_findings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
