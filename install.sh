#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install big-project-orchestrator into a repo or user skills directory.

Usage:
  bash install.sh --repo /path/to/repo
  bash install.sh --user
  bash install.sh --target /absolute/path/to/skills/dir

Options:
  --repo PATH    Install into PATH/<skills-dir>/big-project-orchestrator
  --user         Install into the detected personal skills dir
  --target PATH  Install directly into PATH/big-project-orchestrator
  --force        Overwrite an existing installation
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORCE=0
MODE=""
DEST_BASE=""
SKILLS_SUFFIX=""

detect_user_skills_base() {
  if [[ -n "${CODEX_HOME:-}" ]]; then
    printf '%s\n' "${CODEX_HOME%/}/skills"
    return
  fi
  if [[ -d "${HOME}/.codex/skills" ]]; then
    printf '%s\n' "${HOME}/.codex/skills"
    return
  fi
  if [[ -d "${HOME}/.agents/skills" ]]; then
    printf '%s\n' "${HOME}/.agents/skills"
    return
  fi
  printf '%s\n' "${HOME}/.codex/skills"
}

detect_repo_skills_suffix() {
  local user_base
  user_base="$(detect_user_skills_base)"
  case "$user_base" in
    */.agents/skills) printf '.agents/skills\n' ;;
    *) printf '.codex/skills\n' ;;
  esac
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      MODE="repo"
      DEST_BASE="$2"
      shift 2
      ;;
    --user)
      MODE="user"
      DEST_BASE="$(detect_user_skills_base)"
      shift
      ;;
    --target)
      MODE="target"
      DEST_BASE="$2"
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

if [[ -z "$MODE" ]]; then
  usage >&2
  exit 1
fi

if [[ "$MODE" == "repo" ]]; then
  SKILLS_SUFFIX="$(detect_repo_skills_suffix)"
  DEST_BASE="${DEST_BASE%/}/${SKILLS_SUFFIX}"
fi

DEST="${DEST_BASE%/}/big-project-orchestrator"
mkdir -p "$DEST_BASE"

if [[ -e "$DEST" ]]; then
  if [[ "$FORCE" -ne 1 ]]; then
    echo "Destination already exists: $DEST" >&2
    echo "Re-run with --force to overwrite." >&2
    exit 1
  fi
  rm -rf "$DEST"
fi

cp -R "$SCRIPT_DIR" "$DEST"

echo "Installed to: $DEST"
echo "Restart Codex if the skill does not appear immediately."
