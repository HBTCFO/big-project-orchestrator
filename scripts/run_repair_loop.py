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
    default_verification_plan,
    ensure_greenfield_structure,
    is_placeholder_verifier,
    last_review_path,
    last_verification_path,
    load_json,
    orch_dir,
    read_text,
    render_verification_script,
    save_json,
    state_path,
)
from run_review_pass import run_review_pass
from run_verification import run_verification


def _sync_validation_commands(repo: Path, commands: list[str]) -> bool:
    if not commands:
        return False
    current_path = orch_dir(repo) / "current_requirements.md"
    current = read_text(current_path)
    replacement = "## Validation commands\n\n```bash\n" + "\n".join(commands) + "\n```"
    if "## Validation commands" not in current:
        current = current.rstrip() + "\n\n" + replacement + "\n"
        current_path.write_text(current, encoding="utf-8")
        return True
    start = current.index("## Validation commands")
    end = current.find("## Done when", start)
    if end == -1:
        end = len(current)
    updated = current[:start] + replacement + "\n\n" + current[end:].lstrip("\n")
    if updated != current:
        current_path.write_text(updated, encoding="utf-8")
        return True
    return False


def run_repair_loop(repo: Path, max_attempts: int = 3) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    spec_path = repo / state["input_spec_path"] if state.get("input_spec_path") else None
    spec_text = read_text(spec_path) if spec_path else state.get("goal", "")
    result = load_json(last_verification_path(repo))
    review_result = load_json(last_review_path(repo))
    if not result:
        result = run_verification(repo, generate_custom=True)
        if result["status"] == "passed":
            review_result = run_review_pass(repo)
            if review_result["status"] == "passed":
                return {"status": "passed", "attempts": []}

    milestone_id = state.get("current_milestone_id") or "unknown"
    attempt_count = int(state.get("repair_attempts", {}).get(milestone_id, 0))
    attempts: list[dict] = []

    for _ in range(max_attempts):
        if result["status"] == "passed":
            break
        attempt_count += 1
        actions: list[str] = []
        custom = orch_dir(repo) / "verification.commands.sh"
        plan = default_verification_plan(repo, spec_text, state.get("project_mode", "unknown"))

        if is_placeholder_verifier(custom) and plan["commands"]:
            custom.write_text(render_verification_script(plan["commands"], plan["reason"]), encoding="utf-8")
            custom.chmod(0o755)
            actions.append("Generated concrete verification.commands.sh from detected stack")

        if _sync_validation_commands(repo, plan["commands"]):
            actions.append("Synchronized current milestone validation commands")

        if state.get("project_mode") == "greenfield":
            created = ensure_greenfield_structure(repo, state.get("stack", {}).get("primary", "unknown"), state.get("goal", "Bootstrap project"))
            if created:
                actions.append("Created missing greenfield bootstrap files: " + ", ".join(created))

        review_markdown = orch_dir(repo) / "review.md"
        if not review_markdown.exists():
            review_markdown.write_text("# Review\n\n## Review status\n\n- Status: pending\n", encoding="utf-8")
            actions.append("Created missing review.md placeholder")

        if not actions:
            actions.append("No safe automatic repair was available")

        result = run_verification(repo, generate_custom=True)
        review_result = run_review_pass(repo) if result["status"] == "passed" else {"status": "needs_repair"}
        attempts.append(
            {
                "attempt": attempt_count,
                "actions": actions,
                "verification_status": result["status"],
                "review_status": review_result["status"],
            }
        )
        append_history(repo, f"repair_attempt milestone={milestone_id} attempt={attempt_count} verify={result['status']} review={review_result['status']}")

        if result["status"] == "passed" and review_result["status"] == "passed":
            append_decision(
                repo,
                "Repair verification and review findings",
                f"Milestone={milestone_id}",
                f"Automatic repair succeeded after {attempt_count} attempt(s).",
                "Review the generated hardening artifacts before milestone 2.",
            )
            break

    state = load_json(state_path(repo))
    state.setdefault("repair_attempts", {})[milestone_id] = attempt_count

    status_path = orch_dir(repo) / "status.md"
    handoff_path = orch_dir(repo) / "handoff.md"
    if result["status"] == "passed" and review_result.get("status") == "passed":
        state["current_phase"] = "archive"
        state["next_action"] = "archive"
        status_suffix = "\n## Repair loop\n\n- Automatic repair succeeded and verification/review are now green.\n"
        handoff_suffix = "\n## Repair status\n\n- Verification and review findings were repaired automatically.\n"
    else:
        state["current_phase"] = "blocked"
        state["next_action"] = "resolve blocker"
        state.setdefault("blockers", []).append(
            {
                "milestone_id": milestone_id,
                "reason": "Automatic repair exhausted safe attempts for verification or review findings.",
            }
        )
        status_suffix = "\n## Repair loop\n\n- Automatic repair exhausted safe attempts.\n"
        handoff_suffix = "\n## Repair status\n\n- Next thread should inspect last_verification.json and last_review.json, then continue manually.\n"

    status_path.write_text(read_text(status_path).rstrip() + status_suffix, encoding="utf-8")
    handoff_path.write_text(read_text(handoff_path).rstrip() + handoff_suffix, encoding="utf-8")
    save_json(state_path(repo), state)
    final_status = "passed" if result["status"] == "passed" and review_result.get("status") == "passed" else "failed"
    return {"status": final_status, "attempts": attempts}


def main() -> int:
    parser = argparse.ArgumentParser(description="Attempt safe, local repairs after a verification failure")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--max-attempts", type=int, default=3, help="Repair attempts before blocking")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = run_repair_loop(repo, max_attempts=args.max_attempts)
    print(result["status"])
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
