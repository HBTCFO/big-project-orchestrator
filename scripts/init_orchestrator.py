#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import shutil
import sys


TEMPLATE_NAMES = [
    "new_requirements.md",
    "current_requirements.md",
    "todo.md",
    "decisions.md",
    "status.md",
    "handoff.md",
    "review.md",
    "verification.commands.sh",
    "setup.commands.sh",
]


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def skill_dir() -> Path:
    return script_dir().parent


def ensure_file(src: Path, dest: Path, force: bool) -> None:
    if dest.exists() and not force:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize .codex/orchestrator durable project memory files.")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--force", action="store_true", help="Overwrite existing starter files")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    orch = repo / ".codex" / "orchestrator"
    templates = skill_dir() / "assets" / "templates"

    orch.mkdir(parents=True, exist_ok=True)
    (orch / "completed").mkdir(parents=True, exist_ok=True)

    for name in TEMPLATE_NAMES:
        ensure_file(templates / name, orch / name, args.force)

    history = orch / "planner_history.txt"
    if not history.exists() or args.force:
        history.write_text("", encoding="utf-8")

    state = orch / "state.json"
    if not state.exists() or args.force:
        state.write_text("{}\n", encoding="utf-8")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with history.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} init_orchestrator repo={repo}\n")

    print(f"Initialized orchestrator workspace at: {orch}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
