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
    load_json,
    prompts_dir,
    prompts_manifest_path,
    save_json,
    state_path,
    tracks_manifest_path,
)


def generate_track_prompts(repo: Path, force: bool = False) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    manifest = load_json(tracks_manifest_path(repo))
    tracks = manifest.get("tracks", [])
    if not tracks:
        raise SystemExit("No planned tracks available. Run plan_tracks.py first.")

    prompts_root = prompts_dir(repo)
    prompts_root.mkdir(parents=True, exist_ok=True)

    prompt_entries: list[dict] = []
    for track in tracks:
        prompt_path = prompts_root / f"{track['id']}.md"
        if prompt_path.exists() and not force:
            prompt_entries.append(
                {
                    "track_id": track["id"],
                    "prompt_path": str(prompt_path.relative_to(repo)),
                    "role": track["role"],
                }
            )
            continue

        prompt_text = (
            f"$big-project-orchestrator\n\n"
            f"Continue the active milestone through the track `{track['title']}`.\n\n"
            "Track contract:\n"
            f"- Role: {track['role']}\n"
            f"- Objective: {track['objective']}\n"
            f"- Done when: {track['done_when']}\n"
            f"- Verification focus: {track['verification_focus']}\n\n"
            "Read these files first:\n"
            f"- {track['brief_path']}\n"
            "- .codex/orchestrator/current_requirements.md\n"
            "- .codex/orchestrator/todo.md\n"
            "- .codex/orchestrator/status.md\n"
            "- .codex/orchestrator/review.md\n\n"
            "Execution rules:\n"
            "- Stay inside the assigned track.\n"
            "- Keep changes reviewable and milestone-scoped.\n"
            "- Update durable artifacts when you change the track status.\n"
            "- If you start this lane, mark it in progress with update_track_status.py.\n"
            "- If you complete or block this lane, update the track status before stopping.\n"
        )
        prompt_path.write_text(prompt_text, encoding="utf-8")
        prompt_entries.append(
            {
                "track_id": track["id"],
                "prompt_path": str(prompt_path.relative_to(repo)),
                "role": track["role"],
            }
        )

    payload = {"milestone_id": manifest.get("milestone_id"), "prompts": prompt_entries}
    save_json(prompts_manifest_path(repo), payload)
    state["prompts"] = {
        "status": "ready",
        "manifest_path": str(prompts_manifest_path(repo).relative_to(repo)),
        "count": len(prompt_entries),
    }
    save_json(state_path(repo), state)
    append_history(repo, f"generate_track_prompts milestone={manifest.get('milestone_id')} count={len(prompt_entries)}")
    append_decision(
        repo,
        "Generate track execution prompts",
        f"Milestone={manifest.get('milestone_id')}",
        f"Prepared {len(prompt_entries)} role-aware prompt packs for track fan-out.",
        "Regenerate prompts if the milestone scope or track objectives change materially.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate role-aware prompt packs for planned tracks")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--force", action="store_true", help="Regenerate prompt files even if they exist")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = generate_track_prompts(repo, force=args.force)
    print(prompts_manifest_path(repo))
    print(f"prompt_count={len(result['prompts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
