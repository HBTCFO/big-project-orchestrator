#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from orchestrator_common import (
    append_decision,
    append_history,
    escalation_report_markdown_path,
    escalation_report_path,
    load_json,
    save_json,
    state_path,
    tracks_manifest_path,
)


def generate_escalation_playbook(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    tracks_manifest = load_json(tracks_manifest_path(repo))
    tracks = tracks_manifest.get("tracks", [])
    blocked_tracks = [track for track in tracks if track.get("status") == "blocked"]
    merge = state.get("merge_orchestration", {})
    convergence = state.get("convergence", {})

    active_playbook = None
    recovery_steps: list[str] = []
    severity = "none"

    if blocked_tracks:
        track = blocked_tracks[0]
        active_playbook = {
            "kind": "lane_blocker_recovery",
            "track_id": track["id"],
            "title": track["title"],
            "reason": track.get("note") or "Blocked lane requires intervention.",
        }
        severity = "high"
        recovery_steps = [
            f"Read {track.get('brief_path', 'the track brief')} and inspect the blocker note.",
            "Decide whether the blocker can be fixed inside the lane or must be escalated to the milestone owner.",
            "If the lane can continue, update the track status back to in_progress with a concrete recovery note.",
            "If the lane cannot continue safely, document the blocker in status.md, handoff.md, and decisions.md.",
        ]
    elif merge.get("status") in {"blocked", "needs_repair"}:
        active_playbook = {
            "kind": "post_merge_recovery",
            "track_id": None,
            "title": "Post-merge recovery",
            "reason": "Merged milestone state failed verify/review or is not archive-ready.",
        }
        severity = "high"
        recovery_steps = [
            "Read merge_report.md and convergence.md first.",
            "Inspect last_verification.json and last_review.json to identify the failing gate.",
            "Run the repair loop or fix the failing merged state directly.",
            "Re-run orchestrate_track_merge.py after the fix and only archive when merge_report.json is green.",
        ]
    elif tracks and not convergence.get("ready_to_converge", False):
        active_playbook = {
            "kind": "convergence_recovery",
            "track_id": None,
            "title": "Convergence recovery",
            "reason": "Tracks are not yet ready to merge back into the milestone.",
        }
        severity = "medium"
        recovery_steps = [
            "Refresh track statuses and summaries.",
            "Re-run evaluate_track_readiness.py.",
            "Resolve any remaining planned or in-progress lanes before convergence.",
            "Rebuild the convergence brief with prepare_track_convergence.py.",
        ]
    else:
        active_playbook = {
            "kind": "none",
            "track_id": None,
            "title": "No escalation needed",
            "reason": "No blocked lanes or failing merge cycle detected.",
        }
        severity = "none"
        recovery_steps = [
            "Continue with the supervisor-recommended next action.",
        ]

    payload = {
        "milestone_id": tracks_manifest.get("milestone_id"),
        "active_playbook": active_playbook,
        "severity": severity,
        "recovery_steps": recovery_steps,
    }
    save_json(escalation_report_path(repo), payload)

    lines = [
        "# Escalation report",
        "",
        f"- Milestone: {tracks_manifest.get('milestone_id')}",
        f"- Severity: {severity}",
        f"- Playbook: {active_playbook['kind']}",
        f"- Reason: {active_playbook['reason']}",
        "",
        "## Recovery steps",
        "",
    ]
    lines.extend(f"- [ ] {step}" for step in recovery_steps)
    escalation_report_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["escalation"] = {
        "status": "active" if active_playbook["kind"] != "none" else "clear",
        "manifest_path": str(escalation_report_path(repo).relative_to(repo)),
        "active_playbook": active_playbook,
    }
    save_json(state_path(repo), state)
    append_history(repo, f"generate_escalation_playbook milestone={tracks_manifest.get('milestone_id')} playbook={active_playbook['kind']}")
    append_decision(
        repo,
        "Generate escalation and recovery playbook",
        f"Milestone={tracks_manifest.get('milestone_id')}",
        f"Active playbook is {active_playbook['kind']}.",
        "Refresh the playbook whenever blocked lane or merge state changes.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate escalation and recovery guidance for blocked lanes or failing merge cycles")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = generate_escalation_playbook(repo)
    print(escalation_report_path(repo))
    print(f"playbook={payload['active_playbook']['kind']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
