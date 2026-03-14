#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from action_contracts import build_action_contract
from build_project_state import initialize_state
from orchestrator_common import (
    append_decision,
    append_history,
    dispatch_manifest_path,
    execution_bridge_markdown_path,
    execution_bridge_path,
    load_json,
    save_json,
    state_path,
    tracks_manifest_path,
)

def _track_by_id(tracks: list[dict], track_id: str | None) -> dict | None:
    if not track_id:
        return None
    return next((track for track in tracks if track.get("id") == track_id), None)


def _dispatch_for_track(dispatch_manifest: dict, track_id: str | None) -> dict | None:
    if not track_id:
        return None
    return next((entry for entry in dispatch_manifest.get("dispatch", []) if entry.get("track_id") == track_id), None)


def generate_execution_bridge(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    supervisor = state.get("supervisor", {})
    next_action = supervisor.get("next_recommended_action") or {}
    tracks_manifest = load_json(tracks_manifest_path(repo))
    tracks = tracks_manifest.get("tracks", [])
    dispatch_manifest = load_json(dispatch_manifest_path(repo))
    escalation = state.get("escalation", {})
    action_kind = next_action.get("kind")
    track = _track_by_id(tracks, next_action.get("track_id"))
    dispatch = _dispatch_for_track(dispatch_manifest, next_action.get("track_id"))

    payload = {
        "milestone_id": state.get("current_milestone_id"),
        "action": {
            "kind": action_kind,
            "reason": next_action.get("reason", "No supervisor recommendation available."),
            "track_id": next_action.get("track_id"),
        },
        **build_action_contract(repo, state, next_action, track=track, dispatch=dispatch),
    }

    payload["active_playbook"] = escalation.get("active_playbook")
    save_json(execution_bridge_path(repo), payload)

    lines = [
        "# Execution bridge",
        "",
        f"- Milestone: {payload['milestone_id'] or 'none'}",
        f"- Ready: {'yes' if payload['ready'] else 'no'}",
        f"- Action: {action_kind or 'none'}",
        f"- Reason: {payload['action']['reason']}",
        f"- Track: {payload['action'].get('track_id') or 'n/a'}",
        f"- Active playbook: {(payload.get('active_playbook') or {}).get('kind', 'none')}",
        "",
        "## Commands",
        "",
    ]
    if payload["commands"]:
        lines.extend(f"- `{item}`" for item in payload["commands"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Inputs", ""])
    lines.extend(f"- {item}" for item in payload["inputs"]) if payload["inputs"] else lines.append("- None.")
    lines.extend(["", "## Expected outputs", ""])
    lines.extend(f"- {item}" for item in payload["expected_outputs"]) if payload["expected_outputs"] else lines.append("- None.")
    lines.extend(["", "## Human handoff", ""])
    lines.extend(f"- {item}" for item in payload["human_handoff"]) if payload["human_handoff"] else lines.append("- None.")
    execution_bridge_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["execution_bridge"] = {
        "status": "ready" if payload["ready"] else "pending",
        "manifest_path": str(execution_bridge_path(repo).relative_to(repo)),
        "action_kind": action_kind,
        "ready": payload["ready"],
    }
    save_json(state_path(repo), state)
    append_history(repo, f"generate_execution_bridge milestone={payload['milestone_id']} action={action_kind or 'none'} ready={payload['ready']}")
    append_decision(
        repo,
        "Generate supervisor-to-execution bridge",
        f"Milestone={payload['milestone_id'] or 'none'}",
        f"Mapped supervisor action {action_kind or 'none'} to {len(payload['commands'])} executable command(s).",
        "Use execution_bridge.md as the concrete handoff between supervision and execution.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a concrete execution handoff from the current supervisor recommendation")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = generate_execution_bridge(repo)
    print(execution_bridge_path(repo))
    print(f"action={(payload['action'].get('kind') or 'none')}")
    print(f"ready={payload['ready']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
