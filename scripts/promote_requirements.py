#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import shutil
import re


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "milestone"


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote new_requirements.md to current_requirements.md")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--title", required=True, help="Short milestone title")
    parser.add_argument("--keep-new", action="store_true", help="Keep new_requirements.md after promotion")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    orch = repo / ".codex" / "orchestrator"
    new_file = orch / "new_requirements.md"
    current_file = orch / "current_requirements.md"
    todo_file = orch / "todo.md"
    history = orch / "planner_history.txt"
    completed = orch / "completed"
    completed.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    label = slugify(args.title)

    current_text = current_file.read_text(encoding="utf-8") if current_file.exists() else ""
    current_has_real_content = bool(current_text.strip()) and "## Milestone title\n\nTBD" not in current_text

    if current_has_real_content:
        archive_dir = completed / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{label}-previous-active"
        archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current_file, archive_dir / "current_requirements.md")
        if todo_file.exists():
            shutil.copy2(todo_file, archive_dir / "todo.md")

    new_text = new_file.read_text(encoding="utf-8") if new_file.exists() else ""
    if not new_text.strip():
        raise SystemExit(f"{new_file} is empty. Fill it in before promotion.")

    promoted = f"# Current milestone\n\n## Milestone title\n\n{args.title}\n\n" + new_text.strip() + "\n"
    current_file.write_text(promoted, encoding="utf-8")

    if not todo_file.exists() or not todo_file.read_text(encoding="utf-8").strip():
        todo_file.write_text("# Active milestone checklist\n\n- [ ] Map affected files and code paths\n- [ ] Implement the milestone\n- [ ] Add or update tests\n- [ ] Run validation\n- [ ] Update status, handoff, and decisions\n", encoding="utf-8")

    if not args.keep_new:
        new_file.write_text("# New requirements\n\n## User goal\n\n", encoding="utf-8")

    with history.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} promote_requirements title={args.title} label={label}\n")

    print(f"Promoted milestone: {args.title}")
    print(f"Updated: {current_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
