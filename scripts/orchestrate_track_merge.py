#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from generate_escalation_playbook import generate_escalation_playbook
from orchestrator_common import (
    append_decision,
    append_history,
    convergence_manifest_path,
    load_json,
    merge_report_markdown_path,
    merge_report_path,
    save_json,
    state_path,
)
from prepare_track_convergence import prepare_track_convergence
from run_repair_loop import run_repair_loop
from run_review_pass import run_review_pass
from run_verification import run_verification


def orchestrate_track_merge(repo: Path, max_repair_attempts: int = 3, allow_repair: bool = True) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    convergence = load_json(convergence_manifest_path(repo))
    if not convergence:
        convergence = prepare_track_convergence(repo)
    if not convergence.get("ready_to_converge"):
        payload = {
            "status": "blocked",
            "ready_for_archive": False,
            "reason": "Convergence brief is not ready.",
            "verification_status": state.get("verification", {}).get("status", "not_run"),
            "review_status": state.get("review", {}).get("status", "not_run"),
        }
        save_json(merge_report_path(repo), payload)
        merge_report_markdown_path(repo).write_text(
            "# Merge report\n\n- Status: blocked\n- Reason: Convergence brief is not ready.\n",
            encoding="utf-8",
        )
        state["merge_orchestration"] = {
            "status": "blocked",
            "manifest_path": str(merge_report_path(repo).relative_to(repo)),
            "ready_for_archive": False,
        }
        state["next_action"] = "finish track convergence prerequisites"
        save_json(state_path(repo), state)
        generate_escalation_playbook(repo)
        append_history(repo, "orchestrate_track_merge blocked convergence_not_ready")
        return payload

    state["current_phase"] = "converge"
    state["next_action"] = "post-merge verification"
    save_json(state_path(repo), state)

    verification = run_verification(repo, generate_custom=True)
    repaired = False
    if verification["status"] != "passed" and allow_repair:
        repair = run_repair_loop(repo, max_attempts=max_repair_attempts)
        repaired = repair["status"] == "passed"
        verification = load_json(state_path(repo)).get("verification", {})
        verification = {
            "status": verification.get("status", "failed"),
            "strategy": verification.get("strategy", "unknown"),
            "last_result_path": verification.get("last_result_path", "n/a"),
        }

    review = {"status": "not_run"}
    if verification["status"] == "passed":
        review = run_review_pass(repo)
        if review["status"] != "passed" and allow_repair:
            repair = run_repair_loop(repo, max_attempts=max_repair_attempts)
            repaired = repaired or repair["status"] == "passed"
            review_state = load_json(state_path(repo)).get("review", {})
            review = {
                "status": review_state.get("status", "needs_repair"),
                "blocking_findings": review_state.get("blocking_findings", 0),
                "last_result_path": review_state.get("last_result_path", "n/a"),
            }

    ready = verification["status"] == "passed" and review.get("status") == "passed"
    payload = {
        "status": "ready" if ready else "needs_repair",
        "ready_for_archive": ready,
        "verification_status": verification["status"],
        "review_status": review.get("status", "not_run"),
        "repaired": repaired,
        "source_convergence_manifest": str(convergence_manifest_path(repo).relative_to(repo)),
    }
    save_json(merge_report_path(repo), payload)

    lines = [
        "# Merge report",
        "",
        f"- Status: {payload['status']}",
        f"- Ready for archive: {'yes' if ready else 'no'}",
        f"- Verification status: {payload['verification_status']}",
        f"- Review status: {payload['review_status']}",
        f"- Repair loop used: {'yes' if repaired else 'no'}",
        "",
        "## Post-merge checklist",
        "",
        f"- [x] Re-ran verification ({payload['verification_status']})",
        f"- [x] Re-ran review ({payload['review_status']})",
        f"- [ ] Archive milestone" if ready else "- [ ] Repair post-merge findings before archive",
        "",
        "## Source",
        "",
        f"- Convergence manifest: {payload['source_convergence_manifest']}",
    ]
    merge_report_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state = load_json(state_path(repo))
    state["merge_orchestration"] = {
        "status": payload["status"],
        "manifest_path": str(merge_report_path(repo).relative_to(repo)),
        "ready_for_archive": ready,
    }
    state["current_phase"] = "archive" if ready else "repair"
    state["next_action"] = "archive" if ready else "repair post-merge findings"
    save_json(state_path(repo), state)
    generate_escalation_playbook(repo)
    append_history(repo, f"orchestrate_track_merge status={payload['status']} ready={ready}")
    append_decision(
        repo,
        "Run post-convergence merge orchestration",
        f"Milestone={convergence.get('milestone_id')}",
        f"Post-merge verification={payload['verification_status']} review={payload['review_status']}.",
        "Archive only after merge_report.md is green.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run post-convergence verify/review/hardening before milestone archive")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--max-repair-attempts", type=int, default=3, help="Automatic repair attempts before failing the merge cycle")
    parser.add_argument("--no-repair", action="store_true", help="Do not attempt automatic repair during the merge cycle")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = orchestrate_track_merge(repo, max_repair_attempts=args.max_repair_attempts, allow_repair=not args.no_repair)
    print(merge_report_path(repo))
    print(f"ready_for_archive={payload['ready_for_archive']}")
    return 0 if payload["ready_for_archive"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
