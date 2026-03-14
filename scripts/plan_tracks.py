#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from generate_track_dispatch import generate_track_dispatch
from generate_track_prompts import generate_track_prompts
from run_track_supervisor import run_track_supervisor
from orchestrator_common import (
    append_decision,
    append_history,
    load_json,
    sanitize_track_slug,
    save_json,
    state_path,
    track_board_path,
    tracks_dir,
    tracks_manifest_path,
)


def _active_milestone(state: dict) -> dict | None:
    current = state.get("current_milestone_id")
    for milestone in state.get("milestones", []):
        if milestone.get("id") == current:
            return milestone
    return None


def _default_track_specs(milestone: dict) -> list[dict]:
    deliverables = milestone.get("deliverables", [])
    focus = deliverables[0] if deliverables else milestone["title"]
    return [
        {
            "title": "Implementation lane",
            "role": "worker",
            "objective": f"Own the primary implementation slice for {focus}.",
            "done_when": "Core code changes for the active slice are in place and locally validated.",
            "verification_focus": "Primary behavior and smoke validation",
        },
        {
            "title": "Tests and coverage lane",
            "role": "worker",
            "objective": f"Strengthen tests and coverage around {focus}.",
            "done_when": "Tests covering the active slice are added or updated.",
            "verification_focus": "Unit/integration coverage",
        },
        {
            "title": "Review and hardening lane",
            "role": "reviewer",
            "objective": f"Review correctness, regressions, and edge cases for {focus}.",
            "done_when": "Blocking review findings are either fixed or explicitly documented.",
            "verification_focus": "Regression, security, and risk review",
        },
        {
            "title": "Docs and handoff lane",
            "role": "worker",
            "objective": "Keep status, handoff, and milestone-facing docs current.",
            "done_when": "The next thread can resume from durable artifacts without rereading chat.",
            "verification_focus": "Artifact freshness and clarity",
        },
    ]


def plan_tracks(
    repo: Path,
    max_tracks: int = 4,
    force: bool = False,
    generate_dispatch: bool = True,
    generate_prompts: bool = True,
) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    milestone = _active_milestone(state)
    if not milestone:
        raise SystemExit("No active milestone is available for track planning.")

    existing = state.get("tracks", [])
    if existing and not force and existing[0].get("milestone_id") == milestone["id"]:
        if generate_dispatch:
            generate_track_dispatch(repo, force=force)
        if generate_prompts:
            generate_track_prompts(repo, force=force)
        run_track_supervisor(repo)
        return {"tracks": existing, "milestone_id": milestone["id"], "reused": True}

    track_specs = _default_track_specs(milestone)[:max_tracks]
    manifest: list[dict] = []
    tracks_root = tracks_dir(repo)
    tracks_root.mkdir(parents=True, exist_ok=True)

    for index, spec in enumerate(track_specs, start=1):
        slug = sanitize_track_slug(spec["title"])
        track_id = f"track-{index:02d}-{slug}"
        brief_path = tracks_root / f"{track_id}.md"
        branch_suffix = sanitize_track_slug(f"{milestone['id']}-{slug}")
        manifest.append(
            {
                "id": track_id,
                "milestone_id": milestone["id"],
                "title": spec["title"],
                "role": spec["role"],
                "status": "planned",
                "objective": spec["objective"],
                "done_when": spec["done_when"],
                "verification_focus": spec["verification_focus"],
                "brief_path": str(brief_path.relative_to(repo)),
                "suggested_branch_suffix": branch_suffix,
                "suggested_thread_name": f"{milestone['title']} / {spec['title']}",
            }
        )
        brief = (
            f"# {spec['title']}\n\n"
            f"## Milestone\n\n- {milestone['title']}\n\n"
            f"## Role\n\n- {spec['role']}\n\n"
            f"## Objective\n\n{spec['objective']}\n\n"
            "## Inputs\n\n"
            "- .codex/orchestrator/current_requirements.md\n"
            "- .codex/orchestrator/todo.md\n"
            "- .codex/orchestrator/status.md\n"
            "- .codex/orchestrator/review.md\n\n"
            f"## Done when\n\n- {spec['done_when']}\n\n"
            f"## Verification focus\n\n- {spec['verification_focus']}\n\n"
            "## Suggested execution mode\n\n"
            "- Codex app Worktree thread or focused CLI role\n"
        )
        brief_path.write_text(brief, encoding="utf-8")

    board_lines = [
        "# Track board",
        "",
        f"## Active milestone",
        "",
        f"- {milestone['title']}",
        "",
        "## Tracks",
        "",
    ]
    for track in manifest:
        board_lines.extend(
            [
                f"### {track['title']}",
                "",
                f"- Role: {track['role']}",
                f"- Status: {track['status']}",
                f"- Objective: {track['objective']}",
                f"- Brief: {track['brief_path']}",
                f"- Suggested branch suffix: {track['suggested_branch_suffix']}",
                "",
            ]
        )
    track_board_path(repo).write_text("\n".join(board_lines), encoding="utf-8")
    save_json(tracks_manifest_path(repo), {"milestone_id": milestone["id"], "tracks": manifest})

    state["tracks"] = manifest
    state["next_action"] = "dispatch or continue tracks"
    save_json(state_path(repo), state)
    append_history(repo, f"plan_tracks milestone={milestone['id']} count={len(manifest)}")
    append_decision(
        repo,
        "Plan parallel execution tracks",
        f"Milestone={milestone['id']}",
        f"Created {len(manifest)} tracks for worktree or CLI fan-out.",
        "Collapse to fewer tracks if the milestone is too small to justify parallel lanes.",
    )
    if generate_dispatch:
        generate_track_dispatch(repo, force=force)
    if generate_prompts:
        generate_track_prompts(repo, force=force)
    run_track_supervisor(repo)
    return {"tracks": manifest, "milestone_id": milestone["id"], "reused": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan parallel worktree/track execution for the active milestone")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--max-tracks", type=int, default=4, help="Maximum track count")
    parser.add_argument("--force", action="store_true", help="Rebuild the active track plan")
    parser.add_argument("--no-dispatch", action="store_true", help="Skip dispatch/bootstrap artifact generation")
    parser.add_argument("--no-prompts", action="store_true", help="Skip role-aware prompt pack generation")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = plan_tracks(
        repo,
        max_tracks=args.max_tracks,
        force=args.force,
        generate_dispatch=not args.no_dispatch,
        generate_prompts=not args.no_prompts,
    )
    print(tracks_manifest_path(repo))
    print(f"track_count={len(result['tracks'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
