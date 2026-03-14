#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from evaluate_track_readiness import evaluate_track_readiness
from orchestrate_track_merge import orchestrate_track_merge
from orchestrator_common import (
    append_decision,
    append_history,
    automation_report_markdown_path,
    automation_report_path,
    is_placeholder_verifier,
    load_json,
    orch_dir,
    save_json,
    state_path,
    tracks_manifest_path,
)
from prepare_track_convergence import prepare_track_convergence
from generate_automation_pack import generate_automation_pack
from run_review_pass import run_review_pass
from run_track_supervisor import run_track_supervisor
from update_automation_memory import update_automation_memory
from run_verification import run_verification


def _verification_status(repo: Path, fallback: dict | None = None) -> dict:
    payload = load_json(orch_dir(repo) / "last_verification.json")
    if payload:
        return payload
    return fallback or {"status": "not_run", "strategy": "unknown"}


def _review_status(repo: Path, fallback: dict | None = None) -> dict:
    payload = load_json(orch_dir(repo) / "last_review.json")
    if payload:
        return payload
    return fallback or {"status": "not_run", "blocking_findings": 0}


def run_automation_cycle(
    repo: Path,
    refresh_merge: bool = True,
    skip_verification: bool = False,
    skip_review: bool = False,
) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    tracks_manifest = load_json(tracks_manifest_path(repo))
    tracks = tracks_manifest.get("tracks", [])
    has_tracks = bool(tracks)

    verification = _verification_status(repo, state.get("verification"))
    review = _review_status(repo, state.get("review"))
    notes: list[str] = []
    guardrails = [
        "No code edits were attempted.",
        "Automatic repair was disabled for this cycle.",
    ]

    if skip_verification:
        notes.append("Verification refresh was skipped by request; existing verification state was reused.")
    else:
        verification = run_verification(repo, generate_custom=False)
        notes.append(f"Verification refreshed with strategy={verification.get('strategy', 'unknown')}.")

    if skip_review:
        notes.append("Review refresh was skipped by request; existing review state was reused.")
    else:
        review = run_review_pass(repo)
        notes.append(f"Review refreshed with status={review.get('status', 'not_run')}.")

    readiness_payload = load_json(orch_dir(repo) / "track_readiness.json") if has_tracks else {}
    convergence_payload = load_json(orch_dir(repo) / "convergence.json") if has_tracks else {}
    if has_tracks:
        readiness_payload = evaluate_track_readiness(repo)
        convergence_payload = prepare_track_convergence(repo)
    else:
        notes.append("No track fleet is active; readiness and convergence refresh were skipped.")

    merge_payload = load_json(orch_dir(repo) / "merge_report.json")
    merge_attempted = False
    if refresh_merge and has_tracks and convergence_payload.get("ready_to_converge"):
        merge_payload = orchestrate_track_merge(repo, allow_repair=False)
        merge_attempted = True
        verification = _verification_status(repo, verification)
        review = _review_status(repo, review)
        notes.append("Post-convergence merge report was refreshed without repair.")
        guardrails.append("Post-merge gates were evaluated in report-only mode.")
    elif refresh_merge and has_tracks:
        notes.append("Merge report was not refreshed because convergence is not ready.")
    elif not refresh_merge:
        notes.append("Merge report refresh was skipped by request.")

    supervisor_payload = run_track_supervisor(repo)
    state = load_json(state_path(repo))
    escalation = state.get("escalation", {})
    merge_state = state.get("merge_orchestration", {})
    verification_state = state.get("verification", {})
    review_state = state.get("review", {})
    execution_bridge = state.get("execution_bridge", {})
    orchestration_run = state.get("orchestration_run", {})
    validation = state.get("validation", {})
    next_action = supervisor_payload.get("next_recommended_action")
    active_playbook = escalation.get("active_playbook") or {"kind": "none"}

    custom_verifier = orch_dir(repo) / "verification.commands.sh"
    exact_verifier = custom_verifier.exists() and not is_placeholder_verifier(custom_verifier)
    ready_for_report_only = supervisor_payload.get("next_recommended_action") is not None
    editing_candidate = bool(
        exact_verifier
        and verification_state.get("status") == "passed"
        and review_state.get("status") == "passed"
        and active_playbook.get("kind") == "none"
        and merge_state.get("status") in {"ready", "not_run"}
    )

    overall_health = "green"
    if active_playbook.get("kind") != "none" or merge_state.get("status") in {"blocked", "needs_repair"}:
        overall_health = "red"
    elif verification_state.get("status") != "passed" or review_state.get("status") != "passed":
        overall_health = "yellow"
    elif has_tracks and not convergence_payload.get("ready_to_converge", False) and supervisor_payload["next_recommended_action"]["kind"] != "archive_milestone":
        overall_health = "yellow"

    payload = {
        "mode": "report_only",
        "milestone_id": state.get("current_milestone_id"),
        "overall_health": overall_health,
        "track_fleet_present": has_tracks,
        "refreshes": {
            "verification": verification_state.get("status", verification.get("status", "not_run")),
            "review": review_state.get("status", review.get("status", "not_run")),
            "track_readiness": state.get("track_readiness", {}).get("status", "not_run") if has_tracks else "not_applicable",
            "convergence": state.get("convergence", {}).get("status", "not_run") if has_tracks else "not_applicable",
            "merge_orchestration": merge_state.get("status", merge_payload.get("status", "not_run")),
            "supervisor": state.get("supervisor", {}).get("status", "not_run"),
            "escalation": escalation.get("status", "not_run"),
            "execution_bridge": execution_bridge.get("status", "not_run"),
            "orchestration_run": orchestration_run.get("status", "not_run"),
            "validation": validation.get("status", "not_run"),
        },
        "merge_refresh_attempted": merge_attempted,
        "next_recommended_action": next_action,
        "active_playbook": active_playbook,
        "execution_bridge": {
            "status": execution_bridge.get("status", "not_run"),
            "manifest_path": execution_bridge.get("manifest_path", "n/a"),
            "action_kind": execution_bridge.get("action_kind"),
            "ready": execution_bridge.get("ready", False),
        },
        "orchestration_run": {
            "status": orchestration_run.get("status", "not_run"),
            "manifest_path": orchestration_run.get("manifest_path", "n/a"),
            "action_kind": orchestration_run.get("action_kind"),
            "executed": orchestration_run.get("executed", False),
        },
        "validation": {
            "status": validation.get("status", "not_run"),
            "manifest_path": validation.get("manifest_path", "n/a"),
            "errors": validation.get("errors", 0),
            "warnings": validation.get("warnings", 0),
        },
        "recommended_run_kind": "report_only",
        "ready_for_report_only_automation": ready_for_report_only,
        "editing_candidate": editing_candidate,
        "exact_verification_commands": exact_verifier,
        "guardrails": guardrails,
        "notes": notes,
    }
    save_json(automation_report_path(repo), payload)
    memory_payload = update_automation_memory(repo)
    payload["memory"] = {
        "open_findings": memory_payload["open_findings"],
        "new_findings": memory_payload["new_findings"],
        "known_findings": memory_payload["known_findings"],
        "resolved_since_last_run": memory_payload["resolved_since_last_run"],
    }
    save_json(automation_report_path(repo), payload)
    state = load_json(state_path(repo))

    lines = [
        "# Automation report",
        "",
        f"- Mode: {payload['mode']}",
        f"- Milestone: {payload['milestone_id'] or 'none'}",
        f"- Overall health: {payload['overall_health']}",
        f"- Track fleet present: {'yes' if has_tracks else 'no'}",
        f"- Merge refresh attempted: {'yes' if merge_attempted else 'no'}",
        "",
        "## Refresh summary",
        "",
        f"- Verification: {payload['refreshes']['verification']}",
        f"- Review: {payload['refreshes']['review']}",
        f"- Track readiness: {payload['refreshes']['track_readiness']}",
        f"- Convergence: {payload['refreshes']['convergence']}",
        f"- Merge orchestration: {payload['refreshes']['merge_orchestration']}",
        f"- Supervisor: {payload['refreshes']['supervisor']}",
        f"- Escalation: {payload['refreshes']['escalation']}",
        f"- Execution bridge: {payload['refreshes']['execution_bridge']}",
        f"- Orchestration run: {payload['refreshes']['orchestration_run']}",
        f"- Validation: {payload['refreshes']['validation']}",
        "",
        "## Supervisor recommendation",
        "",
        f"- Kind: {(next_action or {}).get('kind', 'none')}",
        f"- Track: {(next_action or {}).get('track_id', 'n/a') or 'n/a'}",
        f"- Reason: {(next_action or {}).get('reason', 'No recommendation available.')}",
        "",
        "## Escalation playbook",
        "",
        f"- Kind: {active_playbook.get('kind', 'none')}",
        f"- Title: {active_playbook.get('title', 'No escalation needed')}",
        "",
        "## Execution bridge",
        "",
        f"- Status: {payload['execution_bridge']['status']}",
        f"- Manifest: {payload['execution_bridge']['manifest_path']}",
        f"- Action kind: {payload['execution_bridge']['action_kind'] or 'none'}",
        f"- Ready: {'yes' if payload['execution_bridge']['ready'] else 'no'}",
        "",
        "## Orchestration run",
        "",
        f"- Status: {payload['orchestration_run']['status']}",
        f"- Manifest: {payload['orchestration_run']['manifest_path']}",
        f"- Action kind: {payload['orchestration_run']['action_kind'] or 'none'}",
        f"- Executed: {'yes' if payload['orchestration_run']['executed'] else 'no'}",
        "",
        "## Validation",
        "",
        f"- Status: {payload['validation']['status']}",
        f"- Manifest: {payload['validation']['manifest_path']}",
        f"- Errors: {payload['validation']['errors']}",
        f"- Warnings: {payload['validation']['warnings']}",
        "",
        "## Automation posture",
        "",
        f"- Recommended run kind: {payload['recommended_run_kind']}",
        f"- Ready for report-only automation: {'yes' if ready_for_report_only else 'no'}",
        f"- Exact verification commands present: {'yes' if exact_verifier else 'no'}",
        f"- Editing candidate: {'yes' if editing_candidate else 'no'}",
        "",
        "## Finding memory",
        "",
        f"- Open findings: {payload['memory']['open_findings']}",
        f"- New findings: {payload['memory']['new_findings']}",
        f"- Known recurring findings: {payload['memory']['known_findings']}",
        f"- Resolved since last run: {payload['memory']['resolved_since_last_run']}",
        "",
        "## Guardrails",
        "",
    ]
    lines.extend(f"- {item}" for item in guardrails)
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {item}" for item in notes)
    automation_report_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["automation"] = {
        "status": "ready",
        "manifest_path": str(automation_report_path(repo).relative_to(repo)),
        "mode": "report_only",
        "ready_for_report_only": ready_for_report_only,
        "recommended_run_kind": "report_only",
        "editing_candidate": editing_candidate,
        "exact_verification_commands": exact_verifier,
    }
    state["next_action"] = (next_action or {}).get("reason", state.get("next_action", "review automation report"))
    save_json(state_path(repo), state)
    generate_automation_pack(repo)
    append_history(
        repo,
        "run_automation_cycle "
        f"milestone={payload['milestone_id']} health={overall_health} action={(next_action or {}).get('kind', 'none')}",
    )
    append_decision(
        repo,
        "Run report-only automation supervisory cycle",
        f"Milestone={payload['milestone_id'] or 'none'}",
        f"Overall health={overall_health}; recommended next action={(next_action or {}).get('kind', 'none')}.",
        "Use automation_report.md as the safe recurring-automation handoff.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe report-first automation cycle across supervisor, escalation, and merge gates")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--skip-verification", action="store_true", help="Reuse the current verification state instead of running it again")
    parser.add_argument("--skip-review", action="store_true", help="Reuse the current review state instead of running it again")
    parser.add_argument("--no-merge-refresh", action="store_true", help="Do not refresh merge orchestration, even if convergence is ready")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = run_automation_cycle(
        repo,
        refresh_merge=not args.no_merge_refresh,
        skip_verification=args.skip_verification,
        skip_review=args.skip_review,
    )
    print(automation_report_path(repo))
    print(f"overall_health={payload['overall_health']}")
    print(f"next_action={(payload.get('next_recommended_action') or {}).get('kind', 'none')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
