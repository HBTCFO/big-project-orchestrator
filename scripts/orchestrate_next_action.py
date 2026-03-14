#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from action_contracts import SAFE_AUTO_ACTIONS
from build_project_state import initialize_state
from generate_execution_bridge import generate_execution_bridge
from validate_orchestrator_state import validate_orchestrator_state
from orchestrator_common import (
    append_decision,
    append_history,
    execution_bridge_path,
    load_json,
    orchestration_run_markdown_path,
    orchestration_run_path,
    save_json,
    state_path,
)
from run_track_supervisor import run_track_supervisor

def _run_command(repo: Path, command: str) -> dict:
    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "exit_code": result.returncode,
        "status": "passed" if result.returncode == 0 else "failed",
        "output": (result.stdout + result.stderr).strip(),
    }


def _preflight(repo: Path, bridge: dict) -> list[dict]:
    checks: list[dict] = []
    for item in bridge.get("inputs", []):
        if item in {"n/a", "track brief missing", "supervisor_report.md"}:
            checks.append({"input": item, "exists": item != "track brief missing"})
            continue
        path = repo / item
        checks.append({"input": item, "exists": path.exists()})
    return checks


def orchestrate_next_action(repo: Path, allow_merge_repair: bool = False, force: bool = False) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    bridge = load_json(execution_bridge_path(repo))
    if not bridge or force:
        bridge = generate_execution_bridge(repo)

    action = bridge.get("action", {})
    action_kind = action.get("kind")
    preflight = _preflight(repo, bridge)
    missing_inputs = [item["input"] for item in preflight if not item["exists"]]
    commands = list(bridge.get("commands", []))
    if action_kind == "run_merge_cycle" and commands and not allow_merge_repair:
        commands = [f'{commands[0]} --no-repair']

    status = "ready"
    executed = False
    needs_human = False
    reason = action.get("reason", "No supervisor recommendation available.")
    command_results: list[dict] = []

    if not bridge.get("ready"):
        status = "blocked"
        reason = "Execution bridge is not ready."
    elif missing_inputs:
        status = "blocked"
        reason = f"Missing required inputs: {', '.join(missing_inputs)}"
    elif action_kind not in SAFE_AUTO_ACTIONS:
        status = "needs_human"
        needs_human = True
        reason = f"Action {action_kind or 'none'} requires manual intervention."
    else:
        command_results = [_run_command(repo, command) for command in commands]
        executed = True
        if all(item["exit_code"] == 0 for item in command_results):
            status = "passed"
            run_track_supervisor(repo)
        else:
            status = "failed"
            reason = "At least one orchestration command failed."

    refreshed_bridge = load_json(execution_bridge_path(repo))
    refreshed_state = load_json(state_path(repo))
    payload = {
        "milestone_id": state.get("current_milestone_id"),
        "action": action,
        "executed": executed,
        "status": status,
        "needs_human": needs_human,
        "reason": reason,
        "preflight": preflight,
        "commands_run": command_results,
        "expected_outputs": bridge.get("expected_outputs", []),
        "bridge_manifest": str(execution_bridge_path(repo).relative_to(repo)),
        "next_bridge_action": refreshed_bridge.get("action", {}).get("kind"),
    }
    save_json(orchestration_run_path(repo), payload)

    lines = [
        "# Orchestration run",
        "",
        f"- Milestone: {payload['milestone_id'] or 'none'}",
        f"- Action: {action_kind or 'none'}",
        f"- Status: {status}",
        f"- Executed: {'yes' if executed else 'no'}",
        f"- Needs human: {'yes' if needs_human else 'no'}",
        f"- Reason: {reason}",
        f"- Bridge manifest: {payload['bridge_manifest']}",
        f"- Next bridge action: {payload['next_bridge_action'] or 'none'}",
        "",
        "## Preflight",
        "",
    ]
    if preflight:
        lines.extend(f"- {'[x]' if item['exists'] else '[ ]'} {item['input']}" for item in preflight)
    else:
        lines.append("- No preflight checks.")
    lines.extend(["", "## Commands run", ""])
    if command_results:
        for item in command_results:
            lines.extend(
                [
                    f"- Status: {item['status']}",
                    f"  Command: `{item['command']}`",
                    f"  Exit code: {item['exit_code']}",
                ]
            )
    else:
        lines.append("- No commands executed.")
    lines.extend(["", "## Expected outputs", ""])
    if payload["expected_outputs"]:
        lines.extend(f"- {item}" for item in payload["expected_outputs"])
    else:
        lines.append("- None.")
    orchestration_run_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    refreshed_state["orchestration_run"] = {
        "status": status,
        "manifest_path": str(orchestration_run_path(repo).relative_to(repo)),
        "action_kind": action_kind,
        "executed": executed,
    }
    refreshed_state["next_action"] = reason if status != "passed" else refreshed_state.get("next_action", "refresh bridge")
    save_json(state_path(repo), refreshed_state)
    validate_orchestrator_state(repo)
    append_history(
        repo,
        f"orchestrate_next_action milestone={payload['milestone_id']} action={action_kind or 'none'} status={status} executed={executed}",
    )
    append_decision(
        repo,
        "Run semi-automatic orchestration step",
        f"Milestone={payload['milestone_id'] or 'none'}",
        f"Action={action_kind or 'none'} status={status} executed={executed}.",
        "Use orchestration_run.md to see whether the next supervisor action was executed or requires human intervention.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute the next supervisor action when it is safe to automate")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--allow-merge-repair", action="store_true", help="Allow repair-enabled merge orchestration instead of forcing --no-repair")
    parser.add_argument("--force-bridge-refresh", action="store_true", help="Regenerate the execution bridge before orchestrating")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = orchestrate_next_action(repo, allow_merge_repair=args.allow_merge_repair, force=args.force_bridge_refresh)
    print(orchestration_run_path(repo))
    print(f"action={(payload['action'].get('kind') or 'none')}")
    print(f"status={payload['status']}")
    return 0 if payload["status"] in {"passed", "needs_human"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
