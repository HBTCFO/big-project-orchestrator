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
    convergence_brief_path,
    convergence_manifest_path,
    load_json,
    read_text,
    save_json,
    state_path,
    track_readiness_path,
    tracks_manifest_path,
)


def prepare_track_convergence(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    manifest = load_json(tracks_manifest_path(repo))
    readiness = load_json(track_readiness_path(repo))
    tracks = manifest.get("tracks", [])
    review = state.get("review", {})
    verification = state.get("verification", {})

    completed = [track for track in tracks if track.get("status") == "completed"]
    blocked = [track for track in tracks if track.get("status") == "blocked"]
    open_tracks = [track for track in tracks if track.get("status") in {"planned", "in_progress"}]

    ready = bool(tracks) and readiness.get("ready_for_merge", False) and verification.get("status") == "passed" and review.get("status") == "passed"
    blockers: list[str] = []
    if not readiness.get("ready_for_merge", False):
        blockers.append("Track readiness gate is not green.")
    if verification.get("status") != "passed":
        blockers.append("Milestone verification is not green.")
    if review.get("status") != "passed":
        blockers.append("Milestone review is not green.")
    if blocked:
        blockers.append(f"{len(blocked)} track(s) are blocked.")

    completed_summaries = []
    for track in completed:
        summary = track.get("summary") or track.get("note") or "No summary recorded."
        artifacts = ", ".join(track.get("artifacts", [])) if track.get("artifacts") else "No artifacts recorded."
        completed_summaries.append(
            {
                "track_id": track["id"],
                "title": track["title"],
                "summary": summary,
                "artifacts": artifacts,
            }
        )

    payload = {
        "milestone_id": manifest.get("milestone_id"),
        "ready_to_converge": ready,
        "completed_tracks": completed_summaries,
        "open_tracks": [track["id"] for track in open_tracks],
        "blocked_tracks": [track["id"] for track in blocked],
        "blockers": blockers,
        "merge_checklist": [
            "Review lane outputs and summaries",
            "Re-run verification after merging lane changes",
            "Re-run review/hardening after merge",
            "Update status, handoff, and decisions with final merged state",
        ],
    }
    save_json(convergence_manifest_path(repo), payload)

    lines = [
        "# Convergence",
        "",
        f"- Milestone: {manifest.get('milestone_id')}",
        f"- Ready to converge: {'yes' if ready else 'no'}",
        "",
        "## Completed track outcomes",
        "",
    ]
    if completed_summaries:
        for item in completed_summaries:
            lines.extend(
                [
                    f"### {item['title']}",
                    "",
                    f"- Track id: {item['track_id']}",
                    f"- Summary: {item['summary']}",
                    f"- Artifacts: {item['artifacts']}",
                    "",
                ]
            )
    else:
        lines.append("- No completed track outcomes recorded.")
        lines.append("")

    lines.extend(["## Open tracks", ""])
    if open_tracks:
        lines.extend(f"- {track['title']} ({track['status']})" for track in open_tracks)
    else:
        lines.append("- None.")
    lines.extend(["", "## Blockers", ""])
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- None.")
    lines.extend(["", "## Merge checklist", ""])
    lines.extend(f"- [ ] {item}" for item in payload["merge_checklist"])
    convergence_brief_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["convergence"] = {
        "status": "ready" if ready else "pending",
        "manifest_path": str(convergence_manifest_path(repo).relative_to(repo)),
        "ready_to_converge": ready,
    }
    state["next_action"] = "converge tracks" if ready else "finish track work"
    save_json(state_path(repo), state)
    append_history(repo, f"prepare_track_convergence milestone={manifest.get('milestone_id')} ready={ready}")
    append_decision(
        repo,
        "Prepare track convergence brief",
        f"Milestone={manifest.get('milestone_id')}",
        f"Convergence ready={ready} with {len(completed_summaries)} completed track summaries.",
        "Use convergence.md as the merge/hardening brief before milestone archive.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a merge/hardening brief from track outcomes")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = prepare_track_convergence(repo)
    print(convergence_manifest_path(repo))
    print(f"ready_to_converge={payload['ready_to_converge']}")
    return 0 if payload["ready_to_converge"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
