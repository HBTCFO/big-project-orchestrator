#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


SAFE_AUTO_ACTIONS = {
    "plan_tracks",
    "start_lane",
    "prepare_convergence",
    "run_merge_cycle",
    "archive_milestone",
}


def script_path(name: str) -> str:
    return str((Path(__file__).resolve().parent / name).resolve())


def build_action_contract(
    repo: Path,
    state: dict,
    action: dict,
    track: dict | None = None,
    dispatch: dict | None = None,
) -> dict:
    action_kind = action.get("kind")
    payload = {
        "ready": bool(action_kind),
        "commands": [],
        "inputs": [],
        "expected_outputs": [],
        "human_handoff": [],
        "automation_safe": action_kind in SAFE_AUTO_ACTIONS,
    }

    if action_kind == "plan_tracks":
        payload["commands"] = [f'python3 "{script_path("plan_tracks.py")}" --repo "{repo}"']
        payload["inputs"] = [
            ".codex/orchestrator/current_requirements.md",
            ".codex/orchestrator/todo.md",
            ".codex/orchestrator/status.md",
        ]
        payload["expected_outputs"] = [
            ".codex/orchestrator/tracks.json",
            ".codex/orchestrator/track_board.md",
            ".codex/orchestrator/dispatch.json",
        ]
        payload["human_handoff"] = ["Create track plans before attempting lane execution."]
    elif action_kind == "start_lane":
        if dispatch and dispatch.get("shell_path"):
            payload["commands"] = [f'bash "{repo / dispatch["shell_path"]}"']
        elif track:
            payload["commands"] = [
                f'python3 "{script_path("update_track_status.py")}" --repo "{repo}" --track "{track["id"]}" --status in_progress --note "picked up from execution bridge"'
            ]
        payload["inputs"] = [track.get("brief_path", "n/a")] if track else ["track brief missing"]
        payload["expected_outputs"] = [
            ".codex/orchestrator/tracks.json",
            ".codex/orchestrator/supervisor_report.json",
        ]
        if track:
            payload["human_handoff"] = [f'Read {track.get("brief_path")} before running the lane.']
    elif action_kind == "support_in_progress_lane":
        payload["commands"] = [f'python3 "{script_path("run_track_supervisor.py")}" --repo "{repo}"']
        payload["inputs"] = [track.get("brief_path", "n/a")] if track else ["supervisor_report.md"]
        payload["expected_outputs"] = [
            ".codex/orchestrator/supervisor_report.json",
            ".codex/orchestrator/status.md",
        ]
        if track:
            payload["human_handoff"] = [f'Inspect the active lane brief at {track.get("brief_path")} and decide whether it needs unblock help or status refresh.']
    elif action_kind == "resolve_blocker":
        payload["commands"] = [f'python3 "{script_path("generate_escalation_playbook.py")}" --repo "{repo}"']
        payload["inputs"] = [
            ".codex/orchestrator/escalation_report.md",
            track.get("brief_path", "n/a") if track else "track brief missing",
        ]
        payload["expected_outputs"] = [
            ".codex/orchestrator/escalation_report.json",
            ".codex/orchestrator/tracks.json",
        ]
        if track:
            payload["human_handoff"] = [f'Resolve the blocker on {track["id"]} and then move it back to in_progress or document why it remains blocked.']
    elif action_kind == "prepare_convergence":
        payload["commands"] = [
            f'python3 "{script_path("evaluate_track_readiness.py")}" --repo "{repo}"',
            f'python3 "{script_path("prepare_track_convergence.py")}" --repo "{repo}"',
        ]
        payload["inputs"] = [
            ".codex/orchestrator/tracks.json",
            ".codex/orchestrator/track_readiness.json",
        ]
        payload["expected_outputs"] = [
            ".codex/orchestrator/track_readiness.json",
            ".codex/orchestrator/convergence.json",
            ".codex/orchestrator/convergence.md",
        ]
        payload["human_handoff"] = ["Refresh lane completion state before preparing the milestone convergence brief."]
    elif action_kind == "run_merge_cycle":
        payload["commands"] = [f'python3 "{script_path("orchestrate_track_merge.py")}" --repo "{repo}"']
        payload["inputs"] = [
            ".codex/orchestrator/convergence.md",
            ".codex/orchestrator/last_verification.json",
            ".codex/orchestrator/last_review.json",
        ]
        payload["expected_outputs"] = [
            ".codex/orchestrator/merge_report.json",
            ".codex/orchestrator/merge_report.md",
        ]
        payload["human_handoff"] = ["Do not archive until merge_report says ready_for_archive=true."]
    elif action_kind == "resolve_post_merge_findings":
        payload["commands"] = [
            f'python3 "{script_path("generate_escalation_playbook.py")}" --repo "{repo}"',
            f'python3 "{script_path("orchestrate_track_merge.py")}" --repo "{repo}" --no-repair',
        ]
        payload["inputs"] = [
            ".codex/orchestrator/merge_report.md",
            ".codex/orchestrator/escalation_report.md",
        ]
        payload["expected_outputs"] = [
            ".codex/orchestrator/merge_report.json",
            ".codex/orchestrator/escalation_report.json",
        ]
        payload["human_handoff"] = ["Repair the merged state first, then re-run the merge orchestration gate."]
    elif action_kind == "archive_milestone":
        milestone_title = state.get("current_milestone_id") or "milestone"
        payload["commands"] = [f'python3 "{script_path("archive_cycle.py")}" --repo "{repo}" --label "{milestone_title}"']
        payload["inputs"] = [
            ".codex/orchestrator/merge_report.md",
            ".codex/orchestrator/status.md",
            ".codex/orchestrator/handoff.md",
        ]
        payload["expected_outputs"] = [
            ".codex/orchestrator/completed/",
            ".codex/orchestrator/planner_history.txt",
        ]
        payload["human_handoff"] = ["Archive only after checking that the merge gate is green and artifacts are current."]
    else:
        payload["ready"] = False
        payload["human_handoff"] = ["Refresh supervisor and escalation artifacts before attempting execution."]

    return payload
