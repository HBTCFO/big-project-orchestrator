#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
REPO="$(cd "$REPO" && pwd)"
ORCH="$REPO/.codex/orchestrator"
CUSTOM_SETUP="$ORCH/setup.commands.sh"

log() { printf '[setup] %s\n' "$*"; }
warn() { printf '[setup][warn] %s\n' "$*" >&2; }
run_cmd() {
  local cmd="$1"
  log "run: $cmd"
  (cd "$REPO" && bash -lc "$cmd")
}
have() { command -v "$1" >/dev/null 2>&1; }

has_meaningful_custom_script() {
  local file="$1"
  [[ -f "$file" ]] || return 1
  if grep -q 'BIG_PROJECT_ORCHESTRATOR_PLACEHOLDER=1' "$file"; then
    return 1
  fi
  return 0
}

if has_meaningful_custom_script "$CUSTOM_SETUP"; then
  chmod +x "$CUSTOM_SETUP" || true
  log "using repo-specific setup.commands.sh"
  exec bash "$CUSTOM_SETUP"
fi

# Lightweight autodetection. Prefer repo-specific setup.commands.sh for anything critical.

if [[ -f "$REPO/package.json" ]]; then
  if [[ -f "$REPO/pnpm-lock.yaml" ]] && have pnpm; then
    run_cmd "pnpm install"
    if python3 - <<'PY' "$REPO/package.json"; then
import json, sys
pkg = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
raise SystemExit(0 if 'build' in pkg.get('scripts', {}) else 1)
PY
      run_cmd "pnpm build"
    fi
    exit 0
  elif [[ -f "$REPO/yarn.lock" ]] && have yarn; then
    run_cmd "yarn install"
    if python3 - <<'PY' "$REPO/package.json"; then
import json, sys
pkg = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
raise SystemExit(0 if 'build' in pkg.get('scripts', {}) else 1)
PY
      run_cmd "yarn build"
    fi
    exit 0
  elif have npm; then
    run_cmd "npm install"
    if python3 - <<'PY' "$REPO/package.json"; then
import json, sys
pkg = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
raise SystemExit(0 if 'build' in pkg.get('scripts', {}) else 1)
PY
      run_cmd "npm run build"
    fi
    exit 0
  fi
fi

if [[ -f "$REPO/Cargo.toml" ]] && have cargo; then
  run_cmd "cargo build"
  exit 0
fi

if [[ -f "$REPO/go.mod" ]] && have go; then
  run_cmd "go build ./..."
  exit 0
fi

if [[ -f "$REPO/pyproject.toml" || -f "$REPO/requirements.txt" ]]; then
  if have uv && [[ -f "$REPO/pyproject.toml" ]]; then
    run_cmd "uv sync"
    exit 0
  elif [[ -f "$REPO/requirements.txt" ]] && have python3; then
    run_cmd "python3 -m pip install -r requirements.txt"
    exit 0
  fi
fi

warn "No setup workflow detected. Add $CUSTOM_SETUP for exact worktree bootstrapping."
exit 0
