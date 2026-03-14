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
    dispatch_dir,
    dispatch_manifest_path,
    load_json,
    save_json,
    state_path,
    tracks_manifest_path,
)


def _quote(path: Path | str) -> str:
    return str(path).replace('"', '\\"')


def generate_track_dispatch(repo: Path, force: bool = False) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    manifest = load_json(tracks_manifest_path(repo))
    tracks = manifest.get("tracks", [])
    if not tracks:
        raise SystemExit("No planned tracks available. Run plan_tracks.py first.")

    dispatch_root = dispatch_dir(repo)
    dispatch_root.mkdir(parents=True, exist_ok=True)

    skill_scripts = Path(__file__).resolve().parent
    setup_script = skill_scripts / "setup_workspace.sh"
    update_script = skill_scripts / "update_track_status.py"

    repo_git_capable = (repo / ".git").exists()
    worktree_root = repo / ".codex" / "worktrees"
    dispatch_entries: list[dict] = []

    for track in tracks:
        track_id = track["id"]
        branch_name = f"codex/{track['suggested_branch_suffix']}"
        worktree_path = worktree_root / track["suggested_branch_suffix"]
        shell_path = dispatch_root / f"{track_id}.sh"
        brief_path = dispatch_root / f"{track_id}.md"

        shell_text = f"""#!/usr/bin/env bash
set -euo pipefail

REPO="{_quote(repo)}"
TRACK_ID="{track_id}"
BRANCH="{branch_name}"
WORKTREE="{_quote(worktree_path)}"

mkdir -p "$(dirname "$WORKTREE")"

if git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if [ -d "$WORKTREE" ] && [ "$(ls -A "$WORKTREE" 2>/dev/null || true)" != "" ]; then
    echo "worktree already exists: $WORKTREE"
  else
    if git -C "$REPO" show-ref --verify --quiet "refs/heads/$BRANCH"; then
      git -C "$REPO" worktree add "$WORKTREE" "$BRANCH"
    else
      git -C "$REPO" worktree add "$WORKTREE" -b "$BRANCH"
    fi
  fi
  mkdir -p "$WORKTREE/.codex"
  if [ -d "$REPO/.codex/orchestrator" ]; then
    rm -rf "$WORKTREE/.codex/orchestrator"
    ditto "$REPO/.codex/orchestrator" "$WORKTREE/.codex/orchestrator"
  fi
  if [ -d "$REPO/.codex/agents" ]; then
    rm -rf "$WORKTREE/.codex/agents"
    ditto "$REPO/.codex/agents" "$WORKTREE/.codex/agents"
  fi
  if [ -f "$REPO/.codex/config.toml" ]; then
    cp "$REPO/.codex/config.toml" "$WORKTREE/.codex/config.toml"
  fi
  bash "{_quote(setup_script)}" "$WORKTREE" || true
  python3 "{_quote(update_script)}" --repo "$REPO" --track "$TRACK_ID" --status in_progress --note "dispatched to $WORKTREE"
  printf 'track ready: %s\\nbranch: %s\\nworktree: %s\\n' "$TRACK_ID" "$BRANCH" "$WORKTREE"
else
  echo "Repository is not in a git worktree-capable checkout."
  echo "Open the track brief instead: {_quote(brief_path)}"
  exit 2
fi
"""
        shell_path.write_text(shell_text, encoding="utf-8")
        shell_path.chmod(0o755)

        brief_lines = [
            f"# Dispatch for {track['title']}",
            "",
            "## Track",
            "",
            f"- Id: {track_id}",
            f"- Role: {track['role']}",
            f"- Objective: {track['objective']}",
            "",
            "## Suggested worktree",
            "",
            f"- Branch: `{branch_name}`",
            f"- Path: `{worktree_path.relative_to(repo)}`",
            "",
            "## Commands",
            "",
            "```bash",
            f"bash {shell_path.relative_to(repo)}",
            "```",
            "",
            "## Manual fallback",
            "",
            "```bash",
            f"python3 {update_script} --repo \"{repo}\" --track {track_id} --status in_progress --note 'picked up manually'",
            "```",
            "",
            "## Notes",
            "",
            f"- Git worktree auto-dispatch supported: {'yes' if repo_git_capable else 'no'}",
            "- Dispatch script syncs `.codex/orchestrator`, `.codex/agents`, and `.codex/config.toml` into the worktree before setup.",
            f"- Brief source: `{track['brief_path']}`",
        ]
        brief_path.write_text("\n".join(brief_lines) + "\n", encoding="utf-8")

        dispatch_entries.append(
            {
                "track_id": track_id,
                "branch_name": branch_name,
                "worktree_path": str(worktree_path.relative_to(repo)),
                "shell_path": str(shell_path.relative_to(repo)),
                "brief_path": str(brief_path.relative_to(repo)),
                "git_worktree_supported": repo_git_capable,
            }
        )
        track["dispatch"] = {
            "branch_name": branch_name,
            "worktree_path": str(worktree_path.relative_to(repo)),
            "shell_path": str(shell_path.relative_to(repo)),
            "brief_path": str(brief_path.relative_to(repo)),
        }

    manifest["tracks"] = tracks
    save_json(tracks_manifest_path(repo), manifest)

    dispatch_manifest = {
        "milestone_id": manifest.get("milestone_id"),
        "git_worktree_supported": repo_git_capable,
        "dispatch": dispatch_entries,
    }
    save_json(dispatch_manifest_path(repo), dispatch_manifest)

    state["tracks"] = tracks
    state["dispatch"] = {
        "status": "ready",
        "manifest_path": str(dispatch_manifest_path(repo).relative_to(repo)),
        "count": len(dispatch_entries),
    }
    save_json(state_path(repo), state)
    append_history(repo, f"generate_track_dispatch milestone={manifest.get('milestone_id')} count={len(dispatch_entries)}")
    append_decision(
        repo,
        "Generate worktree dispatch artifacts",
        f"Milestone={manifest.get('milestone_id')}",
        f"Prepared {len(dispatch_entries)} dispatch scripts/briefs for track fan-out.",
        "Use the markdown briefs if the repo is not in a git worktree-capable checkout.",
    )
    return dispatch_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate dispatch/bootstrap artifacts for planned tracks")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--force", action="store_true", help="Regenerate dispatch artifacts")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = generate_track_dispatch(repo, force=args.force)
    print(dispatch_manifest_path(repo))
    print(f"dispatch_count={len(result['dispatch'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
