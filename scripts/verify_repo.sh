#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-.}"
REPO="$(cd "$REPO" && pwd)"
ORCH="$REPO/.codex/orchestrator"
CUSTOM_VERIFY="$ORCH/verification.commands.sh"

log() { printf '[verify] %s\n' "$*"; }
warn() { printf '[verify][warn] %s\n' "$*" >&2; }

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

if has_meaningful_custom_script "$CUSTOM_VERIFY"; then
  log "using repo-specific verification.commands.sh"
  chmod +x "$CUSTOM_VERIFY" || true
  exec bash "$CUSTOM_VERIFY"
fi

detected=0

# Make / Makefile first, because many polyglot repos centralize verification there.
if [[ -f "$REPO/Makefile" ]] && have make; then
  if grep -Eq '^[[:space:]]*verify:' "$REPO/Makefile"; then
    run_cmd "make verify"
    detected=1
  elif grep -Eq '^[[:space:]]*check:' "$REPO/Makefile"; then
    run_cmd "make check"
    detected=1
  elif grep -Eq '^[[:space:]]*test:' "$REPO/Makefile"; then
    run_cmd "make test"
    detected=1
  fi
fi

# Rust
if [[ -f "$REPO/Cargo.toml" ]] && have cargo; then
  log "detected Rust repo"
  if cargo fmt --help >/dev/null 2>&1; then
    run_cmd "cargo fmt --all --check"
  fi
  if cargo clippy -V >/dev/null 2>&1; then
    run_cmd "cargo clippy --all-targets --all-features -- -D warnings"
  fi
  run_cmd "cargo test --all"
  run_cmd "cargo build --all-targets"
  detected=1
fi

# Go
if [[ -f "$REPO/go.mod" ]] && have go; then
  log "detected Go repo"
  run_cmd "go test ./..."
  run_cmd "go build ./..."
  detected=1
fi

# Java / Gradle / Maven
if [[ -x "$REPO/gradlew" ]]; then
  log "detected Gradle repo"
  run_cmd "./gradlew test"
  detected=1
elif [[ -f "$REPO/pom.xml" ]]; then
  if [[ -x "$REPO/mvnw" ]]; then
    log "detected Maven repo"
    run_cmd "./mvnw test"
    detected=1
  elif have mvn; then
    log "detected Maven repo"
    run_cmd "mvn test"
    detected=1
  fi
fi

# Python
if [[ -f "$REPO/pyproject.toml" || -f "$REPO/requirements.txt" || -d "$REPO/tests" ]]; then
  if have python3; then
    log "detected Python repo"
    if have ruff; then
      run_cmd "ruff check ."
    fi
    if have mypy; then
      # mypy may fail in repos without config; still a useful default if present.
      run_cmd "mypy ." || warn "mypy reported issues or needs custom config"
    fi
    if python3 -c "import pytest" >/dev/null 2>&1 || have pytest; then
      run_cmd "python3 -m pytest"
    fi
    run_cmd "python3 -m compileall ."
    detected=1
  fi
fi

# Node.js / TypeScript
if [[ -f "$REPO/package.json" ]]; then
  if have node; then
    log "detected Node/TypeScript repo"
    PKG_MANAGER="npm"
    if [[ -f "$REPO/pnpm-lock.yaml" ]] && have pnpm; then
      PKG_MANAGER="pnpm"
    elif [[ -f "$REPO/yarn.lock" ]] && have yarn; then
      PKG_MANAGER="yarn"
    fi

    mapfile -t SCRIPTS < <(python3 - <<'PY' "$REPO/package.json"
import json, sys
pkg = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
for key in ["lint", "typecheck", "test", "build"]:
    if isinstance(pkg.get("scripts", {}), dict) and key in pkg["scripts"]:
        print(key)
PY
)
    if [[ ${#SCRIPTS[@]} -eq 0 ]]; then
      warn "package.json has no lint/typecheck/test/build scripts; add .codex/orchestrator/verification.commands.sh for this repo"
    else
      for script in "${SCRIPTS[@]}"; do
        case "$PKG_MANAGER" in
          pnpm) run_cmd "pnpm run $script" ;;
          yarn) run_cmd "yarn $script" ;;
          npm) run_cmd "npm run $script" ;;
        esac
      done
      detected=1
    fi
  fi
fi

if [[ "$detected" -eq 0 ]]; then
  warn "No supported repo verifier detected."
  warn "Create $CUSTOM_VERIFY with exact project commands."
  exit 2
fi

log "verification completed"
