#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from action_contracts import SAFE_AUTO_ACTIONS
from build_project_state import initialize_state
from orchestrator_common import (
    append_decision,
    append_history,
    execution_bridge_path,
    load_json,
    orchestration_run_path,
    save_json,
    state_path,
    supervisor_report_path,
    validation_report_markdown_path,
    validation_report_path,
)


def _error(code: str, detail: str) -> dict:
    return {"severity": "error", "code": code, "detail": detail}


def _warning(code: str, detail: str) -> dict:
    return {"severity": "warning", "code": code, "detail": detail}


def validate_orchestrator_state(repo: Path) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    supervisor = load_json(supervisor_report_path(repo))
    bridge = load_json(execution_bridge_path(repo))
    orchestration = load_json(orchestration_run_path(repo))

    findings: list[dict] = []
    next_action = (supervisor.get("next_recommended_action") or {}).get("kind")
    bridge_action = (bridge.get("action") or {}).get("kind")
    orchestration_action = (orchestration.get("action") or {}).get("kind")

    if state.get("supervisor", {}).get("status") == "ready" and not supervisor:
        findings.append(_error("supervisor-manifest-missing", "State says supervisor is ready, but supervisor_report.json is missing or empty."))

    if state.get("execution_bridge", {}).get("status") == "ready" and not bridge:
        findings.append(_error("bridge-manifest-missing", "State says execution bridge is ready, but execution_bridge.json is missing or empty."))

    if supervisor and bridge and next_action != bridge_action:
        findings.append(_error("bridge-action-mismatch", f"Supervisor recommends {next_action or 'none'}, but execution bridge is for {bridge_action or 'none'}."))

    if bridge and bridge.get("ready") and not bridge.get("commands"):
        findings.append(_error("bridge-empty-commands", "Execution bridge is marked ready but has no commands."))

    if bridge and bridge_action in SAFE_AUTO_ACTIONS and not bridge.get("automation_safe", False):
        findings.append(_warning("bridge-safe-flag-missing", f"Bridge action {bridge_action} is safe to automate but automation_safe is false or missing."))

    if bridge and bridge_action not in SAFE_AUTO_ACTIONS and bridge.get("automation_safe", False):
        findings.append(_error("bridge-unsafe-flag", f"Bridge action {bridge_action} is not safe to automate but automation_safe is true."))

    if orchestration and orchestration.get("executed") and orchestration_action not in SAFE_AUTO_ACTIONS:
        findings.append(_error("unsafe-action-executed", f"Unsafe action {orchestration_action or 'none'} was executed automatically."))

    if orchestration and orchestration.get("status") == "passed" and orchestration_action == bridge_action:
        findings.append(_warning("bridge-not-advanced", "Orchestration passed, but the bridge still points at the same action; refresh supervisor state if this is stale."))

    if state.get("orchestration_run", {}).get("status") == "not_run" and orchestration.get("action"):
        findings.append(_warning("state-orchestration-stale", "orchestration_run.json exists, but state does not reflect it."))

    errors = [item for item in findings if item["severity"] == "error"]
    warnings = [item for item in findings if item["severity"] == "warning"]
    payload = {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "warnings": warnings,
        "supervisor_action": next_action,
        "bridge_action": bridge_action,
        "orchestration_action": orchestration_action,
    }
    save_json(validation_report_path(repo), payload)

    lines = [
        "# Validation report",
        "",
        f"- Status: {payload['status']}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        f"- Supervisor action: {next_action or 'none'}",
        f"- Bridge action: {bridge_action or 'none'}",
        f"- Orchestration action: {orchestration_action or 'none'}",
        "",
        "## Findings",
        "",
    ]
    if findings:
        lines.extend(f"- [{item['severity']}] {item['code']}: {item['detail']}" for item in findings)
    else:
        lines.append("- No validation findings.")
    validation_report_markdown_path(repo).write_text("\n".join(lines) + "\n", encoding="utf-8")

    state["validation"] = {
        "status": payload["status"],
        "manifest_path": str(validation_report_path(repo).relative_to(repo)),
        "errors": len(errors),
        "warnings": len(warnings),
    }
    save_json(state_path(repo), state)
    append_history(repo, f"validate_orchestrator_state status={payload['status']} errors={len(errors)} warnings={len(warnings)}")
    append_decision(
        repo,
        "Validate orchestration state invariants",
        "Checked supervisor, execution bridge, and orchestration-run alignment.",
        f"Validation status={payload['status']} with {len(errors)} errors and {len(warnings)} warnings.",
        "Review validation_report.md before starting a real project if any errors remain.",
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate orchestrator state invariants and manifest alignment")
    parser.add_argument("--repo", default=".", help="Repository root")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    payload = validate_orchestrator_state(repo)
    print(validation_report_path(repo))
    print(f"status={payload['status']}")
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
