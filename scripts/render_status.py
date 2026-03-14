#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import json
import textwrap


def run(cmd: list[str], cwd: Path) -> tuple[int, str]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
        out = proc.stdout.strip() or proc.stderr.strip()
        return proc.returncode, out
    except FileNotFoundError:
        return 127, f"missing command: {cmd[0]}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a concise STATUS.md from repo state.")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    orch = repo / ".codex" / "orchestrator"
    status_path = orch / "status.md"

    rc_branch, branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo)
    rc_diff, diff_summary = run(["git", "status", "--short"], repo)
    rc_commit, last_commit = run(["git", "log", "-1", "--pretty=%h %s"], repo)

    todo_path = orch / "todo.md"
    todo_lines = []
    if todo_path.exists():
        for line in todo_path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("- [ ]") or line.lstrip().startswith("- [x]"):
                todo_lines.append(line.strip())
    next_items = "\n".join(f"- {line[5:].strip()}" for line in todo_lines[:5]) or "- Review todo.md"

    verification_file = orch / "verification.commands.sh"
    verification_hint = "custom verification.commands.sh present" if verification_file.exists() else "bundled verifier"
    branch_text = branch if rc_branch == 0 else "unknown"
    commit_text = last_commit if rc_commit == 0 else "unknown"
    diff_text = diff_summary if rc_diff == 0 and diff_summary else "(clean working tree)"

    content = textwrap.dedent(f"""    # Status

    _Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_

    ## Current state

    - Branch: {branch_text}
    - Last commit: {commit_text}
    - Verification mode: {verification_hint}

    ## Working tree summary

    ```text
    {diff_text}
    ```

    ## Next visible checklist items

    {next_items}

    ## Notes

    - Refresh this file after meaningful implementation or verification runs.
    - Keep `handoff.md` aligned with the exact next best action.
    """)

    status_path.write_text(content, encoding="utf-8")
    print(status_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
