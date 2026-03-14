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
    automation_pack_dir,
    automation_pack_manifest_path,
    automation_pack_markdown_path,
    load_json,
    save_json,
    state_path,
)


def _profile(
    profile_id: str,
    name: str,
    summary: str,
    schedule_hint: str,
    rrule: str,
    prompt: str,
    guardrails: list[str],
    rationale: str,
    priority: int,
) -> dict:
    return {
        "id": profile_id,
        "name": name,
        "summary": summary,
        "run_kind": "report_only",
        "schedule_hint": schedule_hint,
        "rrule": rrule,
        "prompt": prompt,
        "prompt_path": f".codex/orchestrator/automation/{profile_id}.md",
        "guardrails": guardrails,
        "rationale": rationale,
        "priority": priority,
    }


def _write_prompt(path: Path, title: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n```text\n{body.strip()}\n```\n", encoding="utf-8")


def generate_automation_pack(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    automation = state.get("automation", {})
    supervisor = state.get("supervisor", {})
    escalation = state.get("escalation", {})
    merge_state = state.get("merge_orchestration", {})
    has_tracks = bool(state.get("tracks"))
    is_git_repo = (repo / ".git").exists()
    exact_verifier = bool(automation.get("exact_verification_commands"))

    common_guardrails = [
        "Invoke $big-project-orchestrator explicitly.",
        "Stay in report-only mode.",
        "Do not edit code, run repair loops, or archive automatically.",
        "Update status and handoff artifacts only when the skill normally does so in report-only mode.",
    ]

    profiles: list[dict] = [
        _profile(
            "nightly-verification",
            "Nightly Verification",
            "Refresh verification, review, and the automation report for the active milestone.",
            "Daily at 09:00 local",
            "FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR,SA,SU;BYHOUR=9;BYMINUTE=0",
            "$big-project-orchestrator\n\nReport-only run. Refresh the automation supervisory cycle for the current workspace. "
            "Re-run verification and review, update automation/supervisor/escalation artifacts, summarize failures and risky areas, and do not edit code.",
            common_guardrails,
            "Best default recurring check for any repo that already has an orchestrator workspace.",
            1,
        )
    ]

    if is_git_repo:
        profiles.append(
            _profile(
                "branch-drift-audit",
                "Branch Drift Audit",
                "Check the current branch for drift, merge-risk hotspots, and stale docs or tests.",
                "Tuesdays at 11:00 local",
                "FREQ=WEEKLY;BYDAY=TU;BYHOUR=11;BYMINUTE=0",
                "$big-project-orchestrator\n\nReport-only run. Compare the current branch with the repo baseline, identify drift, likely merge conflicts, stale docs, "
                "and tests most likely to fail after rebase. Update the automation artifacts and do not edit code.",
                common_guardrails,
                "Useful once a repo has parallel lanes or long-lived branches.",
                3,
            )
        )

    if has_tracks:
        profiles.append(
            _profile(
                "track-fleet-supervision",
                "Track Fleet Supervision",
                "Refresh readiness, convergence, supervisor, and escalation artifacts for the active track fleet.",
                "Every 6 hours",
                "FREQ=HOURLY;INTERVAL=6",
                "$big-project-orchestrator\n\nReport-only run. Refresh track readiness, convergence, supervisor, escalation, and automation artifacts for the active milestone. "
                "If the merge gate is already ready, refresh the post-convergence merge report in report-only mode. Do not edit code.",
                common_guardrails + ["Do not start or stop tracks automatically."],
                "Best fit when the milestone is split into worktree lanes and needs frequent supervisory refreshes.",
                0,
            )
        )

    profiles.append(
        _profile(
            "release-readiness",
            "Release Readiness",
            "Summarize blockers, missing tests, docs gaps, and unresolved risks before a release or milestone archive.",
            "Fridays at 14:00 local",
            "FREQ=WEEKLY;BYDAY=FR;BYHOUR=14;BYMINUTE=0",
            "$big-project-orchestrator\n\nReport-only run. Review release readiness for the current branch and active milestone. "
            "List blockers, missing tests, docs gaps, unresolved risks, and whether the current merge/archive gate is green. Do not edit code.",
            common_guardrails,
            "Best for recurring pre-release checks or end-of-week milestone reviews.",
            2,
        )
    )

    if exact_verifier:
        profiles.append(
            _profile(
                "coverage-gap-review",
                "Coverage Gap Review",
                "Propose the highest-value missing tests for the active milestone without writing them.",
                "Wednesdays at 15:00 local",
                "FREQ=WEEKLY;BYDAY=WE;BYHOUR=15;BYMINUTE=0",
                "$big-project-orchestrator\n\nReport-only run. Review the active milestone for the biggest coverage or regression-test gaps. "
                "Propose the top missing tests, note their expected value, and wait for approval before any editing. Do not edit code.",
                common_guardrails + ["Only propose tests; do not write them."],
                "Useful after verification commands are stable enough to support recurring quality reviews.",
                4,
            )
        )

    profiles.sort(key=lambda item: item["priority"])
    recommended = profiles[0]["id"] if profiles else None

    prompt_root = automation_pack_dir(repo)
    for item in profiles:
        _write_prompt(prompt_root / f"{item['id']}.md", item["name"], item["prompt"])

    payload = {
        "milestone_id": state.get("current_milestone_id"),
        "recommended_profile": recommended,
        "profiles": profiles,
        "guarded_editing_candidate": bool(automation.get("editing_candidate")),
        "active_playbook": escalation.get("active_playbook"),
        "supervisor_next_action": supervisor.get("next_recommended_action"),
        "merge_status": merge_state.get("status", "not_run"),
    }
    save_json(automation_pack_manifest_path(repo), payload)

    lines = [
        "# Automation pack",
        "",
        f"- Milestone: {payload['milestone_id'] or 'none'}",
        f"- Recommended profile: {recommended or 'none'}",
        f"- Supervisor next action: {(payload['supervisor_next_action'] or {}).get('kind', 'none')}",
        f"- Active playbook: {(payload['active_playbook'] or {}).get('kind', 'none')}",
        f"- Merge status: {payload['merge_status']}",
        "",
        "## Profiles",
        "",
    ]
    if profiles:
        for item in profiles:
            lines.extend(
                [
                    f"### {item['name']}",
                    "",
                    f"- Id: {item['id']}",
                    f"- Summary: {item['summary']}",
                    f"- Schedule hint: {item['schedule_hint']}",
                    f"- RRULE: {item['rrule']}",
                    f"- Prompt: {item['prompt_path']}",
                    f"- Rationale: {item['rationale']}",
                    "",
                ]
            )
    else:
        lines.append("- No automation profiles were generated.")
    automation_pack_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["automation_pack"] = {
        "status": "ready",
        "manifest_path": str(automation_pack_manifest_path(repo).relative_to(repo)),
        "count": len(profiles),
        "recommended_profile": recommended,
    }
    save_json(state_path(repo), state)
    append_history(repo, f"generate_automation_pack milestone={payload['milestone_id']} count={len(profiles)}")
    append_decision(
        repo,
        "Generate recurring automation dispatch pack",
        f"Milestone={payload['milestone_id'] or 'none'}",
        f"Prepared {len(profiles)} report-only automation profiles; recommended={recommended or 'none'}.",
        "Use automation_pack.md to create Codex app automations without enabling autonomous edits.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate report-only recurring automation profiles for Codex app automations")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = generate_automation_pack(repo)
    print(automation_pack_manifest_path(repo))
    print(f"profile_count={len(payload['profiles'])}")
    print(f"recommended_profile={payload['recommended_profile'] or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
