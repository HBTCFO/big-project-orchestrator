#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from orchestrator_common import append_history, load_json, save_json, state_path, tracks_manifest_path
from run_track_supervisor import run_track_supervisor


def update_track_status(
    repo: Path,
    track_id: str,
    status: str,
    note: str | None = None,
    summary: str | None = None,
    artifacts: list[str] | None = None,
) -> dict:
    manifest = load_json(tracks_manifest_path(repo))
    state = load_json(state_path(repo))
    tracks = manifest.get("tracks", [])
    updated = False
    for track in tracks:
        if track.get("id") == track_id:
            track["status"] = status
            if note:
                track["note"] = note
            if summary:
                track["summary"] = summary
            if artifacts:
                track["artifacts"] = artifacts
            updated = True
            break
    if not updated:
        raise SystemExit(f"Track not found: {track_id}")

    manifest["tracks"] = tracks
    save_json(tracks_manifest_path(repo), manifest)
    state["tracks"] = tracks
    save_json(state_path(repo), state)
    append_history(repo, f"update_track_status track={track_id} status={status}")
    run_track_supervisor(repo)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Update the status of a planned execution track")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--track", required=True, help="Track id")
    parser.add_argument("--status", required=True, choices=["planned", "in_progress", "blocked", "completed"], help="New track status")
    parser.add_argument("--note", help="Optional status note")
    parser.add_argument("--summary", help="Optional summary of the lane outcome")
    parser.add_argument("--artifact", action="append", default=[], help="Artifact path to associate with the lane")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    update_track_status(
        repo,
        args.track,
        args.status,
        note=args.note,
        summary=args.summary,
        artifacts=args.artifact or None,
    )
    print(tracks_manifest_path(repo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
