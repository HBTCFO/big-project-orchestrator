#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from generate_execution_bridge import generate_execution_bridge
from generate_escalation_playbook import generate_escalation_playbook
from validate_orchestrator_state import validate_orchestrator_state
from orchestrator_common import (
    append_decision,
    append_history,
    load_json,
    save_json,
    state_path,
    supervisor_report_markdown_path,
    supervisor_report_path,
    tracks_manifest_path,
)


def _track_summary(track: dict) -> str:
    pieces = [track["title"], f"status={track.get('status', 'planned')}"]
    if track.get("note"):
        pieces.append(f"note={track['note']}")
    if track.get("summary"):
        pieces.append(f"summary={track['summary']}")
    return "; ".join(pieces)


def run_track_supervisor(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    manifest = load_json(tracks_manifest_path(repo))
    tracks = manifest.get("tracks", [])
    convergence = state.get("convergence", {})
    merge_orchestration = state.get("merge_orchestration", {})

    planned = [track for track in tracks if track.get("status") == "planned"]
    in_progress = [track for track in tracks if track.get("status") == "in_progress"]
    blocked = [track for track in tracks if track.get("status") == "blocked"]
    completed = [track for track in tracks if track.get("status") == "completed"]

    next_action: dict
    if blocked:
        track = blocked[0]
        next_action = {
            "kind": "resolve_blocker",
            "track_id": track["id"],
            "reason": track.get("note") or "Blocked lane must be resolved before continuing.",
        }
    elif in_progress:
        track = in_progress[0]
        next_action = {
            "kind": "support_in_progress_lane",
            "track_id": track["id"],
            "reason": "At least one lane is already active; supervise and unblock it before starting another.",
        }
    elif planned:
        track = planned[0]
        next_action = {
            "kind": "start_lane",
            "track_id": track["id"],
            "reason": "No lane is active; start the highest-priority planned lane.",
        }
    elif merge_orchestration.get("ready_for_archive"):
        next_action = {
            "kind": "archive_milestone",
            "track_id": None,
            "reason": "Post-merge verification and review are green; archive the milestone.",
        }
    elif merge_orchestration.get("status") == "needs_repair":
        next_action = {
            "kind": "resolve_post_merge_findings",
            "track_id": None,
            "reason": "The merge cycle reported failing post-merge gates that must be repaired before archive.",
        }
    elif tracks and convergence.get("ready_to_converge"):
        next_action = {
            "kind": "run_merge_cycle",
            "track_id": None,
            "reason": "All lanes are complete and convergence is ready.",
        }
    elif tracks:
        next_action = {
            "kind": "prepare_convergence",
            "track_id": None,
            "reason": "All lanes are complete; refresh readiness and convergence artifacts.",
        }
    else:
        next_action = {
            "kind": "plan_tracks",
            "track_id": None,
            "reason": "No track fleet exists for the active milestone.",
        }

    state["supervisor"] = {
        "status": "ready",
        "manifest_path": str(supervisor_report_path(repo).relative_to(repo)),
        "next_recommended_action": next_action,
    }
    state["next_action"] = next_action["reason"]
    save_json(state_path(repo), state)
    generate_escalation_playbook(repo)
    generate_execution_bridge(repo)
    validate_orchestrator_state(repo)
    state = load_json(state_path(repo))
    escalation = state.get("escalation", {})
    execution_bridge = state.get("execution_bridge", {})
    validation = state.get("validation", {})

    payload = {
        "milestone_id": manifest.get("milestone_id"),
        "track_counts": {
            "planned": len(planned),
            "in_progress": len(in_progress),
            "blocked": len(blocked),
            "completed": len(completed),
        },
        "next_recommended_action": next_action,
        "merge_status": merge_orchestration.get("status", "not_run"),
        "convergence_status": convergence.get("status", "not_run"),
        "escalation_status": escalation.get("status", "not_run"),
        "active_playbook": escalation.get("active_playbook"),
        "execution_bridge_status": execution_bridge.get("status", "not_run"),
        "validation_status": validation.get("status", "not_run"),
    }
    save_json(supervisor_report_path(repo), payload)

    lines = [
        "# Supervisor report",
        "",
        f"- Milestone: {manifest.get('milestone_id')}",
        f"- Planned lanes: {len(planned)}",
        f"- In-progress lanes: {len(in_progress)}",
        f"- Blocked lanes: {len(blocked)}",
        f"- Completed lanes: {len(completed)}",
        "",
        "## Next recommended action",
        "",
        f"- Kind: {next_action['kind']}",
        f"- Track: {next_action['track_id'] or 'n/a'}",
        f"- Reason: {next_action['reason']}",
        "",
        "## Lane snapshots",
        "",
    ]
    if tracks:
        lines.extend(f"- { _track_summary(track) }" for track in tracks)
    else:
        lines.append("- No tracks planned.")
    lines.extend(
        [
            "",
            "## Fleet gates",
            "",
            f"- Convergence status: {convergence.get('status', 'not_run')}",
            f"- Merge orchestration status: {merge_orchestration.get('status', 'not_run')}",
            f"- Escalation status: {escalation.get('status', 'not_run')}",
            f"- Active playbook: {(escalation.get('active_playbook') or {}).get('kind', 'none')}",
            f"- Execution bridge: {execution_bridge.get('status', 'not_run')}",
            f"- Validation: {validation.get('status', 'not_run')}",
        ]
    )
    supervisor_report_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["supervisor"]["manifest_path"] = str(supervisor_report_path(repo).relative_to(repo))
    save_json(state_path(repo), state)
    append_history(repo, f"run_track_supervisor milestone={manifest.get('milestone_id')} action={next_action['kind']}")
    append_decision(
        repo,
        "Run track fleet supervisor",
        f"Milestone={manifest.get('milestone_id')}",
        f"Recommended next action is {next_action['kind']}.",
        "Regenerate the supervisor report after any track status change.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the active track fleet and recommend the next best action")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = run_track_supervisor(repo)
    print(supervisor_report_path(repo))
    print(f"next_action={payload['next_recommended_action']['kind']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
