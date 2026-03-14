#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install repo support files for big-project-orchestrator.

Usage:
  bash scripts/install_repo_templates.sh --repo /path/to/repo [--force]

What it installs:
  - .codex/orchestrator/*
  - .codex/config.toml (if absent, or overwritten with --force)
  - .codex/agents/*.toml
  - AGENTS.md if absent
  - AGENTS.big-project-orchestrator.snippet.md if AGENTS.md already exists
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO=""
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$REPO" ]]; then
  usage >&2
  exit 1
fi

REPO="$(cd "$REPO" && pwd)"
mkdir -p "$REPO/.codex/orchestrator" "$REPO/.codex/agents"

copy_if_absent_or_force() {
  local src="$1"
  local dest="$2"
  if [[ -e "$dest" && "$FORCE" -ne 1 ]]; then
    echo "skip: $dest"
    return
  fi
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
  echo "write: $dest"
}

for file in new_requirements.md current_requirements.md todo.md decisions.md status.md handoff.md review.md verification.commands.sh setup.commands.sh; do
  copy_if_absent_or_force "$SKILL_DIR/assets/templates/$file" "$REPO/.codex/orchestrator/$file"
done

copy_if_absent_or_force "$SKILL_DIR/assets/repo/.codex/config.toml" "$REPO/.codex/config.toml"
for file in explorer.toml reviewer.toml worker.toml monitor.toml; do
  copy_if_absent_or_force "$SKILL_DIR/assets/repo/.codex/agents/$file" "$REPO/.codex/agents/$file"
done

if [[ ! -e "$REPO/.codex/orchestrator/planner_history.txt" || "$FORCE" -eq 1 ]]; then
  : > "$REPO/.codex/orchestrator/planner_history.txt"
  echo "write: $REPO/.codex/orchestrator/planner_history.txt"
fi
if [[ ! -e "$REPO/.codex/orchestrator/state.json" || "$FORCE" -eq 1 ]]; then
  printf '{}\n' > "$REPO/.codex/orchestrator/state.json"
  echo "write: $REPO/.codex/orchestrator/state.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/tracks.json" || "$FORCE" -eq 1 ]]; then
  printf '{"tracks": []}\n' > "$REPO/.codex/orchestrator/tracks.json"
  echo "write: $REPO/.codex/orchestrator/tracks.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/dispatch.json" || "$FORCE" -eq 1 ]]; then
  printf '{"dispatch": []}\n' > "$REPO/.codex/orchestrator/dispatch.json"
  echo "write: $REPO/.codex/orchestrator/dispatch.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/prompts.json" || "$FORCE" -eq 1 ]]; then
  printf '{"prompts": []}\n' > "$REPO/.codex/orchestrator/prompts.json"
  echo "write: $REPO/.codex/orchestrator/prompts.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/track_readiness.json" || "$FORCE" -eq 1 ]]; then
  printf '{"ready_for_merge": false}\n' > "$REPO/.codex/orchestrator/track_readiness.json"
  echo "write: $REPO/.codex/orchestrator/track_readiness.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/track_readiness.md" || "$FORCE" -eq 1 ]]; then
  printf '# Track readiness\n\n' > "$REPO/.codex/orchestrator/track_readiness.md"
  echo "write: $REPO/.codex/orchestrator/track_readiness.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/convergence.json" || "$FORCE" -eq 1 ]]; then
  printf '{"ready_to_converge": false}\n' > "$REPO/.codex/orchestrator/convergence.json"
  echo "write: $REPO/.codex/orchestrator/convergence.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/convergence.md" || "$FORCE" -eq 1 ]]; then
  printf '# Convergence\n\n' > "$REPO/.codex/orchestrator/convergence.md"
  echo "write: $REPO/.codex/orchestrator/convergence.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/merge_report.json" || "$FORCE" -eq 1 ]]; then
  printf '{"ready_for_archive": false}\n' > "$REPO/.codex/orchestrator/merge_report.json"
  echo "write: $REPO/.codex/orchestrator/merge_report.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/merge_report.md" || "$FORCE" -eq 1 ]]; then
  printf '# Merge report\n\n' > "$REPO/.codex/orchestrator/merge_report.md"
  echo "write: $REPO/.codex/orchestrator/merge_report.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/supervisor_report.json" || "$FORCE" -eq 1 ]]; then
  printf '{"next_recommended_action": null}\n' > "$REPO/.codex/orchestrator/supervisor_report.json"
  echo "write: $REPO/.codex/orchestrator/supervisor_report.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/supervisor_report.md" || "$FORCE" -eq 1 ]]; then
  printf '# Supervisor report\n\n' > "$REPO/.codex/orchestrator/supervisor_report.md"
  echo "write: $REPO/.codex/orchestrator/supervisor_report.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/escalation_report.json" || "$FORCE" -eq 1 ]]; then
  printf '{"active_playbook": null}\n' > "$REPO/.codex/orchestrator/escalation_report.json"
  echo "write: $REPO/.codex/orchestrator/escalation_report.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/escalation_report.md" || "$FORCE" -eq 1 ]]; then
  printf '# Escalation report\n\n' > "$REPO/.codex/orchestrator/escalation_report.md"
  echo "write: $REPO/.codex/orchestrator/escalation_report.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/automation_report.json" || "$FORCE" -eq 1 ]]; then
  printf '{"recommended_run_kind": "report_only"}\n' > "$REPO/.codex/orchestrator/automation_report.json"
  echo "write: $REPO/.codex/orchestrator/automation_report.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/automation_report.md" || "$FORCE" -eq 1 ]]; then
  printf '# Automation report\n\n' > "$REPO/.codex/orchestrator/automation_report.md"
  echo "write: $REPO/.codex/orchestrator/automation_report.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/automation_pack.json" || "$FORCE" -eq 1 ]]; then
  printf '{"profiles": []}\n' > "$REPO/.codex/orchestrator/automation_pack.json"
  echo "write: $REPO/.codex/orchestrator/automation_pack.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/automation_pack.md" || "$FORCE" -eq 1 ]]; then
  printf '# Automation pack\n\n' > "$REPO/.codex/orchestrator/automation_pack.md"
  echo "write: $REPO/.codex/orchestrator/automation_pack.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/automation_memory.json" || "$FORCE" -eq 1 ]]; then
  printf '{"registry": [], "recent_runs": []}\n' > "$REPO/.codex/orchestrator/automation_memory.json"
  echo "write: $REPO/.codex/orchestrator/automation_memory.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/automation_memory.md" || "$FORCE" -eq 1 ]]; then
  printf '# Automation memory\n\n' > "$REPO/.codex/orchestrator/automation_memory.md"
  echo "write: $REPO/.codex/orchestrator/automation_memory.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/execution_bridge.json" || "$FORCE" -eq 1 ]]; then
  printf '{"action": null}\n' > "$REPO/.codex/orchestrator/execution_bridge.json"
  echo "write: $REPO/.codex/orchestrator/execution_bridge.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/execution_bridge.md" || "$FORCE" -eq 1 ]]; then
  printf '# Execution bridge\n\n' > "$REPO/.codex/orchestrator/execution_bridge.md"
  echo "write: $REPO/.codex/orchestrator/execution_bridge.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/orchestration_run.json" || "$FORCE" -eq 1 ]]; then
  printf '{"action": null, "executed": false}\n' > "$REPO/.codex/orchestrator/orchestration_run.json"
  echo "write: $REPO/.codex/orchestrator/orchestration_run.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/orchestration_run.md" || "$FORCE" -eq 1 ]]; then
  printf '# Orchestration run\n\n' > "$REPO/.codex/orchestrator/orchestration_run.md"
  echo "write: $REPO/.codex/orchestrator/orchestration_run.md"
fi
if [[ ! -e "$REPO/.codex/orchestrator/validation_report.json" || "$FORCE" -eq 1 ]]; then
  printf '{"errors": [], "warnings": []}\n' > "$REPO/.codex/orchestrator/validation_report.json"
  echo "write: $REPO/.codex/orchestrator/validation_report.json"
fi
if [[ ! -e "$REPO/.codex/orchestrator/validation_report.md" || "$FORCE" -eq 1 ]]; then
  printf '# Validation report\n\n' > "$REPO/.codex/orchestrator/validation_report.md"
  echo "write: $REPO/.codex/orchestrator/validation_report.md"
fi
mkdir -p "$REPO/.codex/orchestrator/completed"
mkdir -p "$REPO/.codex/orchestrator/tracks"
mkdir -p "$REPO/.codex/orchestrator/dispatch"
mkdir -p "$REPO/.codex/orchestrator/prompts"
mkdir -p "$REPO/.codex/orchestrator/convergence"
mkdir -p "$REPO/.codex/orchestrator/automation"

if [[ -e "$REPO/AGENTS.md" ]]; then
  copy_if_absent_or_force "$SKILL_DIR/assets/templates/AGENTS.md" "$REPO/AGENTS.big-project-orchestrator.snippet.md"
else
  copy_if_absent_or_force "$SKILL_DIR/assets/templates/AGENTS.md" "$REPO/AGENTS.md"
fi

echo
echo "Repo support files are ready under: $REPO/.codex/orchestrator"
echo "If you use the Codex app, consider adding this as your worktree setup script:"
echo "  bash .codex/skills/big-project-orchestrator/scripts/setup_workspace.sh "\$PWD""
