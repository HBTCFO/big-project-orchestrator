#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime
import shutil
import re


FILES_TO_ARCHIVE = [
    "current_requirements.md",
    "todo.md",
    "status.md",
    "handoff.md",
    "review.md",
    "decisions.md",
    "state.json",
    "last_verification.json",
    "last_review.json",
    "tracks.json",
    "track_board.md",
    "dispatch.json",
    "prompts.json",
    "track_readiness.json",
    "track_readiness.md",
    "convergence.json",
    "convergence.md",
    "merge_report.json",
    "merge_report.md",
    "supervisor_report.json",
    "supervisor_report.md",
    "escalation_report.json",
    "escalation_report.md",
    "automation_report.json",
    "automation_report.md",
    "automation_pack.json",
    "automation_pack.md",
    "automation_memory.json",
    "automation_memory.md",
    "execution_bridge.json",
    "execution_bridge.md",
    "orchestration_run.json",
    "orchestration_run.md",
    "validation_report.json",
    "validation_report.md",
]


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "milestone"


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive the active orchestrator cycle.")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--label", required=True, help="Short archive label")
    parser.add_argument("--keep-current", action="store_true", help="Do not reset active files after archiving")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    orch = repo / ".codex" / "orchestrator"
    completed = orch / "completed"
    completed.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = slugify(args.label)
    archive_dir = completed / f"{stamp}-{label}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    for name in FILES_TO_ARCHIVE:
        src = orch / name
        if src.exists():
            shutil.copy2(src, archive_dir / name)

    tracks_dir = orch / "tracks"
    dispatch_dir = orch / "dispatch"
    prompts_dir = orch / "prompts"
    convergence_dir = orch / "convergence"
    automation_dir = orch / "automation"
    if tracks_dir.exists():
        shutil.copytree(tracks_dir, archive_dir / "tracks", dirs_exist_ok=True)
    if dispatch_dir.exists():
        shutil.copytree(dispatch_dir, archive_dir / "dispatch", dirs_exist_ok=True)
    if prompts_dir.exists():
        shutil.copytree(prompts_dir, archive_dir / "prompts", dirs_exist_ok=True)
    if convergence_dir.exists():
        shutil.copytree(convergence_dir, archive_dir / "convergence", dirs_exist_ok=True)
    if automation_dir.exists():
        shutil.copytree(automation_dir, archive_dir / "automation", dirs_exist_ok=True)

    history = orch / "planner_history.txt"
    with history.open("a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} archive_cycle label={label} path={archive_dir}\n")

    if not args.keep_current:
        (orch / "current_requirements.md").write_text("# Current milestone\n\n", encoding="utf-8")
        (orch / "todo.md").write_text("# Active milestone checklist\n\n", encoding="utf-8")
        (orch / "status.md").write_text("# Status\n\n## Current state\n\n", encoding="utf-8")
        (orch / "handoff.md").write_text("# Handoff\n\n## What changed\n\n", encoding="utf-8")
        (orch / "review.md").write_text("# Review\n\n## Review status\n\n", encoding="utf-8")
        if (orch / "tracks.json").exists():
            (orch / "tracks.json").write_text("{\"tracks\": []}\n", encoding="utf-8")
        if (orch / "track_board.md").exists():
            (orch / "track_board.md").write_text("# Track board\n\n", encoding="utf-8")
        if tracks_dir.exists():
            shutil.rmtree(tracks_dir)
            tracks_dir.mkdir(parents=True, exist_ok=True)
        if (orch / "dispatch.json").exists():
            (orch / "dispatch.json").write_text("{\"dispatch\": []}\n", encoding="utf-8")
        if dispatch_dir.exists():
            shutil.rmtree(dispatch_dir)
            dispatch_dir.mkdir(parents=True, exist_ok=True)
        if (orch / "prompts.json").exists():
            (orch / "prompts.json").write_text("{\"prompts\": []}\n", encoding="utf-8")
        if (orch / "track_readiness.json").exists():
            (orch / "track_readiness.json").write_text("{\"ready_for_merge\": false}\n", encoding="utf-8")
        if (orch / "track_readiness.md").exists():
            (orch / "track_readiness.md").write_text("# Track readiness\n\n", encoding="utf-8")
        if (orch / "convergence.json").exists():
            (orch / "convergence.json").write_text("{\"ready_to_converge\": false}\n", encoding="utf-8")
        if (orch / "convergence.md").exists():
            (orch / "convergence.md").write_text("# Convergence\n\n", encoding="utf-8")
        if (orch / "merge_report.json").exists():
            (orch / "merge_report.json").write_text("{\"ready_for_archive\": false}\n", encoding="utf-8")
        if (orch / "merge_report.md").exists():
            (orch / "merge_report.md").write_text("# Merge report\n\n", encoding="utf-8")
        if (orch / "supervisor_report.json").exists():
            (orch / "supervisor_report.json").write_text("{\"next_recommended_action\": null}\n", encoding="utf-8")
        if (orch / "supervisor_report.md").exists():
            (orch / "supervisor_report.md").write_text("# Supervisor report\n\n", encoding="utf-8")
        if (orch / "escalation_report.json").exists():
            (orch / "escalation_report.json").write_text("{\"active_playbook\": null}\n", encoding="utf-8")
        if (orch / "escalation_report.md").exists():
            (orch / "escalation_report.md").write_text("# Escalation report\n\n", encoding="utf-8")
        if (orch / "automation_report.json").exists():
            (orch / "automation_report.json").write_text("{\"recommended_run_kind\": \"report_only\"}\n", encoding="utf-8")
        if (orch / "automation_report.md").exists():
            (orch / "automation_report.md").write_text("# Automation report\n\n", encoding="utf-8")
        if (orch / "automation_pack.json").exists():
            (orch / "automation_pack.json").write_text("{\"profiles\": []}\n", encoding="utf-8")
        if (orch / "automation_pack.md").exists():
            (orch / "automation_pack.md").write_text("# Automation pack\n\n", encoding="utf-8")
        if (orch / "automation_memory.json").exists():
            (orch / "automation_memory.json").write_text("{\"registry\": [], \"recent_runs\": []}\n", encoding="utf-8")
        if (orch / "automation_memory.md").exists():
            (orch / "automation_memory.md").write_text("# Automation memory\n\n", encoding="utf-8")
        if (orch / "execution_bridge.json").exists():
            (orch / "execution_bridge.json").write_text("{\"action\": null}\n", encoding="utf-8")
        if (orch / "execution_bridge.md").exists():
            (orch / "execution_bridge.md").write_text("# Execution bridge\n\n", encoding="utf-8")
        if (orch / "orchestration_run.json").exists():
            (orch / "orchestration_run.json").write_text("{\"action\": null, \"executed\": false}\n", encoding="utf-8")
        if (orch / "orchestration_run.md").exists():
            (orch / "orchestration_run.md").write_text("# Orchestration run\n\n", encoding="utf-8")
        if (orch / "validation_report.json").exists():
            (orch / "validation_report.json").write_text("{\"errors\": [], \"warnings\": []}\n", encoding="utf-8")
        if (orch / "validation_report.md").exists():
            (orch / "validation_report.md").write_text("# Validation report\n\n", encoding="utf-8")
        if prompts_dir.exists():
            shutil.rmtree(prompts_dir)
            prompts_dir.mkdir(parents=True, exist_ok=True)
        if convergence_dir.exists():
            shutil.rmtree(convergence_dir)
            convergence_dir.mkdir(parents=True, exist_ok=True)
        if automation_dir.exists():
            shutil.rmtree(automation_dir)
            automation_dir.mkdir(parents=True, exist_ok=True)

    print(f"Archived cycle to: {archive_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
