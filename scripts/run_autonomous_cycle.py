#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from archive_cycle import main as archive_cycle_main
from build_project_state import initialize_state
from generate_milestones import activate_milestone_files, generate_milestones
from orchestrator_common import (
    append_decision,
    append_history,
    dispatch_manifest_path,
    ensure_greenfield_structure,
    load_json,
    orch_dir,
    read_text,
    save_json,
    state_path,
    track_board_path,
)
from evaluate_track_readiness import evaluate_track_readiness
from plan_tracks import plan_tracks
from run_repair_loop import run_repair_loop
from run_review_pass import run_review_pass
from run_verification import run_verification


def _active_milestone(state: dict) -> dict | None:
    current = state.get("current_milestone_id")
    for milestone in state.get("milestones", []):
        if milestone.get("id") == current:
            return milestone
    return None


def _update_status(repo: Path, state: dict, extra_completed: list[str] | None = None) -> None:
    milestone = _active_milestone(state)
    verification = state.get("verification", {})
    review = state.get("review", {})
    tracks = state.get("tracks", [])
    dispatch = state.get("dispatch", {})
    prompts = state.get("prompts", {})
    track_readiness = state.get("track_readiness", {})
    convergence = state.get("convergence", {})
    merge_orchestration = state.get("merge_orchestration", {})
    supervisor = state.get("supervisor", {})
    escalation = state.get("escalation", {})
    automation = state.get("automation", {})
    automation_pack = state.get("automation_pack", {})
    automation_memory = state.get("automation_memory", {})
    execution_bridge = state.get("execution_bridge", {})
    orchestration_run = state.get("orchestration_run", {})
    validation = state.get("validation", {})
    repair_attempts = state.get("repair_attempts", {})
    milestone_attempts = repair_attempts.get(milestone["id"], 0) if milestone else 0
    completed_lines = "".join(f"- [x] {item}\n" for item in (extra_completed or []))
    in_progress = milestone["title"] if milestone else "Awaiting milestone selection"
    status = (
        "# Status\n\n## Current state\n\n"
        f"- Phase: {state['current_phase']}\n"
        "- Branch / thread: current thread\n"
        "- Working mode: Local\n"
        f"- Active milestone: {milestone['title'] if milestone else 'none'}\n"
        f"- Last verification result: {verification.get('status', 'not_run')}\n"
        f"- Last review result: {review.get('status', 'not_run')}\n"
        f"- Primary blocker: {state.get('blockers', [{}])[-1].get('reason', 'none') if state.get('blockers') else 'none'}\n\n"
        "## Completed in this cycle\n\n"
        f"{completed_lines or '- [ ]\n'}\n"
        "## In progress\n\n"
        f"- [ ] {in_progress}\n\n"
        "## Verification summary\n\n"
        f"- Strategy: {verification.get('strategy', 'not_run')}\n"
        f"- Commands run: {verification.get('last_result_path', 'n/a')}\n"
        f"- Failures: {'none' if verification.get('status') == 'passed' else 'inspect last_verification.json'}\n\n"
        "## Review summary\n\n"
        f"- Status: {review.get('status', 'not_run')}\n"
        f"- Findings: {review.get('last_result_path', 'n/a')}\n"
        f"- Blocking findings: {review.get('blocking_findings', 0)}\n\n"
        "## Track summary\n\n"
        f"- Planned tracks: {len(tracks)}\n"
        f"- Board: {track_board_path(repo).relative_to(repo) if tracks else 'n/a'}\n\n"
        "## Dispatch summary\n\n"
        f"- Status: {dispatch.get('status', 'not_run')}\n"
        f"- Manifest: {dispatch.get('manifest_path', 'n/a') if dispatch.get('count', 0) else 'n/a'}\n"
        f"- Count: {dispatch.get('count', 0)}\n\n"
        "## Prompt summary\n\n"
        f"- Status: {prompts.get('status', 'not_run')}\n"
        f"- Manifest: {prompts.get('manifest_path', 'n/a') if prompts.get('count', 0) else 'n/a'}\n"
        f"- Count: {prompts.get('count', 0)}\n\n"
        "## Track readiness\n\n"
        f"- Status: {track_readiness.get('status', 'not_run')}\n"
        f"- Manifest: {track_readiness.get('manifest_path', 'n/a')}\n"
        f"- Ready for merge: {track_readiness.get('ready_for_merge', False)}\n\n"
        "## Convergence summary\n\n"
        f"- Status: {convergence.get('status', 'not_run')}\n"
        f"- Manifest: {convergence.get('manifest_path', 'n/a')}\n"
        f"- Ready to converge: {convergence.get('ready_to_converge', False)}\n\n"
        "## Merge orchestration\n\n"
        f"- Status: {merge_orchestration.get('status', 'not_run')}\n"
        f"- Manifest: {merge_orchestration.get('manifest_path', 'n/a')}\n"
        f"- Ready for archive: {merge_orchestration.get('ready_for_archive', False)}\n\n"
        "## Supervisor summary\n\n"
        f"- Status: {supervisor.get('status', 'not_run')}\n"
        f"- Manifest: {supervisor.get('manifest_path', 'n/a')}\n"
        f"- Next action: {supervisor.get('next_recommended_action', {}).get('kind', 'n/a') if isinstance(supervisor.get('next_recommended_action'), dict) else 'n/a'}\n\n"
        "## Escalation summary\n\n"
        f"- Status: {escalation.get('status', 'not_run')}\n"
        f"- Manifest: {escalation.get('manifest_path', 'n/a')}\n"
        f"- Playbook: {escalation.get('active_playbook', {}).get('kind', 'n/a') if isinstance(escalation.get('active_playbook'), dict) else 'n/a'}\n\n"
        "## Automation summary\n\n"
        f"- Status: {automation.get('status', 'not_run')}\n"
        f"- Manifest: {automation.get('manifest_path', 'n/a')}\n"
        f"- Recommended run kind: {automation.get('recommended_run_kind', 'report_only')}\n\n"
        "## Automation pack\n\n"
        f"- Status: {automation_pack.get('status', 'not_run')}\n"
        f"- Manifest: {automation_pack.get('manifest_path', 'n/a')}\n"
        f"- Profiles: {automation_pack.get('count', 0)}\n\n"
        "## Automation memory\n\n"
        f"- Status: {automation_memory.get('status', 'not_run')}\n"
        f"- Manifest: {automation_memory.get('manifest_path', 'n/a')}\n"
        f"- Open findings: {automation_memory.get('open_findings', 0)}\n"
        f"- New findings: {automation_memory.get('new_findings', 0)}\n\n"
        "## Execution bridge\n\n"
        f"- Status: {execution_bridge.get('status', 'not_run')}\n"
        f"- Manifest: {execution_bridge.get('manifest_path', 'n/a')}\n"
        f"- Action kind: {execution_bridge.get('action_kind', 'n/a')}\n\n"
        "## Orchestration run\n\n"
        f"- Status: {orchestration_run.get('status', 'not_run')}\n"
        f"- Manifest: {orchestration_run.get('manifest_path', 'n/a')}\n"
        f"- Action kind: {orchestration_run.get('action_kind', 'n/a')}\n\n"
        "## Validation\n\n"
        f"- Status: {validation.get('status', 'not_run')}\n"
        f"- Manifest: {validation.get('manifest_path', 'n/a')}\n"
        f"- Errors: {validation.get('errors', 0)}\n"
        f"- Warnings: {validation.get('warnings', 0)}\n\n"
        "## Repair loop\n\n"
        f"- Attempts: {milestone_attempts}\n"
        f"- Last repair action: {'none' if milestone_attempts == 0 else 'see planner_history.txt'}\n\n"
        "## Next best action\n\n"
        f"- [ ] {state.get('next_action', 'continue autonomous cycle')}\n"
    )
    (orch_dir(repo) / "status.md").write_text(status, encoding="utf-8")


def _update_handoff(repo: Path, state: dict, note: str) -> None:
    milestone = _active_milestone(state)
    commands = 'python3 <skill-dir>/scripts/run_autonomous_cycle.py --repo "$PWD" --resume'
    handoff = (
        "# Handoff\n\n## What changed\n\n"
        f"- {note}\n\n"
        "## What still needs work\n\n"
        f"- {milestone['goal'] if milestone else 'Select the next milestone'}\n\n"
        "## Exact next step\n\n1. Continue the autonomous cycle from the recorded state.\n\n"
        "## Track plan\n\n"
        f"- Planned tracks: {len(state.get('tracks', []))}\n"
        f"- Track board: {track_board_path(repo).relative_to(repo) if state.get('tracks') else 'n/a'}\n\n"
        "## Dispatch plan\n\n"
        f"- Status: {state.get('dispatch', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('dispatch', {}).get('manifest_path', 'n/a') if state.get('dispatch', {}).get('count', 0) else 'n/a'}\n\n"
        "## Prompt plan\n\n"
        f"- Status: {state.get('prompts', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('prompts', {}).get('manifest_path', 'n/a') if state.get('prompts', {}).get('count', 0) else 'n/a'}\n\n"
        "## Convergence plan\n\n"
        f"- Status: {state.get('convergence', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('convergence', {}).get('manifest_path', 'n/a')}\n\n"
        "## Merge orchestration\n\n"
        f"- Status: {state.get('merge_orchestration', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('merge_orchestration', {}).get('manifest_path', 'n/a')}\n\n"
        "## Supervisor summary\n\n"
        f"- Status: {state.get('supervisor', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('supervisor', {}).get('manifest_path', 'n/a')}\n\n"
        "## Escalation summary\n\n"
        f"- Status: {state.get('escalation', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('escalation', {}).get('manifest_path', 'n/a')}\n\n"
        "## Automation summary\n\n"
        f"- Status: {state.get('automation', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('automation', {}).get('manifest_path', 'n/a')}\n\n"
        "## Automation pack\n\n"
        f"- Status: {state.get('automation_pack', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('automation_pack', {}).get('manifest_path', 'n/a')}\n\n"
        "## Automation memory\n\n"
        f"- Status: {state.get('automation_memory', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('automation_memory', {}).get('manifest_path', 'n/a')}\n\n"
        "## Execution bridge\n\n"
        f"- Status: {state.get('execution_bridge', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('execution_bridge', {}).get('manifest_path', 'n/a')}\n\n"
        "## Orchestration run\n\n"
        f"- Status: {state.get('orchestration_run', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('orchestration_run', {}).get('manifest_path', 'n/a')}\n\n"
        "## Validation\n\n"
        f"- Status: {state.get('validation', {}).get('status', 'not_run')}\n"
        f"- Manifest: {state.get('validation', {}).get('manifest_path', 'n/a')}\n\n"
        "## Commands to run next\n\n```bash\n"
        f"{commands}\n"
        "```\n\n## Risks / gotchas\n\n"
        "- [ ] Re-check stack assumptions if the implementation starts diverging from the spec.\n"
    )
    (orch_dir(repo) / "handoff.md").write_text(handoff, encoding="utf-8")


def _archive_active_milestone(repo: Path, state: dict) -> None:
    milestone = _active_milestone(state)
    if not milestone:
        return
    archive_cycle_main_args = ["--repo", str(repo), "--label", milestone["title"]]
    import sys

    original = sys.argv
    try:
        sys.argv = ["archive_cycle.py", *archive_cycle_main_args]
        archive_cycle_main()
    finally:
        sys.argv = original


def run_autonomous_cycle(
    repo: Path,
    spec: str | None = None,
    max_milestones: int = 20,
    max_repair_attempts: int = 3,
    plan_tracks_enabled: bool = False,
    max_tracks: int = 4,
    generate_dispatch_enabled: bool = False,
    allow_structure_generation: bool = False,
    goal: str | None = None,
    resume: bool = False,
) -> dict:
    state = load_json(state_path(repo)) if resume else {}
    if not state:
        state = initialize_state(repo, spec_arg=spec, goal=goal)

    if not state.get("milestones"):
        state["current_phase"] = "plan_milestones"
        state["next_action"] = "plan_milestones"
        save_json(state_path(repo), state)
        state = generate_milestones(repo, max_milestones=max_milestones)

    milestone = _active_milestone(state)
    if not milestone:
        state["current_phase"] = "complete"
        state["project_done"] = True
        save_json(state_path(repo), state)
        return state

    if plan_tracks_enabled:
        track_result = plan_tracks(repo, max_tracks=max_tracks, generate_dispatch=generate_dispatch_enabled)
        append_history(repo, f"autonomous_cycle track_plan milestone={track_result['milestone_id']} count={len(track_result['tracks'])}")
        evaluate_track_readiness(repo)

    if state.get("project_mode") == "greenfield" and allow_structure_generation and milestone["id"] == "m1-foundation":
        created = ensure_greenfield_structure(repo, state["stack"]["primary"], state["goal"])
        if created:
            append_history(repo, f"greenfield_bootstrap files={','.join(created)}")
            append_decision(
                repo,
                "Bootstrap greenfield structure",
                f"Milestone={milestone['id']}",
                f"Created {len(created)} bootstrap file(s) for {state['stack']['primary']}.",
                "Replace bootstrap placeholders with milestone-specific implementation.",
            )

    state["current_phase"] = "verify"
    state["next_action"] = "run verification"
    save_json(state_path(repo), state)
    _update_status(repo, state, extra_completed=["Milestone plan prepared"])
    handoff_note = "Autonomous cycle advanced to verification."
    if plan_tracks_enabled and track_board_path(repo).exists():
        handoff_note += " Track board is available for worktree or CLI fan-out."
    _update_handoff(repo, state, handoff_note)

    verification = run_verification(repo, generate_custom=True)
    if verification["status"] != "passed":
        repair = run_repair_loop(repo, max_attempts=max_repair_attempts)
        if repair["status"] != "passed":
            state = load_json(state_path(repo))
            _update_status(repo, state, extra_completed=["Milestone plan prepared"])
            _update_handoff(repo, state, "Autonomous cycle stopped on a blocker after safe repair attempts.")
            append_history(repo, f"autonomous_cycle blocked milestone={milestone['id']}")
            return state

    state = load_json(state_path(repo))
    state["current_phase"] = "review"
    state["next_action"] = "run review"
    save_json(state_path(repo), state)
    _update_status(repo, state, extra_completed=["Milestone plan prepared", "Verification passed"])
    _update_handoff(repo, state, "Verification passed. Autonomous cycle advanced to mandatory review.")

    review = run_review_pass(repo)
    if review["status"] != "passed":
        repair = run_repair_loop(repo, max_attempts=max_repair_attempts)
        if repair["status"] != "passed":
            state = load_json(state_path(repo))
            _update_status(repo, state, extra_completed=["Milestone plan prepared", "Verification passed"])
            _update_handoff(repo, state, "Autonomous cycle stopped on a blocker after review findings could not be repaired safely.")
            append_history(repo, f"autonomous_cycle blocked_review milestone={milestone['id']}")
            return state

    state = load_json(state_path(repo))
    state["current_phase"] = "archive"
    state["next_action"] = "archive"
    _update_status(repo, state, extra_completed=["Milestone plan prepared", "Verification passed", "Review passed"])
    _update_handoff(repo, state, "Active milestone passed verification and review and is ready to archive.")
    save_json(state_path(repo), state)
    _archive_active_milestone(repo, state)

    current_id = state.get("current_milestone_id")
    next_found = False
    for milestone_entry in state.get("milestones", []):
        if milestone_entry["id"] == current_id:
            milestone_entry["status"] = "completed"
            next_found = True
            continue
        if next_found and milestone_entry["status"] == "planned":
            milestone_entry["status"] = "active"
            state["current_milestone_id"] = milestone_entry["id"]
            state["active_tasks"] = milestone_entry["deliverables"]
            state["tracks"] = []
            state["current_phase"] = "implement"
            state["next_action"] = "implement"
            save_json(state_path(repo), state)
            activate_milestone_files(repo, state, milestone_entry)
            if plan_tracks_enabled:
                plan_tracks(repo, max_tracks=max_tracks, force=True, generate_dispatch=generate_dispatch_enabled)
                evaluate_track_readiness(repo)
            break
    else:
        state["current_milestone_id"] = None
        state["current_phase"] = "complete"
        state["next_action"] = "project complete"
        state["project_done"] = True

    save_json(state_path(repo), state)
    append_history(repo, f"autonomous_cycle phase={state['current_phase']}")
    _update_status(repo, state, extra_completed=["Milestone archived"])
    _update_handoff(repo, state, "Autonomous cycle archived the milestone and advanced the state.")
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one autonomous big-project-orchestrator cycle")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--spec", help="Explicit spec file relative to repo root")
    parser.add_argument("--max-milestones", type=int, default=20, help="Maximum milestone count to plan")
    parser.add_argument("--max-repair-attempts", type=int, default=3, help="Automatic repair attempts before blocking")
    parser.add_argument("--plan-tracks", action="store_true", help="Create a parallel track/worktree plan for the active milestone")
    parser.add_argument("--max-tracks", type=int, default=4, help="Maximum track count when --plan-tracks is enabled")
    parser.add_argument("--generate-dispatch", action="store_true", help="Generate per-track worktree/bootstrap dispatch artifacts")
    parser.add_argument("--allow-bootstrap", action="store_true", help="Accepted for compatibility; bootstrap is part of the cycle")
    parser.add_argument("--allow-structure-generation", action="store_true", help="Create a minimal repo skeleton in greenfield mode")
    parser.add_argument("--goal", help="Fallback goal when no spec file exists")
    parser.add_argument("--resume", action="store_true", help="Resume from the current state instead of rebuilding it")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    state = run_autonomous_cycle(
        repo=repo,
        spec=args.spec,
        max_milestones=args.max_milestones,
        max_repair_attempts=args.max_repair_attempts,
        plan_tracks_enabled=args.plan_tracks,
        max_tracks=args.max_tracks,
        generate_dispatch_enabled=args.generate_dispatch,
        allow_structure_generation=args.allow_structure_generation,
        goal=args.goal,
        resume=args.resume,
    )
    print(state_path(repo))
    print(f"phase={state['current_phase']}")
    print(f"project_done={state['project_done']}")
    return 0 if state["current_phase"] not in {"blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
