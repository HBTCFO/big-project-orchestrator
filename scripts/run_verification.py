#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

if __package__ in (None, ""):
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))

from build_project_state import initialize_state
from orchestrator_common import (
    append_history,
    default_verification_plan,
    is_placeholder_verifier,
    last_verification_path,
    load_json,
    orch_dir,
    read_text,
    render_verification_script,
    save_json,
    state_path,
)


def _run(repo: Path, command: str) -> dict:
    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "exit_code": result.returncode,
        "output": (result.stdout + result.stderr).strip(),
        "status": "passed" if result.returncode == 0 else "failed",
    }


def run_verification(repo: Path, generate_custom: bool = False) -> dict:
    state = load_json(state_path(repo)) or initialize_state(repo)
    spec_path = repo / state["input_spec_path"] if state.get("input_spec_path") else None
    spec_text = read_text(spec_path) if spec_path else state.get("goal", "")
    orch = orch_dir(repo)
    custom = orch / "verification.commands.sh"
    plan = default_verification_plan(repo, spec_text, state.get("project_mode", "unknown"))

    if generate_custom and is_placeholder_verifier(custom) and plan["commands"]:
        custom.write_text(render_verification_script(plan["commands"], plan["reason"]), encoding="utf-8")
        custom.chmod(0o755)

    if custom.exists() and not is_placeholder_verifier(custom):
        strategy = "custom"
        commands = [f"bash {custom.relative_to(repo)}"]
    elif plan["commands"]:
        strategy = plan["strategy"]
        commands = plan["commands"]
    else:
        strategy = "bundled"
        commands = [f"bash {Path(__file__).resolve().parent / 'verify_repo.sh'} {repo}"]

    results = [_run(repo, command) for command in commands]
    status = "passed" if all(item["exit_code"] == 0 for item in results) else "failed"
    payload = {
        "status": status,
        "strategy": strategy,
        "commands_run": results,
        "summary": results[-1]["status"] if results else "no_commands",
    }
    save_json(last_verification_path(repo), payload)

    state["verification"] = {
        "status": status,
        "strategy": strategy,
        "last_result_path": str(last_verification_path(repo).relative_to(repo)),
    }
    state["current_phase"] = "archive" if status == "passed" else "repair"
    state["next_action"] = "archive" if status == "passed" else "repair"
    save_json(state_path(repo), state)
    append_history(repo, f"run_verification status={status} strategy={strategy}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repo verification and write a structured result file")
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("--generate-custom", action="store_true", help="Replace placeholder verification.commands.sh when a concrete plan is known")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    result = run_verification(repo, generate_custom=args.generate_custom)
    print(last_verification_path(repo))
    print(f"status={result['status']}")
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
