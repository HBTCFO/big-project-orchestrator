#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from orchestrator_common import (
    append_decision,
    append_history,
    detect_project_mode,
    discover_input_spec,
    ensure_workspace,
    infer_stack,
    read_text,
    save_json,
    state_path,
    summarize_spec,
)


def initialize_state(repo: Path, spec_arg: str | None = None, force: bool = False, goal: str | None = None) -> dict:
    ensure_workspace(repo, force=force)
    path = state_path(repo)
    if path.exists() and not force:
        from orchestrator_common import load_json

        current = load_json(path)
        if current.get("project_mode"):
            return current

    spec = discover_input_spec(repo, spec_arg)
    spec_text = read_text(spec) if spec else ""
    project_mode = detect_project_mode(repo, spec_text)
    stack = infer_stack(repo, spec_text)
    initial_goal = goal or summarize_spec(spec_text)
    state = {
        "history_version": 1,
        "project_mode": project_mode,
        "input_spec_path": str(spec.relative_to(repo)) if spec else None,
        "input_spec_excerpt": "\n".join(spec_text.splitlines()[:20]),
        "goal": initial_goal,
        "stack": stack,
        "current_phase": "bootstrap",
        "current_milestone_id": None,
        "milestones": [],
        "active_tasks": [],
        "completed_tasks": [],
        "verification": {
            "status": "not_run",
            "last_result_path": str(Path(".codex/orchestrator/last_verification.json")),
        },
        "review": {
            "status": "not_run",
            "last_result_path": str(Path(".codex/orchestrator/last_review.json")),
            "blocking_findings": 0,
        },
        "tracks": [],
        "dispatch": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/dispatch.json")),
            "count": 0,
        },
        "prompts": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/prompts.json")),
            "count": 0,
        },
        "track_readiness": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/track_readiness.json")),
            "ready_for_merge": False,
        },
        "convergence": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/convergence.json")),
            "ready_to_converge": False,
        },
        "merge_orchestration": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/merge_report.json")),
            "ready_for_archive": False,
        },
        "supervisor": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/supervisor_report.json")),
            "next_recommended_action": None,
        },
        "escalation": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/escalation_report.json")),
            "active_playbook": None,
        },
        "automation": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/automation_report.json")),
            "mode": "report_only",
            "ready_for_report_only": False,
            "recommended_run_kind": "report_only",
            "editing_candidate": False,
            "exact_verification_commands": False,
        },
        "automation_pack": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/automation_pack.json")),
            "count": 0,
            "recommended_profile": None,
        },
        "automation_memory": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/automation_memory.json")),
            "open_findings": 0,
            "new_findings": 0,
        },
        "execution_bridge": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/execution_bridge.json")),
            "action_kind": None,
            "ready": False,
        },
        "orchestration_run": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/orchestration_run.json")),
            "action_kind": None,
            "executed": False,
        },
        "validation": {
            "status": "not_run",
            "manifest_path": str(Path(".codex/orchestrator/validation_report.json")),
            "errors": 0,
            "warnings": 0,
        },
        "repair_attempts": {},
        "blockers": [],
        "next_action": "refine_requirements",
        "project_done": False,
    }
    save_json(path, state)
    append_history(repo, f"build_project_state mode={project_mode} spec={state['input_spec_path']}")
    append_decision(
        repo,
        "Initialize autonomous orchestrator state",
        f"Detected mode={project_mode}; input spec={state['input_spec_path'] or 'inline-or-missing'}",
        f"Selected stack={stack['primary']} because {stack['reason']}.",
        "Review assumptions before milestone 2 if the spec evolves.",
    )
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or refresh .codex/orchestrator/state.json")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--spec", help="Explicit spec file relative to repo root")
    parser.add_argument("--force", action="store_true", help="Overwrite existing state and template files")
    parser.add_argument("--goal", help="Fallback goal text if no spec file exists")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    state = initialize_state(repo, spec_arg=args.spec, force=args.force, goal=args.goal)
    print(state_path(repo))
    print(f"mode={state['project_mode']}")
    print(f"stack={state['stack']['primary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
