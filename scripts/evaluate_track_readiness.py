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
    load_json,
    save_json,
    state_path,
    track_readiness_markdown_path,
    track_readiness_path,
    tracks_manifest_path,
)


def evaluate_track_readiness(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    manifest = load_json(tracks_manifest_path(repo))
    tracks = manifest.get("tracks", [])

    counts = {"planned": 0, "in_progress": 0, "blocked": 0, "completed": 0}
    for track in tracks:
        counts[track.get("status", "planned")] = counts.get(track.get("status", "planned"), 0) + 1

    ready = bool(tracks) and counts.get("blocked", 0) == 0 and counts.get("planned", 0) == 0 and counts.get("in_progress", 0) == 0
    payload = {
        "milestone_id": manifest.get("milestone_id"),
        "track_count": len(tracks),
        "counts": counts,
        "ready_for_merge": ready,
    }
    save_json(track_readiness_path(repo), payload)

    lines = [
        "# Track readiness",
        "",
        f"- Milestone: {manifest.get('milestone_id')}",
        f"- Track count: {len(tracks)}",
        f"- Ready for merge: {'yes' if ready else 'no'}",
        "",
        "## Status counts",
        "",
        f"- Planned: {counts.get('planned', 0)}",
        f"- In progress: {counts.get('in_progress', 0)}",
        f"- Blocked: {counts.get('blocked', 0)}",
        f"- Completed: {counts.get('completed', 0)}",
    ]
    track_readiness_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["track_readiness"] = {
        "status": "ready" if ready else "pending",
        "manifest_path": str(track_readiness_path(repo).relative_to(repo)),
        "ready_for_merge": ready,
    }
    save_json(state_path(repo), state)
    append_history(repo, f"evaluate_track_readiness milestone={manifest.get('milestone_id')} ready={ready}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate whether planned tracks are ready to converge")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = evaluate_track_readiness(repo)
    print(track_readiness_path(repo))
    print(f"ready_for_merge={payload['ready_for_merge']}")
    return 0 if payload["ready_for_merge"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
